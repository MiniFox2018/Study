# 08｜NLP预训练目标与应用

> 先修：[注意力与Transformer](04-注意力机制与Transformer.md)、[序列概率与teacher forcing](03-序列模型与机器翻译.md)。先明确“输入能看到什么、哪些位置有监督、下一步预测什么”，再运行MLM/CLM与encoder–decoder小例。随机模型只验证目标、形状与反向，不代表已学语言或具备真实任务能力。

## 1. 表示学习的主线及已有基础

token ID是离散编号；one-hot是离散类别的稀疏0/1向量表示，例如ID=2对应词表中的一个位置，one-hot在该位置为1、其余为0。Word2Vec/GloVe学习静态词表示，子词复用稀有形式，上下文编码器根据周围内容改变表示。这个演进不意味着新表示一定正确：相同“苹果”在静态词表通常同一向量，上下文模型也可能消歧失败。词面检索、静态embedding和小模型仍有作为基线/受限任务的价值，不因年代淘汰机制。

Skip-Gram给定中心词预测上下文，CBOW反过来。句子“猫 坐 在 垫子 上”，窗口半径1时以“在”为中心得正对(在,坐)/(在,垫子)。负采样用指定噪声分布构造二分类对，并非每个抽中词都语义错误；其目标不同于完整softmax，不能当softmax梯度无偏估计。层次softmax把概率表达成树路径上二分类概率乘积，保留归一化结构；负采样改写目标，两者都是大词表计算的方案。GloVe显式利用全局共现，Word2Vec更强调局部预测；训练语料、词窗口和低频处理会影响结果。

子词/字符n-gram能组合OOV与形态变化，tokenizer的切分不等于语言学词素。cosine、最近邻和类比用于诊断，不能证明完整理解。上述训练公式/代码由[词向量与子词建模](../语言与文本专题/02-词向量与子词建模.md)维护；[文本预处理](../语言与文本专题/01-文本预处理与稀疏表示.md)维护词表/TF-IDF/计数基线，本章承接Transformer目标而不复制另一套词向量教程。

## 2. 预训练目标、可见范围与监督位置

| 目标 | 模型可见内容 | 监督 | 适合怎样的接口 |
| --- | --- | --- | --- |
| MLM | 受破坏文本的左右上下文 | 选中的位置恢复原token | 上下文编码、分类/标注/配对特征 |
| CLM | 当前输入token及其前缀 | 预测下一个token | 自回归生成与条件前缀建模 |
| T5 span corruption | 用独立sentinel替代的缺失span，源端双向 | decoder依次输出sentinel和缺失片段 | 有明确源→目标的条件生成 |
| BART denoising | 经mask/delete/infill/重排等破坏的源 | decoder恢复整份原文 | 去噪预训练后迁移到摘要/改写等 |

Encoder/decoder/encoder–decoder是骨干与可见性选择，loss定义也须写清。分类可以用decoder表示，生成也有其他因果/迭代方案；不能由品牌或“understand/generate”口号决定一切。标准encoder只靠双向MLM头不是训练好的自回归接口；把同位置原答案经额外输入字段传回模型会泄漏，但历史MLM故意保留部分选中token有自己的目标设计，不能一概判为错误。

## 3. BERT、MLM与完整输入/标签构造

原BERT选择约15%的可遮盖token，其中80%改[MASK]、10%随机替换、10%保留原值；**15%是被选择率，80/10/10是条件在已选位置上的分支比例**。所有已选位置都预测原token，包括未改动/随机分支；未选位置、special与PAD的labels为ignore。这缓解预训练出现[MASK]而下游原文不出现的分布差，但不保证预测准确或使两种分布完全相同。

80/10/10是历史配方，可调mask率、span/whole-word、动态重采样等，不是所有现代encoder的必要定义。随机替换可能碰巧抽回原token，因此“实际输入未改变比例”和“进入保留分支比例”不同。源程序排除原token和special的替换策略并非原BERT所有细节；while拒绝采样在词表无其他合法词时会卡住，应预建有限候选并验证。

Whole-word masking依tokenizer的word_id/offset分组，不是把任意两个邻词叫一个词。按词组一次Bernoulli抽样与“任一subword独立选中后整词扩展”不同，后者长词更容易被选。需要记录组选择预算、展开后的token比例及损失权重；不能只用相同mask_prob就称两个实验等价。

