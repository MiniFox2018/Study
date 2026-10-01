# Understanding Deep Learning（UDL）覆盖核验

> 官网：<https://udlbook.github.io/udlbook/>  
> 官方仓库：<https://github.com/udlbook/udlbook>  
> 核验分支：`main`  
> 核验 commit：`0d84a591362f1cc99c6dc2ce1c2544d559280681`  
> 最新完整教材 release：`v5.0.3`（2026-02-09）  
> 教材/仓库主许可：CC BY-NC-ND 4.0  
> `Notebooks/` 代码许可：MIT（Copyright 2023 Simon Prince）  
> 整理时间：2026-10-01

## 1. 完整性口径
> 最新 PDF 已完成独立逐页核验，见 [UDL-PDF逐页核验](./UDL-PDF逐页核验.md)。该核验以用户提供的 541 页 PDF 为最终正文基线，并补齐 Appendix A/B/C 与正文遗漏。


本次目标不是复制 UDL 网站，而是达到：

> **学习时不再依赖原网页；原网页只用于来源追溯、版本核对和原始资产下载。**

因此执行四层覆盖：

1. 21 章教材知识逐章落位；
2. 官方 Notebook 逐文件核验；
3. selected answers、errata、equations、bibliography、slides、figures 等辅助资产审计；
4. 官网 Further reading / recent additions 的长期知识吸收到现有 Study 结构。

受 CC BY-NC-ND 4.0 限制，不在公开 Study 仓库发布整本教材的改写式逐句中文翻译；主库保存的是原创中文知识重构。

## 2. 21 章覆盖矩阵

| UDL 章节 | 核心内容 | Study 主要落位 |
|---|---|---|
| 1 Introduction | 监督/无监督/强化学习、生成模型、伦理、全书地图 | AI 算法基础 README、07、专题10/11/13 |
| 2 Supervised Learning | 线性回归、损失、训练与测试 | 04、专题01 |
| 3 Shallow Neural Networks | ReLU、分段线性、通用逼近、多输入输出 | 07、专题01 |
| 4 Deep Neural Networks | 网络组合、深度效率、线性区域、参数化 | 07、专题01 |
| 5 Loss Functions | MLE/NLL、回归/二分类/多分类、交叉熵、异方差 | 02、04、专题01 |
| 6 Fitting Models | GD、SGD、Momentum、Nesterov、Adam | 03、专题05 |
| 7 Gradients & Initialization | 计算图、反向传播、自动微分、初始化 | 专题01、专题05 |
| 8 Measuring Performance | 噪声、偏差/方差、双下降、超参数 | 专题09 |
| 9 Regularization | 显式/隐式正则、early stopping、ensemble、dropout、Bayes、transfer、SSL、augmentation | 专题09 |
| 10 Convolutional Networks | 不变/等变、1D/2D 卷积、感受野、上下采样、检测、分割 | 专题02、专题07 |
| 11 Residual Networks | residual block、gradient、batch norm、ResNet/DenseNet/U-Net | 专题02 |
| 12 Transformers | self-attention、多头、位置、BERT、GPT、长序列、ViT | 专题04、09、LLM 基础 |
| 13 Graph Neural Networks | graph representation、GCN、GraphSAGE/GAT 思想、sampling、inductive/transductive | 10-图表示与图神经网络 |
| 14 Unsupervised Learning | 生成模型分类、质量/覆盖/密度评价 | 05、专题10 |
| 15 GAN | GAN/WGAN、conditional、Pix2Pix/CycleGAN、StyleGAN | 专题10 |
| 16 Normalizing Flows | change of variables、coupling、autoregressive、residual/multiscale flow | 专题10 |
| 17 VAE | latent model、ELBO、variational approximation、reparameterization | 06、专题10 |
| 18 Diffusion | forward/reverse process、ELBO、noise prediction、conditional generation | 专题10 |
| 19 Deep Reinforcement Learning | MDP、Bellman、DP、MC、TD、DQN、policy gradient、actor-critic、offline RL | 专题11 |
| 20 Why Does Deep Learning Work? | 过参数化、loss geometry、implicit bias、pruning、distillation、adversarial | 专题12 |
| 21 Deep Learning & Ethics | bias/fairness、misuse、privacy、IP、环境、就业、治理 | 专题13 |

## 3. 官方 Notebook 核验

官网文案写“68 Python notebook exercises”；当前官方仓库 `Notebooks/Chap*/` 实际包含 **69 个 ipynb**。

