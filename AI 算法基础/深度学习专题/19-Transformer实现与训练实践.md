# 19｜Transformer实现与训练实践

本章把[注意力与Transformer原理](04-注意力机制与Transformer.md)接成可以独立执行的训练任务：给定符号序列，输出其逆序。它包含encoder、causal decoder、cross-attention、padding、labels移位、验证与逐步生成；**不是语言语料训练，不能据此声称会理解或生成自然语言**。只用CPU和人为生成的短序列，不下载数据/权重。

## 1. 先定义任务、数据划分与正确答案

词表固定为PAD=0、BOS=1、EOS=2及四个内容符号3～6。源内容 `[3,5,4]` 加EOS；目标答案 `[4,5,3,EOS]`。decoder输入是 `[BOS,4,5,3]`，每位置目标右移一位。teacher forcing在训练时给已知先前目标，causal mask仍阻止读取下一个答案。

训练、验证、测试分别从**不同完整序列**取样，不能把同一序列的不同窗口随机放两边。任务字符表是预先定义的输入合同，没有从测试集fit词表；真实语料Tokenization必须按训练/预训练配置处理，[文本与Tokenizer](../../LLM%20基础/02-文本-Tokenizer与Embedding.md)维护这一关系。未见字/符号、空源、超长序列必须有显式处理。

验证loss计算所有有效target位置的交叉熵总和除有效token总数，忽略PAD；不用不等长batch的平均loss再等权平均。PPL=$e^{NLL}$只在同一词表/切分/EOS协议比较，符号逆序PPL不能与英语字符或BPE PPL比较。

## 2. 本实现的结构与边界

Encoder用双向self-attention+FFN，decoder每层用causal self-attention、cross-attention和FFN。这里选pre-LayerNorm、ReLU FFN、正弦PE、无dropout、两层encoder与两层decoder；这些是明确的教学选择，不因没有RMSNorm/SwiGLU/RoPE就判错误。

模型输入 `B×T` int64，Embedding输出 `B×T×D`。各attention使用True=允许的自定义bool mask；encoder/cross键过滤源PAD，decoder键过滤目标PAD并带因果三角。每个attention行至少有一个有效键；源有EOS、目标以BOS开头。各层后把无效query状态清零，避免它进入后续聚合。输出 logits为 `B×T_target×V`，cross熵接**未做softmax**的logits。

pre-norm堆叠末尾再Norm；Encoder最后的Norm输出仍用于cross K/V。源与目标使用共同输入Embedding（符号任务同词表），输出头独立；权重绑定是另一种可选设计，下节解释，不能暗中把两种参数计数混写。

### 2.1 完整CPU训练、验证和生成程序

程序固定seed、单线程、小维度，步数500是实验预算，不是保证达到某成绩的阈值。生成不使用真答案、不调用随机数据下载，也没有KV缓存；为清楚展示，每次重算前缀。测试集只在训练结束读出一次结果。