原BERT还用NSP判断训练构造的句对连续性。RoBERTa实验表明该设置可以移除并结合数据/训练调整改善结果，不等于NSP在任何数据和目标上必然有害；后续如replaced-token detection也是不同监督目标。2026-10-05核对ModernBERT官方实现使用 `nn.LayerNorm`，来源表将其写为RMSNorm不正确；具体RoPE/GeGLU/local-global/词表与上下文取决模型配置，不继承固定速度/排名。

### 3.1 自含MLM与whole-word采样、有限词表与空监督

本例明确排除special随机候选，但允许随机抽回原值；以分支计数衡量80/10/10，不冒充逐细节复刻官方collator。

```python
import numpy as np
import torch
from collections import Counter
PAD,BOS,EOS,MASK,CLS,SEP=0,1,2,3,4,5
SPECIAL={PAD,BOS,EOS,MASK,CLS,SEP}

def mlm_batch(ids,vocab_size,prob=.15,seed=7,word_spans=None):
    if ids.ndim!=2 or ids.dtype!=torch.long or not 0<=prob<=1:
        raise ValueError("[B,T] long与概率合同")
    if (ids<0).any() or (ids>=vocab_size).any():raise ValueError("token越界")
    pool=[t for t in range(vocab_size) if t not in SPECIAL]
    if not pool:raise ValueError("没有可随机替换的普通词，不进入无限循环")
    rng=np.random.default_rng(seed);inputs=ids.clone();labels=torch.full_like(ids,-100)
    stats=Counter();groups=[]
    for b,row in enumerate(ids.tolist()):
        spans=word_spans[b] if word_spans is not None else [(i,i+1) for i,t in enumerate(row) if t not in SPECIAL]
        seen=set()
        for start,end in spans:
            if not 0<=start<end<=len(row) or set(range(start,end))&seen or any(row[i] in SPECIAL for i in range(start,end)):
                raise ValueError("word跨度必须有效、非重叠且不含special")
            seen.update(range(start,end))
            if rng.random()>=prob:continue
            r=rng.random();branch="mask" if r<.8 else "random" if r<.9 else "keep"
            stats[branch]+=end-start
            labels[b,start:end]=ids[b,start:end]
            if branch=="mask":inputs[b,start:end]=MASK
            elif branch=="random":inputs[b,start:end]=torch.tensor(rng.choice(pool,size=end-start),dtype=torch.long)
            groups.append((b,start,end,branch))
    return inputs,labels,stats,groups

ids=torch.tensor([[CLS,6,7,8,9,SEP,PAD],[CLS,10,11,12,SEP,PAD,PAD]])
masked,labels,stats,groups=mlm_batch(ids,20,prob=.6)
assert (labels!=-100).any() and torch.all(labels[ids<=SEP]==-100)
words=[[(1,3),(3,5)],[(1,2),(2,4)]]
_,whole,_,_=mlm_batch(ids,20,prob=1.,word_spans=words)
assert torch.all(whole[0,1:5]!=-100)
print("MLM输入",masked.tolist(),"labels",labels.tolist(),"分支",dict(stats))
large=torch.arange(6,20).repeat(715)[:10000][None,:]
_,lab,counts,_=mlm_batch(large,20,prob=.15,seed=42)
selected=int((lab!=-100).sum())
assert .13<selected/10000<.17 and .75<counts["mask"]/selected<.85
print("选择率",round(selected/10000,3),"分支比例",{k:round(v/selected,3) for k,v in counts.items()})
try:mlm_batch(torch.tensor([[CLS,SEP]]),6)
except ValueError:print("空随机候选已拒绝")
```

很短batch可能没选任何位置；数据构造本身可以返回全ignore，训练必须跳过/重新采样/累计，不能对全ignore直接mean CE产生NaN。下面的损失函数显式拒绝。数字0有时是PAD、有时任务decoder的起始token，需要分别使用attention mask与loss mask，不能用一个特殊ID推断所有职责。

## 4. CLM：前缀平均、因果mask与稳定损失

对输入X的第i个位置，最简单因果聚合是平均X[0:i+1]，等价下三角行和1矩阵A乘X。静态可学习score S经mask+softmax代替固定平均，内容相关QK/√d再使权重随输入变化；这是一种教学推导，不是所有attention的历史起源证明。因果矩阵每行允许自己与过去，未来j>i设置负无穷，不能乘0后softmax。所有位置都无效时分布未定义；PAD与因果是不同轴条件。