差异来自 Chapter 20 同时存在：

- `20_2_Full_Batch_Gradient_Descent.ipynb`
- `20_2_Full_Batch_Gradient_Descent_GPU.ipynb`

后者是同一实验的 GPU 版本，因此官网仍可把“练习”计为 68，而仓库文件数为 69。

### Chapter 1

- `Chap01/1_1_BackgroundMathematics.ipynb`
- Study 落位：README / 07-深度学习基础 / 专题01

### Chapter 2

- `Chap02/2_1_Supervised_Learning.ipynb`
- Study 落位：04-经典监督学习 / 专题01

### Chapter 3

- `Chap03/3_1_Shallow_Networks_I.ipynb`
- `Chap03/3_2_Shallow_Networks_II.ipynb`
- `Chap03/3_3_Shallow_Network_Regions.ipynb`
- `Chap03/3_4_Activation_Functions.ipynb`
- Study 落位：07-深度学习基础 / 专题01

### Chapter 4

- `Chap04/4_1_Composing_Networks.ipynb`
- `Chap04/4_2_Clipping_functions.ipynb`
- `Chap04/4_3_Deep_Networks.ipynb`
- Study 落位：07-深度学习基础 / 专题01

### Chapter 5

- `Chap05/5_1_Least_Squares_Loss.ipynb`
- `Chap05/5_2_Binary_Cross_Entropy_Loss.ipynb`
- `Chap05/5_3_Multiclass_Cross_entropy_Loss.ipynb`
- Study 落位：02-概率统计与信息论 / 04-经典监督学习 / 专题01

### Chapter 6

- `Chap06/6_1_Line_Search.ipynb`
- `Chap06/6_2_Gradient_Descent.ipynb`
- `Chap06/6_3_Stochastic_Gradient_Descent.ipynb`
- `Chap06/6_4_Momentum.ipynb`
- `Chap06/6_5_Adam.ipynb`
- Study 落位：03-数值优化-蒙特卡洛与采样 / 专题05

### Chapter 7

- `Chap07/7_1_Backpropagation_in_Toy_Model.ipynb`
- `Chap07/7_2_Backpropagation.ipynb`
- `Chap07/7_3_Initialization.ipynb`
- Study 落位：专题01 / 专题05

### Chapter 8

- `Chap08/8_1_MNIST_1D_Performance.ipynb`
- `Chap08/8_2_Bias_Variance_Trade_Off.ipynb`
- `Chap08/8_3_Double_Descent.ipynb`
- `Chap08/8_4_High_Dimensional_Spaces.ipynb`
- Study 落位：专题09-泛化评估与正则化

### Chapter 9

- `Chap09/9_1_L2_Regularization.ipynb`
- `Chap09/9_2_Implicit_Regularization.ipynb`
- `Chap09/9_3_Ensembling.ipynb`
- `Chap09/9_4_Bayesian_Approach.ipynb`
- `Chap09/9_5_Augmentation.ipynb`
- Study 落位：专题09-泛化评估与正则化

### Chapter 10

- `Chap10/10_1_1D_Convolution.ipynb`
- `Chap10/10_2_Convolution_for_MNIST_1D.ipynb`
- `Chap10/10_3_2D_Convolution.ipynb`
- `Chap10/10_4_Downsampling_and_Upsampling.ipynb`
- `Chap10/10_5_Convolution_For_MNIST.ipynb`
- Study 落位：专题02-卷积神经网络与经典架构 / 专题07

### Chapter 11

- `Chap11/11_1_Shattered_Gradients.ipynb`
- `Chap11/11_2_Residual_Networks.ipynb`
- `Chap11/11_3_Batch_Normalization.ipynb`
- Study 落位：专题02-卷积神经网络与经典架构

### Chapter 12

- `Chap12/12_1_Self_Attention.ipynb`
- `Chap12/12_2_Multihead_Self_Attention.ipynb`
- `Chap12/12_3_Tokenization.ipynb`
- `Chap12/12_4_Decoding_Strategies.ipynb`
- Study 落位：专题04-注意力机制与Transformer / 09-Transformer与LLM演进 / LLM基础

### Chapter 13

- `Chap13/13_1_Graph_Representation.ipynb`
- `Chap13/13_2_Graph_Classification.ipynb`
- `Chap13/13_3_Neighborhood_Sampling.ipynb`
- `Chap13/13_4_Graph_Attention_Networks.ipynb`
- Study 落位：10-图表示与图神经网络