```python
import math
import random
from itertools import product
import torch
from torch import nn
import torch.nn.functional as F

torch.set_num_threads(1);torch.manual_seed(7)
PAD,BOS,EOS,V,D,H=0,1,2,7,32,4
MAX_LEN=8
class Attention(nn.Module):
    def __init__(self,d=D,heads=H):
        super().__init__()
        if heads<1 or d%heads:raise ValueError('维度能被正头数整除')
        self.h=heads;self.dh=d//heads
        self.q=nn.Linear(d,d,bias=False);self.k=nn.Linear(d,d,bias=False)
        self.v=nn.Linear(d,d,bias=False);self.o=nn.Linear(d,d,bias=False)
    def forward(self,x,memory,allowed):
        B,T,d=x.shape;S=memory.shape[1]
        if memory.shape[0]!=B or memory.shape[2]!=d or allowed.shape!=(B,T,S) or allowed.dtype!=torch.bool or not allowed.any(-1).all():
            raise ValueError('batch/宽度/mask及非全遮罩合同')
        shape=lambda a,n:a.reshape(B,n,self.h,self.dh).transpose(1,2)
        q,k,v=shape(self.q(x),T),shape(self.k(memory),S),shape(self.v(memory),S)
        score=(q@k.transpose(-2,-1))/math.sqrt(self.dh)
        p=torch.softmax(score.masked_fill(~allowed[:,None,:,:],-torch.inf),dim=-1)
        y=(p@v).transpose(1,2).contiguous().reshape(B,T,d)
        return self.o(y)
class EncoderLayer(nn.Module):
    def __init__(self):
        super().__init__();self.att=Attention()
        self.n1=nn.LayerNorm(D);self.n2=nn.LayerNorm(D)
        self.ff=nn.Sequential(nn.Linear(D,64),nn.ReLU(),nn.Linear(64,D))
    def forward(self,x,valid):
        mask=valid[:,None,:].expand(-1,x.shape[1],-1)
        h=self.n1(x);x=x+self.att(h,h,mask)
        x=x*valid[:,:,None]
        return (x+self.ff(self.n2(x)))*valid[:,:,None]
class DecoderLayer(nn.Module):
    def __init__(self):
        super().__init__();self.selfatt=Attention();self.cross=Attention()
        self.norm=nn.ModuleList([nn.LayerNorm(D) for _ in range(3)])
        self.ff=nn.Sequential(nn.Linear(D,64),nn.ReLU(),nn.Linear(64,D))
    def forward(self,x,memory,valid,source_valid):
        T=x.shape[1];causal=torch.tril(torch.ones(T,T,dtype=torch.bool,device=x.device))
        mask=causal[None,:,:]&valid[:,None,:]
        h=self.norm[0](x);x=(x+self.selfatt(h,h,mask))*valid[:,:,None]
        crossmask=source_valid[:,None,:].expand(-1,T,-1)
        x=(x+self.cross(self.norm[1](x),memory,crossmask))*valid[:,:,None]
        return (x+self.ff(self.norm[2](x)))*valid[:,:,None]
class Transformer(nn.Module):
    def __init__(self):
        super().__init__();self.embed=nn.Embedding(V,D,padding_idx=PAD)
        nn.init.normal_(self.embed.weight,std=.05)
        with torch.no_grad():self.embed.weight[PAD].zero_()
        p=torch.arange(MAX_LEN)[:,None];freq=torch.exp(-torch.arange(0,D,2)*math.log(10000.)/D)
        pe=torch.empty(MAX_LEN,D);pe[:,0::2]=torch.sin(p*freq);pe[:,1::2]=torch.cos(p*freq)
        self.register_buffer('pe',pe)
        self.enc=nn.ModuleList([EncoderLayer() for _ in range(2)])
        self.dec=nn.ModuleList([DecoderLayer() for _ in range(2)])
        self.enorm=nn.LayerNorm(D);self.dnorm=nn.LayerNorm(D);self.head=nn.Linear(D,V,bias=False)
    def check(self,ids):
        if ids.ndim!=2 or ids.shape[0]<1 or not 1<=ids.shape[1]<=MAX_LEN or ids.dtype!=torch.int64 or (ids<0).any() or (ids>=V).any():
            raise ValueError('B×T非空合法int64 ID与表长')
        if not (ids!=PAD).any(-1).all():raise ValueError('不能全PAD')
    def forward(self,src,tgt):
        self.check(src);self.check(tgt)
        if src.shape[0]!=tgt.shape[0] or not (tgt[:,0]==BOS).all():raise ValueError('同batch与目标BOS开头')
        sv,tv=src!=PAD,tgt!=PAD
        x=(self.embed(src)*math.sqrt(D)+self.pe[:src.shape[1]])*sv[:,:,None]
        for layer in self.enc:x=layer(x,sv)
        memory=self.enorm(x)*sv[:,:,None]
        y=(self.embed(tgt)*math.sqrt(D)+self.pe[:tgt.shape[1]])*tv[:,:,None]
        for layer in self.dec:y=layer(y,memory,tv,sv)
        return self.head(self.dnorm(y))

def batch(sequences):
    if not sequences or any(not 1<=len(s)<=MAX_LEN-2 or any(type(w) is not int or not 3<=w<V for w in s) for s in sequences):
        raise ValueError('非空内容序列，禁止结构ID，预留BOS/EOS')
    source=[list(s)+[EOS] for s in sequences]
    answer=[list(reversed(s))+[EOS] for s in sequences]
    inputs=[[BOS]+a[:-1] for a in answer]
    pad=lambda rows:torch.tensor([row+[PAD]*(max(map(len,rows))-len(row)) for row in rows],dtype=torch.long)
    return pad(source),pad(inputs),pad(answer)

def evaluation(model,sequences):
    model.eval();total=0.;n=0;correct=0
    with torch.no_grad():
        for i in range(0,len(sequences),16):
            src,inp,y=batch(sequences[i:i+16]);logits=model(src,inp)
            total+=F.cross_entropy(logits.reshape(-1,V),y.reshape(-1),ignore_index=PAD,reduction='sum').item()
            active=y!=PAD;n+=int(active.sum());correct+=int(((logits.argmax(-1)==y)&active).sum())
    if n==0:raise ValueError('没有评测token')
    return total/n,correct/n

@torch.no_grad()
def generate(model,sequence,max_new=7):
    model.eval();src,_,_=batch([sequence]);inp=torch.tensor([[BOS]])
    out=[]
    for _ in range(max_new):
        if inp.shape[1]>MAX_LEN:break
        logits=model(src,inp)[0,-1].clone();logits[[PAD,BOS]]=-torch.inf
        token=int(logits.argmax())
        if token==EOS:return out,True
        out.append(token);inp=torch.cat([inp,torch.tensor([[token]])],dim=1)
    return out,False

# 不同完整序列分组，默认长度2..5；长长度泛化另行评测，不冒称通过。
pool=[s for n in range(2,6) for s in product(range(3,V),repeat=n)]
rng=random.Random(12);rng.shuffle(pool);train,val,test=pool[:256],pool[256:320],pool[320:384]
assert not(set(train)&set(val) or set(train)&set(test) or set(val)&set(test))
model=Transformer();baseline,_=evaluation(model,val)
# 未来目标改动不能影响prefix；源后补PAD不能影响相同有效结果。
src,inp,y=batch([train[0],train[1]])
with torch.no_grad():
    original=model(src,inp);changed=inp.clone();changed[:,-1]=3+(changed[:,-1]%4)
    assert torch.allclose(original[:,:-1],model(src,changed)[:,:-1],atol=1e-6)
    if src.shape[1]+1<=MAX_LEN:
        padded=torch.cat([src,torch.zeros(len(src),1,dtype=torch.long)],dim=1)
        assert torch.allclose(original,model(padded,inp),atol=1e-6)
opt=torch.optim.AdamW(model.parameters(),lr=.003,weight_decay=.01)
STEPS=500;history=[]
for step in range(STEPS):
    model.train();src,inp,y=batch(rng.sample(train,32))
    # 简单warmup+cosine，本预算已明确；不是固定配置必须用此调度。
    warm=20;ratio=(step+1)/warm if step<warm else .1+.9*.5*(1+math.cos(math.pi*(step-warm)/(STEPS-warm)))
    for group in opt.param_groups:group['lr']=.003*ratio
    logits=model(src,inp);loss=F.cross_entropy(logits.reshape(-1,V),y.reshape(-1),ignore_index=PAD)
    opt.zero_grad(set_to_none=True);loss.backward()
    norm=nn.utils.clip_grad_norm_(model.parameters(),1.)
    if not torch.isfinite(norm):raise ValueError('非有限梯度应中止/检查，不能clip掩盖')
    opt.step()
    if step in [0,99,249,499]:
        vl,acc=evaluation(model,val);history.append((step+1,float(loss.detach()),vl,acc))
        print('step/trainNLL/valNLL/teacher-token-acc',history[-1])
final,teacher_acc=evaluation(model,val);assert math.isfinite(final) and final<baseline
# 完整生成exact-match要求内容逆序且正常EOS，区别于teacher-token accuracy。
hits=0
for s in test:
    got,ended=generate(model,s);hits+=int(ended and got==list(reversed(s)))
print('参数',sum(p.numel() for p in model.parameters()),'验证初始/最终NLL',baseline,final)
print('测试生成完整匹配',hits,'/',len(test))
for s in test[:3]:print('源/真答案/生成',s,list(reversed(s)),generate(model,s))
```