CLM输入 `[BOS,猫,坐]` 监督 `[猫,坐,EOS]`；允许看当前输入，是因为预测**下一**token，不是预测当前同一个。最后PAD不计loss，EOS要学习。训练可同时计算各位置，生成需按自己的输出逐步推进；KV cache保存每层历史K/V而不是简单保存最后hidden。SFT可只监督答案区，但仍需让模型看到合法prompt。DPO/RL等后训练目标不全等于同一个下一token CE；ICL、质量与速度没有由某参数量固定触发的保证。

### 4.1 完整随机双向/因果模型、MLM/CLM反向及未来泄漏检查

这是一组自含小模型。两种self-attention骨干共用同一代码，用不同mask与监督；随机初始化、合成ID，无预训练语料或权重。

```python
import math
import torch
from torch import nn
from torch.nn import functional as F

torch.set_num_threads(1);torch.manual_seed(13)
PAD,BOS,EOS,MASK,CLS,SEP=0,1,2,3,4,5
V,D=20,8
class TinyLM(nn.Module):
    def __init__(self,causal):
        super().__init__();self.causal=causal
        self.emb=nn.Embedding(V,D,padding_idx=PAD);self.pos=nn.Embedding(32,D)
        layer=nn.TransformerEncoderLayer(D,2,16,dropout=0.,batch_first=True,norm_first=True)
        self.blocks=nn.TransformerEncoder(layer,2,enable_nested_tensor=False)
        self.norm=nn.LayerNorm(D);self.head=nn.Linear(D,V,bias=False)
        self.head.weight=self.emb.weight  # tied head，不保证PAD行从此永远零梯度
    def forward(self,ids,valid):
        if ids.ndim!=2 or ids.dtype!=torch.long or ids.shape[0]==0 or ids.shape[1]==0 or valid.shape!=ids.shape or valid.dtype!=torch.bool:
            raise ValueError("非空[B,T] long与同形bool mask")
        if not valid[:,0].all() or ((~valid[:,:-1]) & valid[:,1:]).any() or not torch.equal(valid,ids!=PAD):
            raise ValueError("本TinyLM限定首token有效、右PAD连续；不能沿用到START=PAD任务")
        if (ids<0).any() or (ids>=V).any():raise ValueError("token越界")
        if ids.shape[1]>32:raise ValueError("超出教学位置容量")
        x=self.emb(ids)+self.pos(torch.arange(ids.shape[1]))[None,:,:]
        mask=torch.ones(ids.shape[1],ids.shape[1],dtype=torch.bool).triu(1) if self.causal else None
        hidden=self.blocks(x,mask=mask,src_key_padding_mask=~valid)
        return self.head(self.norm(hidden))

def token_loss(logits,labels):
    count=(labels!=-100).sum()
    if not count:raise ValueError("没有监督位置，应跳过batch或重新采样")
    return F.cross_entropy(logits.reshape(-1,V),labels.reshape(-1),ignore_index=-100,reduction="sum")/count

ids=torch.tensor([[CLS,6,MASK,8,SEP,PAD],[CLS,9,MASK,SEP,PAD,PAD]])
labels=torch.full_like(ids,-100);labels[:,2]=torch.tensor([7,10])
mlm=TinyLM(False);logits=mlm(ids,ids!=PAD);loss=token_loss(logits,labels);loss.backward()
assert torch.isfinite(loss) and all(p.grad is None or torch.isfinite(p.grad).all() for p in mlm.parameters())
sequence=torch.tensor([[BOS,6,7,EOS,PAD],[BOS,8,EOS,PAD,PAD]])
inputs=sequence[:,:-1];targets=sequence[:,1:].clone();targets[targets==PAD]=-100
clm=TinyLM(True);logits=clm(inputs,inputs!=PAD);ce=token_loss(logits,targets);ce.backward()
assert torch.isfinite(ce)
clm.eval()
with torch.no_grad():
    original=clm(inputs,inputs!=PAD)
    changed=inputs.clone();changed[0,2]=11
    new=clm(changed,changed!=PAD)
    assert torch.allclose(original[0,:2],new[0,:2],atol=1e-6)
# 稳定CE使用logsumexp，不用max(prob,1e-12)把巨大错误损失截断。
extreme=torch.tensor([[1000.,-1000.]],requires_grad=True)
large_loss=F.cross_entropy(extreme,torch.tensor([1]));large_loss.backward()
assert large_loss.item()==2000. and torch.isfinite(extreme.grad).all()
assert abs(F.cross_entropy(torch.zeros(1,V),torch.tensor([3])).item()-math.log(V))<1e-6
try:token_loss(torch.zeros(1,1,V),torch.full((1,1),-100))
except ValueError:print("空监督loss已拒绝")
for bad in [torch.empty(0,3,dtype=torch.long),torch.empty(1,0,dtype=torch.long),torch.tensor([[PAD,6]]),torch.tensor([[6,PAD,7]])]:
    try:clm(bad,bad!=PAD)
    except ValueError:pass
    else:raise AssertionError("非法空项/左PAD/内部PAD应拒绝")
print("MLM/CLM shape",tuple(logits.shape),"有效CLM目标",int((targets!=-100).sum()),"反向/因果/极端CE通过")
```

