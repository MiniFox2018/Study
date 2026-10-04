# 04｜注意力机制与 Transformer

> 先修：点积、矩阵乘法、Softmax。先做一个 query 对两个 key 的计算，再扩大到多头；明确每个矩阵的轴比背结构名称更重要。

## 1. 注意力的基本问题

固定长度向量很难无损压缩长序列。注意力允许查询根据当前需求，从一组键值对中动态聚合信息。

基本抽象：

$$
\operatorname{Attention}(q,K,V)=\sum_i\alpha(q,k_i)v_i
$$

其中 $\alpha_i\ge0$ 且 $\sum_i\alpha_i=1$，通常由合法位置上的 Softmax 得到。

## 2. 从核回归理解注意力

Nadaraya-Watson 核回归可视为早期的“查询—键—值”加权平均：

- query：要预测的位置；
- key：训练样本位置；
- value：训练样本标签；
- kernel：相似度函数。

若非负核 $K_h$ 的权重和为正，$\alpha_i=K_h(q-k_i)/\sum_jK_h(q-k_j)$；例如高斯核按距离衰减，带宽小更偏重近邻，大更平滑。value可以是实数标签或向量。核参数可固定或学习；不能把任意负值相似度直接归一后称作概率权重。

这说明注意力本质不是“Transformer 专属组件”，而是一种数据依赖的加权聚合机制。

## 3. Attention Scoring Function

常见评分：

### Additive Attention

通过可学习网络计算 query 与 key 的兼容度，适合维度不一致的情况。典型 $e_i=u^T\tanh(W_q q+W_k k_i+b)$：分别把query/key映射到共同评分宽度，$u$再压成一个标量，对合法key的 $e_i$ 做softmax后加权value。它与点积是不同评分函数，不是把两个不同宽度向量直接相乘。

### Scaled Dot-Product

$$
\operatorname{score}(q,k)=\frac{q^\top k}{\sqrt{d_k}}
$$

若 query/key 分量近似独立、均值为 0、方差为 1，点积方差约为 $d_k$；除以 $\sqrt{d_k}$ 将其尺度控制在常数量级。这是初始化附近的动机，不是任意训练后分布的严格保证。

## 4. Bahdanau Attention

经典 Seq2Seq 用一个固定 context 表示整个输入，长序列形成瓶颈。

Bahdanau Attention 让 decoder 每个时间步都重新对 encoder 的所有隐藏状态分配权重，从而产生动态 context。

它把“对齐”直接变成可学习、可微的模型组件。

## 5. Self-Attention

当 Q、K、V 都来自同一序列时，就是 Self-Attention。

优点：

- 任意位置之间路径短；
- 训练阶段可并行；
- 可以显式建模全局交互。

代价：

- 标准实现的注意力矩阵随序列长度呈 (O(n^2)) 增长。

## 6. Multi-Head Attention

多个 head 在不同投影子空间中独立计算注意力，再拼接：

$$
\operatorname{head}_i=\operatorname{Attention}(QW_i^Q,KW_i^K,VW_i^V)
$$

它允许模型同时学习不同关系模式。

现代模型可能改为 MQA/GQA 等以降低 KV Cache 成本，但多头分解思想仍是理解基础。

## 7. 位置编码

没有位置特征和位置相关 mask 的 Self-Attention 对输入排列等变。位置编码、相对位置偏置或结构性 mask 可以引入顺序信息；不能将带 causal mask 的系统与完全无位置结构的系统混为一谈。

D2L 重点介绍正弦位置编码。长期需要掌握的是：

- absolute position；
- relative position；
- rotary position（RoPE）；
- 位置外推与上下文长度是独立工程问题。

## 8. Transformer Encoder

典型 block：

```text
Self-Attention
→ Residual + Norm
→ FFN
→ Residual + Norm
```

Encoder 适合生成上下文表征。

## 9. Transformer Decoder

Decoder 在 Self-Attention 中使用 causal mask，确保位置 (t) 看不到未来 token；同时在 encoder-decoder 架构中再加入 cross-attention。

自回归生成必须保持训练与推理的因果约束一致。

