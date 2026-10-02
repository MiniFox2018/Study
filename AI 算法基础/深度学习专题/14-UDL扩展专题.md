# 14｜UDL 网站扩展专题

> 参考地图，不是必修课程。先选一个已经遇到的具体问题再进入对应节；如未遇到 SAT、Kalman 或元学习需求，可暂时跳过。

> 来源：Understanding Deep Learning 官网 “Further reading” 与近年新增博客。  
> 用途：把官网主教材之外但仍具长期学习价值的专题保留在 Study 内部；与主知识库已有内容重复的部分只给出落位和增量，不另建第二套体系。

## 1. Transformers 与 LLM

官网扩展内容包括：

- LLM 基本路线：pretraining、instruction tuning、RLHF；
- Transformer 的 encoder / decoder / encoder-decoder；
- absolute / sinusoidal / learned / relative position；
- long-context 方法；
- sparse / kernelized / linear attention；
- attention 与 RNN、hypernetwork、routing、graph、convolution、gating、memory 的联系；
- Transformer 深层训练稳定性；
- SFT、RLHF、DPO；
- efficient inference：attention-free、RWKV、linear transformer、Performer、RetNet。

在 Study 中统一落位：

- [Transformer 与 LLM 演进](../09-Transformer与LLM演进.md)
- [LLM 基础](../../LLM%20%E5%9F%BA%E7%A1%80/README.md)
- [LLM 工程实践](../../LLM%20%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/README.md)

长期结论：

> Transformer 的核心问题已从“会不会 attention”扩展到训练稳定性、上下文扩展、KV 状态、内存带宽、序列复杂度和后训练。

## 2. 机器学习数学

### 线性代数增量

官网特别强调：

- determinant / trace；
- null space；
- SVD；
- least squares；
- block matrix inverse；
- Schur complement；
- Sherman–Morrison–Woodbury；
- matrix determinant lemma。

这些恒等式在：

- Bayesian inference；
- Gaussian Process；
- Kalman Filter；
- low-rank update；

中非常常见。

### 概率与共轭

重点分布：

- Bernoulli / Beta；
- Categorical / Dirichlet；
- Gaussian；
- Normal-Inverse-Gamma；
- Normal-Inverse-Wishart。

共轭先验的价值在于让 posterior 与 prior 属于同一分布族，从而获得解析更新。

## 3. Gradient-based Optimization

除 SGD / Adam 外，官网补充：

- convexity；
- steepest descent；
- Newton；
- Gauss–Newton；
- line search；
- reparameterization。

Newton 类方法利用 Hessian：

$$
\theta_{t+1}=\theta_t-H^{-1}\nabla L(\theta_t)
$$

但深度网络中 Hessian 过大，通常使用：

- approximation；
- quasi-Newton；
- curvature-aware block approximation。

## 4. Bayesian Optimization

用于昂贵黑盒目标：

$$
x^*=\arg\max_x f(x)
$$

基本流程：

```text
历史评估
→ surrogate model
→ acquisition function
→ 选择下一点
→ 实际评估
→ 更新 surrogate
```

经典 surrogate 是 Gaussian Process。

Acquisition 常见思想：

- exploitation；
- exploration；
- uncertainty。

常用于评估昂贵、预算有限的目标；当评估极便宜时，代理模型和采集函数的额外开销可能不划算。离散或高维搜索需要相应方法，不能仅根据变量类型一概排除。

## 5. SAT / SMT Solver

官网把逻辑求解作为优化之外的另一类通用计算工具。

### SAT

判断布尔公式是否存在满足赋值。

重要概念：

- CNF；
- Tseitin transform；
- unit propagation；
- resolution；
- DPLL；
- CDCL。

### SMT

在 SAT 之上加入理论，例如：

- integer / real arithmetic；
- arrays；
- bit-vectors。

用途包括：

- verification；
- scheduling；
- constraint solving；
- 神经网络离散结构搜索。

## 6. Temporal Models

官网保留经典状态空间模型：

### Kalman Filter

适用于线性高斯动态系统。

滤波本身包含预测与观测更新，估计当前时刻状态；smoothing 是利用后续观测回头修正过去状态的相关任务，不能把它视为在线 Kalman Filter 的必需步骤。

### EKF / UKF

处理非线性转移或观测。

### Particle Filter

用带权样本近似后验，适合更一般的非线性、非高斯系统。

这些方法仍是理解 tracking、state estimation、SLAM 和序列贝叶斯推断的重要基础。

## 7. 经典计算机视觉几何

官网扩展包括：

- image whitening / histogram equalization；
- filtering / edge / corner；
- pinhole camera；
- radial distortion；
- homogeneous coordinates；
- intrinsic / extrinsic calibration；
- Euclidean / similarity / affine / projective transform；
- two-view geometry；
- essential / fundamental matrix；
- rectification；
- multiview reconstruction。

