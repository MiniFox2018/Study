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


## 7. Decoder-only构件：形状检查与行为证据

本章既有程序是完整encoder-decoder逆序任务，保留其CPU结果和代码。Phase19第33～35课另用decoder-only骨架：ID→token和learned position→N个pre-LN块→final norm→vocab logits。它与encoder-decoder的cross-attention、任务数据不同；共享输入表、输出绑定、norm和mask均按实际结构说明，不能把一个任务的成绩迁成自然语言能力。

### 7.1 多头矩阵、掩码与检查用权重

对D维输入、H个等宽head、Dh=D/H，fused QKV把(B,T,D)投成(B,T,3D)，按约定切Q/K/V，再view为(B,T,H,Dh)、transpose成(B,H,T,Dh)。Q乘K的末两维转置并除sqrt(Dh)，分数为(B,H,T,T)。fullsequence因果mask允许对角与过去，未来填-inf，沿key轴softmax，weights乘V，再transpose／contiguous合并为(B,T,D)，最后输出投影混合heads。已有第2.1程序核shape、无全遮罩和padding，不在这里复制MHA。

fused在同宽度与堆叠顺序下等价三个projection，不少参数、不共用Q/K/V权重；launch减少是否更快依后端/shape。MQA/GQA的KV head宽度可不同，不能硬套3D。scaled dotproduct的方差解释依分量与初始化假设；混合精度点积、softmax、全masked行和有效mask仍需独立检查。cache多token时Q、K长度与绝对位置不同，不能直接取左上方阵；[推理合同](../../LLM%20工程实践/14-Transformer推理与规模设计.md)统一维护。

返回weights时明确它是softmax概率还是dropout后值。训练attention dropout会让某些权重归0并放大其余，行和不必1；第33课测试p=0/eval时的row sum不能套到p>0。repeat fixture每行一个token重复，当前token本身就等于nexttarget，不需要向前看即可解；loss降与热图变化不证明heads形成语义专门化，热图也不是因果解释。原16个测试定义核指定shape、future不变性、梯度与toy训练，未实跑。

### 7.2 pre/post-LN、MLP与梯度对照的条件

pre-LN为`u=x+Attention(LN1(x)); y=u+MLP(LN2(u))`；post-LN为`u=LN1(x+Attention(x)); y=LN2(u+MLP(u))`。前者保留未经norm的identity路径，后者让该路径经过norm。但是否需要warmup、哪些LR稳定必须用真正任务loss及训练轨迹比较，pre-LN不能成为无条件去掉warmup的承诺。

源第34课实际只建6层、复制同weights、关闭dropout、做单次平方输出loss的backward，没有learning rate／optimizer。两stack最后都有LayerNorm，初始gamma1/beta0时每token输出平方和为`D*v/(v+eps)`，v为输入人口方差，几乎是D常量；gradient ratio主要受eps和方差影响，不是12层任务训练实验。应使用相同初始化、数据、任务loss、更新预算、多个seed和梯度分布／验证质量去检验假设。本章原CE逆序程序是可复用的有效训练例，未改其结果。

LayerNorm用最后维度人口方差（PyTorch的unbiased=False），epsilon加在方差内再sqrt，gamma/beta各D。RMSNorm不减均值，常只一项gamma，shape不变也不数值等价。源std测试默认样本标准差与人口var不同；D64时可约1.0079，并不精确1。4D的GELU MLP是此配置，SwiGLU还需要门控与另一个投影，仅把GELU换SiLU不等Llama骨架。

dropout应分清identity与分支。第34～35代码实际有attention weights、attention输出residual update、MLP update三处，不是文案“两处不是三处”；不能drop整个identity后仍声称原梯度路径未变。原10个测试定义只核指定前向与梯度，不证明每个现代模型都pre-LN、fused、无bias或不需要warmup。

### 第33课的实践核对与中文自检

本课图示的含义与边界：QKV投影D→3D与H分头说明形状；专门化并非训练必然结果，causal/scale/softmax条件和dropout后行和另讲。本组课内没有独立SVG，实际注册的动态示意由统一记录静态核对，未执行网页或来源JS。