## 10. Mask 的两类含义

需要区分：

- **padding mask**：忽略补齐位置；
- **causal mask**：阻止访问未来位置。

错误 mask 会造成隐蔽的数据泄漏或训练异常。

## 11. 为什么 Transformer 成为通用架构

关键不是“Attention 比 RNN 神奇”，而是组合优势：

- 全局交互；
- 高度并行；
- 残差网络；
- 归一化；
- FFN；
- 可扩展的数据和计算规模。

## 12. 与现代 LLM 的连接

从 D2L 的 Transformer 继续向现代 LLM 推导：

```text
MHA → MQA / GQA / MLA
absolute/sinusoidal → relative / RoPE
FFN → gated FFN / SwiGLU
LayerNorm → RMSNorm
dense → MoE
full attention → local / sparse / efficient attention
```

因此学习重点应是结构功能，而不是固定在 2017 年实现。

## 手算一次注意力

令 query $q=(1,0)$，两个 key 分别为 $(1,0)$ 和 $(0,1)$，$d_k=2$。打分为 $(1/\sqrt2,0)$，Softmax 权重约为 $(0.6698,0.3302)$。若两个 value 是标量 10 和 20，输出约为 13.3024。

自查：若第二个位置是未来 token，正确遮罩后输出是多少？**答案：**其 logit 设为负无穷再 Softmax，权重变成 $(1,0)$，输出为 10。只把其 logit 乘以 0 无法保证屏蔽，因为 Softmax(0) 仍分到正概率。

若某个 query 的全部位置都被遮罩，Softmax 可能出现未定义/NaN；构造 batch 和 mask 时要先防止这种情况。公式正确仍需要数据形状和合法位置共同正确。

## 13. 并行能力、依赖深度与真正的计算成本

RNN 的一般非线性递推 $h_t=f(h_{t-1},x_t)$ 沿时间形成依赖链；门控和梯度路径可以缓解遗忘，但不保证记住任意长历史。早期“把整段压成单一向量”是特定encoder-decoder设计的瓶颈，不是所有RNN都必须如此，Bahdanau已用动态context改变它。

Transformer训练可对一个已知序列的各位置同时计算本层Q/K/V、分数与输出；层之间仍顺序依赖，自回归生成的下一个未知token通常也依赖已生成前缀。一个batched matmul调用不是一个基本算术步骤，也不是只需一次矩阵乘法：还有softmax、AV、投影和FFN。有限扇入树的求和深度 $O(\log N)$；Hillis–Steele扫描同样是对数层，工作量约 $O(N\log N)$，不能称“scan一层完成”。

固定d的全注意力核心QK和AV工作量 $O(N^2d)$，投影/FFN还受 $Nd^2$ 等项影响。固定d的普通RNN工作量约 $O(Nd^2)$，储存训练中间态与生成状态是不同内存问题。FlashAttention以分块、融合和重计算降低读写/中间矩阵存储，不把全注意力计算变成线性，也不只是在原N²矩阵上“藏常数”。延迟由工作量、依赖深度、带宽、并行度、精度和设备共同决定，不能声称GPU只看深度或浪费99%。

### 13.1 同一前缀和任务的串行与分层扫描

原来源拿 `.9*h+x` 与 `sum(xs)/N` 计时，两函数并非同一数学问题；后者也没有Q/K/V或N²矩阵，不是完整attention速度基准。以下用同一个prefix-sum核对依赖图，Python里的“parallel”循环仍串行运行，不产生GPU速度证据。

```python
import numpy as np

def serial(xs):
    out=[];acc=0.
    for x in xs:acc+=x;out.append(acc)
    return np.array(out)

def hillis_steele(xs):
    out=np.asarray(xs,dtype=float).copy();step=1;levels=0;adds=0
    while step<len(out):
        old=out.copy();out[step:]=old[step:]+old[:-step]
        adds+=len(out)-step;levels+=1;step*=2
    return out,levels,adds
x=np.arange(1024,dtype=float)
p,depth,adds=hillis_steele(x)
assert np.array_equal(p,serial(x)) and depth==10
print('1024前缀和：串行依赖1024，扫描层数',depth,'扫描加法',adds)
# 特殊线性递推可写闭式并行加权和；不能由它证明任意非线性RNN不可重组。
x=np.array([1.,2.,3.]);h=0.
for v in x:h=.9*h+v
closed=np.sum(x*.9**np.arange(len(x)-1,-1,-1))
assert np.isclose(h,closed) and not np.isclose(h,x.mean())
print('加权递推与平均不同',h,x.mean())
```