这些内容属于“几何视觉”，与深度视觉互补，而不是被 CNN/ViT 替代。

## 8. 图模型

### Directed / Undirected Graphical Model

核心语言：

- conditional independence；
- factorization；
- exact / approximate inference。

### Chain / Tree

- HMM；
- Viterbi；
- forward-backward；
- belief propagation；
- sum-product。

### Grid / MRF / CRF

- graph cut；
- alpha expansion；
- conditional random field。

它们统一落位于：

- [概率模型与潜变量方法](../06-概率模型与潜变量方法.md)

## 9. Few-shot 与 Meta-learning

### Metric-based

- Matching Networks；
- Prototypical Networks；
- Relation Networks。

核心思想：把新任务转化为 embedding 空间中的比较。

### Optimization-based

- MAML；
- Reptile。

目标是学到一个参数初始化，使模型经过少量梯度步骤就能适应新任务。

### Memory / Sequence-based

- LSTM meta learner；
- memory-augmented network；
- SNAIL。

长期问题：

> meta-learning 学的不是一个固定任务，而是“如何更快适应一类任务”。

## 10. Neural NLG

官网扩展将生成分成：

### Decoding

- greedy；
- beam search；
- diverse beam；
- top-k；
- nucleus sampling。

### Sequence-level Training

训练目标从 token-level likelihood 扩展到 sequence-level reward：

- RL fine-tuning；
- minimum risk training；
- scheduled sampling（改变训练输入，不等同于直接优化序列级奖励）；
- reward augmented maximum likelihood。

关键问题是：

> 训练时 teacher forcing 与推理时自回归之间存在 exposure bias。

## 11. Parsing

官网保留三层递进：

1. CFG + CYK；
2. Weighted CFG + semiring + inside algorithm；
3. PCFG + inside-outside + EM。

这些方法的长期价值是理解：

- 动态规划；
- structured prediction；
- latent structure；
- weighted algebra。

不是要求在现代 LLM 中重新使用传统 parser 作为主模型。

## 12. ML Theory

已在 [深度学习理论](./12-深度学习理论.md) 展开：

- Gradient Flow；
- NTK；
- NNGP；
- Bayesian ML parameter/function space；
- Bayesian Neural Networks；
- ODE / SDE。

## 13. Unsupervised Learning

官网补充：

- mixture model；
- t distribution；
- factor analysis；
- EM；
- VAE；
- Normalizing Flow。

深度生成模型统一进入：

- [深度生成模型](./10-深度生成模型.md)

经典潜变量模型进入：

- [概率模型与潜变量方法](../06-概率模型与潜变量方法.md)

## 14. Responsible AI

官网扩展：

- fairness；
- local/global explainability；
- differential privacy；
- DP-SGD；
- PATE；
- differentially private generation。

统一进入：

- [负责任 AI](./13-负责任AI.md)

## 15. ODE / SDE

### ODE

$$
\frac{dx}{dt}=f(x,t)
$$

关注：

- initial/boundary condition；
- existence / uniqueness；
- closed-form solution；
- numerical integration。

### SDE

加入随机项：

$$
dx=f(x,t)\,dt+g(x,t)\,dW_t
$$

它们连接：

- gradient descent；
- SGD；
- ResNet / Neural ODE；
- diffusion / score model；
- physics-informed ML。

## 16. 外链内容如何处理

官网还包含：

- 媒体采访；
- 书评；
- 播客；
-购买链接；
- 作者社交账号；
- 新闻更新。

这些不属于需要掌握的技术知识，因此不进入主知识正文。

但以下内容保留为来源审计信息：

- 官方教材 release；
- Notebook；
- selected answers；
- errata；
- equations；
- bibliography；
- slides；
- interactive figures；
- video lectures。

目标是：

> 本页提供已收集专题的定位和概念入口。只列名称的部分不构成完整教程；需要推导、原始图示或实作时，应沿来源继续查证。

## 用一维测量理解滤波与平滑

预测某位置为 10，预测方差为 4；新传感器测量为 12，测量噪声方差为 1，观测模型是直接测位置。Kalman 增益为 $K=4/(4+1)=0.8$，更新均值为 $10+0.8(12-10)=11.6$，方差为 $(1-0.8)4=0.8$。

自查：为什么结果更靠近测量 12？**答案：**测量噪声方差比预测方差小，这次测量相对更可靠。若测量噪声方差改为 16，则 $K=0.2$，更新仅到 10.4。

该步骤只使用当前及过去信息，属于滤波；明天取得新观测后再修正今天的位置才属于平滑。扩展专题先掌握这种可计算的区别，再深入矩阵和非线性版本。