原非编号改参练习：保持D=32，把H从4改成8，Dh由8变4；QKV和输出投影参数量不因此改变，但head维度的score存储会增加。比较同输入的shape、因果性与数值，再另测任务效果；热图变了不是语义专门化证据。

1. **fused QKV为什么与三投影等价？** 同宽度与切分顺序下，fused矩阵就是堆叠三个投影，数学输出等价，不少参数也不强迫QKV共权。是否更快需测backend，GQA还可能有不同KV宽度。

2. **D、H和Dh怎样约束？** 等宽MHA使用Dh=D/H并要求D可整除H。MQA／GQA另有KV head数量，不能照搬这个完整形状。

3. **缩放用哪个维度？** 除sqrt(Dh)能在常见分量假设下改善dotproduct尺度，但并不免除激活、混合精度溢出和softmax有限值检查。

4. **未来位置怎样被遮住？** fullsequence score在softmax前把未来上三角填-inf。padding、全遮罩行及cache绝对位置另核，不能以一个方阵覆盖所有输入合同。

5. **输出投影做什么？** heads汇聚后输出线性投影混合其特征，并保持(B,T,D)。它与用于汇聚V的attention weights是不同对象。

6. **热图和returned weights意味着什么？** 每行表示该query使用哪些key位置。本例返回dropout后的权重，训练时行和不必1；repeat任务看当前token已能解，热图不能证明head语义专门化或因果解释。

### 第34课的实践核对与中文自检

本课图示的含义与边界：preLN残差加法需同形状；norm在计算分支内，无需warmup并非无条件保证，图第二残差add省略，不证明实际训练稳定。本组课内没有独立SVG，实际注册的动态示意由统一记录静态核对，未执行网页或来源JS。

原编号练习的验收方式：

1. **去掉线性层bias，怎样核参数节省？** 将QKV、attention输出以及MLP的两层线性投影设为无bias，其他配置和初始化条件保持一致，再分别手算并检查实际Parameter数。每块少3D+D+4D+D=9D个线性bias，12层、D=768共少82,944个；LayerNorm的shift不属于这些线性bias，若同时去掉，应另列节省量。参数少不自动表示准确率更好。

2. **把LayerNorm换成RMSNorm，怎样验证？** 实现x/sqrt(mean(x²)+eps)再乘gamma，不减均值；保留相同输入／输出形状，并明确是否有beta。先核零向量、有限值、数值结果和梯度，再在同任务与预算下比较训练表现。仅证明shape不变，不能证明与LayerNorm等价或更稳定。

3. **输出第一head权重时，怎样检查因果性？** 取softmax之后、dropout之前的权重，或在eval且dropout关闭时检查：未来上三角为0，每个有有效key的行和约为1。返回值应为(B,T,T)，注明取的是哪个head。若取训练时dropout之后的权重，行和可以不为1，不要把它误判成softmax错误。

4. **相同权重的pre/post-LN前向应怎样对照？** 使用同一组参数、同一个(2,16,384)输入、H=6，并关闭dropout；这样Dh=64。分别运行两种norm位置，核输出shape一致，再比较数值是否不同。差异说明两条计算路径不同，不说明哪个训练更好，也不能替代warmup实验。

1. **一个本文decoder块由什么组成？** 本文decoder块由causalattention和position-wise MLP组成，各有residual与norm。现代架构可以改变门控、norm和布局，不能将本例当唯一形式。

2. **pre/post-LN怎样影响梯度，能否据此去掉warmup？** pre-LN的identity路径不经过该norm，post-LN让它经过，因而梯度路径不同。源只有6层单次平方loss、没有LR／optimizer，finalLN又使该loss近常数，不能据此证明12层稳定或取消warmup。

3. **因果掩码先于还是后于softmax？** 先把未来score设-inf，再沿key做softmax；同时核labels移位和文档／padding政策。源码顺序比示意文字更可靠。

4. **fused一定在所有硬件更快吗？** 同数学条件下fused可能减少launch，但速度依硬件／shape／backend；不能称每个accelerator必快，或所有Llama都用同样fused布局。