架构选择看训练/流式生成、上下文长度、状态与KV缓存、领域和精度需求。RNN/SSM、全或局部attention、混合架构都有适用场景；一些SSM能利用可结合扫描训练。不能从Chinchilla等Transformer计算预算研究推出“任意等参数RNN必输”，也不按1B训练token或64K长度设未经核验的绝对禁令。

## 14. Q/K/V、Softmax轴与交叉注意力的完整形状

自注意力输入 $X\in\mathbb R^{B×T×D}$，$W_Q,W_K\in\mathbb R^{D×d_k}$、$W_V\in\mathbb R^{D×d_v}$，分别投影为 $Q,K\in\mathbb R^{B×T×d_k}$ 和 $V\in\mathbb R^{B×T×d_v}$。一般交叉注意力允许 $T_q\ne T_k$：Q来自目标序列，K/V来自源序列，分数是 $B×T_q×T_k$，softmax在最后的**键轴**，输出 $B×T_q×d_v$。K和V的键位置数必须相同，不能转置batch或query轴。

数据库类比只是“按分数聚合”的解释，不是精确检索正确事实的保证。Q/K/V是学习投影，不天生代表某种自然语言语义；同长不同输入通常改变分数，形状和参数保持不变。随机初始化得到不同热图，不代表已学主谓、指代或归纳头。

Softmax减行最大值防overflow，但不能防所有位置负无穷、NaN输入、空行或过小概率下溢。来源示意分数 `[2.1,.3,.1,.8,.2]` 对应的权重应实际重算，原表 `[.52,.09,.07,.14,.08]` 和为.9，不是一行归一权重。注意力权重是模型内部归一系数，不是“这个词是真因果证据”的概率；可视化不替代消融或任务评测。

### 14.1 完整批量注意力与解析反向核对

本实现明确 `allowed=True` 表示可见，每个query至少有一个有效key。张量只支持相同batch，不暗中广播不同样本；一组标量value可用最后一维1。

```python
import numpy as np

def attention(q,k,v,allowed=None):
    q,k,v=[np.asarray(x,dtype=float) for x in (q,k,v)]
    if any(x.ndim!=3 or not np.isfinite(x).all() for x in (q,k,v)):
        raise ValueError('有限B×T×D')
    if not (q.shape[0]==k.shape[0]==v.shape[0] and k.shape[1]==v.shape[1] and q.shape[2]==k.shape[2]) or min(*q.shape,*k.shape,*v.shape)<1:
        raise ValueError('Q/K维度、K/V键长、batch与非空合同')
    s=q@k.transpose(0,2,1)/np.sqrt(q.shape[-1])
    a=np.ones_like(s,dtype=bool) if allowed is None else np.asarray(allowed)
    if a.dtype!=bool or a.shape!=s.shape or not a.any(axis=-1).all():
        raise ValueError('allowed为同形bool，每行至少一个可见键')
    s=np.where(a,s,-np.inf);p=np.exp(s-np.max(s,axis=-1,keepdims=True))
    p/=p.sum(axis=-1,keepdims=True)
    return p@v,p

def backward(q,k,v,p,dout):
    # dA=dO Vᵀ；softmax行Jacobian的向量积；最后补sqrt(dk)缩放。
    da=dout@v.transpose(0,2,1)
    ds=p*(da-(p*da).sum(axis=-1,keepdims=True))
    dq=ds@k/np.sqrt(q.shape[-1]);dk=ds.transpose(0,2,1)@q/np.sqrt(q.shape[-1])
    dv=p.transpose(0,2,1)@dout
    return dq,dk,dv

q=np.array([[[1.,0.]]]);k=np.array([[[1.,0.],[0.,1.]]]);v=np.array([[[10.],[20.]]])
o,p=attention(q,k,v);assert np.allclose(o,13.3023845067)
causal=np.array([[[True,False]]]);om,pm=attention(q,k,v,causal)
assert np.array_equal(pm,[[[1.,0.]]]) and om.item()==10
rng=np.random.default_rng(2);q=rng.normal(size=(1,2,3));k=rng.normal(size=(1,3,3));v=rng.normal(size=(1,3,2));g=rng.normal(size=(1,2,2))
mask=np.array([[[True,False,True],[True,True,False]]]);out,p=attention(q,k,v,mask)
grads=backward(q,k,v,p,g);err=0.
for x,dx in zip((q,k,v),grads):
    for index in np.ndindex(x.shape):
        old=x[index];eps=1e-6;x[index]=old+eps;plus=np.sum(attention(q,k,v,mask)[0]*g)
        x[index]=old-eps;minus=np.sum(attention(q,k,v,mask)[0]*g);x[index]=old
        err=max(err,abs((plus-minus)/(2*eps)-dx[index]))
assert err<1e-7
print('手算输出与causal=10通过；Q/K/V全部梯度max误差',err)
```

