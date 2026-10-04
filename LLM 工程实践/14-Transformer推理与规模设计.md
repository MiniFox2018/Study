# 14｜Transformer 推理与规模设计

本篇维护路由、缓存、注意力计算与训练规模之间的具体权衡。先读 [Transformer 基础](../AI%20算法基础/深度学习专题/04-注意力机制与Transformer.md)；服务协议和请求调度回到 [推理与服务化](03-推理与服务化.md)、[ML 系统设计](11-AI推理与ML系统设计.md)，设备与并行原理回到 [计算性能](../AI%20算法基础/深度学习专题/06-计算性能与并行训练.md)。下面的合成程序检验数学、形状和状态，不证明真实模型质量或 GPU 加速倍数。

## 1. 先区分容量、算术、搬运和延迟

总参数决定需要存哪些权重，激活参数描述一个 token 参与计算的部分；KV 记录历史状态；中间激活和工作区还有自己的预算。FLOPs 少不一定延迟短：小矩阵利用率、访存、同步、通信和调度都能成为瓶颈。prefill 和 decode、单请求与大 batch 的瓶颈不同，需要分别测量。

全前缀 dense attention 的一次前向约有 `O(T²d)` 算术。生成 n 步若每步重跑整个越来越长的前缀，注意力部分求和是 `Σt²=O(n³)`；使用缓存，只计算新 query 对旧 K 的交互，求和为 `Σt=O(n²)`，每步仍随已见长度增长。参数投影/FFN重算又有自己的成本。源课的 naive/cached 程序都只计算一个 query，对10个前缀的交互数都为55，没有实现历史层/投影重算，不能据它宣布“总注意力 O(n²)→O(n)”或100倍加速。

## 2. MoE：逐 token 路由与有效计算

MoE 用多个独立 FFN 替代某些 dense FFN。输入 `X∈R^(N×d)`，router给每 token E 个分数，top-k选专家集合，输出为 `Σ g_e(X) Expert_e(X)`；每个专家须输出同样的d维才能接 residual。SwiGLU FFN可写 `(SiLU(XW1)⊙XW3)W2`，三矩阵参数约 `3dh`，不是源演示一个线性层就完整复现SwiGLU。

若每专家 P 参数、E个路由专家、S个共享专家、router和其他模块 P_base：总参数为 `(E+S)P+P_base`，每token激活约 `(k+S)P+P_base`。注意力、embedding、router也占容量/计算，不能把整模型简单等同 `E×FFN`。共享专家每token运行，但“学共同知识、路由学专门知识”是设计动机，需实验验证。

### 2.1 容量、overflow 与负载损失

top-k时共N*k个专家分派，均匀目标为 `N*k/E`。容量可以约定 `ceil(capacity_factor*N*k/E)`，实际框架可能用其他舍入/分组。超过容量可丢该分派、重路由、排队或采用dropless调度；丢一个专家分派不一定丢整token，剩余gate是否重新归一必须明确，不能默默改变输出幅度。

一种Switch式辅助目标为 `L_bal=λ E Σ_e f_e P_e`：f为硬分派占比，P为平均router概率。下面将top-k扩展的f定义为 `count/(N*k)`；均匀时 `EΣfP=1`。这不是一般的“专家次数方差”，也不保证达到全局最小就质量最好。还可监测router logits大小、专家饥饿、overflow及每设备负载。

偏置平衡在选择分数上加专家bias，按近期负载增减，gate仍用原始亲和分数。它不产生该bias的辅助梯度，但**改变选择就会改变输出**，不是“完全不影响预测”。例如DeepSeek-V3原报告用sigmoid亲和分数并对所选分数归一，还有互补序列级辅助目标；本例用logit的top-k softmax说明选择/gate分工，不冒称相同实现。更新幅度过大可能振荡；不承诺迭代若干次一定均匀，也不把这种策略宣布成所有新模型默认。