5. **残差和dropout如何放置？** 为了维持本文identity路径，dropout放在明确的分支更新中。源码实际有weights、attention输出和MLP输出三处，源“两处”表述不符。

6. **为什么把mask注册成buffer？** buffer可随module搬设备并复用mask，减少某些分配。仍要核T²存储、cache位置和persistent=False后的恢复，不能理解为零代价。

## 8. GPT尺寸、绑定与生成的可核对账本

本文GPT2式布局取V词表、D宽度、L位置、N层，bias打开、MLP4D、每块两LayerNorm、最终LayerNorm且输出head共享token表。参数账为`VD+LD+N*(12D²+13D)+2D`：每块attention4D²、MLP8D²；线性bias9D与两norm的scale/shift4D合成13D。V50257/D768/L1024/N12得124439808，取消绑定增加38597376，固定sin替learned表减少786432。参数数吻合只是一部分结构证据，不保证权重映射、forward语义和模型能力。

共享要在Parameter层绑定，optimizer只收一份、反传合并两路径；第3节已有实跑探针。复制相同值不是共享，保存alias需按checkpoint格式处理。初始化0.02及residual输出再除sqrt(2N)是GPT2式选择，不是所有模型的强制参数；N与D/H等构造值先核合法，不能让0层在缩放处除0。