正值softmax权重加和为1时输出落在value向量的凸包；后续输出投影/残差/FFN不保留这一凸包约束。attention dropout使一次训练时的权重和未必恰为1，不能把基础公式的所有性质直接套训练中dropout结果。

## 15. 多头、GQA与缓存：参数不等于运行成本

常见MHA总宽D=H×d_h，先将Q/K/V从 `B×T×D` reshape为 `B×T×H×d_h`，再transpose成 `B×H×T×d_h`。分数 `B×H×Tq×Tk`，输出各头 `B×H×Tq×d_h`，逆transpose再拼接，最后 $W_O\in\mathbb R^{D×D}$混合头。不能把reshape和transpose顺序交换而仍当相同分头。

固定D、Q/K/V总投影宽仍为D时，无bias的四投影参数 $4D^2$ 不随H变化；**并非多头免费**。分数/softmax中间态约 BHN²，核调度、头宽和内存访问也变。一个head可结合多种信息，多个head可冗余，没有“每头刚好一种关系”或小于32维必坏的定律。

GQA让Hq个query头共享Hkv组K/V，常见合同Hq能被Hkv整除、每头dk相同。MQA是Hkv=1，MHA是两者相等。K/V投影宽为Hkv×dk，不能仍生成D宽然后随便repeat成更多维。训练从MHA改为GQA可能需要权重转换与适配，不保证无损。

### 15.1 完整split/concat、MHA及GQA对照

```python
import numpy as np
import torch
from torch.nn.functional import scaled_dot_product_attention as sdpa
torch.set_num_threads(1)
rng=np.random.default_rng(4);B,T,D,H=2,4,8,4;dh=D//H
x=rng.normal(size=(B,T,D));weights=[rng.normal(size=(D,D))*.2 for _ in range(4)]
def split(a,heads):
    b,t,d=a.shape
    if heads<1 or d%heads:raise ValueError('总宽能被正头数整除')
    return a.reshape(b,t,heads,d//heads).transpose(0,2,1,3)
def combine(a):
    b,h,t,d=a.shape
    return a.transpose(0,2,1,3).reshape(b,t,h*d)
assert np.array_equal(combine(split(x,H)),x)
q,k,v=[split(x@w,H) for w in weights[:3]]
score=q@k.swapaxes(-2,-1)/np.sqrt(dh)
mask=np.tril(np.ones((T,T),dtype=bool))
score=np.where(mask,score,-np.inf);a=np.exp(score-score.max(-1,keepdims=True));a/=a.sum(-1,keepdims=True)
y=combine(a@v)@weights[3]
tq,tk,tv=[torch.tensor(z,dtype=torch.float64) for z in (q,k,v)]
yref=combine(sdpa(tq,tk,tv,attn_mask=torch.tensor(mask),dropout_p=0.).numpy())@weights[3]
assert np.allclose(y,yref)
# GQA：少量KV头实际存储；numpy repeat仅教学展开，不能把展开缓存说省内存。
hkv=2;wk=rng.normal(size=(D,hkv*dh))*.2;wv=rng.normal(size=wk.shape)*.2
ks,vs=split(x@wk,hkv),split(x@wv,hkv)
kr,vr=np.repeat(ks,H//hkv,axis=1),np.repeat(vs,H//hkv,axis=1)
s=q@kr.swapaxes(-2,-1)/np.sqrt(dh);s=np.where(mask,s,-np.inf)
p=np.exp(s-s.max(-1,keepdims=True));p/=p.sum(-1,keepdims=True)
yt=sdpa(tq,torch.tensor(ks),torch.tensor(vs),attn_mask=torch.tensor(mask),dropout_p=0.,enable_gqa=True)
assert np.allclose(p@vr,yt.numpy())
print('MHA输出',y.shape,'与CPU SDPA一致；GQA未展开KV',ks.shape,vs.shape)
print('KV元素 MHA/GQA',k.size+v.size,ks.size+vs.size)
```