```python
import math
import torch
from torch import nn

torch.set_num_threads(1); torch.manual_seed(4)
class Expert(nn.Module):
    def __init__(self,d=4,h=6):
        super().__init__()
        self.a=nn.Linear(d,h,bias=False); self.b=nn.Linear(d,h,bias=False)
        self.out=nn.Linear(h,d,bias=False)
    def forward(self,x): return self.out(nn.functional.silu(self.a(x))*self.b(x))

experts=nn.ModuleList([Expert() for _ in range(3)])
shared=Expert(); router=nn.Linear(4,3,bias=False)
x=torch.randn(4,4)
# 人工路由分数让所有token先选0/1，检验overflow；不声称已学会路由。
logits=torch.tensor([[3.,2.,0.]]*4,requires_grad=True)
bias=torch.zeros(3)
k=2;capacity=math.ceil(1.0*len(x)*k/3)
selected=torch.argsort(logits+bias,dim=1,descending=True,stable=True)[:,:k]
gates=torch.softmax(logits.gather(1,selected),dim=1)
count=torch.bincount(selected.flatten(),minlength=3)
used=[0]*3;dropped=0; outputs=[]
for t in range(len(x)):
    value=shared(x[t:t+1])[0]
    for e,gate in zip(selected[t].tolist(),gates[t]):
        if used[e]==capacity: dropped+=1;continue
        used[e]+=1;value=value+gate*experts[e](x[t:t+1])[0]
    outputs.append(value)
y=torch.stack(outputs)
f=count.detach().float()/(len(x)*k)
prob=torch.softmax(logits,dim=1).mean(dim=0)
balance=3*(f*prob).sum()
loss=y.square().mean()+0.01*balance;loss.backward()
assert y.shape==x.shape and dropped==2 and used==[3,3,0]
assert torch.isfinite(logits.grad).all() and shared.a.weight.grad is not None
assert experts[2].a.weight.grad is None  # 未选专家没有主任务梯度。
uniform=3*(torch.full((3,),1/3)*torch.full((3,),1/3)).sum()
assert torch.isclose(uniform,torch.tensor(1.))
# 选择bias可改变top-k；固定选择集合时原始logits对应gate不改。
new_bias=torch.tensor([-4.,-4.,4.])
assert not torch.equal(selected,torch.argsort(logits.detach()+new_bias,descending=True)[:,:k])
P=3*4*6
assert (3+1)*P+4*3==300 and (2+1)*P+4*3==228
print("MoE合成：capacity",capacity,"派发",count.tolist(),"丢弃",dropped,"总/激活参数300/228")
```

这段故意不对残余gate重新归一，最后token只走共享专家；生产残差/overflow策略需完整记录。router模块仅展示参数尺寸，人工logits独立测试路由机制；它没有训练真实router或语义专长。

### 2.2 专家并行与训练/推理路由一致性

expert parallel将专家分散到设备，dispatch把token按专家聚合，combine把结果按原token及gate合回。all-to-all通信、最忙专家和跨节点带宽可能决定耗时，但不能认定所有MoE一定通信占主导；小batch、共享专家与本地分片会改变情况。所有权重需存在于某存储层，可分片/卸载，未必全驻同一GPU；激活参数少不代表显存只装这些参数。

细分专家增加可选组合，不意味着每组合是一个独立已训练模型，也不自动提高质量或保持延迟。hash路由可提供稳定分派，学习路由可适配任务，但必须同预算比较，不能预设学习者总胜。策略梯度等工作流应记录生成时的router状态、选中专家、bias/容量和drop策略；若更新时重新选专家，可能改变所评策略。强制复用路由也是一种明确协议，不能冒称自动完成GRPO正确性。

## 3. KV cache：因果位置与完整前向等价

对确定性的因果decoder，未来token不改变旧位置表示，因而每层旧K/V可缓存。开启dropout、改adapter/权重/位置策略或让旧token读取未来时，不能直接保证等价。cache需绑定模型修订、token序列、position IDs、attention/padding mask、KV dtype/分片和上下文策略；同文字但不同chat template或tokenizer不是同前缀。

新输入长为t，旧cache长s，则query绝对位置是`s..s+t−1`，key是`0..s+t−1`；允许key位置≤对应query位置。若只对`t×(s+t)`矩阵画左上角下三角，会让新query错误看不到旧前缀。多token增量、GQA、PAD以及滑窗丢掉旧缓存时还要保留绝对位置和有效长度。

### 3.1 完整小decoder：全序列、逐token、多token与回滚

用两个pre-norm随机block、绝对位置embedding和GQA，每query头对应一组KV。只支持无PAD、同长度batch的fixture；未实现RoPE、分页、量化或生产cache。concat缓存仅用于可读性。代码比较所有位置logits，展示共享前缀分支不原地污染，以及丢掉被拒草稿后下一token与完整重算一致。