生成取最后位置logits，finite正temperature下除T，按top-k或top-p筛候选，再softmax／采样。源第35课threshold top-k遇同分可能留超过k，k=1也可能随机选多个并列项；greedy应明确argmax及tie规则。对重复token的penalty>1，负logit要乘、正logit要除，统一除会抬高负logit并奖励重复；这不是概率的乘法规则。top-p按排序后的概率累计，保留跨过阈值的项且至少留一个，p的边界、ties及所有项被filter的情况明确。[固定HF生成实现](https://github.com/huggingface/transformers/blob/55c3cc9f03cd4fbf2d27d382dcc8fcc544631f8e/src/transformers/generation/logits_process.py)仅选读这些处理器范围，未运行现成模型。

源generate用eval/no_grad、finally恢复整个model mode，并裁lastcontext再令learned positions从0开始；它没有KV cache或EOS终态协议。有效prompt、max_new_tokens、topK和temperature的类型/范围必须明确，NaN/inf和空prompt不能当正常结果。全局manual_seed会影响别的调用，真实并发应用用可控request-local RNG并记录设备/库条件；不能从一次同seed结果推出跨硬件完全一致。

### 第35课的实践核对与中文自检

本课图示的含义与边界：12blocks/124M/绑定head为特定GPT2示意，不能认定源码默认共享参数；独立head多VD，要核实际对象与state。本课已核GPTConfig的weight_tying默认True；实际绑定对象的证据来自源码与对应合同，不来自动画。本组课内没有独立SVG，实际注册的动态示意由统一记录静态核对，未执行网页或来源JS。

原编号练习的验收方式：

1. **取消输出head绑定后，怎样确认参数差？** 保留同一V、D、层数和其他配置，分别构造共享与独立head，确认前者是同一个Parameter，后者是两个独立对象。差应为V×D=50,257×768=38,597,376；optimizer也应按对象身份去重。数值复制相等或data_ptr一次相等，都不替代完整绑定合同。

2. **用固定sin位置表替换learned表，应检查什么？** 构造相同D和可用位置长度的正弦表，确认前向shape与位置政策一致，并检查它作为buffer的设备、dtype和恢复配置。参数数应少L×D=1024×768=786,432。生成或验证效果需另测，少参数不证明性能保持。

3. **增加greedy解码后，怎样核确定性？** 增加明确的argmax分支，关闭采样，并说明同分时选哪个ID；模型置eval，保持输入、配置、库和设备相同后比较输出。它不依赖采样seed，但设备算子和执行环境仍可能有差异，不能由同机器两次相同推广为跨平台bitwise保证。

4. **重复惩罚怎样处理正负logit？** 先按约定收集prompt及生成历史中的重复token ID，每个ID处理一次。penalty大于1时，正logit除以penalty、负logit乘以penalty，避免把负值统一相除后反而抬高分数；是否排除prompt也要固定。用同输入和解码预算比较重复率与完整性，一次样本变化不能保证普遍减少重复。

5. **top-p应怎样截断并验收？** 每个batch行分别按概率从高到低排序，累加到指定p，保留首次达到或跨过阈值的项，并至少保留一个可采样token，再对保留项重新归一。检查p的范围、非有限值和同分规则。不要只验证总和超过p，还应查是否误多留或误删第一项。

1. **124M尺寸是否证明模型正确？** 所列GPT2-small配置在本实现账本上是124,439,808参数。数量吻合只证明部分尺寸一致，不证明权重映射、attention语义或语言质量正确。

2. **真正共享与数值copy有什么区别？** 共享是同一个Parameter服务lookup和输出，反传合并且optimizer只列一次。复制数值相同不是共享；独立head多38,597,376参数。

3. **裁到lastcontext怎样影响位置？** 每步只送lastctx，但返回可保完整历史。learned位置每个窗口重置是此实现政策，不等RoPE缓存的绝对位置或无限上下文。

4. **residual输出初始化为什么缩小？** GPT2式配置把两个residual输出权重除sqrt(2N)，旨在控制初始化尺度。真实稳定性仍需训练证据，N=0等错误配置先拒绝。

5. **温度有什么前提？** finite正温度下logits/T改变尖锐程度；T=0使用明确greedy分支。NaN、inf或负值不能混入正常采样，同seed也只在相同执行合同下复现。

6. **top-k在同分时是否恰留k项？** 按kth值设阈值，ties可能留下超过k个候选，k=1也可能不是单一argmax。固定阈值同分政策或确选k项，再核采样集合。

## 9. 训练迭代、验证采样与恢复分别记录

一更新的顺序是：取版本固定的x/y和有效mask→设当前LR→zero_grad→model train forward与CE→backward→检查finite／必要时clip→optimizer step→持久记录。验证关闭dropout和grad，不改变weights；用有效target的NLL总和/总数作全局归约。第36课固定同B/T且无mask时batch均值可比，但迁移成不等长或response-only样本时不能继续等权平均batch loss。

源`make_batches`在valid starts上随机有放回采样，不是第31课的无放回DataLoader。每次probe重建固定seed的val generator而取相同随机窗口，并非script开头固定一次全部slice；`evaluate_model`在for loop拿下一batch后才查上限，会多消耗一次，0上限／空流返回0也不属于有效验证。模式恢复须放finally，generation和eval失败不应使后续训练悄悄保持eval。

LR函数step0是max/W，stepW-1与W都可能为max，最后stepN-1未恰到min；源test在循环之外step=N检查floor。不要只凭图写“从0到最后正好min”。clip限制梯度范数，不修NaN／无保证安全更新；AMP先unscale，decay/no-decay参数组核唯一且覆盖所有可学Parameter。norm/bias不decay是可比较的策略，不是放了decay就一定损坏的定理。

最重要的源码反证是原80行`outputs/losses.jsonl`：train NLL从5.56095到1.07352，val四次约6.57827、7.53464、7.31514、7.49094。train/val还使用不同32周期base与10%噪声分布，可能同时包含拟合与分布差异；不能写“验证显著变好”。这是上游产物静读，没有本轮运行环境证明或真实文本质量成绩。

JSONL可供检查，但不是恢复状态。源train会unlink旧log；只读last step也恢复不了weights、optimizer moments、LR globalstep、RNG、sampler/loader位置和precision。完整checkpoint及恢复轨迹由[预训练数据与模型交付](../../LLM%20工程实践/16-预训练数据与模型交付实践.md)第4～5节维护，继续复用实跑证据。训练曲线、定性样本、独立任务指标和有效tokens/s分别报告，不靠输出一段文本掩盖验证退化。

### 第36课的实践核对与中文自检

本课图示的含义与边界：循环与指数下降曲线为预设动画，不是训练loss结果；train/eval模式恢复、全token计权、update计数需源码核。本组课内没有独立SVG，实际注册的动态示意由统一记录静态核对，未执行网页或来源JS。

原编号练习的验收方式：

1. **如何验证decay参数组完整且不重复？** 检查每个可训练Parameter只进入一个参数组，组间不重叠，合起来覆盖全部可训练参数；绑定表按对象身份去重。逐名称核线性weight与embedding采用的decay策略，bias／norm是否按约定不decay，冻结参数是否排除。这样避免遗漏或重复更新，而不只是看两组数量。

2. **用真实文本替换合成tokens，应怎样评价？** 先按完整文档划分训练／验证，再用固定Tokenizer编码，并核Unicode往返、词表范围和标签shift。定性生成可观察字符或词的模式，但模型仍可能输出训练未见过的有效ID，不能强制把“只出现文件中字符”当训练正确的证明。结合独立验证NLL和任务结果判断。

3. **设置10%的min_lr后，怎样核调度？** 源默认min_lr已经等于max_lr的10%，不要重复添加同一功能。先定义step0、warmup末点和最后实际更新步N-1的LR，再画出或列出关键点；不要把循环之外step=N达到floor误说成最后更新已经达到。恢复训练时以同一个globalstep续算。

4. **增加checkpoint与resume后，需要保存什么？** 除model和optimizer外，保存globalstep、调度器状态、随机数与数据采样位置、精度状态、Tokenizer／数据配置和摘要。使用原子写入并保留上一完整版本，恢复后先核配置和身份，再用短受控对照比较连续训练与恢复训练的轨迹。JSONL最后一行只有观测，不能补回丢失的状态。

5. **tokens/s怎样测得可比？** 明确分子是全部输入token、非padding token还是有效监督目标，分母使用实际墙钟时间。GPU测量按协议处理预热和同步，另外注明是否包含eval、generation、数据读取及日志时间。吞吐不保证始终在固定窄区间；变化时结合负载和阶段耗时定位。

1. **输入与目标错位会怎样？** nexttoken要求输入0～T-1、target1～T。复制同位置可形成捷径；flatten为(BT,V)与(BT)前先核caller／model谁负责shift。

2. **验证模式、采样与空集怎样处理？** 验证关闭grad和dropout，用同协议样本估NLL。源异常时未finally恢复、上限0／空流给假0且多消费一batch，不能拿这些值做有效验证比较。

3. **decay组是什么策略？** 矩阵weight／embedding decay、norm／bias不decay是源策略。按Parameter身份查完整、不重复及冻结排除，不将这一常用策略说成数学强制。

4. **实际LR在step0和最后一步是什么？** 源step0为max/W，而训练最后N-1没有恰达min；test用循环外step=N检查floor。按实际更新步记录warmup边界、末步与resume时钟。

5. **clip是否能修复非有限梯度？** clip限制梯度范数，不修NaN，也不保证AdamW更新安全。AMP先unscale，再按协议检查finite／clip；阈值1需任务依据。

6. **JSONL能否单独恢复训练？** JSONL是观测日志，不能恢复model、optimizer、RNG和数据顺序；源还会删除旧log。其上游val约6.578升到7.491，不能从train loss降声称泛化变好。

## 10. 预训练权重映射：全部预检后再提交

真实checkpoint包含张量名、shape、dtype、布局与模型配置；Tokenizer／位置／QKV顺序／激活与norm epsilon亦要匹配。GPT2 Conv1D常存(in,out)，本地nn.Linear为(out,in)：QKV(768,2304)需转成(2304,768)，方阵c_proj即使shape一样也要按已知布局转置，不能只凭shape猜。官方GPT2LMHeadModel还有`transformer.wte`等wrapper前缀，原第37课stub只有`wte/h.N`，不能宣称所有small/medium/large文件只换config就可加载。[固定官方GPT2模块](https://github.com/huggingface/transformers/blob/55c3cc9f03cd4fbf2d27d382dcc8fcc544631f8e/src/transformers/models/gpt2/modeling_gpt2.py)只核相关类/投影和head身份。

加载分两阶段：列全部tensor及完整映射，核name唯一、missing、明确允许的extra、layer索引集合、shape/layout、实际dtype与finite，预计内存／转换边界；全部通过后才更新模型。加载失败保留原完整版本，不留一半旧随机一半新参数。源loader只在shape_mismatch时拒绝全部copy，missing是在复制后才报、unexpected不影响ok，所以还可能半加载。第37课11个测试定义没有覆盖缺项原子拒绝。

Safetensors作为纯Tensor格式降低pickle任意代码风险，但不认证来源、正确架构或值finite；官方Format明确NaN/Inf可存在。`safe_open`可延迟取tensor，源先把全部pending materialize也仍要算内存。PyTorch `weights_only=True`的受限加载也有资源／下游数据边界，不应因错误提示就自动改False。来源、许可、digest与资源限定由[模型获取与环境管理](../../LLM%20工程实践/02-模型获取与环境管理.md)维护；本次未打开模型权重或安装库。

复制tensor到target.dtype不会把float32模型自动变bf16；先确定整个模型dtype/设备及必要buffer、再核cast误差和溢出。tied head可能在文件省略alias，也可能存在另名或untied，按格式处理。加载前后same greedy输出不表示未加载，different也不证明正确；粗L2 norm fingerprint非唯一身份。逐tensor值／摘要、完整report和参考模型的logits对照比“样本变了”更有证明力。

### 完整标准库例：预检拒绝半加载

以下只模拟二维标量张量的metadata、转置、共享别名和单进程代际提交。没有Tensor库、Safetensors parser、真实checkpoint、签名或网络；不是可部署loader。所有预检通过后替换内存字典，真实并发／多设备复制还需事务、dtype转换预检、失败恢复与可信源。

```python
from dataclasses import dataclass
import copy
import math

@dataclass(frozen=True)
class TensorRecord:
    shape: tuple
    values: tuple
    layout: str

def validate_tensor(record):
    if type(record) is not TensorRecord or type(record.shape) is not tuple or len(record.shape) != 2:
        raise ValueError('本教学合同仅二维Tensor元数据')
    if any(type(n) is not int or n < 1 for n in record.shape):
        raise ValueError('维度为非bool正整数')
    if type(record.values) is not tuple or len(record.values) != math.prod(record.shape):
        raise ValueError('形状与实际值数量不同')
    def finite(x):
        if type(x) not in (int, float): return False
        try: return math.isfinite(x)
        except OverflowError: return False
    if any(not finite(x) for x in record.values):
        raise ValueError('值必须有限，bool不是权重')
    if type(record.layout) is not str or record.layout not in {'in_out', 'out_in'}:
        raise ValueError('明确矩阵布局')

def as_out_in(record):
    validate_tensor(record)
    if record.layout == 'out_in': return record
    rows, cols = record.shape
    transposed = tuple(record.values[r * cols + c] for c in range(cols) for r in range(rows))
    return TensorRecord((cols, rows), transposed, 'out_in')

class ModelStore:
    def __init__(self):
        # 一个代表参数与一个共享别名；不是实际torch.Parameter。
        self.params = {'token': TensorRecord((2, 2), (0., 0., 0., 0.), 'out_in'),
                       'projection': TensorRecord((2, 2), (0., 0., 0., 0.), 'out_in')}
        self.aliases = {'head': 'token'}
        self.generation = 0
    def load(self, checkpoint, mapping, expected_generation):
        if type(expected_generation) is not int or expected_generation != self.generation:
            raise ValueError('模型已改变，不能用旧版本提交')
        if type(checkpoint) is not dict or type(mapping) is not dict:
            raise ValueError('检查点与映射为字典')
        if any(type(k) is not str or not k for k in checkpoint) or any(type(k) is not str or not k
                or type(v) is not str or not v for k, v in mapping.items()):
            raise ValueError('明确非空参数名称')
        if set(checkpoint) != set(mapping) or len(set(mapping.values())) != len(mapping):
            raise ValueError('缺失/未知来源或重复目标映射')
        if set(mapping.values()) != set(self.params):
            raise ValueError('未完整覆盖所有代表参数')
        pending = {}
        for source, target in mapping.items():
            if type(source) is not str or not source or type(target) is not str:
                raise ValueError('明确参数名称')
            converted = as_out_in(checkpoint[source])
            if converted.shape != self.params[target].shape:
                raise ValueError('形状不匹配，整个提交拒绝')
            pending[target] = converted
        # 全部通过后替换；真实系统需事务/隔离、dtype转换预检及回滚。
        self.params = pending
        self.generation += 1
    def parameter(self, name):
        return self.params[self.aliases.get(name, name)]

model = ModelStore()
checkpoint = {'wte': TensorRecord((2, 2), (1., 2., 3., 4.), 'out_in'),
              'c_proj': TensorRecord((2, 2), (5., 6., 7., 8.), 'in_out')}
mapping = {'wte': 'token', 'c_proj': 'projection'}
baseline = copy.deepcopy(model.params)
for bad in ({'wte': checkpoint['wte']}, dict(checkpoint, surprise=checkpoint['wte']),
            dict(checkpoint, c_proj=TensorRecord((2, 2), (5., float('nan'), 7., 8.), 'in_out')),
            dict(checkpoint, c_proj=TensorRecord((True, 2), (5., 6.), 'in_out')),
            dict(checkpoint, c_proj=TensorRecord((2, 2), (10**400, 6., 7., 8.), 'in_out')),
            dict(checkpoint, c_proj=TensorRecord((1, 4), (5., 6., 7., 8.), 'out_in'))):
    try: model.load(bad, mapping, 0)
    except ValueError: pass
    else: raise AssertionError('异常检查点未拒绝')
    assert model.params == baseline and model.generation == 0
model.load(checkpoint, mapping, 0)
assert model.parameter('head') is model.parameter('token')
assert model.params['projection'].values == (5., 7., 6., 8.)  # 方阵也必须转置。
assert model.generation == 1
try: model.load(checkpoint, mapping, 0)
except ValueError: pass
else: raise AssertionError('旧代际提交未拒绝')
print('缺失/未知/形状/非有限/布尔维度预检拒绝且未部分加载；方阵转置、共享别名、旧代际通过')
print('仅二维标量元数据一致性，不加载实际checkpoint、验证来源签名或运行模型')

before = copy.deepcopy(model.params)
for invalid_mapping in ({'wte': [], 'c_proj': 'projection'}, {'wte': True, 'c_proj': 'projection'}):
    try: model.load(checkpoint, invalid_mapping, 1)
    except ValueError: pass
    else: raise AssertionError('错误映射类型未拒绝')
    assert model.params == before and model.generation == 1
print('映射值列表/布尔类型明确拒绝，已提交模型保持原样')
```

2026-10-12以Python3.12.13标准库实际执行，缺失、未知、形状、非有限值、布尔维度及错误映射类型均拒绝且旧模型保持；方阵转置、alias与旧代际检查通过。没有读取真实权重或运行模型。

### 第37课的实践核对与中文自检

本课图示的含义与边界：名称/shape映射只约束结构，方阵错误transpose仍同形；完整映射、tokenizer和前向logits数值parity缺一不可。本组课内没有独立SVG，实际注册的动态示意由统一记录静态核对，未执行网页或来源JS。

原编号练习的验收方式：

1. **加载dtype与模型dtype有什么区别？** 把源tensor临时转为bf16再copy到float32 Parameter，最终仍是float32模型。先统一目标模型和必要buffer的dtype／设备，再加载并检查cast误差、有限值及溢出，最后与参考前向比较。成功生成一次只证明能走该路径，不证明质量保持。

2. **怎样检查expected_layers？** 从checkpoint解析完整层索引集合，和模型预期集合逐项对比，拒绝缺层、重复／未知层及相关参数缺项，而非只比较层数。把这一步放在任何copy之前，失败时确认所有目标参数仍为原值。

3. **加载前后样本怎样作合理对照？** 使用同prompt、eval模式和固定解码协议，同时检查完整LoadReport、逐tensor值／摘要及参考模型logits。随机stub只验证加载机制；相同greedy文字不意味着没载入，不同文字也不证明映射全部正确。

4. **导出再载入怎样验证round-trip？** 按明确名称与逆布局映射导出，处理共享别名，并保存模型／Tokenizer配置。恢复时核完整参数覆盖，比较tensor数值和同输入logits的合理容差。只报告零shape mismatch会漏掉方阵转置或相同shape的错误映射。

5. **扩展到Llama为何不能只换NAME_MAP？** 先匹配具体模型版本的RMSNorm、SwiGLU门控、RoPE、KV head数、bias和输出绑定政策，再映射相应权重。官方实现可能采用独立q_proj/k_proj/v_proj，不能统一假定fused qkv。stub仍只证结构，真实checkpoint的数值对照另有范围。

1. **映射哪些名称和语义？** 映射须匹配名称、wrapper前缀、层集合、维度、QKV顺序和布局。当前官方GPT2LMHeadModel有transformer前缀而stub没有，不是任意真实文件可直接替换。

2. **哪类矩阵需要转置？** GPT2 Conv1D通常是(in,out)，nnLinear是(out,in)；相应c_attn/c_proj/c_fc转置。方阵shape相同也不证明方向正确。

3. **共享head是否一定不在文件中？** 该stub按共享规则省head，真实导出也可能保lm_head或使用独立head。先核checkpoint合同，再恢复alias，不把省略当格式通则。

4. **缺项、未知与形状错怎样阻止半加载？** 源shape错会阻断全部copy，缺项却在copy之后才报，未知项也不影响ok。完整名称／dtype／finite／shape预检完成后再提交，失败核目标仍原值。

5. **stub通过能否直接换真实文件？** stub只验证离线路径，实际是4层D192，不是文案12层。真实文件还要锁格式、结构和Tokenizer，并作数值对照，不能把样本变化当预训练效果。

6. **输出相同是否表示权重没加载？** 加载后同一greedy样本仍可能相同，不表示没load；不同也不证明完整正确。用逐tensor核对和参考logits比较，粗norm指纹并非唯一身份。


本次增量整理2026-10-12。来源是AI Engineering from Scratch固定提交 `3be078b37ffd8f0c04953c0678e48f5c6d0c7775`，[33 multihead-self-attention](https://github.com/rohitg00/ai-engineering-from-scratch/tree/3be078b37ffd8f0c04953c0678e48f5c6d0c7775/phases/19-capstone-projects/33-multihead-self-attention)课内全部文件实际静读2026-10-11；[34 transformer-block](https://github.com/rohitg00/ai-engineering-from-scratch/tree/3be078b37ffd8f0c04953c0678e48f5c6d0c7775/phases/19-capstone-projects/34-transformer-block)课内全部文件实际静读2026-10-11；[35 gpt-model-assembly](https://github.com/rohitg00/ai-engineering-from-scratch/tree/3be078b37ffd8f0c04953c0678e48f5c6d0c7775/phases/19-capstone-projects/35-gpt-model-assembly)课内全部文件实际静读2026-10-11；[36 training-loop-eval](https://github.com/rohitg00/ai-engineering-from-scratch/tree/3be078b37ffd8f0c04953c0678e48f5c6d0c7775/phases/19-capstone-projects/36-training-loop-eval)课内全部文件实际静读2026-10-11；[37 loading-pretrained-weights](https://github.com/rohitg00/ai-engineering-from-scratch/tree/3be078b37ffd8f0c04953c0678e48f5c6d0c7775/phases/19-capstone-projects/37-loading-pretrained-weights)课内全部文件实际静读2026-10-11；原程序和测试未执行，没有安装依赖、下载模型、启动服务或进行真实训练；测试断言、原日志和动画只按其实际范围解释。旧程序字节和旧核验日期保留。 2026-10-12选读[PyTorch Serialization](https://docs.pytorch.org/docs/stable/notes/serialization.html)的weights_only范围及[Safetensors Format](https://github.com/safetensors/safetensors/blob/e246a2560645b7525f5775669ed816eb57c5bcc8/README.md)；版本/范围详见本批维护记录。