同batch/层/位置数N，KV缓存字节约 $2BNH_{kv}d_h×bytes$，还要加其他状态和分配开销。MQA/GQA减少该部分，不代表整个模型内存同比下降。MLA可共享压缩latent以减少缓存，需要考虑位置相关分支及计算重组，不能把“解压后存回完整KV”仍说成压缩缓存。完整推理解码由[Transformer推理与规模设计](../../LLM%20工程实践/14-Transformer推理与规模设计.md)维护，本章预算和小例提供形状基础。

## 16. 掩码合同：方向、padding、全遮罩与缓存偏移

本章NumPy用True=允许；2026-10-05核对PyTorch官方：`F.scaled_dot_product_attention`的bool也是True=允许，而 `nn.MultiheadAttention/nn.Transformer` 的bool attention/padding mask中True=禁止。浮点mask是加到分数上的bias，禁止处用负无穷；把mask乘0不能屏蔽softmax。

padding key必须在源/目标self-attention和cross-attention相应键轴排除。padding query的输出不会因key mask自动为0，loss/池化或需要时显式query mask处理。源序列可以双向但仍需padding mask；encoder“无因果遮罩”不等“没有任何mask”。全遮罩query需明确拒绝/安全零输出策略，不能靠把NaN删掉冒充概率分布。

方形decoder训练中位置i可看j≤i；已经输入当前位置token，再预测下一个目标。若缓存已含past，Q长1、K长N，直接套从左上起的 `tril(1,N)` 只让它看第一个键，错误。用**绝对query/key位置**构造 $key\_pos≤query\_pos$；官方SDPA非方形causal语义按接口版本核验。

```python
import torch
from torch.nn.functional import scaled_dot_product_attention as sdpa
torch.set_num_threads(1)
q=torch.zeros(1,1,1,2);k=torch.zeros(1,1,4,2)
v=torch.tensor([[[[1.],[2.],[3.],[4.]]]])
# 最后一个query位于绝对位置3，合法键0..3全部可见。
query_pos=torch.tensor([3]);key_pos=torch.arange(4)
allowed=key_pos[None,:]<=query_pos[:,None]
good=sdpa(q,k,v,attn_mask=allowed,dropout_p=0.)
wrong=sdpa(q,k,v,is_causal=True,dropout_p=0.)
assert good.item()==2.5 and wrong.item()==1.
print('缓存绝对位置mask输出',good.item(),'直接左上causal输出',wrong.item())
```

函数式SDPA的dropout按 `dropout_p`执行，不自动读取模块eval状态，评测需显式传0。是否用Flash/其他融合后端取决于设备、dtype、尺寸和mask等，不是调用这个名字就一定CUDA/Flash；本章CPU对照不承担GPU性能证据。

## 17. 正弦、RoPE与ALiBi：可计算不等于可靠外推

没有位置或位置相关mask时，self-attention对重排**等变**：重排输入，输出按同样顺序重排；不是每行数值完全相同的“排列不变”。对整个输出做不计位置的平均池化才可能得到不变结果。causal等结构mask自身含顺序约束，不能把它称彻底无顺序信息。