```python
import math
import torch
from torch import nn

torch.set_num_threads(1);torch.manual_seed(8)
class Block(nn.Module):
    def __init__(self,d=8,hq=4,hkv=2):
        super().__init__();self.hq=hq;self.hkv=hkv;self.dh=d//hq
        self.n1=nn.LayerNorm(d);self.n2=nn.LayerNorm(d)
        self.q=nn.Linear(d,hq*self.dh,bias=False)
        self.k=nn.Linear(d,hkv*self.dh,bias=False);self.v=nn.Linear(d,hkv*self.dh,bias=False)
        self.o=nn.Linear(d,d,bias=False);self.ff=nn.Sequential(nn.Linear(d,16),nn.GELU(),nn.Linear(16,d))
    def forward(self,x,past=None):
        b,t,d=x.shape;h=self.n1(x)
        shape=lambda z,heads:z.view(b,t,heads,self.dh).transpose(1,2)
        q=shape(self.q(h),self.hq);k=shape(self.k(h),self.hkv);v=shape(self.v(h),self.hkv)
        s=0 if past is None else past[0].shape[2]
        if past is not None:k=torch.cat([past[0],k],dim=2);v=torch.cat([past[1],v],dim=2)
        keys=k.repeat_interleave(self.hq//self.hkv,dim=1)
        values=v.repeat_interleave(self.hq//self.hkv,dim=1)
        allowed=torch.arange(s+t)[None,:]<=torch.arange(s,s+t)[:,None]
        scores=(q@keys.transpose(-1,-2))/math.sqrt(self.dh)
        scores=scores.masked_fill(~allowed,-torch.inf)
        y=(torch.softmax(scores,dim=-1)@values).transpose(1,2).reshape(b,t,d)
        x=x+self.o(y);x=x+self.ff(self.n2(x))
        return x,(k,v)

class TinyDecoder(nn.Module):
    def __init__(self):
        super().__init__();self.embed=nn.Embedding(17,8);self.pos=nn.Embedding(32,8)
        self.blocks=nn.ModuleList([Block(),Block()]);self.head=nn.Linear(8,17)
    def forward(self,ids,past=None):
        if ids.ndim!=2 or ids.shape[0]==0 or ids.shape[1]==0:raise ValueError("非空B×T token序列")
        s=0 if past is None else past[0][0].shape[2]
        if s+ids.shape[1]>32:raise ValueError("超出本fixture位置范围")
        x=self.embed(ids)+self.pos(torch.arange(s,s+ids.shape[1]))
        caches=[]
        for i,block in enumerate(self.blocks):
            x,cache=block(x,None if past is None else past[i]);caches.append(cache)
        return self.head(x),caches

def crop(cache,length):
    if type(length) is not int or length<0 or any(length>k.shape[2] for k,v in cache):
        raise ValueError("只能截到已有有效前缀")
    return [(k[:,:,:length].clone(),v[:,:,:length].clone()) for k,v in cache]

model=TinyDecoder().double().eval()
ids=torch.tensor([[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15]])
with torch.no_grad():
    full,_=model(ids)
    cache=None;parts=[]
    for t in range(ids.shape[1]):
        logits,cache=model(ids[:,t:t+1],cache);parts.append(logits)
    assert torch.allclose(torch.cat(parts,dim=1),full,atol=1e-10,rtol=1e-10)
    _,prefix_cache=model(ids[:,:5]);suffix,_=model(ids[:,5:],prefix_cache)
    assert torch.allclose(suffix,full[:,5:],atol=1e-10,rtol=1e-10)
    _,prefix10=model(ids[:,:10]);_,scratch=model(ids[:,10:],prefix10)
    kept=crop(scratch,12)  # 5草稿中前2被接受，第3被拒，其后全部舍弃。
    correction=torch.tensor([[16]])
    next_logits,_=model(correction,kept)
    rebuilt,_=model(torch.cat([ids[:,:12],correction],dim=1))
    assert torch.allclose(next_logits,rebuilt[:,-1:],atol=1e-10,rtol=1e-10)
    assert prefix10[0][0].shape[2]==10  # 分支没有污染共享前缀。
    assert kept[0][0].shape[1]==2  # 缓存KV头数2，而非query头数4。
try:model(torch.empty((0,2),dtype=torch.long))
except ValueError:pass
else:raise AssertionError("空batch必须明确拒绝")
print("全前向/逐token/多tokenlogits一致；prefix/GQA/回滚一致，空batch拒绝")
```

回滚保留“前缀+已接受草稿”；替代token尚未拥有KV，需下一次把它送入decoder，或按实现显式计算后提交。bonus token同理。只改tokens列表、不修各层KV/位置/页面引用会留下被拒上下文。真实异长batch需按请求维护长度、mask和位置，不能套上例统一s。