代码使用2层encoder-style实现masked self-attention+FFN，因果模式没有cross-attention，因此是教学decoder-only骨干；不冒充BERT/GPT完整实现。均匀分布损失lnV，任意高斯随机logits并不必等于lnV；源例给真实下一个token的logit手工加2是oracle答案偏置，没有完成训练。未来token改动不得影响更早CLM logit，是比“画出下三角”更有意义的因果检查。

## 5. T5与BART：输入破坏、输出协议与encoder–decoder

标准encoder–decoder将源编码一次，decoder每步以自身状态作Q读取encoder K/V，同时用因果self-attention读目标前缀。encoder缓存是表示结果，参数训练时依然可反向更新；图中的“freeze”不是训练时必须冻结encoder。这里讨论标准cross-attention，不把它说成任何条件生成架构唯一可传信息的方式。

T5用随机连续span替换为不同sentinel，目标按原先顺序输出每个sentinel及被删片段，按具体预处理约定加结束sentinel/EOS。通常约15%噪声、平均span约3是原训练配方，不是每个短样本必须精确相同；原站Gaussian贪心找span可能预算未用完，也不是官方随机分段算法。恢复原文必须在**源sentinel原位置插回对应目标片段**，不能把未遮源词与目标词直接连接到末尾。

BART恢复完整原文。token mask保留位置，delete改变长度，text infill用一个mask替代一个span而不暴露其长度，sentence permutation换句顺序，document rotation移动起点。原论文比较过多个noise配方，某组合在相应实验表现好，不保证跨任务永远最佳。BART的目标通常更长，但计算/质量仍依noise、序列长和预算，不能按名称固定断言更贵/更好。

FLAN是在带任务指令的多任务数据上进一步微调，能用于encoder–decoder，不是RLHF只能decoder-only的证明。文字任务前缀是训练时的任务条件，随便给未对应训练的模型加“translate”并不保证它会做该任务。结构化目标还需输出schema/grammar与语义验证，合法JSON不等于正确抽取。

### 5.1 完整span生成、sentinel往返、BART noise与边界

教学实现用普通词ID≥6、sentinel从30起，EOS=2。从随机正整数分段构造交替clean/noise，明确保证非空输入至少一个clean/一个noise，不宣称与所有T5数据版本完全一致。构造固定数量噪声时，round/clamp也会使短文本实际比例偏离15%。