正弦PE为 $PE_{p,2i}=\sin(p/base^{2i/D})$、奇维配cos，可对任何p计算；实现的表长限制、学到的长度泛化和公式是否有定义是不同问题。learned absolute表外索引需显式处理；普通BERT常用learned absolute，不是正弦。正弦仍是有用教学/任务选择，不因年代淘汰。

RoPE对Q/K的成对分量旋转，$\theta_i=base^{-2i/d_h}$，$R(p)$是各2×2旋转块。固定未旋转q/k有：

$$[R(m)q]^T[R(n)k]=q^TR(n-m)k.$$

相对位置依赖进入内积，**它仍依赖q/k内容**，不能说attention分数只由距离决定。一般每对同时出现cos和sin交叉项，不是只乘一个cos。旋转保范数，共同位移保持这对固定q/k的分数；整网输入/上下文变化时向量本身可能变化。

### 17.1 正确旋转、位置偏置与共同位移测试

```python
import numpy as np

def sinusoidal(n,d,base=10000.):
    if n<1 or d<2 or d%2 or base<=0:raise ValueError('本例正长/偶维/正base')
    angles=np.arange(n)[:,None]*base**(-np.arange(0,d,2)/d)
    p=np.empty((n,d));p[:,0::2]=np.sin(angles);p[:,1::2]=np.cos(angles)
    return p

def rope(x,pos,base=10000.):
    x=np.asarray(x,dtype=float);pos=np.asarray(pos,dtype=float)
    if x.ndim!=2 or x.shape[-1]%2 or x.shape[-1]<2 or pos.shape!=(len(x),) or base<=0 or not np.isfinite(x).all() or not np.isfinite(pos).all():
        raise ValueError('有限T×偶head维与对应位置')
    angle=pos[:,None]*base**(-np.arange(0,x.shape[-1],2)/x.shape[-1])
    a,b=x[:,0::2],x[:,1::2];c,s=np.cos(angle),np.sin(angle)
    y=np.empty_like(x);y[:,0::2]=a*c-b*s;y[:,1::2]=a*s+b*c
    return y
rng=np.random.default_rng(1);q=rng.normal(size=(2,8));k=rng.normal(size=(2,8))
qm=np.array([3,7]);kn=np.array([5,9]);score=(rope(q,qm)*rope(k,kn)).sum(-1)
shifted=(rope(q,qm+100)*rope(k,kn+100)).sum(-1)
assert np.allclose(score,shifted) and np.allclose(np.linalg.norm(rope(q,qm),axis=1),np.linalg.norm(q,axis=1))
# 相同gap、不同q/k不必同分数；共同offset测试必须固定内容。
assert not np.isclose(score[0],score[1])
p=sinusoidal(512,128);assert p.shape==(512,128)
slopes=2.**(-8*np.arange(1,5)/4)  # 4头为2次幂，原论文常见坡度序列。
distance=np.abs(np.arange(5)[:,None]-np.arange(5)[None,:])
bias=-slopes[:,None,None]*distance
assert bias.shape==(4,5,5) and np.all(bias[:,np.arange(5),np.arange(5)]==0)
print('共同位移与范数通过，内容不同两分数',score,'ALiBi slopes',slopes)
```

RoPE通常应用于每头Q/K，是否部分旋转、偶奇交错或split-half配对需匹配checkpoint，旋转维必须成对；V不一定采用同样旋转。缓存中的K已有位置/频率约定，不能中途换base继续复用。i=0的频率是1，与base无关，增base不会拉长**所有**波长，也不消除相位周期性。

ALiBi在合法注意力分数上加随距离线性惩罚；causal时只用历史距离，不能以有限负惩罚替代future mask。斜率按头可不同，非2次幂头数有具体分配规则，本例不冒充全实现。没有位置Embedding参数不等于没有计算/内存成本。长距离惩罚可带来远处信息利用的取舍。