### 3.2 KV字节：batch、层、KV头都不能漏

标准K/V缓存估算为 `2×B×L×S×H_kv×d_head×bytes`。前面的2表示K和V，dtype为每元素字节；GQA减的是KV头，query头可仍很多。例 `B=1,L=32,S=32768,H_kv=32,d=128,bytes=2` 是17179869184字节，即16GiB；源课16KB/token漏乘32个头。换8个KV头得4GiB。GB为十进制1e9，GiB为2^30。

paged布局、元数据、padding、碎片、scale和workspace不在这份基础公式中。MLA缓存的是特定低秩latent及位置相关部分，不能把它直接当一个普通K/V头套式子。量化KV的scale、误差和kernel支持也要核验，不能由字节小自动推出质量不变。

## 4. FlashAttention：精确计算的在线softmax与IO

对一行scores，维护已读块的最大值m、指数和l、未归一化输出u。新块最大值m_b，令m'=max(m,m_b)、a=exp(m−m')，则：

$$l'=a l+\sum_j e^{s_j-m'},\qquad u'=a u+\sum_j e^{s_j-m'}v_j.$$

最后输出u/l。旧块指数用a重标定，避免后续更大的score使先前结果失真。数学上等价完整softmax，不是近似注意力；浮点运算重排仍有误差，不能要求逐bit一致。全部被mask的行没有softmax分母，应按明确协议拒绝/屏蔽，不能让−∞减−∞变NaN。

```python
import numpy as np

def online_attention(q,k,v,allowed,tile=3):
    q,k,v=np.asarray(q,float),np.asarray(k,float),np.asarray(v,float)
    allowed=np.asarray(allowed,bool)
    if (q.ndim!=2 or k.ndim!=2 or v.ndim!=2 or q.shape[1]!=k.shape[1]
        or len(k)!=len(v) or allowed.shape!=(len(q),len(k)) or type(tile) is not int or tile<=0):
        raise ValueError("形状/块大小不符合契约")
    if not all(np.isfinite(a).all() for a in (q,k,v)) or q.shape[1]==0:
        raise ValueError("非零维有限输入")
    out=[]
    for query,mask in zip(q,allowed):
        m=-np.inf;l=0.;u=np.zeros(v.shape[1])
        for start in range(0,len(k),tile):
            take=mask[start:start+tile]
            if not take.any():continue
            keys=k[start:start+tile][take];values=v[start:start+tile][take]
            scores=keys@query/np.sqrt(len(query))
            new=max(m,float(scores.max()));a=0. if m==-np.inf else np.exp(m-new)
            weight=np.exp(scores-new)
            u=a*u+weight@values;l=a*l+weight.sum();m=new
        if l==0:raise ValueError("全部mask的query没有概率分布")
        out.append(u/l)
    return np.array(out)

rng=np.random.default_rng(7);q=rng.normal(size=(7,4))*20;k=rng.normal(size=(7,4));v=rng.normal(size=(7,3))
mask=np.tri(7,dtype=bool)
scores=q@k.T/2;scores=np.where(mask,scores,-np.inf)
weights=np.exp(scores-scores.max(axis=1,keepdims=True));weights/=weights.sum(axis=1,keepdims=True)
for tile in (1,2,3,20):assert np.allclose(online_attention(q,k,v,mask,tile),weights@v,atol=1e-12)
try:online_attention(q,k,v,np.zeros((7,7),bool))
except ValueError:pass
else:raise AssertionError("all-masked应明确失败")
print("online softmax在4种tile与完整因果注意力容限内一致；all-masked拒绝")
```

GPU FlashAttention将Q/K/V分块放到片上工作区，融合score/softmax/value累积，避免完整T×T score/probability往返HBM；反向可重算部分中间量，节省存储。它不把dense attention的T²算术变成线性，也不是“所有数据只读一次”或SRAM内装下整个softmax矩阵。本例是NumPy算法核对，没有实现GPU kernel、backward调度或任何速度测试。

## 5. 改注意力拓扑：局部、稀疏、差分与线性

### 5.1 滑窗与稀疏模式

本篇W表示**包括当前token的可见key数量**，因果窗口为 `[max(0,i−W+1),i]`。W≥T恢复全因果mask，W=1只见自身。L层纯局部网络结构上最多经L跳依赖到 `L(W−1)` 个位置之前，不保证真实信息被有效记住。混合全局层后缓存不能全部按W截断，全局层仍保留其所需历史。