2026-10-05在记录的Python3.12/PyTorch2.14.1 CPU环境运行：42560参数，验证NLL约2.41974→0.001079，独立测试64/64完整生成且EOS正常结束。这个结果只对应固定seed、长度2～5和四符号逆序任务，不承担其他seed、长度或语言数据的保证。

观察输出时，先看验证NLL是否下降，再区分teacher-forced token准确率与从BOS开始的整句生成匹配。后者会放大早期错误；训练loss低不能替代它。当前程序只评同长度范围的独立符号组合，没验证长序列、自然语言或真实部署。生成到上限但未EOS会返回`False`，不能把截断叫正常结束。

## 3. Weight tying、优化与参数估计

decoder LM可把输出权重与输入Embedding共享。输入表 $E\in\mathbb R^{V×D}$，输出logits $hE^T$，不能再单独计一份VD输出矩阵；但padding_idx只抑制lookup路径梯度，共享输出路径可能更新该行。共享并不自动提升所有任务，源/目标词表不同也不能直接绑定。

```python
import torch
from torch import nn
torch.manual_seed(2)
V,D=7,8
embedding=nn.Embedding(V,D);head=nn.Linear(D,V,bias=False)
head.weight=embedding.weight
assert head.weight is embedding.weight
# 两路径共用一个Parameter，不能在optimizer列表里重复登记。
params=list(dict.fromkeys(list(embedding.parameters())+list(head.parameters())))
assert len(params)==1 and params[0].numel()==V*D
ids=torch.tensor([[3,4]]);h=embedding(ids);logits=head(h)
loss=nn.functional.cross_entropy(logits.reshape(-1,V),torch.tensor([4,2]));loss.backward()
assert embedding.weight.grad is not None and torch.isfinite(embedding.weight.grad).all()
print('共享参数',V*D,'logits形状',tuple(logits.shape),'两路径合并梯度通过')
```

