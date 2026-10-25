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

源Phase10/12 attention在缓存时只取K[0]/V[0]，会丢其他batch项；decode还在每层内部advance共享seq_len，多层会错误推进长度。源单层/B1演示能运行不能证明多层/多batch正确。完整decoder应所有层使用同一旧长度，各自返回新cache，由模型/request边界提交一次长度；下方现有两层程序保留这一合同。

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

## 10. 投机采样的训练栈：EAGLE版本、树与词表

### 10.1 先明确基本分布保证的适用边界

本篇继续统一p=target、q=draft。§7的接受/残差/bonus恒等式和§3的真实小decoder回滚程序保留，不重建另一套基础解释。每次候选必须来自所保存的完整q_i，p_i按同一已接受前缀与采样约束计算；q_i仅保存被抽token的标量概率不足以生成残差向量。Phase10/25正文`q_probs[k]`就是标量却从完整p向量逐项减它，错误；该课main.py保存target/draft完整向量的静态fixture则是另一份实现，应分开判断。

Phase10/12草稿token是uniform随机，另生成一组独立Dirichlet作q，又按人为acceptance_rate接受而不用p/q，拒绝时直接从p抽，不是严格speculative sampling。Phase10/15/25只用上下文无关概率分布，不包含真实EAGLE网络、tree LM验证或物理KV；名称和注释不替代能力。min(1,p/q)的极小非零q不能任意改成q+epsilon/max(q,epsilon)后仍声称数学精确；数值稳定应按实际概率/log-ratio与完整合同处理。

若第j候选拒绝，只保留prefix及前j−1 accepted候选的KV；替代token尚待进入目标网络产生自己的KV，不能把旧被拒token的KV当替代token已完成。全部accepted后的bonus同理有“已输出但尚未处理”的阶段。EOS/max-output、每请求实际长度和scratch页面引用都需要按真正提交结果裁剪；源逻辑计数器直接+correction不证明物理缓存已正确。本篇§3.1实际decoder的crop与重算等价检查是这些状态的主验证入口。

### 10.2 EAGLE-1/2/3各自增加了什么

原EAGLE在可用高层特征上做自回归，用向前移动一时刻的已采样token输入消除特征预测的采样不确定性；目标侧的特征层位置和head路径依论文/公开checkpoint实现，不根据名称泛称“最后一层”。特征回归与token预测共同约束草稿输出。树候选和tree attention也已存在，不能说第2代才首次有树。