local+strided模式允许本地W个和每s个历史位置，配对数约 `O(TW+T²/s)`；只有s和W随T适当选择时才有`O(T√T)`等复杂度。Longformer/BigBird的局部、全局与随机连接有不同设计，不能所有名字都归成同一mask。逻辑稀疏不等物理稀疏：先算完整QK再mask，仍支付dense算术/存储；需兼容block-sparse内核真正跳块。预训练full模型推理时改窗会改变函数，必须评质量，不能当无损加速。

### 5.2 差分注意力的负权重与范围

差分分支算 `(A1−λA2)V`，A1/A2分别为softmax。行和是1−λ，可能含负值，因此不再是普通概率分布。它希望压制共同噪声，但两图是否学会“信号/噪声”并无保证，随机图不能证明消除了attention sink。模型还涉及λ参数化、头布局和输出归一；总KV是否翻倍取决实际维度/共享设计，不能用“两张图”直接推出所有配置2倍显存。

### 5.3 线性注意力更改核，不能冒充softmax等价

令正特征映射φ维度r，因果状态 `S_i=Σ_{j≤i}φ(k_j)v_j^T`、`z_i=Σφ(k_j)`，输出 `φ(q_i)^T S_i/(φ(q_i)^T z_i)`。这等价以`φ(q)^Tφ(k)`为亲和核的dense计算，可用固定大小状态递推；通常不等于`exp(q·k/√d)`softmax注意力。固定状态可能丢历史细节，内存/速度与r、value维度有关。

```python
import numpy as np
rng=np.random.default_rng(2);q=rng.normal(size=(6,3));k=rng.normal(size=(6,3));v=rng.normal(size=(6,2))
phi=lambda x:np.maximum(x,0)+1  # 正特征toy核，不声称复现Performer。
Q,K=phi(q),phi(k);S=np.zeros((3,2));z=np.zeros(3);online=[];dense=[]
for i in range(6):
    S+=np.outer(K[i],v[i]);z+=K[i]
    online.append(Q[i]@S/(Q[i]@z))
    weight=K[:i+1]@Q[i];dense.append(weight@v[:i+1]/weight.sum())
assert np.allclose(online,dense)
T=6;W=3;pos=np.arange(T)
full=pos[None,:]<=pos[:,None]
local=full & (pos[:,None]-pos[None,:]<W)
assert local[-1].tolist()==[False,False,False,True,True,True]
assert np.array_equal(full,full & (pos[:,None]-pos[None,:]<T))
s1=np.array([2.,0.,-1.]);s2=np.array([0.,2.,-1.])
a=np.exp(s1-s1.max());a/=a.sum();b=np.exp(s2-s2.max());b/=b.sum()
diff=a-.7*b
assert diff.min()<0 and np.isclose(diff.sum(),.3)
print("正核在线/完整一致；W含当前项；差分有负权、行和0.3，非概率")
```

## 6. 缩放经验式：拟合与计算最优

经验式 `L(N,D)=A N^(−α)+B D^(−β)+E` 描述特定模型/数据/tokenizer/损失定义和训练方法下的观察，不是任意架构通用定律。E是拟合下界项，不能叫损失ceiling，也不必等于已知真实数据熵。近似训练预算`C=κND`常取κ≈6用于dense矩阵主成本；长序列attention、embedding、优化器、架构和重计算会改变近似。

固定C代入`D=C/(κN)`并求导，得到：

$$N_* =\left[\frac{\alpha A}{\beta B}\left(\frac C\kappa\right)^\beta\right]^{1/(\alpha+\beta)},\qquad D_* =C/(\kappa N_*).$$

所以N*随`C^(β/(α+β))`增长，D*随`C^(α/(α+β))`增长，比例D*/N*随`C^((α−β)/(α+β))`变化。只有α=β等特殊条件下比例才恒定。某研究范围得到约20，不是固定所有预算、微调或MoE的20tokens/param标准；源两条同样0.6√(C/6)还会给比例1，不能同时推20。