线性位置插值、动态base、YaRN/LongRoPE等改变频率与训练/适配安排，需要按模型原方法核验。某个base公式在d=2还可能除零；不复制它作为任意上下文的万能放大器。能计算到更远位置不代表准确率/PPL/检索可靠；比较相同数据、有效长度、截断/分组、多个位置与任务。NIAH只是其中一个诊断，不能取代完整上下文验收，也不固定8倍或1–5B token的保证门槛。

## 18. Norm、FFN与残差的精确角色

LayerNorm在每个token的D维上计算均值和方差（常用分母D），$y=\gamma\odot(x-\mu)/\sqrt{var+\epsilon}+\beta$；不是对batch/整句归一。RMSNorm不减均值：$y=\gamma\odot x/\sqrt{mean(x^2)+\epsilon}$，常无beta。它会按r缩放均值，不能说“均值保持原值”；零向量仍为零而不是RMS必为1。

pre-norm是 $x+F(Norm(x))$，post-norm是 $Norm(x+F(x))$。post-norm的输出经过归一，不能预言叠12层其激活必爆炸；pre-norm残差累积反而可能使未归一stream范数增长。深层训练的梯度、尺度、初始化、学习率和warmup需共同比较，pre-norm不保证无任何warmup需求。

FFN逐位置共享参数，经典两层 $W_2\phi(W_1x+b_1)+b_2$，本身不混时间；attention负责跨位置聚合。SwiGLU是 $W_2[SiLU(W_1x)\odot(W_3x)]$（行向量实现对应右乘），门控乘法改变表达。固定D，classic hidden=4D无bias参数8D²；三矩阵gate hidden约8D/3可匹配参数。具体宽度常按硬件倍数取整，不是一律2.6D，是否bias也是设计选择而非错误判据。

### 18.1 LayerNorm/RMSNorm的完整反向与参数计数

```python
import numpy as np
import torch
from torch import nn
rng=np.random.default_rng(4);x=rng.normal(size=(2,5));g=rng.normal(size=x.shape);eps=1e-5
xc=x-x.mean(-1,keepdims=True);r=np.sqrt((xc*xc).mean(-1,keepdims=True)+eps);xh=xc/r
ln=xh;dln=(g-g.mean(-1,keepdims=True)-xh*(g*xh).mean(-1,keepdims=True))/r
rms=np.sqrt((x*x).mean(-1,keepdims=True)+eps);yr=x/rms
dr=g/rms-x*(g*x).mean(-1,keepdims=True)/rms**3
for kind,y,analytic in [('LN',ln,dln),('RMS',yr,dr)]:
    z=torch.tensor(x,requires_grad=True,dtype=torch.float64)
    yy=(z-z.mean(-1,keepdim=True))/torch.sqrt(z.var(-1,unbiased=False,keepdim=True)+eps) if kind=='LN' else z/torch.sqrt(z.square().mean(-1,keepdim=True)+eps)
    (yy*torch.tensor(g)).sum().backward()
    assert np.allclose(yy.detach().numpy(),y) and np.allclose(z.grad.numpy(),analytic)
    print(kind,'均值',y.mean(-1),'RMS',np.sqrt((y*y).mean(-1)))
# D512、8头的bias-free MHA + gate hidden2048 + 两个可学RMS gamma。
D,H,HID=512,8,2048
proj=nn.ModuleList([nn.Linear(D,D,bias=False) for _ in range(4)])
ff=nn.ModuleList([nn.Linear(D,HID,bias=False),nn.Linear(HID,D,bias=False),nn.Linear(D,HID,bias=False)])
norm=nn.ParameterList([nn.Parameter(torch.ones(D)) for _ in range(2)])
count=sum(p.numel() for m in [proj,ff,norm] for p in m.parameters())
assert count==4*D*D+3*D*HID+2*D
print('明确配置的单block参数',count)
```

四投影MHA只计 $4D^2$；若GQA参数不同，FFN是否两/三矩阵、Norm参数、cross-attention、输出词表头和共享embedding都需单算。原来源把D4096/32层的乘法估计又叫“每层1.5B”是算术/单位混乱，不能用它拟合某商业模型参数。post/pre-norm对比可作为实测诊断，不把12层随机网络范数当任何模型的训练结论。