```python
import numpy as np
PAD,BOS,EOS,MASK,CLS,SEP=0,1,2,3,4,5
SENT=30

def positive_segments(total,k,rng):
    if not 1<=k<=total:raise ValueError("正段数不可超出总长度")
    cuts=np.sort(rng.choice(np.arange(1,total),k-1,replace=False))
    return np.diff(np.r_[0,cuts,total]).tolist()

def t5_corrupt(tokens,rate=.15,mean_span=3.,seed=17):
    if len(tokens)<2 or not 0<rate<1 or mean_span<=0 or any(not 6<=t<SENT for t in tokens):
        raise ValueError("至少2普通token、合法rate/span、sentinel不冲突")
    rng=np.random.default_rng(seed);n=len(tokens)
    noise=min(n-1,max(1,round(n*rate)))
    k=min(noise,n-noise,max(1,round(noise/mean_span)))
    clean_lengths=positive_segments(n-noise,k,rng);noise_lengths=positive_segments(noise,k,rng)
    source=[];target=[];cursor=0
    for i,(a,b) in enumerate(zip(clean_lengths,noise_lengths)):
        source+=tokens[cursor:cursor+a];cursor+=a
        source.append(SENT+i);target+=[SENT+i]+tokens[cursor:cursor+b];cursor+=b
    target += [SENT+k,EOS];source += [EOS]
    return source,target,k

def restore(source,target,k):
    if source[-1:]!=[EOS] or target[-2:]!=[SENT+k,EOS]:raise ValueError("缺结束sentinel/EOS")
    mapping={};cursor=0
    for i in range(k):
        if target[cursor]!=SENT+i:raise ValueError("sentinel顺序非法")
        cursor+=1;span=[]
        while cursor<len(target) and target[cursor]<SENT and target[cursor]!=EOS:
            span.append(target[cursor]);cursor+=1
        if not span:raise ValueError("目标片段不可空")
        mapping[SENT+i]=span
    if cursor!=len(target)-2:raise ValueError("目标末端不匹配")
    restored=[];seen=[]
    for token in source[:-1]:
        if token>=SENT:
            if token not in mapping or token in seen:raise ValueError("未知/重复源sentinel")
            restored+=mapping[token];seen.append(token)
        else:restored.append(token)
    if len(seen)!=k:raise ValueError("源缺少sentinel")
    return restored

def bart_noise(tokens,mode,seed=7):
    rng=np.random.default_rng(seed);t=list(tokens)
    if mode=="mask":return [MASK if rng.random()<.3 else x for x in t]
    if mode=="delete":return [x for x in t if rng.random()>=.3]
    if mode=="infill":
        if len(t)<4:raise ValueError("fixture需4token")
        return t[:1]+[MASK]+t[3:]  # 定义span[1,3)，一个mask替两个词
    if mode=="rotate":
        if not t:return []
        pivot=int(rng.integers(len(t)));return t[pivot:]+t[:pivot]
    if mode=="permute_sentences":
        order=rng.permutation(len(t));return [t[i] for i in order]
    raise ValueError("未知noise")

original=list(range(6,26));src,tgt,k=t5_corrupt(original,rate=.3,mean_span=2.)
assert restore(src,tgt,k)==original
assert len([t for t in src if t>=SENT])==k
assert bart_noise(original,"infill")[1]==MASK
assert bart_noise(original,"delete")!=original
sentences=[[6,7],[8,9],[10,11]]
assert sorted(bart_noise(sentences,"permute_sentences"))==sorted(sentences)
print("T5源/目标",src,tgt,"round-trip通过，sentinel数",k)
for mode in ["mask","delete","infill","rotate"]:print("BART",mode,bart_noise(original[:8],mode))
try:restore(src,tgt[:-1],k)
except ValueError:print("缺EOS已拒绝")
```

原BART目标为未破坏的tokens+EOS，无论input变短/重排，不能把noise后的source当labels。noise并不一定唯一可逆，模型学习条件分布；T5的round-trip只在已给真实目标span时证明构造正确，不是在测试模型推断。

## 6. 完整随机encoder–decoder与PAD起始合同

T5常以PAD ID启动decoder，BART/其他模型可能用EOS/BOS等，必须读取decoder_start_token_id，不能全局硬编码BOS=1。如果起始ID恰等PAD，用 `decoder_ids != PAD` 会错误屏蔽合法首步；decoder有效位置应来自长度/attention_mask。labels的ignore=-100是loss合同，shift right时不能拿-100去Embedding索引。