```python
import numpy as np
from scipy.optimize import least_squares

def optimal(C,A=406.4,B=410.7,alpha=.34,beta=.28,kappa=6):
    if not np.isfinite([C,A,B,alpha,beta,kappa]).all() or min(C,A,B,alpha,beta,kappa)<=0:
        raise ValueError("拟合系数与预算必须有限且正")
    N=((alpha*A/(beta*B))*(C/kappa)**beta)**(1/(alpha+beta))
    return N,C/(kappa*N)
ratios=[]
for C in (1e20,1e22,1e24):
    N,D=optimal(C);ratios.append(D/N)
    # 对数网格核对解析极小值；不是模型训练。
    grid=N*np.exp(np.linspace(-.2,.2,101));data=C/(6*grid)
    loss=406.4/grid**.34+410.7/data**.28+1.69
    assert np.argmin(loss)==50
assert ratios[0]<ratios[1]<ratios[2]
# 合成可分辨二维网格，用相对单位N/N0、D/D0；未训练任何语言模型。
n,d=np.meshgrid(np.array([1.,2.,4.,8.,16.]),np.array([1.,3.,9.,27.,81.]))
n,d=n.ravel(),d.ravel();truth=np.array([.4,.6,.35,.25,1.3])
def predict(log_params,n,d):
    A,B,a,b,E=np.exp(log_params)
    return A/n**a+B/d**b+E
loss=predict(np.log(truth),n,d)
train=np.arange(len(n))%5!=4;test=~train
fit=least_squares(lambda p:predict(p,n[train],d[train])-loss[train],
                  np.log([.5,.5,.3,.3,1.2]),max_nfev=3000,gtol=1e-12,xtol=1e-12,ftol=1e-12)
error=np.max(np.abs(predict(fit.x,n[test],d[test])-loss[test]))
assert error<1e-7
print("解析最优D/N",[round(x,2) for x in ratios],"合成拟合留出误差",round(error,10))
```

真实拟合需按相同训练协议收集多组N,D与留出损失，记录数据质量、重复token、学习率/训练充分性及tokenizer；报告残差、拟合不确定性、参数可辨识性和外推范围。单条预算曲线或5个点可能难分辨α、β和E，不能把优化器跑完当可靠定律。dense拟合不能直接把MoE active参数代入，未知新token分布的loss也不能和旧拟合比较排名。

### 6.1 训练最优与全生命周期成本

计算最优预训练仅最小化某训练预算下的loss。若要服务大量输出，可选择更小N、更多D，以增加训练投入换部署容量；但最终取决于输入prefill、输出decode、KV、并发、质量约束、总服务量和硬件成本。一个粗模型是训练`κND`加M输出token的`2NM`主矩阵成本，不能忽略长上下文和服务工作区，也不能直接换算成固定价格。

数据质量、重复、优化器、后训练和多模态都可能改变曲线形状/系数，不能声称它们必定只改常数。EM等离散指标会使平滑概率变化表现成跳跃，但某篇对“涌现”的解释不证明所有能力跃迁均不存在；预算要同时看连续损失与任务错误，不能用loss预测保证推理能力。

## 7. 投机采样：分布保证需要接受、残差与条件前缀

本篇统一 **p=目标分布，q=草稿分布**；源课把字母反过来，但正确公式可通过一致换名得到。对于候选y~q，接受率`min(1,p(y)/q(y))`，拒绝后从`r(x)∝max(p(x)−q(x),0)`抽样。

接受贡献为`q(x)min(1,p/q)=min(p(x),q(x))`；总拒绝概率`R=1−Σmin(p,q)=Σ(p−q)_+`，残差贡献为`R*r(x)=(p−q)_+`，相加恰为p。q中为0的token不会被它提出，但可以从残差产生；R=0时不会真正拒绝，不能把“残差无定义”当正常回退。平均单步接受率是`Σmin(p,q)=1−TV(p,q)`，KL相关但不决定一条严格单调接受曲线。`KL(p||q)=Σp log(p/q)`，若p(x)>0而q(x)=0则为无穷，不能跳过这一项返回0。

多草稿必须按草稿前缀自回归提出，各保存**完整q_i分布**；目标一次因果前向得到每个候选位置及bonus位置的p_i。逐个接受到首次拒绝，此后草稿全部丢弃，残差在“已接受的当前前缀”计算；全部接受后再抽一个目标bonus。遇已接受EOS、拒绝替代EOS或bonus EOS应停止提交，丢掉此后的草稿并把cache裁到实际提交长度；最大输出预算只允许提交所需前缀，不能把bonus无条件多发给用户。词表/文本空间映射、temperature/top-k/grammar等处理后的实际分布必须一致可比。greedy相等性验证与随机分布保证是不同协议，不能无条件套给所有Medusa/EAGLE/tree方法。

### 7.1 完整自回归fixture与精确单步证明核对