### Chapter 14

- 官方章节 Notebook：无（Chapter 14 为统一问题定义与评价框架）。
- Study 落位：05-特征工程-评估与无监督学习 / 专题10-深度生成模型

### Chapter 15

- `Chap15/15_1_GAN_Toy_Example.ipynb`
- `Chap15/15_2_Wasserstein_Distance.ipynb`
- Study 落位：专题10-深度生成模型

### Chapter 16

- `Chap16/16_1_1D_Normalizing_Flows.ipynb`
- `Chap16/16_2_Autoregressive_Flows.ipynb`
- `Chap16/16_3_Contraction_Mappings.ipynb`
- Study 落位：专题10-深度生成模型

### Chapter 17

- `Chap17/17_1_Latent_Variable_Models.ipynb`
- `Chap17/17_2_Reparameterization_Trick.ipynb`
- `Chap17/17_3_Importance_Sampling.ipynb`
- Study 落位：06-概率模型与潜变量方法 / 专题10-深度生成模型

### Chapter 18

- `Chap18/18_1_Diffusion_Encoder.ipynb`
- `Chap18/18_2_1D_Diffusion_Model.ipynb`
- `Chap18/18_3_Reparameterized_Model.ipynb`
- `Chap18/18_4_Families_of_Diffusion_Models.ipynb`
- Study 落位：专题10-深度生成模型

### Chapter 19

- `Chap19/19_1_Markov_Decision_Processes.ipynb`
- `Chap19/19_2_Dynamic_Programming.ipynb`
- `Chap19/19_3_Monte_Carlo_Methods.ipynb`
- `Chap19/19_4_Temporal_Difference_Methods.ipynb`
- `Chap19/19_5_Control_Variates.ipynb`
- Study 落位：专题11-深度强化学习

### Chapter 20

- `Chap20/20_1_Random_Data.ipynb`
- `Chap20/20_2_Full_Batch_Gradient_Descent.ipynb`
- `Chap20/20_2_Full_Batch_Gradient_Descent_GPU.ipynb`
- `Chap20/20_3_Lottery_Tickets.ipynb`
- `Chap20/20_4_Adversarial_Attacks.ipynb`
- Study 落位：专题12-深度学习理论

### Chapter 21

- `Chap21/21_1_Bias_Mitigation.ipynb`
- `Chap21/21_2_Explainability.ipynb`
- Study 落位：专题13-负责任AI



## 4. Notebook 本地来源保全

当前已将官方 `Notebooks/Chap*/` 实际存在的 **69 个 ipynb** 原样保全到：

- [来源保全/UDL-Notebooks](./来源保全/UDL-Notebooks/README.md)

同时补齐 Notebook 使用的 5 个本地图像：

- `Chap10/test_image.png`
- `Chap19/Empty.png`
- `Chap19/Fish.png`
- `Chap19/Hole.png`
- `Chap19/Penguin.png`

完整性复核：

- 上游 Notebook：69；
- Study 保全 Notebook：69；
- missing：0；
- extra：0；
- 对 69 个 ipynb + 5 个图像逐文件比较 Git blob SHA：**74/74 一致，0 mismatch**；
- MIT `LICENSE` 已随来源保全目录保存。

因此代码练习本身也已经退出“必须回官网获取”的流程。

另有：

- [已知问题与兼容性](./来源保全/UDL-Notebooks/已知问题.md)

记录 2026-10-01 时仍 open 的上游问题，包括 NumPy 2 beam-search 兼容、Monte Carlo Notebook 语法错误、Q-learning 参考值错误等。来源文件保持原样，不在保全层直接篡改。

## 5. 教材辅助资产

### Selected Answers

- `UDL_Answer_Booklet_Students.pdf`
- 用于核对部分课后题答案。
- Study 不复制答案手册正文；关键推导已进入对应知识章节。
- 2026 年官方 issue 仍有个别答案勘误，因此答案手册不是绝对静态真值。

### Errata

- `UDL_Errata.pdf`
- 作用：修正教材已知错误。
- Study 采用最新 release 与当前 issue/errata 交叉核验，不固化已知错误。

### Equations

- `UDL_Equations.tex`
- 汇总全书公式。
- Study 中关键公式已按知识主题重新组织，而不是另存一份平行公式手册。

### Bibliography

- `understanding-deep-learning-final.bib`
- 用于追溯论文与教材引用。
- 主知识库不复制 30 多万字节 BibTeX；在需要论文来源时按主题追溯。

