# 22｜MDP、表格法与回合实践

先读[强化学习主线](11-深度强化学习.md)的MDP/价值/TD概念，本章用概率、条件期望与小数组把它们变成可独立运行的表格算法。无需先学DQN、PPO或世界模型，后续复杂系统再接[进阶与世界模型](15-强化学习进阶与世界模型.md)。所有环境都是内存里的合成状态机/格子，不操作真实游戏、机器人或业务系统，不安装Gym或下载数据。

## 1. 建模先决定状态、奖励时点和终止

MDP可用状态S、动作A、联合转移 $p(s',r\mid s,a)$、初始状态分布及目标/折扣描述。联合分布同时处理下一状态和奖励随机性；写 $P(s'|s,a)$、$R(s,a,s')$ 时需说明R是确定奖励还是条件期望。策略 $\pi(a|s)$给动作概率，不是环境转移概率。合法动作也可能随状态变化。

统一时间：在 $S_t$选择 $A_t$，环境给 $R_{t+1},S_{t+1}$；

$$G_t=R_{t+1}+\gamma R_{t+2}+\cdots+\gamma^{T-t-1}R_T.$$

当前奖励、一步回报和价值是不同对象。$V^\pi(s)=E_\pi[G_t|S_t=s]$，$Q^\pi(s,a)=E_\pi[G_t|S_t=s,A_t=a]$；Q在第一动作固定后从下一步跟π，不等一条轨迹的实际结果。

Markov状态是对未来动力学/奖励足够的描述，不必等于当前observation。棋盘还需轮到谁、王车易位/吃过路兵/历史规则等；帧堆叠或RNN可以帮助推断隐藏变量，却不保证任意任务变完全可观测。部分可观测任务可用历史/信念状态或明确POMDP处理，不能把它一概归为“建模者失败”。有限时域若规则依剩余时间，应把时钟/剩余步数纳入状态。

RL可用示范、离线数据或模型，未必只有在线奖励无任何标签；DPO等偏好目标不能因有关联就都叫在线RL。状态/动作/奖励框架帮助理解，不自动证明所有方法共享同一种策略更新或critic。

### 1.1 γ、单位与手算值

无限折扣、奖励有界时 $0≤\gamma<1$使 $|G|≤R_{max}/(1-\gamma)$。$\sum\gamma^k=1/(1-\gamma)$是权重总量，“有效horizon约100步”不是100步以后权重为零；物理时间还需每步秒数。γ1在有限回合/适当终止条件下可合法；无限零奖励序列也有return0，所以不能说γ1必让所有值无穷，但唯一固定点/一般收敛需另证，average-reward目标又是另一问题。

4×4格子每移动一次奖励−1，最短到goal需6步：**未折扣总奖励−6**；γ.99的最优折扣值是 $-\sum_{k=0}^5.99^k≈-5.851985$。同一曲线不能一边报折扣MC G、一边把−6叫同协议DP答案。全为负奖励时，增γ通常让V更负，离goal较远的长尾更敏感；不是价值“更快变好”。

正比例缩放全部奖励在固定目标下保最优策略，但值/优化尺度改变；加常数、clip或按轨迹归一可能改变回合时长偏好和目标。reward shaping要检查真实目标、单位和是否改变最优解，不能随意归一成[-1,1]就说任务不变。

## 2. Bellman递归、残差与DP的假设

$$V^\pi(s)=\sum_a\pi(a|s)\sum_{s',r}p(s',r|s,a)[r+\gamma V^\pi(s')],$$
$$Q^\pi(s,a)=E[r+\gamma\sum_{a'}\pi(a'|s')Q^\pi(s',a')],\quad
V^*(s)=\max_aE[r+\gamma V^*(s')].$$

终止后续价值约定0，终止**转移**的奖励仍算一次。已知有限模型时可枚举期望；采样的step只给一个结果，不等知道全部P。Model-based/model-free按算法是否利用模型学习/规划分，不因环境是几行Python就自动叫model-based。

给定π，令 $P_\pi(s,s')=\sum_a\pi(a|s)P(s'|s,a)$、$r_\pi=E[R_{t+1}|s]$，有 $(I-\gamma P_\pi)V=r_\pi$。γ<1时折扣Bellman算子在sup norm为γ contraction，唯一固定点。浮点线性求解与迭代仍要核对残差，不把打印几位小数叫精确数学解。

为什么contraction成立？对同一动作的两种价值U/V，转移概率加权差至多$\|U-V\|_\infty$，再乘γ；max的差也不超过各动作差的最大值，所以$\|TU-TV\|_\infty≤\gamma\|U-V\|_\infty$。固定点为V*时，三角不等式给$\|V-V^*\|≤\|V-TV\|+\gamma\|V-V^*\|$，移项即下面的残差界。

若 $\delta=\|TV-V\|_\infty$，则误差界 $\|V-V^*\|_\infty≤\delta/(1-\gamma)$（给定策略用其T和Vπ）。γ越近1，同一残差阈值的价值误差界越宽。同步sweep的相邻迭代变化与最终Bellman残差不同；in-place逐项变化也不能不加说明当最终残差。

先手算一次backup：无slip、γ.9、V₀全0，第一轮非terminal V₁都为−1，goal仍0。第二轮在(3,2)，向右进goal的Q=−1；其它三动作Q=−1+.9×(−1)=−1.9。最优backup取max得到−1，uniform policy backup取平均得到−1.675。这是规划目标与策略预测目标的实际区别，不能将Vπ和V*混用。

## 3. 完整转移模型、策略/价值迭代与修改策略迭代

程序固定goal15、四动作up/down/left/right，边界动作留在原地，仍付−1；进入goal那一步也付−1，之后reward0。Slip用.9本动作、两个垂直动作各.05，碰壁导致重复next-state时概率相加。模型、策略概率必须非负、归一且有限。本DP实现刻意限定γ<1，γ1的有限horizon后面另说明。

```python
import numpy as np

def grid_model(slip=0.):
    if not np.isfinite(slip) or not 0<=slip<=1:raise ValueError('slip范围[0,1]')
    S,A,goal=16,4,15;P=np.zeros((S,A,S));r=np.full((S,A),-1.)
    moves=[(-1,0),(1,0),(0,-1),(0,1)]
    for s in range(S):
        for a in range(A):
            if s==goal:P[s,a,s]=1;r[s,a]=0;continue
            perp=[2,3] if a<2 else [0,1]
            for action,prob in [(a,1-slip),(perp[0],slip/2),(perp[1],slip/2)]:
                row,col=divmod(s,4);dr,dc=moves[action]
                nr,nc=np.clip([row+dr,col+dc],0,3);P[s,a,int(4*nr+nc)]+=prob
    assert np.all(P>=0) and np.allclose(P.sum(2),1)
    return P,r

def check(P,r,gamma):
    if P.ndim!=3 or P.shape[0]!=P.shape[2] or r.shape!=P.shape[:2] or not np.isfinite(P).all() or not np.isfinite(r).all() or np.any(P<0) or not np.allclose(P.sum(-1),1):raise ValueError('MDP矩阵合同')
    if not np.isfinite(gamma) or not 0<=gamma<1:raise ValueError('本程序折扣γ在[0,1)')
def q_from(P,r,V,gamma):return r+gamma*np.einsum('san,n->sa',P,V)
def evaluate(P,r,pi,gamma):
    check(P,r,gamma)
    if pi.shape!=r.shape or np.any(pi<0) or not np.isfinite(pi).all() or not np.allclose(pi.sum(1),1):raise ValueError('策略概率合同')
    kernel=np.einsum('sa,san->sn',pi,P);reward=(pi*r).sum(1)
    V=np.linalg.solve(np.eye(len(P))-gamma*kernel,reward)
    assert np.max(np.abs((pi*q_from(P,r,V,gamma)).sum(1)-V))<1e-9
    return V

def value_iteration(P,r,gamma,tol=1e-8,max_sweeps=10000):
    check(P,r,gamma);V=np.zeros(len(P))
    if tol<=0 or max_sweeps<1:raise ValueError('正tol/预算')
    for sweep in range(1,max_sweeps+1):
        V=q_from(P,r,V,gamma).max(1)
        residual=float(np.max(np.abs(q_from(P,r,V,gamma).max(1)-V)))
        if residual<=tol:return V,np.argmax(q_from(P,r,V,gamma),1),sweep,residual
    raise RuntimeError('预算用尽未达到Bellman残差，不假称收敛')

def policy_iteration(P,r,gamma):
    check(P,r,gamma);actions=np.zeros(len(P),dtype=int);evaluations=0
    for outer in range(1,100):
        pi=np.eye(r.shape[1])[actions];V=evaluate(P,r,pi,gamma);evaluations+=1
        q=q_from(P,r,V,gamma);greedy=q.argmax(1)
        # 当前动作已是数值容差内最优时保留它，防等价动作来回更换。
        best=q.max(1);keep=np.isclose(q[np.arange(len(P)),actions],best,rtol=0,atol=1e-10)
        new=np.where(keep,actions,greedy)
        if np.array_equal(new,actions):return V,actions,outer,evaluations
        actions=new
    raise RuntimeError('策略迭代预算未稳定')

def modified_policy_iteration(P,r,gamma,k):
    check(P,r,gamma)
    if type(k) is not int or k<1:raise ValueError('每轮k个正评估sweep')
    V=np.zeros(len(P));actions=np.zeros(len(P),dtype=int);total_sweeps=0
    for outer in range(10000):
        pi=np.eye(r.shape[1])[actions]
        for _ in range(k):V=(pi*q_from(P,r,V,gamma)).sum(1);total_sweeps+=1
        actions=q_from(P,r,V,gamma).argmax(1)
        residual=float(np.max(np.abs(q_from(P,r,V,gamma).max(1)-V)))
        if residual<1e-8:return V,outer+1,total_sweeps,residual
    raise RuntimeError('MPI预算用尽')

for slip in [0.,.1]:
    P,r=grid_model(slip)
    for gamma in [.9,.99]:
        V,a,sweeps,res=value_iteration(P,r,gamma);Vp,ap,outer,evals=policy_iteration(P,r,gamma)
        assert np.allclose(V,Vp,atol=1e-6)
        print('slip/gamma/start/VI sweeps/PI outer/residual',slip,gamma,V[0],sweeps,outer,res)
        print('V*\n',np.round(V.reshape(4,4),3))
        if slip==0:assert np.isclose(V[0],-sum(gamma**i for i in range(6)))
# uniform action平均后对称slip转移不变，所以同π的Vπ也不变。
P0,r0=grid_model(0.);P1,r1=grid_model(.1);uniform=np.full((16,4),.25)
assert np.allclose(np.einsum('sa,san->sn',uniform,P0),np.einsum('sa,san->sn',uniform,P1))
assert np.allclose(evaluate(P0,r0,uniform,.99),evaluate(P1,r1,uniform,.99))
print('uniform Vstart',evaluate(P0,r0,uniform,.99)[0],'对称slip不改Pπ通过')
reference=value_iteration(P1,r1,.99)[0]
for k in [1,2,5,10,50]:
    V,o,s,res=modified_policy_iteration(P1,r1,.99,k)
    print('MPI k/outer/实际评估sweeps/start误差',k,o,s,abs(V[0]-reference[0]))
```

本次CPU核对：无slip时VI用6个sweep得到最优起点值−5.851985；slip .1、γ.99时得到−6.428252。Uniform π在γ.99时的线性解是−39.411648，确实可四舍五入成源程序的−39.41；它属于这个特定模型和π，不能当别的环境/策略的通用gold。MPI的k=1/2/5/10/50分别用25/26/35/60/200个实际评估sweep达到同残差阈值，这只说明本模型下更充分的每轮evaluation未必更省总扫描。

PI的evaluation这里是一次线性求解，不是原脚本“sweeps+=1”那样把outer计成所有内层扫描。稀疏转移每sweep成本随 $\sum_{s,a}|support(P(\cdot|s,a))|$；稠密模型最坏O(S²A)，线性求解成本也另算，不是固定O(SA)或10⁷状态通用上限。in-place/synchronous取舍依顺序、数据结构和误差预算，不能预定一个永远更快。

## 4. 策略改进与有限时域的不同问题

Greedy新策略π′使$T_{π′}V^π≥T_πV^π=V^π$；按同一新策略反复backup，凭单调性和折扣收敛得到$V^{π′}≥V^π$。因此精确evaluate并greedy improve在相应折扣有限MDP下不降低价值；稳定处理ties可避免等价策略循环。近似evaluate、神经值误差或模型不准时不自动继承该保证。Value iteration/MPI等体现GPI，但“都可叫GPI”不是所有Q-learning/PPO等都有同一收敛证明。MCTS还含选择/扩展/估计/回传，不能简化为普通全状态DP。

γ1无限任务需适当条件；有限时域可以从最后一步向前算 $V_h(s)=\max_aE[r+\gamma V_{h-1}(s')]$，$V_0=0$。此处h是剩余机会，计时影响最优动作/价值。给有限任务时限和外部采样上限用相同`done`会改变问题，下节专门区分。

```python
import numpy as np
# 两非终止状态A/B+terminal；A安全立即1结束，风险立即0转B，B下一步给3结束。
P=np.zeros((3,2,3));R=np.zeros((3,2));P[0,0,2]=1;R[0,0]=1
P[0,1,1]=1;P[1,:,2]=1;R[1,:]=3;P[2,:,2]=1
V=np.zeros(3);history=[V.copy()]
for remaining in [1,2]:
    Q=R+np.einsum('san,n->sa',P,V);V=Q.max(1);history.append(V.copy())
    print('剩余步数/VA/greedyA',remaining,float(V[0]),int(Q[0].argmax()))
assert history[1][0]==1 and history[2][0]==3
print('相同A但剩余时间不同最优动作不同，状态需时钟')
```

## 5. Episode、终止与截断

真实terminated由任务定义：到goal、任务失败或内在有限horizon用完；后续value0。外部truncated是收集暂停，底层MDP仍能继续，通常接final observation的bootstrap。自动reset后的新observation不是截断末态，保存transition时必须用最后真实观测。

纯MC需要完整return。外部cap200后把tail设0会改变估计；只删超时回合也会按未来结果选择样本而引入偏差。可延长至自然终止、把有限任务/时钟明确建模，或用tail value构造有说明的n-step/hybrid目标；不能把最后一种叫不含bootstrap的完整MC。

```python
# continuing singleton：每步1，γ.9，真实V=10；每步因外部采样上限停止。
gamma,alpha=.9,.1;correct=wrong=0.
for _ in range(600):
    reward,terminated,truncated=1.,False,True
    correct+=alpha*(reward+gamma*(0 if terminated else correct)-correct)
    wrong+=alpha*(reward+gamma*(0 if terminated or truncated else wrong)-wrong)
assert abs(correct-10)<.03 and abs(wrong-1)<1e-10
print('继续任务外部截断：正确bootstrap/统一done误算',correct,wrong)
# 与已有11手算一致：V2,r1,Vnext3,γ.9,α.1。
print('真正终止/仅截断一次更新',2+.1*(1-2),2+.1*(1+.9*3-2))
```

这个failure例在内存里模拟，不调用Gym。源MDP rollout记录undiscounted total而policy evaluation用γ.99，MC源码200cap后零tail、硬编码−39.41和最优−6也需逐项区分协议，不能混成一个gold reference。

## 6. First-visit与every-visit：先算return，再按正序选访问

给完整episode $(S_t,A_t,R_{t+1})$，逆序计算 $G_t=R_{t+1}+\gamma G_{t+1}$；first-visit指**正向第一次**，不是逆序扫描遇到的第一项（那是最后访问）。状态估值对s去重，动作价值对(s,a)去重。Every-visit保留同回合全部访问，样本相关，有限样本比率估计可能有偏；固定policy、适当回合/矩条件下可一致，不保证每任务方差更低或收敛更快。

以下A状态每次有.5概率reward1后继续A，.5概率reward2后终止，固定唯一动作；γ.9的真值为 $V=1.5/(1-.45)=2.72727$。完整回合自然终止，极端保护预算用尽会中止并报错，不静默用短return或剔除。

```python
import numpy as np
rng=np.random.default_rng(13);gamma=.9

def returns_from(rewards,gamma):
    G=0.;out=np.empty(len(rewards))
    for t in range(len(rewards)-1,-1,-1):G=rewards[t]+gamma*G;out[t]=G
    return out
# 明确多次访问：A,A,B的reward1,2,3，γ.5；A first=2.75，every平均3.125。
states=['A','A','B'];ret=returns_from([1.,2.,3.],.5)
assert np.allclose(ret,[2.75,3.5,3.])
first={};every={}
for s,G in zip(states,ret):
    if s not in first:first[s]=G
    every.setdefault(s,[]).append(G)
assert first['A']==2.75 and np.mean(every['A'])==3.125
fv=ev=0.;nf=ne=0;first_returns=[]
for _ in range(4000):
    rewards=[]
    for t in range(10000):
        if rng.random()<.5:rewards.append(2.);break
        rewards.append(1.)
    else:raise RuntimeError('保护上限触发，未得到完整MC回合')
    G=returns_from(rewards,gamma);nf+=1;fv+=(G[0]-fv)/nf;first_returns.append(G[0])
    for value in G:ne+=1;ev+=(value-ev)/ne
truth=1.5/(1-.5*gamma)
se=np.std(first_returns,ddof=1)/np.sqrt(nf)
print('first/every/真值/first标准误差',fv,ev,truth,se,'样本数',nf,ne)
```

未访问状态值是“未知/初始化”，不能把Q表中的0当已验证V=0。评估Vπ应比同π的DP答案；V*是另一条策略的最优值，不能自动当普通MC预测的真值。First-visit标准误差需独立固定策略回合等假设，every-visit不能按所有访问次数当iid来缩小误差条。

### 6.1 GridWorld完整采样与同π的DP核对

这里与第3节同一个4×4环境，uniform π每步四动作各.25，γ.99。先算同π线性解，再用**自然终止**轨迹估first/every值，报告raw return、折扣return、每状态首次访问次数和检查点；不能只拿最优−6作随机policy的真值。末态V=0是已知边界，未访问非末态仍是未知。下例是完整自含程序，不依赖前面的变量。

```python
import numpy as np
import random
S,goal,gamma=16,15,.99
moves=[(-1,0),(1,0),(0,-1),(0,1)]
def step(s,a):
    if s==goal:return goal,0.,True
    row,col=divmod(s,4);dr,dc=moves[a]
    nr=max(0,min(3,row+dr));nc=max(0,min(3,col+dc));ns=4*nr+nc
    return ns,-1.,ns==goal
# uniform π的Pπ，不需要知道哪条轨迹最后走了哪个动作。
P=np.zeros((S,S));reward=np.full(S,-1.);reward[goal]=0
for s in range(S):
    for a in range(4):ns,_,_=step(s,a);P[s,ns]+=.25
for g in [.5,.9,.99]:
    truth=np.linalg.solve(np.eye(S)-g*P,reward)
    print('uniform gamma/V矩阵',g,'\n',np.round(truth.reshape(4,4),3))
truth=np.linalg.solve(np.eye(S)-gamma*P,reward)
rng=random.Random(18);fv=np.zeros(S);ev=np.zeros(S);nf=np.zeros(S,dtype=int);ne=np.zeros(S,dtype=int)
raw=[];starts=[]
for episode in range(1,10001):
    s=0;trajectory=[]
    for _ in range(10000):
        a=rng.randrange(4);ns,r,done=step(s,a);trajectory.append((s,r));s=ns
        if done:break
    else:raise RuntimeError('自然终止保护上限，整项MC实验中止而非删样本/零tail')
    G=0.;returns=np.empty(len(trajectory))
    for t in range(len(trajectory)-1,-1,-1):G=trajectory[t][1]+gamma*G;returns[t]=G
    raw.append(sum(r for s,r in trajectory));starts.append(returns[0]);seen=set()
    for (s,r),G in zip(trajectory,returns):
        ne[s]+=1;ev[s]+=(G-ev[s])/ne[s]
        if s not in seen:nf[s]+=1;fv[s]+=(G-fv[s])/nf[s];seen.add(s)
    if episode in [100,1000,5000,10000]:print('episodes/first Vstart/DP值',episode,fv[0],truth[0])
assert np.all(nf[:goal]>0) and nf[goal]==0
print('raw回报mean/std',np.mean(raw),np.std(raw,ddof=1))
print('first/every Vstart/同π DP',fv[0],ev[0],truth[0])
print('first V矩阵\n',np.round(fv.reshape(4,4),3),'\n首次访问次数\n',nf.reshape(4,4))
print('start独立回合SEM',np.std(starts,ddof=1)/np.sqrt(len(starts)))
```

本次10,000回合：raw mean/std=−59.8252/50.0123，first/every Vstart=−39.685884/−39.577692，first的start SEM≈.21547；同π真值−39.411648。检查点误差没有严格单调下降，有限随机样本出现反复很正常，不能把“曲线每次更接近”写为算法保证。

固定策略、从start独立重置的回合使每条start return可作独立样本；every-visit的同回合多个return不满足同样的iid假设。其它状态的首次访问样本数小于回合总数。源代码在200步强行结束，原运行Vstart−38.89与同π DP−39.411648存在差距；一次seed的差距包含有限采样与截尾影响，不能仅凭数值给二者各分配多少误差。

## 7. 完整ε-soft MC控制与探索条件

ε-greedy通常随机动作包含greedy动作：K个动作、一项唯一greedy的总概率为 $1-ε+ε/K$，其它各ε/K。多个并列greedy时先规定是随机并列还是固定序，行为概率与IS日志保持一致。ε>0只保证在**已经访问的状态**各动作有概率，不保证所有状态可达或无限访问。

本程序4×4自然terminal，逆序return/正序first(s,a)/采样平均/ε-greedy improvement俱全，外部保护cap用尽显式失败。固定ε的控制不应宣称Q必是纯greedy Q*；政策随估计变化，历史return并非当前π的独立同分布样本，sample-average和constant-alpha各有取舍。源称只满足访问/Robbins条件就保证所有MC控制Q*太强，需具体算法和定理对应。

```python
import numpy as np
import random
moves=[(-1,0),(1,0),(0,-1),(0,1)]
def step(s,a):
    if s==15:return 15,0.,True
    row,col=divmod(s,4);dr,dc=moves[a];r,c=np.clip([row+dr,col+dc],0,3)
    ns=int(4*r+c);return ns,-1.,ns==15

def choose(Q,s,epsilon,rng):
    if rng.random()<epsilon:return rng.randrange(4)
    best=np.flatnonzero(Q[s]==Q[s].max());return int(rng.choice(list(best)))

def mc_control(epsilon,episodes=1500,seed=14):
    rng=random.Random(seed);Q=np.zeros((16,4));N=np.zeros((16,4),dtype=int);curve=[]
    for episode in range(episodes):
        s=0;trajectory=[]
        for t in range(2000):
            a=choose(Q,s,epsilon,rng);ns,r,terminal=step(s,a);trajectory.append((s,a,r));s=ns
            if terminal:break
        else:raise RuntimeError(f'ε={epsilon}, episode={episode+1}：2000步保护上限，未自然结束；实验中止，不使用截尾return')
        G=0.;returns=np.zeros(len(trajectory))
        for t in range(len(trajectory)-1,-1,-1):G=trajectory[t][2]+.99*G;returns[t]=G
        seen=set()
        for (s,a,r),G in zip(trajectory,returns):
            if (s,a) in seen:continue
            seen.add((s,a));N[s,a]+=1;Q[s,a]+=(G-Q[s,a])/N[s,a]
        curve.append(returns[0])
    s=0;discounted=0.;path=[s]
    for t in range(100):
        a=int(Q[s].argmax());s,r,terminal=step(s,a);discounted+=.99**t*r;path.append(s)
        if terminal:break
    return np.mean(curve[-200:]),discounted,terminal,path,N
for epsilon in [.01,.1,.3]:
    try:
        training,greedy,ended,path,count=mc_control(epsilon)
    except RuntimeError as error:
        print('未完成实验：',error);continue
    print('eps/训练探索折扣均回报/独立greedy折扣回报/EOS',epsilon,training,greedy,ended)
    print('greedy路径',path,'已访问非terminal(s,a)',int((count[:15]>0).sum()),'/60')
```

本次运行ε=.01在第3回合触发保护上限，程序明确报告该实验未完成并继续其它对照，未用未结束轨迹更新MC值。这说明较小ε可让不良greedy环难以逃脱；不能为了让代码打印成功而删掉超时样本或把tail伪设0。ε=.1/.3的末200回合训练折扣return分别−6.4463/−8.0166，两项greedy部署均6步/−5.851985，60个非terminal(s,a)均至少访问过；这没有证明估值已全部精确，更不代表实际业务泛化。

不预设ε越小越好或20k次误差必<.1。若ε逐渐到0，仍须验证无限探索的理论前提；ε_t=1/t的标量和发散不代表需要多次探索动作才能到的每个深状态都无限出现。例如某条通路需要同回合两次连续探索，机会可能按ε_t²衰减；ε_t=1/t时∑ε_t发散而∑ε_t²收敛，所以仅检查总探索量不能证明深状态被无限访问。GLIE是性质而非某一万能数列。

## 8. Off-policy MC：ordinary、per-decision与weighted IS

目标π、行为b共用同一环境转移/奖励。要估Vπ的回报从t开始，权重 $\rho_{t:T-1}=\prod_{k=t}^{T-1}\pi(A_k|S_k)/b(A_k|S_k)$；b需覆盖目标有正概率的动作，日志要保采样当时概率。估Qπ(s,a)的第一动作已条件化，典型比例从t+1开始，不能不加区别套V权重。

ordinary IS是 $N^{-1}\sum\rho_iG_i$，满足覆盖/可积条件可无偏但高方差；weighted/self-normalized为 $\sum\rho_iG_i/\sum\rho_i$，有限样本通常有偏，零分母无估计，不能返回0冒称价值。Per-decision IS让每个reward只乘到它之前的动作比例，不是直接截断/clip weights。Clip权重是另一个会引入偏差的操作，weighted/per-decision也不必每任务方差最低。

### 8.1 完整两步日志与三估计器对照

在s0，目标选a0拿1进s1，再选a0拿2终止；行为每处.5/.5，另一个动作reward0结束。真值为1+.9×2=2.8，b覆盖target。完全匹配目标路径权重4；先匹配后偏离时ordinary整段权重0，但per-decision首reward仍贡献。

```python
import numpy as np
truth,gamma=2.8,.9
b=np.array([[.5,.5],[.5,.5]]);pi=np.array([[1.,0.],[1.,0.]])
assert np.all(b[pi>0]>0) and np.allclose(b.sum(1),1)
def estimate(N,seed):
    rng=np.random.default_rng(seed);weighted_returns=[];weights=[];pd=[];clipped=[]
    for _ in range(N):
        a0=int(rng.integers(2));trajectory=[(0,a0,1. if a0==0 else 0.)]
        if a0==0:
            a1=int(rng.integers(2));trajectory.append((1,a1,2. if a1==0 else 0.))
        G=sum(gamma**t*r for t,(s,a,r) in enumerate(trajectory))
        rho=1.;per=0.
        for t,(s,a,r) in enumerate(trajectory):
            rho*=pi[s,a]/b[s,a];per+=gamma**t*rho*r
        weights.append(rho);weighted_returns.append(rho*G);pd.append(per);clipped.append(min(rho,1)*G)
    total=sum(weights)
    weighted=sum(weighted_returns)/total if total>0 else np.nan
    return np.mean(weighted_returns),np.mean(pd),weighted,np.mean(clipped),int(np.count_nonzero(weights))
r=np.array([estimate(128,seed)[:4] for seed in range(40)])
print('40次估计 ordinary/PD/weighted/clipped 的mean',r.mean(0))
print('各方法跨seed标准差',r.std(0,ddof=1),'truth',truth)
# 零分母反例：N=1且首动作偏离目标，不能产生有权样本。
assert np.isnan(estimate(1,0)[2])
# 本例目标路径return恒定，所以有权样本时weighted恰真；这不是普遍零方差。
assert np.allclose(r[:,2],truth)
print('无匹配目标路径时weighted必须NaN，不称0；clip1极限均值.7不是2.8')
```

本例weighted显著小方差是固定路径/return导致，不能推广。ESS常用$(\sum w)^2/\sum w^2$诊断权重集中，但不是目标支持/估计正确性的证明；相关轨迹/策略漂移仍须分组与不确定性分析。

## 9. TD(0)、Q-learning、SARSA与Expected SARSA

TD(0)目标 $r+\gamma(1-terminated)V(s')$，无需知道P或等完整episode。Q-learning以max Q的greedy target更新，SARSA用同行为策略实际下一动作，Expected SARSA用行为策略动作分布平均。Expected版本减少“选择a'”引入的条件方差，不保证所有误差/计算成本都更小。

QL行为可以保持ε1随机；在折扣$0≤γ<1$的表格有限MDP中，只要奖励/噪声条件、每pair覆盖与学习率条件等成立，也能学习Q*；不要求行为自己greedy-in-limit。SARSA控制朝Q*的GLIE/学习率/覆盖条件更强，固定ε学习含探索的目标，不能仅因ε→0就给无条件保证。固定α通常有稳态误差但可追踪非平稳；per-pair访问次数的$1/N$满足常见平方可和条件，是否快由问题决定，不强制[.05,.3]。

神经函数近似、离线缺覆盖、非stationary环境不自动继承Watkins–Dayan表格收敛。把小MDP误差30%直接诊断代码bug也太强：先查目标π/ε、γ、状态覆盖、步数与不确定性，再查实现。

### 9.1 完整GridWorld/CliffWalking的三种TD与Double Q

格子在纯Python里，cliff只是合成reward−100并reset起点（不终止）；goal真正终止。算法carry SARSA的a'到下一步，其他算法按更新后的表再选动作。固定α/ε预算用于观察，不装作无限渐近证明。

```python
import numpy as np
import random
class Grid:
    def __init__(self,cliff=False):
        self.H=4;self.W=12 if cliff else 4;self.cliff=cliff
        self.start=(self.H-1)*self.W if cliff else 0;self.goal=self.H*self.W-1
    def step(self,s,a):
        if s==self.goal:return s,0.,True
        row,col=divmod(s,self.W);dr,dc=[(-1,0),(1,0),(0,-1),(0,1)][a]
        row=max(0,min(self.H-1,row+dr));col=max(0,min(self.W-1,col+dc))
        if self.cliff and row==self.H-1 and 0<col<self.W-1:return self.start,-100.,False
        ns=row*self.W+col;return ns,-1.,ns==self.goal

def probabilities(row,epsilon):
    greedy=np.flatnonzero(row==row.max());p=np.full(len(row),epsilon/len(row));p[greedy]+=(1-epsilon)/len(greedy)
    return p

def choose(row,epsilon,rng):
    if rng.random()<epsilon:return rng.randrange(len(row))
    return int(rng.choice(list(np.flatnonzero(row==row.max()))))

def train(env,kind,episodes=1800,gamma=.99,epsilon=.1,alpha=.25,seed=16):
    if kind not in ['q','sarsa','expected','double'] or not 0<=gamma<=1 or not 0<alpha<=1 or not 0<=epsilon<=1:raise ValueError('算法/参数范围')
    rng=random.Random(seed);A=np.zeros((env.H*env.W,4));B=np.zeros_like(A);counts=np.zeros_like(A,dtype=int);returns=[];cuts=0
    value=lambda:(A+B)/2 if kind=='double' else A
    for ep in range(episodes):
        s=env.start;carry=choose(value()[s],epsilon,rng);total=0.
        for t in range(600):
            a=carry if kind=='sarsa' else choose(value()[s],epsilon,rng)
            ns,r,terminated=env.step(s,a);truncated=t==599 and not terminated;total+=r
            if kind=='double':
                update,evaluate=(A,B) if rng.random()<.5 else (B,A)
                best=int(update[ns].argmax());target=r+(0 if terminated else gamma*evaluate[ns,best])
                update[s,a]+=alpha*(target-update[s,a])
            else:
                if kind=='sarsa':next_a=choose(A[ns],epsilon,rng) if not terminated else 0;next_value=A[ns,next_a]
                elif kind=='expected':next_value=probabilities(A[ns],epsilon)@A[ns]
                else:next_value=A[ns].max()
                target=r+(0 if terminated else gamma*next_value);A[s,a]+=alpha*(target-A[s,a])
            counts[s,a]+=1
            if terminated or truncated:cuts+=int(truncated);break
            s=ns
            if kind=='sarsa':carry=next_a
        returns.append(total)
    return value().copy(),counts,np.mean(returns[-200:]),cuts

def evaluate_greedy(env,Q,gamma):
    s=env.start;path=[s];total=discounted=0.
    for t in range(100):
        s,r,terminated=env.step(s,int(Q[s].argmax()));path.append(s);total+=r;discounted+=gamma**t*r
        if terminated:return total,discounted,True,path
    return total,discounted,False,path  # 截断，不冒称成功
for cliff in [False,True]:
    env=Grid(cliff);gamma=1. if cliff else .99
    for kind in ['q','sarsa','expected','double']:
        Q,N,training,cuts=train(env,kind,gamma=gamma)
        raw,discounted,ended,path=evaluate_greedy(env,Q,gamma)
        print('cliff/算法/训练探索末均return/截断次数',cliff,kind,training,cuts)
        print('greedy未折扣/折扣/终止/路径',raw,discounted,ended,[divmod(s,env.W) for s in path])
        if not cliff:
            Vstar=np.array([-sum(gamma**k for k in range(6-s//4-s%4)) for s in range(16)])
            Qstar=np.zeros_like(Q)
            for s in range(15):
                for a in range(4):ns,r,terminal=env.step(s,a);Qstar[s,a]=r+(0 if terminal else gamma*Vstar[ns])
            mask=N>0
            print('已访问pair maxQ误差/覆盖',float(np.max(np.abs(Q[mask]-Qstar[mask]))),int(mask[:15].sum()),'/60')
```

本次cliff训练末200回合，QL/SARSA mean raw return分别−51.535/−20.0；greedy部署分别13步/15步。Double greedy走17步，固定budget里没有优于另三者，且QL/Double各有1个外部截断训练回合，不能删掉这些结果再宣称保证。Grid里四法greedy都6步，但SARSA的Q包含探索的目标，不该因对Q*的误差较大就自动判断它实现失败。

训练曲线含探索的raw return、greedy测试raw与discounted return分别报告；固定seed不保证不同算法走同一路径。SARSA在经典cliff里可能更避险，是ε/目标导致的经验差别，不是安全约束保证，真实风险任务还需专门安全目标和验证。cliff并不是所有失败都terminal的例子；本程序按任务定义reset继续。

## 10. Maximization bias与Double估计的边界

若每动作估计有噪声，$E[\max_a\hat Q_a]≥\max_aE[\hat Q_a]$。Double用一表选、另一表评，减少“同一噪声既选又评分”的偏差。两表真实学习可能相关，也可出现低估，不保证每次seed、有限budget或所有环境都严格无偏/更优。

```python
import numpy as np
rng=np.random.default_rng(17)
A=rng.normal(0,5,(20000,10));B=rng.normal(0,5,A.shape)
selected=A.argmax(1);single=A.max(1);double=B[np.arange(len(B)),selected]
print('独立零均值动作估计：max均值/独立表评均值',single.mean(),double.mean(),'真各动作值0')
assert single.mean()>5 and abs(double.mean())<.2
# 这里两噪声表刻意独立，不是已经训练DoubleQ更优的证据。
```

原“σ5格子必显著过估而Double不”练习应按多seed、相同reward噪声分布/预算/覆盖对照，上例展示机制而不预设完整任务结论。Double TD算法已在第9.1节真实更新。

## 11. 探索、学习率与离策略评价的误区

Exploring starts要初始(s,a)可达且有覆盖分布，不现实环境不可任意reset；ε-greedy/UCB等设计也须结合可达性。Q初始化0对每步负reward是乐观，对正奖励未必；“全部零”不是中性物理事实。连续observation随便round成tuple可能合并不同MDP状态，导致state aliasing；哈希解决字典索引，不证明Markov充分。

样本平均α1/N适合固定政策iid/适当数据，constant α追踪变化但不保证无偏或收敛；MC控制使用旧不同政策return不是自动错误，也不能说一句“只要constantα就完全处理非平稳”。GLIE/Robbins是渐近条件，有限count图无法证明无限覆盖或安全部署。

n-step目标是未来n步折扣reward，加非terminal边界的γⁿvalue；n达到自然终止时退化完整MC。TD(λ)前向是特定加权n-step目标，回合末/不同trace实现条件要明确，λ1在合适episodic约定连接MC。PPO常用GAE但不等每个算法都必须critic；GRPO可用组相对回报且不必GAE，DPO另接偏好优化，不把“90%RL是QL/SARSA”当定理。

源图是知识比喻：Q-grid把先算的最优V乘episode/300，未采transition或更新Q；goal/pit、reward与本程序4×4不同。Value-iteration-gamma直接画γ^distance并给goal边界value1，非真的迭代求reward-on-entry/terminalV0模型。Epsilon regret图给每次ε×.4的固定gap，ε~1/t累计约log t而不是有界“平了”；真实regret还含估值错误与动作差异，不能从图推泛化/训练速率。

一份可核对的小任务记录应写明：状态/observation与动作的shape/合法性，P是已知还是仅可采样，reward时点和单位，γ与时间步，initial policy/value，算法目标π/b，停止残差或回合预算，count/误差诊断，训练探索与部署方式。原source输出模板的“100回合”“10⁶/10⁷状态”“reward差100倍”不是通用科学门槛：计算成本取决于稀疏度/存储/预算，置信精度取决于方差/相关性和样本，不因过了某个整数就有效。用PPO或QL baseline作参照也不是Vπ的数学bound；已知模型时先同π核对。

## 12. 练习参考答案与可继续学习的步骤

### 12.1 状态、奖励与折扣的三题

1. Random-policy 10,000回合：第6.1节完成自然终止采样，打印raw mean/std；−6是最短greedy的raw return，随机π不应收敛到−6。源“greedy down/right”在边界仍抽无效动作，不是真正最短greedy。
2. Uniform γ=.5/.9/.99的矩阵见第6.1节。负reward随γ增大更负，远期访问使差异更大；goalV0。“终点附近随着γ增大更快变好”不成立，先区分符号、绝对值与状态位置。
3. 对称slip .1会使uniform值更差吗？不会，本章第3节验证动作平均后Pπ不变；其它π或非对称slip可改变值，不能把随机动力学一概当下降。

### 12.2 DP的三题

1. VI在γ.9/.99的矩阵见第3节。本实现按**最终Bellman残差≤1e−8**停止，无slip用6个sweep；与源max迭代变化<1e−6是不同停止标准，比较要写清。
2. PI/VI在slip .1的Vstart相同至指定误差；分别计Bellman扫描、内评估/线性求解、outer与实际时间。本次正式程序输出sweep/outer，真实耗时写入执行记录；没有重复计时/硬件基准，不能声称PI wall-clock必快。策略ties不同仍可同样最优。
3. MPI k=1/2/5/10/50的误差和总评估sweep已打印；横轴k同时改变每轮工作与outer数量，画图必须固定残差协议。数字表足以核对该取舍，没有生成真实硬件性能曲线。

### 12.3 MC的三题

1. First-visit 10,000回合预测uniform π见第6.1节；检查点100/1000/5000/10000对照**同π**线性解−39.411648。终止后零值、未访问未知、原200步cap均须区别。多访问手算A first2.75/every3.125说明正序去重，不能将两个SEM都用总访问数。
2. ε=.01/.1/.3控制见第7节，预算明确是1,500完整回合，不冒称源20,000。本次.01触发自然终止保护上限，未完成实验不是低回报成绩；其它项报告训练探索/部署greedy/coverage。策略不断改变时，固定ε、采样平均和旧policy混合不能被一个bias–variance口号解释或保证Q*。
3. Ordinary/PD/weighted IS第8节完整两步例给出日志概率和真值，解释支持、reward时点与Q/V权重起点。没有跑原4×4多seed离策略实验；两步例weighted真值2.8有特殊结构，不推广为普遍最小variance，clip1极限.7会偏。

### 12.4 TD的三题

1. QL/SARSA第9.1节按1,800回合、同γ/α/ε分别学习并部署greedy，报告末200回合return、coverage与路径。不是原2,000回合/每100回合曲线，因此不能虚称完成了该图或某方法普遍更快。
2. 4×12 cliff已完整构造，跌崖reward−100并reset起点**不终止**。路径坐标可直接核对：本次QL greedy沿cliff上方一行，SARSA多远离一行；训练探索与greedy部署是不同风险协议，不能据一seed证明安全。没有截图需求，本章坐标本身可复现路径。
3. Double Q控制第9.1节已实现；第10节独立双噪声表解释max偏差。不预定σ5长训练中Double必胜，没有把未运行的高噪声多seedGridWorld写成结果；若继续做，应同reward噪声分布/预算/覆盖对照，再分别报告估值偏差、方差与部署return。

继续学习时先改一个条件并解释输出：增加非对称slip、改变γ、用不同π预测、故意混淆terminated/truncated、降低ε后检查未完成回合。改变模型/目标时重算答案，不能把toy固定seed数值当用户已掌握或真实部署证据。

## 来源与核验

固定[AI Engineering from Scratch](https://github.com/rohitg00/ai-engineering-from-scratch/tree/3be078b37ffd8f0c04953c0678e48f5c6d0c7775)，Phase09第01～04课，2026-10-05完整读取docs/Python/outputs/SVG/实际动态图与helpers。既有UDL第19章与EasyRL入口由[11](11-深度强化学习.md)/[15](15-强化学习进阶与世界模型.md)保留，本章实质补表格与回合操作，不另建来源镜像或更新旧历史日期。

一手核验：[Sutton–Barto教材入口](http://incompleteideas.net/book/the-book-2nd.html)、[Q-learning原证明](https://www.gatsby.ucl.ac.uk/~dayan/papers/cjch.pdf)、[Double Q原论文](https://papers.nips.cc/paper_files/paper/2010/file/091d584fced301b442654dd8c23b3fc9-Paper.pdf)、[特定optimistic policy iteration收敛分析](https://jmlr.org/papers/v3/tsitsiklis02a.html)、[Gymnasium时间限制](https://gymnasium.farama.org/tutorials/gymnasium_basics/handling_time_limits/)。作者站PDF正文路由失败，另取Stanford托管教材草稿及作者网页版相应段核对，未逐页读全书；经典方程与算法条件分别查原论文/教材相应段，不把有限toy值当所有算法的渐近保证。

后续中文维护提示：改变reward/终止/时钟/slip、π/b/γ、α/ε或IS日志后，重跑概率归一、Bellman残差、完整回报与终止/truncation反例；保存训练/评估/覆盖/失败定义和代码SHA。真实环境/长游戏/机器人/业务泛化未验证，CPU表格记录不写成用户已掌握。