下例目标/草稿概率随上下文改变，能输出全部接受token、拒绝替代或bonus。为独立展示协议，目标逐prefix调用是fixture，不是真正一次模型并行验证，不能把调用数当加速成绩；第3节独立验证真实小decoder的cache回滚。

```python
import numpy as np

def distribution(values):
    p=np.asarray(values,float)
    if p.ndim!=1 or not len(p) or not np.isfinite(p).all() or np.any(p<0) or not np.isclose(p.sum(),1):
        raise ValueError("非空有限概率向量且和为1")
    return p/p.sum()

def residual(p,q):
    p,q=distribution(p),distribution(q)
    if p.shape!=q.shape:raise ValueError("词表必须对应")
    raw=np.maximum(p-q,0);total=raw.sum()
    if not np.isfinite(total) or total==0:raise ValueError("零或非有限拒绝质量时残差不适用")
    return raw/total

def target(ctx):return distribution([.7,.2,.1] if not ctx or ctx[-1]==0 else [.1,.3,.6])
def draft(ctx):return distribution([.3,.6,.1] if not ctx or ctx[-1]==0 else [.5,.25,.25])

def step(prefix,N,rng,p_model=target,q_model=draft):
    if type(N) is not int or N<1:raise ValueError("草稿长度必须为正整数")
    context=list(prefix);tokens=[];q_dists=[]
    for _ in range(N):
        q=distribution(q_model(context));y=int(rng.choice(len(q),p=q))
        tokens.append(y);q_dists.append(q);context.append(y)
    p_dists=[distribution(p_model(list(prefix)+tokens[:i])) for i in range(N+1)]
    out=[]
    for i,y in enumerate(tokens):
        p,q=p_dists[i],q_dists[i]
        if p.shape!=q.shape:raise ValueError("目标/草稿词表不匹配")
        if rng.random()<min(1.,p[y]/q[y]):out.append(y)
        else:
            out.append(int(rng.choice(len(p),p=residual(p,q))))
            return out,{"accepted":i,"status":"rejected","drafts":tokens}
    p=p_dists[N];out.append(int(rng.choice(len(p),p=p)))
    return out,{"accepted":N,"status":"all_accepted_bonus","drafts":tokens}

p=distribution([.7,.2,.1]);q=distribution([.3,.6,.1])
accepted=np.minimum(p,q);R=1-accepted.sum()
assert np.allclose(accepted+R*residual(p,q),p)
assert np.isclose(accepted.sum(),1-.5*np.abs(p-q).sum())
assert np.allclose(residual([1.,0.],[0.,1.]),[1.,0.])
small=residual([.5+1e-15,.5-1e-15],[.5,.5])
assert np.array_equal(small,[1.,0.])  # 任意真实正拒绝质量保留，不按任意epsilon抹掉。
rng=np.random.default_rng(9);seen=set()
for _ in range(100):
    out,info=step([0],3,rng);seen.add(info['status'])
    assert len(out)==info['accepted']+1 and 1<=len(out)<=4
assert seen=={'rejected','all_accepted_bonus'}
# 完全相同分布必须全接受，bonus也是从新前缀的目标分布产生。
out,info=step([0],3,rng,q_model=target)
assert info['accepted']==3 and len(out)==4
print("精确单步混合=p；自回归草稿、拒绝/全接受bonus、相同分布分支通过")
```

该程序的随机100轮只覆盖分支，分布证明来自上面的恒等式；不是χ²阈值30“证实定理”。经验验证应对固定理论p的频数做正确统计检验、明确样本/预设容差，或检验整段联合概率；拒绝/bonus、EOS、最大输出预算、空合法集合和数值精度都要测试。

### 7.2 可加速条件与系统验证

假设每位置独立同接受率α，N草稿加bonus的期望产出为 `1+α+...+α^N=(1−α^(N+1))/(1−α)`，α=1时N+1。这是简化模型，真实α随位置/上下文变化。分母成本至少有N次草稿、一个长度N的目标验证、同步/缓存/采样及可能prefill；增加N不保证总时延更小，不能把每次验证产出数直接当墙钟speedup。