RMSNorm若只含一个D维gamma，最后Norm参数就是D，不是2D。Source第14课估计函数的final额外算了D；同时它估计默认4层D128/block128，实际训练是3层D64/block64，所以不能拿preview行当实际模型参数。用配置、真实模型 `.parameters()` 和各项手算核对，是否bias、tied、可学PE或sinusoidalbuffer分别标注。

AdamW的decoupled weight decay与把L2直接加loss并不对任意optimizer等价。warmup/余弦LR、梯度裁剪、bf16是可选训练方法：clip限制梯度范数，不保证无爆炸或修复NaN；autocast的设备支持、归一/累加精度、optimizer state与loss稳定需核验。CPU小例采用fp32，不假称用了bf16或GPU。

可复现实验至少保存Tokenizer/词表、特殊ID、结构/位置/mask配置、seed、数据划分、模型/optimizer状态、步数、精度与验证协议。若保存checkpoint供继续训练，还要保存调度步数/RNG，加载后确认参数和配置一致；不能只存模型权重就保证续跑同轨迹。本次临时运行记录保存代码SHA与真实输出，不向仓库提交权重。

## 4. 原capstone实际提供什么，哪些尚未执行

固定来源第14课main实际：内置Shakespeare短节选或读取本地文件，按Python字符建立词表；3层、4头、D64、context64、batch16、500步；pre-RMSNorm+SwiGLU、learned absolute position、手写全注意力、tied输出、AdamW固定LR、clip1，随机窗口train/val，top-k采样。没有GPTConfig、下载器、SDPA/Flash、bf16 autocast、余弦LR或top-p采样。它选设备可能自动选MPS/GPU，本批只允CPU，原运行如受控改配置需单独记，不把修改版当原字节main。

ASCII节选里的字符恰可与字节数重合，但一般Python字符词表是Unicode码点，不是byte级。词表从全部文本建立会使用验证字符集合，是否作为允许的固定字母表需说明；无资源下载不等代码真的训练了完整tinyshakespeare。验证段短于context+1时窗口采样要拒绝或减窗；它每次仅取随机验证batch，不是全验证集稳定loss。