EAGLE-2基于草稿confidence建立context-aware动态树并在预算内修剪，避免静态树把节点花在难以接受的位置。confidence只是acceptance的近似，不等于target与draft真实接受概率；树宽/深、节点总数和验证成本一起优化。[EAGLE原论文](https://arxiv.org/abs/2401.15077)，[EAGLE-2](https://arxiv.org/abs/2406.16858)

EAGLE-3的公开论文§3.1–3.2将target的low/mid/high特征各d维拼成3d，再FC压到d维g。g与**已采样的下一token embedding**拼接/FC后输入单层causal decoder，得到自由向量a，经LM head得到草稿分布。target尚未验证的后续位置没有真实g，于是用草稿自身a代替该g继续预测。它去掉“a必须逼近target高层feature”的回归loss，以token预测为目标。[EAGLE-3论文](https://arxiv.org/abs/2503.01840)

如果只在真实g输入上训练第一步，去掉feature约束后a可能偏离g的分布；第二步却要使用a，所以第一步接受提高不保证长链草稿也好。Training-time test在训练中展开自己的a作为后续输入，逐步施加token目标。关键是**自由特征的反馈分布**与相应attention因果结构，不是仅把模型输出token再喂回就自动修复exposure bias。原Figure6的多原始位置并行展开，后续测试步只读其正确原始前缀与自身分支，不能让相邻训练位置的不同预测彼此偷看。

不同EAGLE版本、checkpoint、target修订、词表及具体decoder/head协议要匹配。“同家族”并不能保证兼容，更不能把论文的最大6.5×或某batch64实测值转写成所有2026服务默认与固定加速。源练习指§4讲TTT也不准确，§4是实验，方法在§3.1–3.2与Figure3/5/6。

### 10.3 完整随机CPU草稿：fusion与自由向量反馈

以下target是真正随机三层causal Transformer、冻结embedding/head；draft是3d→d fusion、拼token embedding→d、一个causal decoder。输入形状[B,T,d]，每个训练样本独立展开两个测试步；初始g_t与已观察token t+1配对，输出a_{t+1}预测token t+2；再把a_{t+1}追加为下一步feature，不接target的真实feature。监督使用随机teacher同位置soft-target token CE，没有feature回归。

它保留**多层feature fusion、token shift、自由a反馈、因果decoder和完整梯度**这些机制，但不是EAGLE-3 checkpoint复现：teacher没预训练、未实现原多位置展开优化mask/动态树/生产head路径与缓存，也没有真实语料/接受率测量。训练中token输入采用已观察fixture，与推理真正随机采样的区别明确保留。

```python
import torch
from torch import nn
import torch.nn.functional as F
torch.set_num_threads(1);torch.manual_seed(7)
B,T,D,V=12,6,8,17
ids=torch.randint(V,(B,T))
class Teacher(nn.Module):
    def __init__(self):
        super().__init__();self.embedding=nn.Embedding(V,D)
        self.layers=nn.ModuleList([nn.TransformerEncoderLayer(D,2,16,dropout=0.,batch_first=True) for _ in range(3)])
        self.head=nn.Linear(D,V)
    def forward(self,ids):
        h=self.embedding(ids);features=[];mask=torch.triu(torch.ones(T,T,dtype=torch.bool),1)
        for layer in self.layers:h=layer(h,src_mask=mask);features.append(h)
        return features,self.head(h)
teacher=Teacher().eval().requires_grad_(False)
with torch.no_grad():features,target_logits=teacher(ids);teacher_p=target_logits.softmax(-1)
class Draft(nn.Module):
    def __init__(self):
        super().__init__();self.fusion=nn.Linear(3*D,D);self.pair=nn.Linear(2*D,D)
        self.decoder=nn.TransformerEncoderLayer(D,2,16,dropout=0.,batch_first=True)
    def forward(self,g,next_ids):
        pair=self.pair(torch.cat([g,teacher.embedding(next_ids)],-1))
        n=pair.shape[1];mask=torch.triu(torch.ones(n,n,dtype=torch.bool),1)
        a=self.decoder(pair,src_mask=mask)
        return a,teacher.head(a)
draft=Draft();opt=torch.optim.Adam(draft.parameters(),lr=.003)
def objective():
    # g_t pairs with the observed next token e_{t+1} to predict token t+2.
    g=draft.fusion(torch.cat(features,-1))[:,:3]
    shifted=ids[:,1:4];loss=0.
    for j in range(2):
        a,logits=draft(g,shifted)
        loss+=-(teacher_p[:,3+j]*F.log_softmax(logits[:,-1],-1)).sum(-1).mean()
        if j==0:
            # Feed an unconstrained draft vector back; no target feature-fit loss.
            g=torch.cat([g,a[:,-1:]],1);shifted=torch.cat([shifted,ids[:,4:5]],1)
    return loss/2
initial=float(objective().detach())
for _ in range(60):
    loss=objective();opt.zero_grad();loss.backward()
    assert torch.isfinite(loss) and all(p.grad is None for p in teacher.parameters())
    opt.step()
print('random teacher soft-target token CE before/after',initial,float(objective().detach()))
print('fusion/pair/one causal decoder; two-step free-vector feedback; no target-feature regression')
```

本次soft-target CE从约2.9294降至2.7108，teacher参数梯度始终None。这个数字仅证明小网络执行了所定义的优化目标，不是target能力、EAGLE接受率或加速结果。真实草稿训练还要匹配prompt/模板、覆盖实际温度/约束、分层采集与校准/留出、训练数据及权重许可，并测逐深度接受率，不能用简单高斯扰动概率向量冒充训练收益。

## 11. 树状验证：共享前缀不允许兄弟互看

候选树节点携带parent、depth、token；每节点只读committed prefix、自己的祖先及自身位置。把扁平index当连续位置会让同深度兄弟得到不同的位置语义；实际position_ids应按prefix长度+depth定义。生产kernel是否支持任意tree mask、paged/tree cache或稀疏结构须核实，不能声称任意FlashAttention默认支持任意mask。

下面是自含的单头、无position embedding的attention+head随机fixture，算出所有候选位置logits后，与每条单独祖先路径逐一比较，并验证修改兄弟V不影响另一分支。最后做**greedy** walk：在当前节点target argmax候选存在时沿其子节点走，否则输出target argmax并结束。这不同于从所有叶子选概率最大者；后者会改变随机采样分布。

```python
import numpy as np
rng=np.random.default_rng(6)
# Root is last committed prefix token, followed by a 2x2 candidate tree.
parents=np.array([-1,0,0,1,1,2,2]);ids=np.array([0,1,2,3,4,3,4])
E=rng.normal(size=(5,4));Wq=rng.normal(size=(4,4));Wk=rng.normal(size=(4,4));Wv=rng.normal(size=(4,4));head=rng.normal(size=(4,5))
paths=[]
for i in range(len(parents)):
    path=[];cur=i
    while cur>=0:path.append(cur);cur=int(parents[cur])
    paths.append(path[::-1])
mask=np.zeros((7,7),dtype=bool)
for i,path in enumerate(paths):mask[i,path]=True
q=E[ids]@Wq;k=E[ids]@Wk;v=E[ids]@Wv
scores=q@k.T/2;scores=np.where(mask,scores,-np.inf)
a=np.exp(scores-scores.max(-1,keepdims=True));a/=a.sum(-1,keepdims=True);logits=(a@v)@head
for i,path in enumerate(paths):
    sc=q[i]@k[path].T/2;w=np.exp(sc-sc.max());w/=w.sum()
    assert np.allclose(logits[i],(w@v[path])@head)
assert not mask[3,2] and not mask[3,4] and mask[3,1]
# A different sibling value cannot affect this branch's logits.
v2=v.copy();v2[2]+=100
assert np.allclose((a@v2)[3],(a@v)[3])
# Greedy tree walk must follow the current node's target distribution.
cur=0;accepted=[]
while True:
    wanted=int(logits[cur].argmax());children=np.flatnonzero(parents==cur)
    match=[j for j in children if ids[j]==wanted]
    if not match:accepted.append(wanted);break
    cur=match[0];accepted.append(wanted)
print('tree nodes',len(parents),'ancestor counts',mask.sum(1).tolist(),'greedy emitted',accepted)
print('all candidate attention logits match individual paths; sibling isolation')
```

root+2+4共7节点，祖先数为[1,2,2,3,3,3,3]，本次greedy输出[2,2]。未实现全Transformer树、位置/多层KV或随机树采样协议；没有把top3宽树“最长看起来正确分支”叫精确随机采样。若多候选随机拒绝/接受，需要对应提议过程及条件残差证明，普通线性链的公式不自动覆盖任意tree选择。

### 11.1 tokenizer相同是基本p/q的充分接口条件之一

基础p/q公式中的每一坐标必须表示同一token事件，所以词表、special token与ID映射要对应，tokenizer字节不同不能直接按index相减。可研究具有明确文本对齐协议的跨tokenizer辅助生成：decode草稿成文本、带最近上下文重新encode为target tokens，再对齐追加点；target回给draft也要修其被丢弃KV。这比只确认两个模型同家族复杂。[Hugging Face UAG方法说明](https://huggingface.co/blog/universal_assisted_generation)

该官方文章按发布时实现区分跨tokenizer的匹配采样与同tokenizer的严格拒绝采样；不能把UAG支持推成“任意tokenizer可直接套p/q”。具体当前库模式需查实际代码/版本，本章没有运行模型或给出跨词表精确性的新证明。EAGLE专用草稿依target特征结构，更要使用对应模型修订/训练协议。

## 12. 成本、统计与回退策略

### 12.1 产出数不是墙钟加速

恒定独立接受率α的简化模型，K草稿的期望总产出（含correction或bonus）是`Σ_{j=0}^K α^j`，α1时K+1。真实位置条件接受率不同，应该用`1+α1+α1α2+...`，不能用一个平均率抹掉所有相关性。

时间/token应计`(K*C_draft + C_verify(K,prefix,batch) + C_sync/cache/sample)/E[tokens]`。verify长K通常更贵，draft自身KV/feature提取、树scratch、target不同batch利用率也有成本；source默认verify=1只是简化模型。接受率高未必胜过廉价草稿；高并发也不意味着永远禁用，方法与目标设备不同可能改变结果。模型参数/FLOP比例c不能自动当wall-time比例。

```python
import numpy as np
from scipy.stats import chisquare,chi2_contingency

def expected(alpha,K):
    if not np.isfinite(alpha) or not 0<=alpha<=1 or type(K) is not int or K<1:raise ValueError('合法alpha/K')
    return sum(alpha**j for j in range(K+1))
def estimate(alpha,K,draft_step,verify,sync):return (K*draft_step+verify(K)+sync)/expected(alpha,K)
for a in [.5,.7,.9]:
    costs=[estimate(a,K,.04,lambda k:1.+.03*k,.02) for K in range(1,21)]
    K=int(np.argmin(costs))+1
    print('declared varying-verify model',a,'bestK',K,'time/token',round(costs[K-1],4))
assert expected(1.,4)==5 and expected(0.,4)==1
p=np.array([.3,.22,.15,.1,.08,.07,.05,.03]);rng=np.random.default_rng(8)
counts1=rng.multinomial(50000,p);counts2=rng.multinomial(50000,p)
gof=chisquare(counts1,f_exp=50000*p)
hom=chi2_contingency(np.stack([counts1,counts2]),correction=False)
print('fixed-target goodness-of-fit chi2/p',float(gof.statistic),float(gof.pvalue))
print('two-sample pooled homogeneity chi2/p',float(hom.statistic),float(hom.pvalue))
# Larger temperature does not necessarily lower alpha; identical p/q always accept.
logits=np.array([3.,1.,-2.])
for T in [.5,1.,1.5,10.]:
    prob=np.exp((logits-logits.max())/T);prob/=prob.sum()
    assert np.minimum(prob,prob).sum()==1 or np.isclose(np.minimum(prob,prob).sum(),1)
print('p=q accepts at every temperature; finite-frequency checks do not prove exact sampling')
```

在**已声明的虚拟verify=1+.03K**模型、draft每步.04、sync.02下，α=.5/.7/.9在K1–20的最优为3/5/12；换目标/设备/队列就会不同。温度提高不必使接受崩溃：p=q时所有温度都全接受；相同温度处理、alignment与sampling mask才是概率条件。source固定T>.8关闭、α<.4拒绝、K=chat4/code6均不作普适规则。

### 12.2 分布证明与频数检验分开

§7恒等式是数学证明；有限抽样只验证实现可观测的误差。用固定理论p作expected counts可做goodness-of-fit；比较两份随机频数需pooled homogeneity检验，不能拿第二份随机计数当无噪声理论期望再套同一χ²临界值。低expected-count、预先挑样本/重复直到pass、多重比较也要处理。source15的一侧随机χ²14.07门槛不能“证明定理”。source25 10K/32词频的TV是否<.01依样本波动，不是应该保证的阈值。

监测requested/actually drafted/accepted/committed token数、按深度接受、拒绝位置、EOS/长度限制、prefill/verify/draft时间和缓存峰值。每request回退决策要有稳定的滑动窗口与冷启动处理，比较同质量、温度、输出长度、并发下的TTFT/TPOT/尾延迟/throughput。没有原始测量前不记录固定百分比性能。

## 13. 分页缓存的所有权与可运行LRU

分页把逻辑token位置映射到物理block，并非prefix trie的另一个名字。source12只存trie节点/部分KV对象，没有真正page allocator。块长b、序列长n占ceil(n/b)块，末块最多b−1个空位；这不消除metadata、对齐、workspace、动态尾页和所有碎片。contiguous可以动态增长，不是所有实现都预留最大128，所以图中max−seq只是所设策略。

共享前缀需引用计数。写共享未满尾页先copy-on-write；释放一request只能归还无人引用的页面。缓存key由调用者完整编码target修订、tokenizer/模板、adapter、位置/attention规则、dtype/量化以及权限namespace；以下contract只用rev/tenant做示意，不能作为生产key完整设计。

```python
from collections import Counter,OrderedDict
class Pool:
    def __init__(self,size=4,capacity=8):self.size=size;self.free=list(range(capacity));self.pages={};self.refs={};self.requests={}
    def alloc(self,data=None):
        if not self.free:raise MemoryError('page pool exhausted')
        p=self.free.pop();self.pages[p]=list(data or []);self.refs[p]=1;return p
    def start(self,r):
        if r in self.requests:raise ValueError('duplicate request')
        self.requests[r]=[]
    def fork(self,src,dst):
        if dst in self.requests:raise ValueError('duplicate fork target')
        self.requests[dst]=self.requests[src].copy()
        for p in self.requests[dst]:self.refs[p]+=1
    def append(self,r,token):
        table=self.requests[r]
        if not table or len(self.pages[table[-1]])==self.size:table.append(self.alloc())
        elif self.refs[table[-1]]>1:
            old=table[-1];new=self.alloc(self.pages[old]);self.refs[old]-=1;table[-1]=new
        self.pages[table[-1]].append(token)
    def read(self,r):return [x for p in self.requests[r] for x in self.pages[p]]
    def release(self,r):
        for p in self.requests.pop(r):
            self.refs[p]-=1
            if self.refs[p]==0:del self.refs[p];del self.pages[p];self.free.append(p)
    def validate(self):
        assert Counter(p for t in self.requests.values() for p in t)==Counter(self.refs)
        assert not (set(self.free)&set(self.pages))
p=Pool();p.start('A');p.append('A',1);p.append('A',2);p.fork('A','B')
p.append('A',3);assert p.read('A')==[1,2,3] and p.read('B')==[1,2]
p.append('B',4);p.validate();p.release('A');assert p.read('B')==[1,2,4]
p.validate();p.release('B');assert not p.pages and len(p.free)==8
class PrefixLRU:
    # Capacity counts whole-prefix entries, not tokens/bytes. Payloads immutable.
    def __init__(self,capacity):
        if type(capacity) is not int or capacity<1:raise ValueError('positive capacity')
        self.capacity=capacity;self.entries=OrderedDict()
    def insert(self,contract,tokens,kv):
        if len(tokens)!=len(kv) or not tokens:raise ValueError('complete nonempty prefix KV required')
        key=(contract,tuple(tokens));self.entries[key]=tuple(kv);self.entries.move_to_end(key)
        while len(self.entries)>self.capacity:self.entries.popitem(last=False)
    def lookup(self,contract,tokens):
        hits=[k for k in self.entries if k[0]==contract and tuple(tokens[:len(k[1])])==k[1]]
        if not hits:return 0,()
        key=max(hits,key=lambda k:len(k[1]));self.entries.move_to_end(key)
        return len(key[1]),self.entries[key]
c=PrefixLRU(2);c.insert(('rev1','tenantA'),[1,2],['k1','k2']);c.insert(('rev1','tenantA'),[3],['k3'])
assert c.lookup(('rev1','tenantB'),[1,2,4])==(0,())
assert c.lookup(('rev1','tenantA'),[1,2,4])[0]==2
c.insert(('rev1','tenantA'),[5],['k5']);assert c.lookup(('rev1','tenantA'),[3])==(0,())
try:c.insert(('rev1','tenantA'),[6,7],['k6'])
except ValueError:pass
else:raise AssertionError('incomplete KV falsely cached')
print('partial-page fork uses COW; release/refcounts safe; contract-scoped longest complete prefix with LRU')
```

第一部分是真实page table/refcount/COW对象程序，保存整数token作为页载荷以便核查，不是GPU KV kernel。第二部分是**完整前缀entry**的LRU，容量按entry计，payload不可缺，lookup仅相同contract并选最长前缀；它没有承诺trie式任意partial-prefix复用或字节级容量控制。源trie沿结构走到某depth却可能对应kv_data=None，这不能算实际命中。生产可研究按block hash/radix/nodeLRU，同时保活引用，避免eviction删除正在执行的cache。

## 14. 三课完整练习的处理与边界

Inference12五题：FP16/FP8/INT4 KV容量先算Hkv而非Hq、每rank模型分片/缓存/metadata/peak；INT4容量不必4×，质量/支持另验。Pareto请求50条的slot占用曲线应声明arrival/prefill/cost与SLO，不能强制>80%；GQA例Hq64/Hkv8减KV理想8×但不减全部模型内存；LRU500/1000请求共享60%不能保证hit55%，热prefix长度/entry定义/到达模式影响；tree `[2,2,2]`的8叶对应全部节点数和每分支因果，不能把叶子数当verify成本。本章分页/树机制与工程03完整scheduler例给出独立验证，未做真实推理引擎/GPUbenchmark。

EAGLE15五题：50K频数以固定p/pooled test正确检验，不由χ²通过证实定理；N1–10的wall time需要实测成本，virtual formula不叫实际延迟；8条树路径随机选择协议与greedy分开；两序列分别记录accepted/pending correction/bonus及KVcrop，不能统一逻辑length或写成“无任何浪费”；TTT是§3的自由feature反馈，不只是§4某段token自喂。

Spec25五题：精确拒绝本篇§7主入口保留，TV容差按样本/词表与统计设计确定；最优K要有c与verify(K)，α单独不能求有成本的最优；124M→30M/100Mtoken distillation是开放实验，本批不下载/训练，不能预设接受.6–.7；top3树验证用祖先mask/真实target，不从parent列表宣称已验证LM；T1.5是否变慢由p/q和成本测试，不必崩溃。source15/25主程序只做静态分布、parent mask或计数器，它们的完整执行与能力范围另记。

增量来源：固定AI Engineering from Scratch3be078b Phase10/12、15、25及相关source05/19图示，整理2026-10-05。保留原Phase07六个程序的最终代码SHA及当时真实CPU执行证据，本轮只运行新增/变化块；[vLLM当前speculative入口](https://docs.vllm.ai/en/latest/features/speculative_decoding/)用于核验支持与实际版本，未启动服务、下载草稿或模型，不保留“所有服务默认EAGLE3”或未经条件说明的速度排名。

## 15. 把分页与投机机制接到服务调度

### 15.1 token预算、KV预算与先后顺序

§3/8/13已分别维护真实小decoder、KV字节和页面引用，沿用这些已验证程序。服务端每轮还要检查：哪些请求已取消/EOS/到max输出、哪些已有decode工作、还有多少**本轮待计算token预算**，以及是否能提供相应KV块。`max_num_batched_tokens`不是GPU能存的token总数：它约束一轮forward算多少token；cache还为以前的token占空间。因此两预算可独立先耗尽。

连续批处理是在迭代边界接纳/释放请求。V1的chunked-prefill策略会先为decode排工作，再用剩余token预算安排prefill，大prompt不足以一次放入则切块。小token预算可降低decode被长prefill阻塞的ITL，但可能拖长新prompt的TTFT；较大预算可能增prefill吞吐，也可能加重decode尾。default是否启用及数值依引擎版本、模型、任务和并行配置，不能写所有引擎固定512。新请求完整预填充通常能直接产生第一个输出token，状态机必须明确这点，不能将“prefill结束时间”未经真实模型协议就冒称客户端TTFT。

想象预算8，本轮三个decode各耗1，剩5给一个12token新prompt；下一轮decode仍先用3，再给该prompt5，最后一轮给剩2。每轮的KV增长仍需page资源。若队首请求最小资源大于整个池且无其他running请求，应明确拒绝/拆分或转到更大端点，不能无限等待一个永不满足的条件；饥饿还需deadline/等待老化处理。取消时释放所有私有页，但共享页必须按引用计数归还。

源课04的模拟提前为`prompt+max_output`保所有块，并没有按需增长；`waiting and running and not running`分支不可达，超池大请求可反复不进展；prefill结束就记TTFT并非收到first token；未限制总batched tokens。其线性虚拟耗时和static padding也不能代表真实GPU fused batch效果。教学可用其状态名称，但不能用输出证明vLLM的速度排名或“chunk一定吞吐不变”。[vLLM优化文档](https://docs.vllm.ai/en/latest/configuration/optimization/)2026-10-10核验了decode优先、默认条件与token预算调节，未启动服务。

### 15.2 Radix缓存是索引、所有权和排程三件事

Radix树把公共token段压成边，新token串匹配到中途时可拆边，已有KV以paged载荷共享；树的CPU索引不等于GPUattention kernel。完成请求的可复用前缀可保留，LRU从未在用的叶节点递归淘汰，正在执行的路径与祖先必须保护。不是“任意删一个最旧block”而不用修完整路径。§13的旧entry-LRU只是完整前缀entry容量，并未假装复现Radix树。

cache-aware排序利用**当前已经到达**队列的最长可用前缀，帮助相近路径保持驻留，但要兼顾等待上界和租户公平。FCFS仍可作为可预测/公平的基线，不是所有共享场景必错。同batch内命中、跨请求驻留命中、复用token/输入token比例及request-hit比例不能混为一个数。前缀复用主要减少prefill，并不免做新输出decode。缓存边界还要包括模型/adapter/模板/位置与权限namespace，不能跨租户直接复用私密文档。

规范序列化通常将稳定系统约束和工具schema放在前、变化内容放后；但**重排prompt可能改变模型语义与质量**，不应为了hit rate任意移动高优先级指令、历史或检索信息。先固定合法模板，再用同tokenizer/hash与前缀长度分布核查；所谓“文本相似”不等于token前缀相同。失效可能来自早位时间戳/请求ID、模板版本、adapter/dtype/模型变化、冷池/小缓存或路由到另一副本。先分别观测再改。

原SGLang作者2024博客按Llama7B/A10G、旧vLLM0.2.5等配置报告最高5×，这不能支持源课2026H1008B、6.4×或所有prefix-heavy服务固定优胜。当前vLLM的[APC](https://docs.vllm.ai/en/latest/features/automatic_prefix_caching/)也复用公共前缀，源“vLLM全部重复prefill”已不适合作为对照。[SGLang原作者说明](https://lmsys.org/blog/2024-01-17-sglang/)用于核对树操作/LRU与实验条件。

源06玩具池160块，却把SYSTEM125+TOOLS19+DOC32+Q4共180块塞入；插入中可淘汰正构建的祖先，留下无完整路径的节点，甚至超预算。其score对所有带相同SYSTEM的请求可相同，stable-sort仍等于原顺序，不能保证cache-aware收益；它提前知道全部未来请求频率也是离线oracle。生产索引需原子预留/失败回退、pin/refcount、树一致性与边界验证，已有§13所有权程序提供基础检查。

### 15.3 EAGLE接受率：至少保留三个分母

EAGLE-3的feature fusion、去feature回归与training-time test已在§10解释并有CPU小网络，继续维护一个入口。新增服务观察时区分：**位置条件接受概率**（前面的候选已接受时，第j个能否接受）、**总accepted/proposed草稿比例**、**每verification step实际产出长度**（含correction/bonus）。顺序链在首次拒绝后舍弃后续草稿，后两项不能不加条件地代入同一个“每位置独立α”。

若五个位置的条件概率都为0.7，§7/12给期望产出 `1+.7+.7²+...+.7⁵≈2.94117`，不是原课`1+5*.7=4.5`。若每轮成本假设为1.1个plain decode单位，简化speedup≈2.674；这是算式，未测硬件。经验accepted/proposed在每轮固定提议5个时约为`(2.94117−1)/5≈0.388234`，即使位置条件0.7也不是经验比例0.7。同理70%/30%任务的条件接受率.7/.4若每轮5草稿，应先分别算期望产出并按**verification-step占比**加权，而非将request占比直接当step占比；题干给出的blended .61不是wall-time收益证明。

拒绝后的修正抽样使用本轮已算的目标分布与草稿完整分布；算法不要求固定额外一次target forward再“reroll”。修正token的KV待下一轮输入处理，见§3/7，这与同一轮多算一次模型不同。流式响应可能一次发出多个accepted token：均摊批次耗时不是用户真实逐token到达间隔，客户端还可能看到零间隔burst及较长下一块等待。

vLLM当前experimental `metrics.speculative_decoding`把`num_accepted_draft_tokens/num_draft_tokens`记为draft acceptance rate，把`1+accepted/num_spec_steps`记为mean acceptance length；可变draft长度要用实际proposed数。默认不收集，该输出限单sequence，streaming依最终usage chunk，因此“没字段”不等拒绝率0。真实EOS、grammar失效提议和输出截断要明确分母；版本API可能变化。[固定源码说明](https://github.com/vllm-project/vllm/blob/a98247ab4db686ee03c66d5feb3c761e52a2f8ab/docs/features/speculative_decoding/acceptance_metrics.md)

上线对照固定模型/目标分布、模板/温度、输出长与负载，扫K及并发，记录草稿/验证/采样/缓存时间、acceptance histogram、内存、TTFT/ITL/合格请求率与总费用。不能以α≥.55、24h、短输出<50、离线batch或消费卡作为统一批准/拒绝门槛；低QPS低batch恰可能留有空闲算力。原05公式和tail模拟用不同成本模型，固定二次forward与随机均摊不能校准通用阈值。

## 16. 从流式时间线到合格吞吐

### 16.1 first token不是HTTP第一个空chunk

记录请求提交`t0`、第一非空输出token`t1`、后续token或stream chunk时间和最终token`tN`。TTFT=`t1−t0`；N>1时请求平均TPOT=`(tN−t1)/(N−1)`；逐tokenITL是相邻到达间隔的分布。E2E到最后token为`TTFT+(N−1)*TPOT`，末尾DONE/空响应、工具结果或音频播放可有另外终点，必须命名。N=1时无相邻间隔，TPOT记“不适用”，不以0表示“快”。

客户端chunk可能含几个token，而tokenizer估数也可能与服务usage不同。GenAI-Perf当前README按后一个stream response中产出token数分配该chunk间隔；NIM/AIPerf公式排除TTFT，需先确认相同response切分。LLMPerf固定`f1d6bed`的OpenAI client把首TTFT放入间隔总和，并把SSE事件计数当初始output数量；主benchmark采集循环用该数量相除，另一路末尾采集才用重新tokenize数相除。故它不是一套总能等于`E2E/真实N`的协议。名字一样也要对照commit、client、token统计与具体路径。

请求TPOT的P99与所有token间隔的P99也不同：少数请求内部卡住20次，平均后可能平缓；聚合所有token又会让长输出请求权重更大。报告两者时明确单位/分母，按输入/输出长度、租户、冷/暖、缓存命中和错误分层。TTFT含队列、网络、tokenization、prefill及first-output，source三项式只是分解近似，不是所有请求完整时间线。

### 16.2 联合通过率与每秒合格请求分开

设观察窗T秒内提交N个请求，G个同时满足请求级延迟、正确输出/质量及安全要求。联合通过比例是`G/N`，合格吞吐是`G/T req/s`；token-goodput另定义合格请求输出token之和/T。timeouts、失败、缺事件、被取消和队列拒绝需记录各自合同，不能只挑成功请求作分母；取消是否业务主动终止也应单列。

若TTFT/TPOT/E2E每项分别99%合格，联合比例可能只有97%：三组各1%的失败请求互不重叠时正是97%。一请求是否合格按它自己的边界判断，不能问“一请求P99是否合格”；P99是群体统计。也不能仅以三项P99推联合达标。吞吐多与合格率高是互补，优化目标是满足质量/SLO下的容量与成本。

以下程序用**确定性事件**核验边界：第一token已计入TTFT、单token不适用、缺失/超时进入分母、三项分开与联合97%的反例，以及页预算与权重压缩的独立性。时间均为人为输入，未发API请求。

```python
import math

def trace(submitted, arrivals):
    values = [submitted, *arrivals]
    if (not arrivals or any(isinstance(x, bool) or not isinstance(x, (int, float))
        or not math.isfinite(x) for x in values)
        or any(b < a for a, b in zip(values, values[1:]))):
        raise ValueError('非空有限且单调的时间线')
    ttft, e2e = arrivals[0]-submitted, arrivals[-1]-submitted
    tpot = (e2e-ttft)/(len(arrivals)-1) if len(arrivals)>1 else None
    return ttft, tpot, e2e
assert trace(0., [.5,.6,.7]) == (.5, (.7-.5)/2, .7)
assert trace(0., [.5])[1] is None
attempts = [trace(0., [.5,.6,.7]), None, trace(0., [3.,3.1])]
good = sum(t is not None and t[0]<=1 and t[2]<=2
           and (t[1] is None or t[1]<=.2) for t in attempts)
assert good == 1 and good/len(attempts) == 1/3
fail_sets = [{0}, {1}, {2}]
assert all((100-len(s))/100 == .99 for s in fail_sets)
assert (100-len(set.union(*fail_sets)))/100 == .97
# 源09明确假设L64/Hkv8/D128/B128/S2048；不是实测模型架构。
kv = 2*128*64*2048*8*128*2
assert kv == 68_719_476_736 and 35e9+kv+3.5e9 > 80e9
for bad in ([], [float('nan')], [.5,.4]):
    try: trace(0., bad)
    except ValueError: pass
    else: raise AssertionError('非法事件必须拒绝')
print('first-token/单token/失败分母正确；边际99%不等联合97%；教学KV68.719GB使80GB不够')
```

负载测试还要说明开放到达还是固定并发闭环：闭环会在变慢时减少发送，隐藏排队饱和。按实际分布扫描输入/输出长、prefix-hit、并发或arrival rate，报告接受/完成/失败/timeout数、测窗、warmup和样本量。固定30轮×100请求不自动保证可靠P99；当真实超界概率1%、只有100样本，可能完全没见超界，需要不确定性/重采样、持续时间与失败处理。没有业务定义就先写SLO，语音还包含TTS/播放与打断，不能拿文本TTFT固定300ms代替用户等待。

## 17. 服务引擎四课的原练习与测验核对

**引擎04五项练习。** ① 混合长度的static/continuous差异可来自等待/padding/资源回收，原toy虚拟系数不分离真实kernel效率，不能用它给硬件吞吐。② batched-token预算与KV池分开，扫候选值测TTFT/ITL/吞吐/OOM，H100型号与free blocks不足以唯一求值。③ 按实际安装版本完整核对feature/model/backend组合，0.18.0是来源旧快照而非当前版本；本批未安装。④ `Σ(8192−实际有效长度)`是最大预留浪费，分页为`Σ(ceil(n/16)*16−n)`；均值1500和std600不足以求精确余数分布，最末页每请求最多15槽，输入+输出不能漏。若只作可核算例、1000条都长1500，每条ceil(1500/16)=94块、1504槽，末页空4，总空4000槽；最大8192预留则共空6692000槽。两者除各自已分配槽位才是浪费比例，不能混分母。⑤ chunk改任务排程，可平衡compute/memory提高吞吐，也可能增加开销，不能说孤立吞吐必不改。

**04六道测验。** ① static某些实现padding/整批等待会浪费，不能泛称所有static始终一样；② 页与block table减外部碎片，<4%属原论文配置非所有长度；③ 连续调度在迭代边界接纳/释放，而非每请求只调一次；④ 长prefill混合流量优先保护decode ITL，并权衡新prompt TTFT；⑤ 原0.18矩阵允许的组合限其版本/方法/模型，本批不写任意组合必兼容；⑥ chunk会改变计算与访存混合，吞吐影响需测，不接受原“只减jitter所以必不增吞吐”。

**EAGLE05五项练习。** ① K5、条件α恒定，用§7/12几何和除显式成本；教学成本1.1时2×需几何和≥2.2，条件α约≥0.55938；3×需几何和≥3.3，条件α约≥0.75159。只按所设成本数值求根，verify/draft成本变大时要求也变大，不能从1+5α求错误阈值。② .7*.7+.3*.4=.61仅是在同分母/权重条件下的接受概率平均；net-positive还需step/任务权重和成本，见§15.3。③ 当前不止三个模式，查真实引擎列表与feature矩阵，例draft/EAGLE/n-gram不是穷尽。④ mean改善、P99变差先查按深度接受、K/verify成本、batch/队列、chunk发包/时间定义，再降低K、按业务选路或回退，不能断言固定二次forward。⑤ draft参数量×实际dtype字节加scale/feature/cache给容量；需精确checkpoint结构，与1B草稿全参数/缓存比较，题干不足以定值。

**05六道测验。** ① 小batch decode常带宽受限，batch/长KV/模型会改瓶颈，不叫GPU总闲；② α分清条件概率/accepted-proposed比；③ EAGLE3增加多层融合，更关键是去feature回归与自由向量training-time test；④ .55不是通用盈亏点；⑤ 看尾与真实成本、请求质量，不能把拒绝必第二target前向当原因；⑥ 配置是可选加速，实际收益依checkpoint/负载与预算，不是默认所有2026必须开。

**Radix06五项练习。** ① 合法reuse主要省prefill，不免decode，队列排序与cache容量另影响；源score/180入160bug不作速度验证。② 乱序会分成不同token前缀，短公共段仍可复用，所以不是所有命中必归零；先保证语义一致再测。③ HBM按2×layers×Hkv×head_dim×2000×dtype算公共KV；若明确假设L32/Hkv8/D128/BF16，则一份262144000byte≈0.244GiB，16份约3.906GiB。实际8B模型配置仍需核验，page尾/引用/工作区另计，不用参数量猜层。④ 只淘汰无active引用叶子并递归更新祖先，可保持完整路径，任意block删除破坏索引；容量、pin与LRU策略共同决定收益。⑤ 8%命中可查早位动态内容/模板tokenizer、模型adapter/namespace、缓存容量与路由/冷热，分别用prefix分布、key与eviction/路由日志诊断。

**06六道测验。** ① radix token段到KV映射不是fullprompt hash单项缓存；② FCFS可能破坏局部性，但兼有公平/等待优点，不能普遍判错；③ 未用叶子递归LRU并保引用，非固定“最短用分支”；④ 稳定合法模板前置不变段，改序须质量验；⑤ 唯一prefix少可省少，但选引擎看完整kernel/模型功能，不能拒SGLang；⑥ 7%→74%没有本批可核原始部署证据，只保留“动态早位降低可共享prefix”的机制。

**指标08五项练习。** ① 原tail_spike_rate按每token抽不是每request；用相同事件计算request-TPOT与token-ITL、联合分母和新阈值，不预报百分比。② 供应商tok/s至少问同模型/精度/硬件数、输入输出/并发/缓存状态、TTFT/ITL/错误率及测窗。③ chunk可改变mean与tail，保护decode被长prefill占用的间隔，不说只影响P99。④ voice从用户结束说话到可听内容，还要ASR/TTS/播放/取消，按可测流程立约。⑤ 已核工具差异包括首TTFT纳入、chunk/真实token分母和E2E/DONE终点，以及throughput测窗/warmup；先按固定版本源码核对，不凭工具名臆造另外三项差异。

**08六道测验。** ① TTFT通常含排队/网络/预填充，还要tokenize/first输出；② 联合比例与req/s分别报，吞吐不是无用；③ 均值配分位/分层，不笼统拒均值；④ GenAI-Perf/LLMPerf因定义及计数路径不同，见§16；⑤ 长输出常由生成主导但仍需真实长度/延迟；⑥ 800/25/3000ms与99%仅教学SLO，用户需求/输出长/质量定义决定，不能当所有70B标准。原metrics SVG混用“每请求P99”与联合比例已改正。

本节增量来源：固定AI Engineering from Scratch`3be078b`，Phase17第04/05/06/08课，整理2026-10-10。论文方法选读为[投机解码v2](https://arxiv.org/abs/2211.17192v2)§2.3/3.1/Algorithm1、[EAGLE3v3](https://arxiv.org/abs/2503.01840v3)§3.1–3.2及Figure5，图式已目检；LLMPerf固定[f1d6bed client](https://github.com/ray-project/llmperf/blob/f1d6bed47e4501b0e371082b41601b59ab55269f/src/llmperf/ray_clients/openai_chat_completions_client.py)与[benchmark](https://github.com/ray-project/llmperf/blob/f1d6bed47e4501b0e371082b41601b59ab55269f/token_benchmark_ray.py)，[GenAI-Perf README](https://github.com/triton-inference-server/perf_analyzer/blob/main/genai-perf/README.md)及[NIM定义](https://docs.nvidia.com/nim/benchmarking/llm/latest/metrics.html)核对相关段；没有执行模型/服务benchmark。源动态图04列分矩阵不是PagedAttention，06roofline不是Radix索引，08固定饱和曲线不是SLO实验；这里只保留其一般分片/带宽/吞吐尾延迟含义。

## 来源与维护

[AI Engineering from Scratch](https://github.com/rohitg00/ai-engineering-from-scratch/tree/3be078b37ffd8f0c04953c0678e48f5c6d0c7775)，固定 `3be078b37ffd8f0c04953c0678e48f5c6d0c7775`，Phase07第11/12/13/15/16课，整理2026-10-05。正文按统一机制组织，不复制源skills的硬门槛、固定榜单/型号容量/吞吐、Flash版本支持清单或未经核验的模型能力。

原论文核验入口：[Switch](https://arxiv.org/abs/2101.03961)、[Loss-Free Balancing](https://arxiv.org/abs/2408.15664)、[DeepSeek-V3](https://arxiv.org/abs/2412.19437)、[FlashAttention](https://arxiv.org/abs/2205.14135)、[Chinchilla](https://arxiv.org/abs/2203.15556)、[生命周期规模成本](https://arxiv.org/abs/2401.00448)、[投机采样](https://arxiv.org/abs/2211.17192)、[并行引入的采样方法](https://arxiv.org/abs/2302.01318)。核验理论/实现范围与CPU合成验证分开；未下载权重/外部数据、未使用GPU、未调用服务，CPU浮点结果不作为真实kernel速度或模型质量。注意力拓扑依据：[GQA](https://arxiv.org/abs/2305.13245)、[Sparse Transformer](https://arxiv.org/abs/1904.10509)、[Differential Transformer](https://arxiv.org/abs/2410.05258)、[线性注意力](https://arxiv.org/abs/2006.16236)、[PagedAttention](https://arxiv.org/abs/2309.06180)；这些论文中的条件与架构不外推成所有模型的自动质量/速度保证。


## 18. 综合推理服务：把无损采样、负载和收益放在同一合同

<a id="17-综合推理服务把无损采样负载和收益放在同一合同"></a>

本章§7、§10与§15已经有完整投机采样条件、EAGLE机制、树mask、KV回滚和调度，不再复制算法。综合项目要解决的是：所服务的实际target是哪一版，在同一负载与采样协议下，投机是否增加合格请求吞吐并降低总费用。

### 一次接受规则的偏差核对

令两词target `p=(0.8,0.2)`，draft `q=(0.5,0.5)`。按正确拒绝采样，A总是接受，B以0.4接受；拒绝事件的总质量为0.3，残差`normalize(max(p−q,0))=(1,0)`。最终A概率`0.5+0.3=0.8`，B为`0.5×0.4=0.2`。如果像源脚手架只收`p(token)≥0.5·max(p)`的A，然后拒绝处直接重新从p抽，A会变成`0.5+0.5×0.8=0.9`，已不等原target。

真正随机实现保存完整q和已接受prefix条件下的p；greedy则按target argmax判匹配，不能把随机baseline与另一greedy接收混在一起。拒绝suffix后修正采样、全接受bonus、停止/EOS和KV回滚沿用已有程序；量化改变目标模型分布，所谓无损是相对于同一实际target协议，不能恢复未量化权重的质量。

### 用同工作量验收收益

先冻结模型/量化/adapter/tokenizer/template、温度及采样过滤、输入/输出长、prefix命中、实际到达过程和硬件。无投机baseline、多个K/draft、off或ngram回退使用同质量约束和流量；记录draft生成、verify、采样、KV与排队时间，TTFT、ITL、完整响应和合格请求率，并计内存、失败、重试与费用。候选、检查、接受prefix、最终commit和末轮截断各有计数，不能用固定K×calls作所有情形分母。

[当前vLLM投机文档](https://docs.vllm.ai/en/latest/features/speculative_decoding/)选读明确关联memory-bound及中低QPS的延迟优化，也按工作负载区分方法。这里只保留决策方式，不沿用vLLM0.7/SGLang0.4的具体开关或旧模型名称。target call减少忽略了草稿成本，不能当真实speedup；低接受率时ngram未必获益，应包含关闭投机的对照。调度/扩缩容/滚动升级沿§15及[推理与服务化](03-推理与服务化.md)，终态与排队SLO优先于教材固定2.5倍目标。
容量预算还要包含实际weight、KV、activation、workspace与draft，不用70B×2B约140GB就推断141GB显存能完整服务。

### 原综合项目的实现范围与图示

draft.propose直接target.distribution且ctxseed仅pos，不依真实生成token；target未来分布与实际prefix无关系，无KV。

verify阈值不是p/q，拒绝补原p，baseline随机却docstring称greedy；tokens_verified只是常数统计，无batch forward/真实时间。

metric speedup=targetcalls ratio，未计draft/verify cost与真实硬件；最后一轮full accepted计数可包含未committoken。

固定0.7/0.4与EAGLE3支持绑定年代不作为当前recipe，currentvLLM docs说明workload/支持条件；P-EAGLE/name/speculator下载版本若未核不保保证。

.76acceptance与3.2accepted/step缺K/分母不能互相推出；所有固定2.5x、accept.6–.8、rejection总增p99和MOErouting注入结论需实测。

静态图吸收：draft→target批验→acceptedprefix＋修正/bonus→stream；图直接fromtarget重抽应改残差，不能展示threshold算法为无损；metrics/rolling drain为工程合同。 动态标记`cf-spec-decode`的实际函数由本批统一核对记录；动画不是训练、网络、吞吐或防御实验的证据。

### 五项原练习的中文实践判断

1. **draft/target版本漂移**：真正存在draft/target版本对照，固定采样与任务分布，记录收益和tail，不编不存在Llama3.4案例。
2. **ngram/off回退**：fallback比较ngram/off/其他draft的实际收益与SLO，带hysteresis/holdout，不仅低α机械切换。
3. **MoE路由实验**：MoE研究先定义可控扰动/训练路由实现，性能/质量/分布改变分别看；不能把未核routing noise当生产操作指南。
4. **更大显存容量**：H200容量仍要算runtime/KV/context/concurrency与binarydecimal单位；70B16bit名义140GB不代表141GB显存能跑完整服务。
5. **推理引擎对照**：同硬件/revision/量化/采样/负载对TRT/vLLM，报joint quality/TTFT/ITL/goodput/wallcost，不预设供应商wins。

这些真实实践均未在本轮执行；上面的标准库验证只覆盖标出的合同。

### 七道原测验的中文核对

1. **草稿与target怎样保持分布？**：草稿候选target批量verify，正确accept/residual维护目标分布，简单acceptprefix不足保证。
2. **EAGLE3与ngram如何区别？**：EAGLE3多层特征融合训练token prediction参见既有章节，不承诺所有任务高接受率。
3. **为何分负载报告P99？**：按负载/长度/请求级P99与batch分层才能看回退/大verify成本，不是拒绝每次必更慢。
4. **接受率为何发生漂移？**：输入分布/版本与采样条件影响q对p匹配，需独立计actual。
5. **queuewait为何只是信号之一？**：queuewait可用扩缩容信号配容量/冷启动，CPU不是理论禁止。
6. **parallel/tree方案能随意等同吗？**：parallel/tree候选应按实际论文/实现协议，不能把所有parallel草稿称唯一P-EAGLE树定义。
7. **2.5倍能当统一门禁吗？**：2.5x仅教材作业门槛，不满足也可能值得上线或停用，按业务goodput和成本门限。

增量来源：[AI Engineering from Scratch，Phase19/14](https://github.com/rohitg00/ai-engineering-from-scratch/tree/3be078b37ffd8f0c04953c0678e48f5c6d0c7775/phases/19-capstone-projects/14-speculative-decoding-server)，固定`3be078b37ffd8f0c04953c0678e48f5c6d0c7775`，2026-10-11逐文件静读正文、Python、全部关联TS模块/测试/配置、产物要求、测验及SVG；产物中的Skill/安装/调用/部署要求只作学习材料。旧代码字节保留，无来源程序、模型、API、设备、真实服务、训练或攻击执行。


## 19. 分页实现：容量、块复用与最后一个token

这组实现例固定vLLM **0.31.0 / db9527a46873454610df6dbedf79a36d6bf1a7f6**，外层来源截止2026-10-23，本次2026-10-24～25静读/纯数据核算。作者捕获主要10月17～23日；这是可追溯教学快照，不是当前安装版本推荐。原程序、模型、HTTP服务、SDK、CLI与测试均未执行。

### 19.1 先对齐预算的分母和单位

对普通全注意力、未做额外压缩的一份KV，理想载荷为`2×本地层数×本地KV头数×head_dim×每值字节数`。TP、KV头复制、滑窗/混合层、MLA/状态空间、页对齐及元数据需要另算，不能把全模型公式无条件除以GPU数。

Qwen3-8B教学配置为36层、8 KV头、head_dim128，BF16为147456字节=144KiB/token；Qwen3-30B-A3B为48层、4 KV头，BF16为98304字节=96KiB/token。MoE权重总量更大不表示KV更大，专家权重与注意力KV是两项预算。

作者L4比较把池固定为1506个16-token块，即24096token。每请求512输入＋128输出=640token、没有共享、全部增长到该长度时，可容纳floor(24096/640)=37份，余416token。启动打印24096/8192≈2.94x用的是每请求占满8192的估计，不是实际最多只能两个用户。日志40个running也不矛盾：尚未写满输出时持有更少KV；并发上限还受调度、工作空间和SLO限制。

一GiB除以144KiB/72KiB得到理想7281/14563个完整token，但在16-token块分配下应先按块向下取整，分别7280/14560token，再扣其他布局开销。来源fig2.4是理想字节计算，不是实测容量，不能用其7281当真实可分配块数。

`gpu-memory-utilization`约束单实例的计划份额，分母是设备总量而非启动时空闲量；0.31.0来源默认0.92，作者实验又显式设0.9/0.75/0.83，不可混称默认实验。权重、profile激活、CUDA graph、KV池分别占内存。`kv-cache-memory-bytes`直接指定KV预算，官方该pin说明非None时会忽略`gpu_memory_utilization`的自动估算；`num-gpu-blocks-override`用于控制实验的固定块数，不能当不检查物理内存的生产扩容手段。

| 失败证据 | 先判断什么 | 有针对性的改变 |
|---|---|---|
| 目标份额大于实际free memory | 其他进程/已有实例占用 | 调整实例预算或经授权协调占用者 |
| 一条max_model_len请求装不进KV池 | 单请求最大长度与可用KV | 在任务允许范围内缩长度，或真正增加KV容量 |
| profile/graph capture阶段OOM | 激活峰值、批大小、图捕获工作区 | 调整max_num_seqs/token budget/graph尺寸并重测 |
| weights还未加载完成就OOM | 权重本体与布局 | 合适量化/分片/硬件；不能指望改KV参数解决所有权重问题 |

来源有两处措辞冲突：前文正确说“降低max_model_len通常不增大已固定的池”，批处理/排障页又把它直接叫“给池增加内存”。应区分单请求上限、profile/图产生的间接变化和实际池容量；固定同一block pool时，改长度上限不会凭空增加token槽。

GB10统一内存还与OS、页缓存和其他程序竞争，计划份额不是OS级硬隔离。作者日志121.69GiB可见内存、56.93GiB权重、31.32GiB available KV、约3GiB其他开销，份额0.75约91.3GiB。实验手动将KV池缩到234960token以接近另一引擎，不能拿31.32GiB/96KiB推导的约342098token替换其实际池。营销“128GB”与运行时可见GiB还涉及单位/预留，不直接写数学等号。权重加载330.5秒是作者单次观察；没有证明所有GB10重启都同速或固定份额安全。

全注意力层保留其历史KV，滑窗层只需要窗口内块，Mamba等状态空间层保留每请求状态及可复用检查点，不能按全注意力的每tokenKV公式统一乘。混合模型按层类型组织cache groups，每组有页布局与命中条件；一段文本相同，不证明所有组需要的状态都仍可用。RoPE/YaRN等长度推导和Mamba checkpoint模式在版本间改变时，核实际派生长度、内存与runner，不能只把max_model_len手工增大就宣布模型支持该质量范围。

### 19.2 引用计数、复用队列和logits边界

前缀键按前块hash和本块token串链，LoRA、多模态输入与租户salt等会影响键；稳定system/tool前缀放前，常变问题/时间/请求ID放后。共享20token在16-token块例中复用前16、重算余4；但块长并非所有backend/混合模型都固定16，读取实际配置。

完整prompt已命中也不意味着本轮zero compute。同pin的`kv_cache_manager.py:289～299`把最大命中长度设`num_tokens−1`以重算末token取得logits；对齐还可能导致整个末块重算。相同32-token prompt、块长16的教学反例中，最大命中31只能按完整块复用16，其余重算。这解释了为什么“所有完整命中块都不再算”仍需最后一块边界。

请求结束、引用计数变0的缓存块可进free queue并保留hash；被后来的相同前缀使用前再取出/增加引用。官方`block_pool.py`先复用无hash的空块，缓存块在队尾保持FIFO/LRU式淘汰，重新分配时才移除旧hash。**free queue真空时并没有另一批可随意驱逐的闲置缓存块**；所有块被引用时需排队或先抢占释放。来源fig8.3“队列空时再驱逐LRU cached block”的图注会混淆这点，不能覆盖仍被运行请求引用的块。

缓存省的是已命中部分prefill，不是“旧turn免费”：后续decode仍读所需KV，缓存占内存，外存回载还占带宽/时间。摘要/截断中间对话也会改变相应位置之后的前缀；只为命中而永不删上下文不一定符合任务预算或信息时效。

租户salt应由可信网关从身份/隔离政策派生，不能靠任意调用方填一个可猜salt获得授权。哈希也不证明内容/模型版本可信。权重/适配器/位置语义变化或RL更新后应明确失效合同，避免旧KV套上新权重。

### 19.3 算法保证与服务实际产出分开

完整投机接受/残差采样、EAGLE训练和树mask继续维护在7/10/11/12/15.3，不复制一个弱化版本。固定示例若18个提议draft中接受5个、共6次verify，则accepted/proposed=5/18≈27.8%，在每次verify都贡献一个correction/bonus且无提前截断的计数合同下，产出均值1+5/6≈1.833。若总响应12 token含prefill首token，则余11/6才对应这6次verify的产出；不能用12/6替换所有字段定义。EOS、末尾预算、可变draft与具体引擎计数范围都要明确。固定成本下更深草稿不一定更快；新runner/async支持也可能随proposer改变，性能证据统一看[评测35](06-评测与实验管理.md)。

自检：24096/640为什么只保证37份完整长度？整除余416，且未考虑额外限制；日志40running为何不必矛盾？尚未增长到上限；32-token整命中为什么可能只复用16？末token logits与块对齐；free queue空时能否直接改仍被引用的块？不能。

来源为[第一来源固定vLLM手册](https://github.com/rohitg00/ai-engineering-from-scratch/tree/3f9715c62a3bedcffb68a260f1a65ee2dd9cc10a/manuals/vllm-101)。同pin官方[executor配置](https://github.com/vllm-project/vllm/blob/db9527a46873454610df6dbedf79a36d6bf1a7f6/vllm/config/parallel.py)、[UniProcExecutor](https://github.com/vllm-project/vllm/blob/db9527a46873454610df6dbedf79a36d6bf1a7f6/vllm/v1/executor/uniproc_executor.py)、[KV管理](https://github.com/vllm-project/vllm/blob/db9527a46873454610df6dbedf79a36d6bf1a7f6/vllm/v1/core/kv_cache_manager.py)、[BlockPool](https://github.com/vllm-project/vllm/blob/db9527a46873454610df6dbedf79a36d6bf1a7f6/vllm/v1/core/block_pool.py)与[缓存配置](https://github.com/vllm-project/vllm/blob/db9527a46873454610df6dbedf79a36d6bf1a7f6/vllm/config/cache.py)关键段已核。134路径读取层次、24个摘录有序匹配、154测量点字段投影、已存统计核与独立算术范围见[10融合记录](../维护/来源更新/2026-10-24/10-vLLM运行缓存与测量融合.json)。来源记录内部一致不等真实GPU复现或用户已经掌握；缺失逐题/逐请求原始数据的范围没有补造。


## 计算练习：MoE损失与在线softmax的边界

第2节定义f=count/(T*k)、P为全专家概率的token均值，均匀分配时EΣfP=1，但1不是普遍下界。三个token、两专家、top-1概率为(.51,.49)、(.51,.49)、(.01,.99)：f=(2/3,1/3)，P=(103/300,197/300)，损失403/450<1。相反，所有logit相等且同分选低id时，路由可能全挤专家0而损失仍为1。应同时观察硬分配、overflow和设备负载；不能只凭这个辅助数判断均匀或任务质量。原练习随机fixture还出现.9701768001385012，与反例方向一致，但数值表不是定理证明。

在线softmax合并新块时，旧指数和l与加权累加器a都要乘exp(m_old-m_new)，最终输出a/l、logsumexp=m+log(l)。先处理全屏蔽首块的-inf-(-inf)，最后不足整块也不能漏。本练习NumPy工作区为O(Tq*min(block_size,Tk))，只有固定块长时随Tq线性；block_size>=Tk仍生成全score块。这验证在线归一化机制，不证明真实GPU FlashAttention速度。单层预分配KV的append先核K/V行数和容量，再复制并增长length；失败保持旧状态，keys()/values()的view也不自动防外部写。已有完整decoder/page/树验证继续保留。


2026-10-25增量：基于[固定3f9715c的计算练习](https://github.com/rohitg00/ai-engineering-from-scratch/tree/3f9715c62a3bedcffb68a260f1a65ee2dd9cc10a/practice)，源截止2026-10-23。已读题目/参考/提示并按知识去重复用，未运行来源练习、测试或训练；反例仅自写标准库核算，旧程序及原成功日期不变。51题落点、710路径读取层级与本批正文验证见[11记录](../维护/来源更新/2026-10-24/11-算法练习纠偏与训练路径融合.json)。