Medusa增加多位置头并用树候选验证；EAGLE类复用目标特征训练草稿/候选树，具体版本的训练信号与tree安排不同；lookahead利用迭代候选并校验。多位置头的监督可令第i个额外头用同一因果h_t预测t+i+1，分别错位labels并屏蔽不存在的尾部目标；需要说明只训练头还是同时改骨干，后者也改变目标分布。tree验证需让每候选只读取自己的祖先路径，不能让兄弟分支互相看见。方法名不能自动证明精确采样和零质量代价。实际验收先核对生成分布/greedy输出/EOS，再测不同任务、并发和草稿长的TTFT、TPOT、尾延迟、总吞吐、接受率、模型/缓存内存及失败率，见 [评测入口](06-评测与实验管理.md)。

## 8. 分页、共享前缀与调度的具体边界

分页KV按固定token块分配，逻辑位置经block table映射到物理块；长度5、块长4要2块，内部空余3位置。它减少某些外部碎片并支持按块释放/共享，不消灭所有浪费。共享完整前缀块需引用计数，追加到共享尾块要copy-on-write；一次释放请求不能把其他请求仍引用的块归还free-list。

prefix cache命中要包含完整输入和模型状态契约，量化、adapter、位置/attention规则及权限作用域变化都可能失效；相同文本不等于相同KV。cache没有计算新回答，也不保证任何Agent请求5倍收益。动态/continuous batching、chunked prefill需兼顾排队、长输入阻塞、decode尾延迟和取消状态，主要服务定义留在03/11；这篇维护底层状态的正确性。

## 9. 练习与核对答案

1. E=3、k=2、N=4：均匀分派目标8/3，不是4/3；容量系数1时ceil得到3，八次分派全挤两个专家就有2个overflow。
2. MoE300总、228激活来自本例FFN+router部分，不能代表整模型或显存；hash更平衡也未必任务更好。
3. KV公式漏32头会少算32倍。B1/L32/S32768/Hkv32/D128/fp16是16GiB，改Hkv8为4GiB。
4. s=10、t=2的cached mask允许两query分别看到key0～10和0～11，不是画2×12左上角三角形。
5. W=4、L=3纯局部结构最多回溯9位置（含当前共10），不等于可保证回忆12token；全局层另保所需cache。
6. 差分两softmax相减后有负权且和1−λ，不是概率；随机权重变小不能证明真实sink消失。
7. α=.34、β=.28：D*/N*随C^.09677增加。源码两条相同系数平方根式给比例1，不能推20。
8. p=[.7,.2,.1]、q=[.3,.6,.1]：接受贡献[.3,.2,.1]、R=.4、残差[1,0,0]，合成p；反转p/q会错误。
9. 前缀10、草稿5、第3拒绝：旧+前2 accepted的cache长12，再处理替代token；后续3个草稿全部作废，不只改文本列表。
10. 可选真实实践：同一模型比较full/SWA/混合/差分，固定参数与训练token、报告质量/内存/耗时；拟合多组规模的留出loss；模拟page分配释放与共享prefix。开放实验没有预设优胜或固定GPU速度，本次未训练/部署。

## 来源与维护

[AI Engineering from Scratch](https://github.com/rohitg00/ai-engineering-from-scratch/tree/3be078b37ffd8f0c04953c0678e48f5c6d0c7775)，固定 `3be078b37ffd8f0c04953c0678e48f5c6d0c7775`，Phase07第11/12/13/15/16课，整理2026-10-05。正文按统一机制组织，不复制源skills的硬门槛、固定榜单/型号容量/吞吐、Flash版本支持清单或未经核验的模型能力。

原论文核验入口：[Switch](https://arxiv.org/abs/2101.03961)、[Loss-Free Balancing](https://arxiv.org/abs/2408.15664)、[DeepSeek-V3](https://arxiv.org/abs/2412.19437)、[FlashAttention](https://arxiv.org/abs/2205.14135)、[Chinchilla](https://arxiv.org/abs/2203.15556)、[生命周期规模成本](https://arxiv.org/abs/2401.00448)、[投机采样](https://arxiv.org/abs/2211.17192)、[并行引入的采样方法](https://arxiv.org/abs/2302.01318)。核验理论/实现范围与CPU合成验证分开；未下载权重/外部数据、未使用GPU、未调用服务，CPU浮点结果不作为真实kernel速度或模型质量。注意力拓扑依据：[GQA](https://arxiv.org/abs/2305.13245)、[Sparse Transformer](https://arxiv.org/abs/1904.10509)、[Differential Transformer](https://arxiv.org/abs/2410.05258)、[线性注意力](https://arxiv.org/abs/2006.16236)、[PagedAttention](https://arxiv.org/abs/2309.06180)；这些论文中的条件与架构不外推成所有模型的自动质量/速度保证。