改变Tokenizer不只是词表扩大。`cl100k_base`不是约50k的词表，具体编码/特殊ID需要查配套定义，而不是复制型号表。词表扩大增加Embedding/输出头参数与计算，但不能推出固定容量升级就得到流利英文。源“10Btoken单A10024小时”、固定M2六分钟、val<2.0或<2.5必合格均不作为本仓库事实。

## 5. 生成、缓存与训练扩展怎样验收

温度>0时logits/T改变分布，top-k与top-p是不同截断：前者保k个最高分，后者按概率累积到p。把生成截到最近context窗口会改变位置/可见历史，learned absolute位置若重置不能与“无限上下文”混称。KV缓存保存已有token的K/V，需位置偏移、cache长度、mask、dtype/模型一致；用同一前缀比较无缓存与缓存logits，再谈延迟。源码没有cache，不能承诺加上就必快5–20倍。

Attention/position/norm/FFN替换应先用小fixture校验形状、泄漏、梯度和缓存一致，再在同划分/步数/参数或计算预算对照。RMSNorm+SwiGLU+RoPE不保证一百步loss更低；ALiBi与RoPE的长长度效果须额外训练/测试，不把共同位移恒等式当长度泛化证据。

多token预测可增加一个辅助head预测位置t+2，构造移两位标签并mask掉不足的尾部；这是MTP思想的教学简化，不复刻某研究模型全部顺序预测模块。主loss与辅助loss系数要明确，不让模型在推理时读取真实未来token。检验主任务验证/生成是否改善，不能只报告新增loss下降。

MoE用router选部分专家FFN，需容量、路由、负载与梯度处理，不等于增加四个模块就让“active参数相同”；对照总参数、每token激活参数、实际FLOPs和吞吐。原5项capstone开放练习保留如下判断标准，不因外部数据/长训练未做就编造答案。

## 6. 练习参考答案与运行边界

1. 源capstone的val阈值是否保证？不保证，取决于数据、tokenizer、模型、步数和验证采样。先复现真实配置与整个验证协议，增加步数需防过拟合；本章符号逆序的NLL/整句匹配实测，不与tinyshakespeare阈值混用。
2. 把learned PE换RoPE：在各头Q/K旋转，去掉原输入位置表，cache位置同步；固定其他预算比较验证与长长度，不能预设至少一样好。
3. 添加缓存：先逐token核对cached/uncached logits、位置和因果可见范围，再预热/设备同步测生成时间；本章默认无缓存，不跑GPU500token基准。
4. 第二预测head：t+2标签与尾部mask、辅助系数明确；单head的教学MTP-like不等论文全部模块，同主任务评价是否获益。
5. 四专家top2：路由/容量/负载预算记录，按active参数和实际计算对照；原MoE消融本次未执行，不给预定收益。
6. 能把逆序任务成功说成“学会语言”吗？不能。训练/验证/测试完整序列不重叠，只说明同范围组合任务；自然语言能力需要另一个数据与评测协议。

## 来源与核验

- 固定[ai-engineering-from-scratch](https://github.com/rohitg00/ai-engineering-from-scratch/tree/3be078b37ffd8f0c04953c0678e48f5c6d0c7775)，Phase07第05、14课与核心注意力实现；原始读取2026-10-04，整理核验2026-10-05。
- 一手依据：[Transformer论文](https://arxiv.org/abs/1706.03762)、[PyTorch Transformer](https://docs.pytorch.org/docs/stable/generated/torch.nn.Transformer.html)、[SDPA](https://docs.pytorch.org/docs/stable/generated/torch.nn.functional.scaled_dot_product_attention.html)。本程序保留教学简化和原配置差异，不把随机前向、源样本文字或硬编码速度当已验证实绩。
- 后续中文维护提示：改输入/输出/位置/mask或训练数据后，重跑因果与padding不变性、labels移位、token加权验证和独立生成；保留初始与当前核验日期，标明CPU合成/原程序受控范围/外部实验未做，不重复建立来源课程目录。