### Slides

官方仓库有 26 个 PPTX，包括教材 Chapter 2～13 的 slides 与 CM20315 课程课件。

处理：

- 概念与例子已由对应正文/Notebook 覆盖；
- 不在主知识库重复保存 PPT 二进制；
- slides 仅作为来源保全资产。

### Figures

`PDFFigures/` 提供 Chapter 1～21 和 Appendix 的图包。

处理：

- 图中的概念关系已进入文字知识；
- 不机械复制图片素材；
- 需要重建原图时可按原路径追溯。

## 6. 官方仓库其他内容

### Blogs（6 个 Notebook）

- Bayesian function-space；
- Bayesian parameter-space；
- Gradient Flow；
- NTK；
- ODE numerical；
- NNGP。

已吸收到：

- [深度学习理论](./12-深度学习理论.md)
- [UDL 扩展专题](./14-UDL扩展专题.md)

### Trees（SAT / SMT 配套 Notebook）

仓库包含 SAT construction、crossword、graph coloring、Sudoku、Tseitin、Z3 及答案 Notebook。

已吸收到：

- [UDL 扩展专题](./14-UDL扩展专题.md) 的 SAT / SMT 部分。

这些是 Further reading 的配套练习，不纳入深度学习主线。

### CM20315 / CM20315_2023

属于作者课程教学材料，覆盖：

- Background maths；
- supervised learning；
- shallow/deep networks；
- loss；
- training；
- gradients；
- convolution；
- Transformer；
- coursework。

与教材和官方 `Notebooks/` 高度重叠，因此执行去重，不建立第三套课程笔记。

## 7. 官网 Further Reading 覆盖

官网额外资料已按长期知识归入：

| 官网栏目 | Study 落位 |
|---|---|
| Transformers & LLMs | 09、LLM 基础、LLM 工程实践、专题14 |
| Math for ML | 01、02、专题14 |
| Optimization | 03、专题05、专题14 |
| Temporal Models | 06、专题14 |
| Computer Vision geometry | 专题07、专题14 |
| Reinforcement Learning / Transformers in RL | 专题11 |
| ML Theory | 专题12 |
| Unsupervised Learning | 05、06、专题10 |
| Graphical Models | 06、专题14 |
| Machine Learning | 04～06、专题14 |
| Few-shot / Meta-learning | 专题14 |
| Neural NLG / Parsing | 08/09、LLM 基础、专题14 |
| Responsible AI | 专题13 |
| ODE / SDE | 专题12、专题14 |

## 8. 不进入主知识库的网页内容

以下内容已检查，但不属于需要掌握的知识：

- 购买链接；
- Amazon / Goodreads 等评论；
- 媒体书评；
- 采访和播客本身；
- 作者社交账号；
- download count；
- 网站 React/Vite 构建代码；
- CSS / UI 组件；
- favicon / cover；
- 纯宣传新闻。

它们不会影响“脱离原网页后学习知识是否完整”。

## 9. 时效性处理

### 长期保留

- 数学、概率、优化；
- 神经网络结构；
- loss / backprop；
- CNN / ResNet / Transformer / GNN；
- GAN / Flow / VAE / Diffusion；
- RL；
- NTK / NNGP / Bayesian NN / ODE-SDE 理论；
- fairness / XAI / differential privacy。

### 版本敏感

以下只保留原理，不把旧实现视为 2026 标准：

- Notebook 依赖版本；
- NumPy / PyTorch 具体 API；
- 历史模型性能数字；
- GPT-3 等历史模型的具体能力边界；
- 早期长序列/高效 attention 的性能比较。

## 10. 当前验收结论

按 Study 的“完整吸收”标准，本轮完成：

- 21/21 教材章节有明确落位；
- 69/69 当前官方章节 Notebook 有明确落位；
- 69/69 Notebook 已本地原样保全；
- 5/5 Notebook 本地图像依赖已保全；
- 74/74 上游 Notebook/图像 blob SHA 校验一致；
- Chapter 14 无 Notebook 的缺口已明确记录；
- answers / errata / equations / bibliography / slides / figures 已审计；
- Blogs / Trees / course materials 已审计；
- 官网 Further reading 各栏目已进入现有主干或专题；
- 重复内容未建立平行教材；
- 许可边界已记录。

后续 UDL 更新时，只需对比官方 release、commit 与本文件，即可增量补充，不需要重新从零整理。