```python
import torch
from torch import nn
from torch.nn import functional as F
from torch.nn.utils.rnn import pad_sequence

torch.set_num_threads(1);torch.manual_seed(21)
PAD,EOS,START,V,D=0,2,0,40,8  # 有意START==PAD，测试真实mask语义
sources=[[6,30,9,EOS],[7,30,8,9,EOS]]
targets=[[30,10,11,31,EOS],[30,12,31,EOS]]
src=pad_sequence([torch.tensor(x) for x in sources],batch_first=True,padding_value=PAD)
labels=pad_sequence([torch.tensor(x) for x in targets],batch_first=True,padding_value=-100)
lengths=torch.tensor([len(x) for x in targets]);valid=torch.arange(labels.shape[1])[None,:]<lengths[:,None]
dec=torch.full_like(labels,PAD);dec[:,0]=START
dec[:,1:]=torch.where(labels[:,:-1]==-100,PAD,labels[:,:-1])
assert valid[:,0].all() and (dec[:,0]==PAD).all()
class TinySeq2Seq(nn.Module):
    def __init__(self):
        super().__init__();self.emb=nn.Embedding(V,D);self.pos=nn.Embedding(32,D)
        self.encoder=nn.TransformerEncoder(nn.TransformerEncoderLayer(D,2,16,dropout=0.,batch_first=True),1,enable_nested_tensor=False)
        self.decoder=nn.TransformerDecoder(nn.TransformerDecoderLayer(D,2,16,dropout=0.,batch_first=True),1)
        self.head=nn.Linear(D,V)
    def encode(self,source):
        x=self.emb(source)+self.pos(torch.arange(source.shape[1]))[None,:]
        return self.encoder(x,src_key_padding_mask=source==PAD)
    def decode(self,decoder,memory,source_valid,target_valid):
        x=self.emb(decoder)+self.pos(torch.arange(decoder.shape[1]))[None,:]
        causal=torch.ones(decoder.shape[1],decoder.shape[1],dtype=torch.bool).triu(1)
        h=self.decoder(x,memory,tgt_mask=causal,tgt_key_padding_mask=~target_valid,memory_key_padding_mask=~source_valid)
        return self.head(h)
model=TinySeq2Seq();memory=model.encode(src)
logits=model.decode(dec,memory,src!=PAD,valid)
loss=F.cross_entropy(logits.reshape(-1,V),labels.reshape(-1),ignore_index=-100,reduction="sum")/valid.sum()
loss.backward();assert torch.isfinite(loss) and all(p.grad is None or torch.isfinite(p.grad).all() for p in model.parameters())
model.eval()
with torch.no_grad():
    memory=model.encode(src);a=model.decode(dec,memory,src!=PAD,valid)
    changed=dec.clone();changed[0,3]=15;b=model.decode(changed,memory,src!=PAD,valid)
    assert torch.allclose(a[0,:3],b[0,:3],atol=1e-6)
print("随机条件生成logits",tuple(logits.shape),"有效目标",int(valid.sum()),"START=PAD有效，有限反向/目标因果通过")
```

输出 `(2,5,40)`、有效目标9。完整训练图有encoder与decoder梯度，但未学T5/BART语义；正式架构的relative position、shared embeddings、norm等依模型实现。真实推理先encode一次，再不断decode prefix直到EOS/max长度；beam重排cache、每样本结束状态、时间偏置等由[Seq2Seq](03-序列模型与机器翻译.md)及[现代生成](../../LLM%20基础/09-现代语言模型架构与生成.md)维护。不能把每一步重新encode视为正确且免费性能方案。

## 7. 采样与任务应用的判断

