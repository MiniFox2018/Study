# Understanding Deep Learning 最新 PDF 逐页核验

> 文件：UnderstandingDeepLearning_02_09_26_C.pdf  
> 作者：Simon J. D. Prince  
> 标题页日期：2026-02-08  
> PDF 修改时间：2026-02-09  
> 物理页数：541  
> 文件大小：22,344,992 bytes  
> SHA-256：f8237d393163900fa8e43210e680a3f987b45ccac7750b372e156fae3df0bf32  
> 许可证：Creative Commons CC BY-NC-ND 4.0  
> 核验时间：2026-10-01

## 1. 核验方法

本次不再只依据官网目录或 GitHub Markdown，而是直接对用户提供的最新版 PDF 做完整结构扫描。

执行了四层检查：

1. PDF 元数据、页数、目录、书签和页面结构；
2. 541 页逐页文本提取与章节边界识别；
3. 对关键表格、图示和复杂版面做页面渲染复核；
4. 将 PDF 中此前 Study 未充分展开的知识增量写回现有知识文档。

本文件是覆盖凭据，不是教材的翻译镜像。

## 2. PDF 结构

前置部分包括：

- title / copyright；
- dedication；
- contents；
- preface；
- acknowledgements。

正文从 PDF 第 15 页开始，书内页码从第 1 页开始。

| 章 | PDF物理页 | 书内页码 | 二/三级节数 | Problems | Notebook引用 |
|---|---:|---:|---:|---:|---:|
| 1 Introduction | 15-30 | 1-16 | 16 | 0 | 1 |
| 2 Supervised learning | 31-38 | 17-24 | 7 | 3 | 1 |
| 3 Shallow neural networks | 39-54 | 25-40 | 10 | 18 | 4 |
| 4 Deep neural networks | 55-69 | 41-55 | 13 | 11 | 3 |
| 5 Loss functions | 70-90 | 56-76 | 18 | 10 | 3 |
| 6 Fitting models | 91-109 | 77-95 | 12 | 11 | 5 |
| 7 Gradients and initialization | 110-131 | 96-117 | 13 | 17 | 3 |
| 8 Measuring performance | 132-151 | 118-137 | 12 | 9 | 4 |
| 9 Regularization | 152-174 | 138-160 | 16 | 6 | 5 |
| 10 Convolutional networks | 175-199 | 161-185 | 19 | 19 | 5 |
| 11 Residual networks | 200-220 | 186-206 | 14 | 9 | 3 |
| 12 Transformers | 221-253 | 207-239 | 30 | 10 | 4 |
| 13 Graph neural networks | 254-282 | 240-268 | 25 | 14 | 4 |
| 14 Unsupervised learning | 283-289 | 269-275 | 4 | 0 | 0 |
| 15 Generative adversarial networks | 290-317 | 276-303 | 23 | 6 | 2 |
| 16 Normalizing flows | 318-340 | 304-326 | 21 | 11 | 3 |
| 17 Variational autoencoders | 341-362 | 327-348 | 21 | 7 | 3 |
| 18 Diffusion models | 363-387 | 349-373 | 22 | 12 | 4 |
| 19 Reinforcement learning | 388-415 | 374-401 | 25 | 8 | 5 |
| 20 Why does deep learning work? | 416-434 | 402-420 | 33 | 3 | 4 |
| 21 Deep learning and ethics | 435-450 | 421-436 | 23 | 13 | 2 |

正文之后：

| 内容 | PDF物理页 | 书内页码 |
|---|---:|---:|
| Appendix A Notation | 451-453 | 437-439 |
| Appendix B Mathematics | 454-462 | 440-448 |
| Appendix C Probability | 463-476 | 449-462 |
| Bibliography | 477-526 | 463-512 |
| Index | 527-541 | 513-527 |

## 3. Appendix A：Notation

PDF 中有一套明确的符号约定，主要用于正确阅读教材公式：

- Roman letters 表示变量；
- Greek letters 表示参数；
- 小写粗体表示列向量；
- 大写粗体表示矩阵或 tensor；
- 函数使用方括号表示参数；
- argmin / argmax 区分最优值和取得最优值的变量；
- Pr(x)、Pr(y|x)、Pr(x,y) 分别表示边缘、条件和联合概率；
- Big-O 用于比较随输入规模增长的计算复杂度；
- 左箭头表示赋值。

这些是 UDL 的阅读约定，不另建通用数学体系；已在覆盖核验中保留为来源特定说明。

## 4. Appendix B：Mathematics 的知识增量

最新版 PDF 的数学附录不仅包含矩阵基础，还包括：

- injection / surjection / bijection / diffeomorphism；
- Lipschitz continuity；
- contraction mapping；
- convexity；
- exponential / logarithm / Gamma / Dirac delta；
- Stirling approximation；
- binomial coefficients；
- autocorrelation；
- vector/matrix/tensor；
- norms；
- matrix products / dot products；
- inverse；
- column space / null space；
- eigenspectrum / spectral norm；
- determinant / trace；
- diagonal / triangular / orthogonal / permutation matrix；
- matrix calculus。

已将此前不足的部分补入：

- AI 算法基础/01-线性代数与矩阵微积分.md

重点新增：

- Lipschitz 与 contraction；
- convexity；
- Dirac delta；
- subspace / null space；
- spectral norm；
- 特殊矩阵；
- 计算复杂度意识。

## 5. Appendix C：Probability 的知识增量

PDF 概率附录完整覆盖：