## 19. 三种拓扑与可运行完整模型入口

Encoder-only常对源序列双向编码，用于分类、检索或标注；decoder-only用因果self-attention对前缀建模；encoder-decoder把源双向编码，目标因果self-attention再cross-attend源。cross-attention只属于有外部memory的decoder，纯GPT型decoder没有它。架构名称不等固定任务赢家，生成/判别/多模态可有不同适配。

完整模型还需Tokenizer/ID/Embedding、位置约定、输出头、labels移位、loss、优化和评测。原第05课原程序只有随机源/目标矩阵的2层encoder/decoder前向，输出 `T_target×D`，没有词表头、position、final norm或训练；不能把文档里建议的接口当它已有功能。[19｜Transformer实现与训练实践](19-Transformer实现与训练实践.md)将这些连接为可独立运行的CPU训练与生成任务。

## 20. 练习参考答案与来源审查

1. Q/K/V来自同序列是self，Q来自目标、K/V来自源是cross；query/key位置数不同也合法，输出长度随query。权重每行键轴加和1，热图只是内部系数。
2. $D=512,H=8$ 时经典分头 $d_h=64$，不是每头512；参数固定不等kernel/内存免费。MQA/GQA按真实KV宽估缓存，改变头数的收益需训练消融。
3. 允许i看到自己但不看未来，对下一token预测不泄漏；padding和causal是两类合同，Torch两套bool mask方向相反。
4. 随机两句/随机embedding不同图不能解释为已学语法；attention图源`it→cat`是手设亲和加分，缩放图也用固定logits，不是语言模型实绩。
5. 正弦可算超表位置但泛化未保证；RoPE固定内容共同偏移内积不变；内容不同即使同gap仍不同。ALiBi保惩罚又保causal，不能用bias代替禁止未来。
6. 增大RoPEbase不改变i0频率、不保证外推；来源声称Torch functional有通用RoPE工具，当前核验环境没有该公开命名API；RoPE用明确实现或模型官方模块，不用虚构导入。特定模型一律YaRN等型号表也不能沿用，须查配套配置。
7. 原Rust LCG `state>>33`取高31位却按32位最大值归一，均匀变量最高约.5，不能称标准Box–Muller高斯。矩阵/shape/softmax/rotation算法仍可理解，随机分布应改用正确位宽/成熟RNG；没有Rust/Julia环境时只标已读，不标其微基准执行。
8. 源第五课Julia提供LN/RMS解析梯度，本章改成NumPy+PyTorch对照实际核算；RMS缩放均值、不中心化，二者eps影响均方接近而非恰1。
9. 原GPU64..65536计时、复制/长长度256→1024或512→2048、MLA rank质量实验本次未跑。保比较协议：同任务/数据/参数或active预算、device/dtype/cache一致，延迟充分同步预热；不预设固定速度或PPL改善。

增量来源：[ai-engineering-from-scratch](https://github.com/rohitg00/ai-engineering-from-scratch/tree/3be078b37ffd8f0c04953c0678e48f5c6d0c7775)，Phase07第01～05课，读取始于2026-10-04，整理核验2026-10-05。保留既有核回归/Bahdanau/手算/mask内容；原算法中有效部分和语言实现边界融合，剔除硬件浪费率/固定性能/架构统一默认等断言。

一手核验：[Transformer](https://arxiv.org/abs/1706.03762)、[RoPE](https://arxiv.org/abs/2104.09864)、[ALiBi](https://arxiv.org/abs/2108.12409)、[Norm位置](https://arxiv.org/abs/2002.04745)、[RMSNorm](https://arxiv.org/abs/1910.07467)、[GLU变体](https://arxiv.org/abs/2002.05202)、[PyTorch SDPA](https://docs.pytorch.org/docs/stable/generated/torch.nn.functional.scaled_dot_product_attention.html)、[MultiheadAttention](https://docs.pytorch.org/docs/stable/generated/torch.nn.MultiheadAttention.html)。CPU程序只核对数学/合同；没有GPU、外部权重或真实语料训练。