温度按logits/T改变尖锐度，top-k按排名截断，top-p保留累积概率达到p的最小集合（包含跨过阈值的词），min-p按p_i≥min_p×max(p)筛选。筛后重新归一化，配置非法/所有位置被遮需拒绝或规定回退；随机seed只控制随机抽样，不保证任意硬件/并发下bitwise一致。T=0应走greedy分支，不能直接除0。详细策略接[生成章节](../../LLM%20基础/09-现代语言模型架构与生成.md#8-decoding)。

```python
import numpy as np

def filtered(logits,temperature=1.,top_k=None,top_p=None,min_p=None):
    x=np.asarray(logits,dtype=float)
    if x.ndim!=1 or not len(x) or not np.isfinite(x).all() or not np.isfinite(temperature) or temperature<=0:
        raise ValueError("有限非空logits与正温度")
    if top_k is not None and (type(top_k) is not int or not 1<=top_k<=len(x)):raise ValueError("k非法")
    if top_p is not None and not 0<top_p<=1:raise ValueError("top-p非法")
    if min_p is not None and not 0<=min_p<=1:raise ValueError("min-p非法")
    score=x/temperature;prob=np.exp(score-score.max());prob/=prob.sum()
    keep=np.ones(len(x),dtype=bool)
    if top_k is not None:
        order=np.argsort(-prob,kind="stable");keep[:]=False;keep[order[:top_k]]=True
    if top_p is not None:
        order=np.argsort(-prob,kind="stable");cross=np.searchsorted(np.cumsum(prob[order]),top_p,side="left")
        nucleus=np.zeros(len(x),dtype=bool);nucleus[order[:min(cross+1,len(x))]]=True;keep &= nucleus
    if min_p is not None:keep &= prob>=min_p*prob.max()
    prob=np.where(keep,prob,0.)
    if not prob.sum():raise ValueError("配置交集没有候选")
    return prob/prob.sum()

logits=np.log([.6,.25,.1,.05])
assert np.allclose(filtered(logits,top_p=.7),[.6/.85,.25/.85,0,0])
assert np.allclose(filtered(logits,min_p=.2),[.6/.85,.25/.85,0,0])
assert np.array_equal(filtered(logits,top_k=1),[1,0,0,0])
rng=np.random.default_rng(3);p=filtered(logits,top_p=.9)
print("greedy",int(np.argmax(logits)),"top-p",p,"一次抽样",int(rng.choice(len(p),p=p)))
for bad_t in [0.,float("nan"),float("inf")]:
    try:filtered(logits,temperature=bad_t)
    except ValueError:pass
    else:raise AssertionError("非法温度应拒绝")
print("T=0/NaN/Inf温度已拒绝；T=0应单独greedy")
```

本例多个filter在同一基础分布上取交集，其他生成库可能顺序重算分布，配置要写清。sampling不改已固定模型的教师强制PPL；比较beam/greedy的生成文本得分不能叫模型本身PPL改变。beam与长度惩罚不保证任务质量；speculative decoding要分greedy验证与保持目标采样分布的拒绝采样校正，不要求采样文本等于greedy，也不保证固定2～3倍速度。完整证明/实现由本批推理专题维护。

分类要给task head与合法划分，MLM的CLS不是未经训练就保证有用的检索向量；mean pool排PAD，contrastive training的双塔和query-doc cross-encoder有不同成本/交互。frozen encoder+head是linear probe，联合更新才是另一微调方案，不能说所有BERT都只训练head。NER/POS/共指/链接见[序列标注](../语言与文本专题/04-序列标注与实体消歧.md)，情感/分类见[文本分类](../语言与文本专题/03-文本分类主题与跨语言学习.md)，NLI的方向/三类/世界真值边界与BLEU/ROUGE见[文本评价](../语言与文本专题/05-摘要推断与文本评价.md)。

经典attention-based NLI保留“跨句对齐→比较→聚合”流程：为premise/hypothesis的token表示计算跨句匹配权重，各位置读取对方的加权上下文；将本地表示与对齐表示拼接、相减或逐元素乘积等，再用小网络比较；对有效token的比较特征做sum/mean等聚合，最后预测三类关系。对齐、局部比较和句级聚合各有职责，PAD需从权重与聚合中排除。这个流程是理解文本对推断的经典机制，不要求现代cross-encoder显式分成同样模块；注意力不是事实证据，NLI方向/三类与世界真值边界仍由语言与文本05统一维护。

## 8. ViT与Whisper：复用骨干不等于复制输入处理

ViT的patch局部线性投影可用Conv2d实现；位置/patch参数共享就是结构先验，不能说“永不卷积、完全无归纳偏置”。原站masked patch预测练习并不等于DINOv2训练；DINO/iBOT teacher、蒸馏、对齐/检索与SSL指标由[视觉自监督](../感知与多模态专题/06-自监督视觉与检索学习.md)维护。完整patch/Conv等价、CLS/位置插值、小ViT梯度由[视觉训练第8节](../感知与多模态专题/05-图像表征卷积与视觉训练.md#8-vitpatch是局部投影位置是显式结构信息)维护，必要新2D位置例归入该节而不在这里复制模型。

Whisper是以时间轴log-mel经Conv1d压缩再编码、文字decoder生成的模型，不是把二维mel直接当ViT方形patch；其encoder和decoder层数、80/128mel、第一conv stride1/第二stride2、中心STFT边界/词时间与窗口映射的完整合同与实跑例见[语音识别与流式交互](../感知与多模态专题/13-语音识别与流式交互.md)。源能量标量复制到3000帧并不形成80/128频率滤波器。跨模态是统一部分运算抽象，具体采样单位、encoder可见性与训练目标仍不同。

## 9. 练习与参考判据

1. mask率15%与80%是什么关系？**答**：先选可遮盖位置，再条件分支；80%不指整个语料，随机碰回原词仍是random分支。
2. MLM选中但未改位置是否仍有loss？**答**：有，历史配方就是如此；未选/PAD通常ignore，没有监督batch不计算NaN mean。
3. source小词表while替换何时卡住？**答**：无合法不同普通词时，显式有限候选拒绝或定义允许抽回原值。
4. CLM为何可以看自身输入？**答**：同位置预测下一个token，labels错位；未来改动不可改变此前logit。
5. 全PAD query/key怎么处理？**答**：先定义有效长度或拒绝空项，不以softmax NaN/全0当概率分布；loss mask与attention mask分开。
6. teacher forcing和采样会改变模型PPL吗？**答**：固定语料/模型条件下教师强制PPL不因解码策略改变，生成质量另测。
7. T5 decoder起始等PAD时能否全部mask掉0？**答**：不能，首步合法；用长度/decoder attention mask定义真实padding。
8. T5非sentinel源词+target串能直接拼回吗？**答**：不能，必须在原位置替换相应span并验证结束sentinel/EOS。
9. BART删除后target要删除吗？**答**：去噪目标还是完整原文，input长度与output长度可不同。
10. 为什么不能称随机logits偏置+2为训练？**答**：直接注入目标信息，没有从独立监督学参数；只是oracle效果。
11. 模型选择为何不按encoder速度表决定？**答**：任务/语言/数据/长度/预训练/预算/评价共同决定，不普遍禁止小数据微调或decoder做分类。
12. ViT/Whisper图高亮等于实际运行吗？**答**：不是，固定几何/文字是示意，随机程序也只检查结构，真实模型质量须独立数据。

| 来源任务 | 可执行学习与验收 |
| --- | --- |
| BERT Easy | 分开统计选择率与80/10/10条件分支，特殊词/PAD排除，小词表与无监督batch边界。 |
| BERT Medium | 正确word_id/offset分组，控制token预算/损失与数据划分，whole-word不预设必提高准确率。 |
| BERT Hard | 2层真实随机模型先做有限梯度/数据合同，再在独立句/来源划分的语料训练与同预算分类比较；本批不下载万句语料。 |
| GPT Easy | 下三角/row归一化，再做未来token干预证明prefix不变，mask图不能代替模型检查。 |
| GPT Medium | 使用同模型beam与greedy比较序列得分/任务质量，固定参考语料PPL不随解码改变。 |
| GPT Hard | 区分greedy exact验证与采样分布验证的speculative算法，计入draft成本与拒绝率，不要求两种协议同一输出。 |
| T5 Easy | 原位sentinel映射、closing/EOS、随机段预算与无重叠、空/短输入明确处理；不是直接concat。 |
| BART Medium | 五种noise的具体input→完整clean target示例，infill一个mask覆盖多词不透露长度。 |
| Seq2Seq Hard | 200对独立生成/留出toy语料、相同预算/词表/协议，BLEU配exact/错误类别；不预设T5或更大decoder胜。 |
| ViT Easy | H/W/P/通道合法与patch顺序、Conv等价、CLS/位置shape，复用视觉章已验收CPU小模型。 |
| ViT Medium | 2D位置分别编码row/col，非法D拒绝；真实CIFAR比较需相同seed/预算/切分，本批未下载。 |
| ViT Hard | 小ViT合成梯度不是MNIST成绩，masked-patch损失不是DINOv2；真正SSL须定义teacher/centering/crop/损失与无泄漏划分。 |
| Audio Easy | 无中心framing98/2998与Whisper中心去尾100/3000分开，scalar energy≠log-mel bins。 |
| Audio Medium | FFT/window/power/mel scale/Slaney/HTK/边界/log规范均一致再比数值，不能凭“80 bins”宣布processor相同。 |
| Audio Hard | 窗口10s/overlap2s仅一种fixture，绝对时间/去重/partial稳定/语言/VAD与真WER分别验收，本批不跑podcast权重。 |

## 来源与维护

原D2L的word2vec/负采样/层次softmax/GloVe/子词/类比、情感/NLI/任务head有效知识保留并回链专题。2026-10-05融合 AI Engineering From Scratch Phase07/06～10，固定commit `3be078b37ffd8f0c04953c0678e48f5c6d0c7775`，入口见[来源记录](../../来源保全/AI-Engineering-From-Scratch.md)。日期只新增本批，视觉与音频10-04等旧验证日期保留。

原始/官方核验：[BERT](https://arxiv.org/abs/1810.04805)、[RoBERTa](https://arxiv.org/abs/1907.11692)、[T5](https://arxiv.org/abs/1910.10683)、[BART](https://arxiv.org/abs/1910.13461)、[ModernBERT实现](https://github.com/huggingface/transformers/blob/main/src/transformers/models/modernbert/modeling_modernbert.py)、[T5预处理](https://github.com/google-research/text-to-text-transfer-transformer/blob/main/t5/data/preprocessors.py)。示例在临时CPU环境PyTorch2.14.1/NumPy2.4.6运行，固定合成ID，不下载模型或语料；后续改动按实际代码SHA复核，不以来源当年的API/榜单/速度成为永久知识。