- joint / marginal / conditional probability；
- likelihood；
- Bayes rule；
- independence；
- expectation rules；
- mean / variance / covariance；
- standardization；
- univariate / multivariate Gaussian；
- product of Gaussians；
- linear change of variables；
- inverse-CDF sampling；
- ancestral sampling；
- KL divergence；
- Jensen-Shannon divergence；
- Fréchet / 2-Wasserstein distance；
- Gaussian distributions 之间的闭式距离。

已将此前不足的部分补入：

- AI 算法基础/02-概率统计与信息论.md

## 6. PDF 深读发现并补齐的正文缺口

### Chapter 8：High-dimensional spaces

此前 Study 已记录 Double Descent，但没有充分展开高维空间的反直觉性质。

本次新增：

- curse of dimensionality；
- 随机向量近正交；
- distance concentration；
- 高维球体积集中在表面；
- 最近/最远邻距离趋同；
- 高维插值与 inductive bias 的关系。

落位：

- 深度学习专题/09-泛化评估与正则化.md

### Chapter 11：Residual networks

此前主干覆盖 ResNet/BatchNorm，但没有充分吸收 UDL 的 shattered gradients 解释。

本次新增：

- gradient autocorrelation；
- shattered gradients；
- identity path 带来的短反向路径；
- residual addition 的方差增长；
- BatchNorm 在 residual block 中的尺度稳定作用；
- residual connection 为什么有效仍不存在单一解释。

落位：

- 深度学习专题/02-卷积神经网络与经典架构.md

### Chapter 14：Generative model evaluation

此前只保留了通用 fidelity / diversity 维度。

最新版 PDF 明确给出：

- efficient sampling；
- sample quality；
- coverage；
- well-behaved latent space；
- disentangled latent space；
- efficient likelihood；

以及：

- test likelihood；
- Inception Score；
- Fréchet Inception Distance；
- manifold precision / recall。

这些已经完整吸收到：

- 深度学习专题/10-深度生成模型.md

PDF 第 286 页 Figure 14.3 的模型属性比较表也进行了视觉核验。

### Chapter 15：GAN 训练技巧

此前遗漏的三个具体机制已补齐：

- progressive growing；
- minibatch discrimination；
- truncation。

并明确记录 truncation 的质量—多样性权衡。

### Chapter 17：Importance Sampling

官方 Notebook 17.3 不只是附加代码，其背后方法与 likelihood 估计、ELBO 松紧度有关。

本次已补入：

- importance weight；
- proposal coverage；
- likelihood estimation；
- IWAE 思想入口。

### Chapter 20：Why does deep learning work?

这是本轮 PDF 深读新增最多的理论部分。

新增：

- 随机数据/随机标签仍可拟合；
- full-batch GD 仍能把随机标签训练到零误差；
- overparameterization 与训练可行性的理论解释边界；
- 参数训练轨迹处于低维子空间；
- 多个 minima 之间的低损失连接；
- Goldilocks zone；
- Grokking；
- weight norm 与平滑插值；
- leaving the data manifold；
- adversarial examples 与分布内非鲁棒特征。

落位：

- 深度学习专题/12-深度学习理论.md

### Chapter 21：Deep learning and ethics

此前 Study 偏重 fairness / XAI / privacy 的工程视角，PDF 的哲学与制度框架更广。

本次新增：

- outer alignment / inner alignment；
- technical / normative alignment；
- principal-agent 视角；
- artificial moral agency；
- functional / structural / run transparency；
- value-free ideal of science；
- responsible AI as collective action problem；
- scientific communication；
- diversity / standpoint epistemology；
- participatory design / design justice；
- 四条 ways forward。

落位：

- 深度学习专题/13-负责任AI.md

PDF 第 448 页的 Diversity and heterogeneity / Ways forward 页面也进行了视觉核验。

## 7. 图表与版面复核

文本提取并不能可靠保留：

- 图表中的视觉关系；
- 公式版面；
- 页边 Notebook / Problem 引用；
- 表格勾选/叉号；
- 多列参考文献。

因此本次额外渲染检查了：

- 标题页与目录；
- Chapter 14 生成模型性质表；
- Chapter 20 理论章节；
- Chapter 21 Ways forward；
- Appendix B/C 的数学与概率公式页。

渲染结果与解析文本在结构上吻合。

## 8. Bibliography 与 Index

Bibliography 和 Index 不是独立学习正文，因此不逐条复制到 Study。

处理原则：

- Bibliography 保留为来源追踪层；
- 需要某个方法的论文来源时按主题追溯；
- Index 用于完整性检查和反向发现术语；
- 不把数十页引用和索引机械复制为知识笔记。

## 9. 版权与来源保全边界

PDF 明确使用 CC BY-NC-ND 4.0。

因此：

- 不在公开 Study 中发布逐页中文翻译；
- 不将整本 PDF 改写后作为另一版本发布；
- 不复制大段教材原文；
- 只做原创知识重构、公式解释、概念关系和学习笔记；
- 官方 MIT Notebook 继续在独立来源保全目录中原样保存。

## 10. 最终验收

最新版 PDF 已从此前的“目录/仓库级核验”升级为：

**541 页 PDF 结构级全量扫描 + 重点章节深读 + 关键页面视觉核验 + Appendix A/B/C 吸收 + 现有知识缺口回写。**

当前可以确认：

- 21/21 正文章节已核验；
- Appendix A/B/C 已核验；
- Problems 与 Notebook 边栏引用已按章节统计；
- Bibliography / Index 已纳入完整性边界；
- PDF 新发现的主要知识缺口已补入现有 Study 文件；
- 未建立第二套 UDL 教材镜像。

后续若出现新 PDF，只需比较：

- 文件 SHA-256；
- 页数；
- outline；
- 章节页码；
- 新增/删除术语；

即可做增量更新。
