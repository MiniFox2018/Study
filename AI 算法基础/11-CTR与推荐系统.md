# 11｜CTR 与推荐系统

> 推荐系统是华校专持续更新最频繁的板块之一。本文保留体系与演进规律，不把单篇论文的线上增益当成普遍结论。

## 1. 推荐系统不是单模型

工业推荐常见多阶段：

```text
Candidate Generation / Recall
→ Pre-Ranking
→ Ranking
→ Re-Ranking
→ Business Rules
```

不同阶段目标不同：

- Recall：从海量物品中找到候选；
- Ranking：精准排序；
- Re-ranking：处理多样性、约束、长期目标。

## 2. Collaborative Filtering

### User-based

相似用户喜欢的物品推荐给目标用户。

### Item-based

与用户历史物品相似的物品。

Amazon I2I 的长期价值在于：

> 物品关系通常比用户关系更稳定，且容易离线预计算。

## 3. Matrix Factorization

用户 embedding：

\[
p_u
\]

物品 embedding：

\[
q_i
\]

预测：

\[
\hat r_{ui}=p_u^Tq_i
\]

BPR 使用 pairwise ranking：

\[
u,i^+,i^-
\]

使正样本比分负样本更高。

## 4. CTR Prediction

目标：

\[
P(click=1|user,item,context)
\]

CTR 模型最大的结构特点：

- categorical feature 多；
- field 多；
- input 极度稀疏；
- feature interaction 重要。

## 5. LR → FM

LR 只建一阶：

\[
y=w_0+\sum_iw_ix_i
\]

FM 加入二阶交互：

\[
\sum_{i<j}
\langle v_i,v_j\rangle x_ix_j
\]

通过 latent vector 避免显式为每对特征维护独立参数。

## 6. Wide & Deep

两条路径：

### Wide

memorization：记住人工交叉或稀疏模式。

### Deep

generalization：embedding + MLP 学习非线性交互。

长期思想：

> 推荐系统同时需要记忆特定组合和泛化到未见组合。

## 7. DeepFM / DCN / xDeepFM

这些方法核心都围绕：

> 如何更有效建模 feature interaction？

### DeepFM

FM + DNN，共享 embedding。

### DCN

显式 cross network：

逐层增加有限阶交叉，同时保持参数可控。

### xDeepFM

通过 CIN 显式建模 vector-wise 高阶交互。

## 8. Attention for CTR

### DIN

目标 item 作为 query，对历史行为做 target-aware attention。

关键变化：

> 用户兴趣不再用一个固定向量表示，而是随候选 item 动态变化。

### DIEN

进一步建模 interest evolution。

### BST / Transformer-style

用 self-attention 建模用户行为序列。

## 9. Long Behavior Sequence

长序列推荐的核心矛盾：

- 历史越长，潜在信息越丰富；
- 但 Attention 与 Serving 成本快速上涨。

因此后续方法持续探索：

- retrieval/select first；
- multi-stage interest extraction；
- compressed history；
- sparse attention；
- efficient long sequence modeling。

## 10. Embedding Table 是核心成本

工业推荐中参数往往主要来自超大 categorical embedding table，而不是 MLP。

因此长期优化方向包括：

- mixed dimension；
- pruning；
- hashing；
- quantization；
- adaptive embedding；
- parameter server。

## 11. Sequential Recommendation

从：

- GRU4Rec；
- SASRec；
- BERT4Rec；

逐渐走向 Transformer/self-supervised sequence modeling。

重要区分：

### Causal

根据过去预测下一项。

### Bidirectional

利用双向上下文学习表示，训练和 serving 形式不同。

## 12. Retrieval / Matching

召回需要：

- 高覆盖；
- 高效率；
- ANN-friendly representation。

Dual Encoder：

\[
score(u,i)=f(u)^Tg(i)
\]

允许物品向量预计算并做 ANN。

## 13. Multi-Interest

单个用户一个向量难以表达多种长期兴趣。

MIND、ComiRec 等思想：

> 将用户表示成多个 interest vectors，再与候选物品匹配。

## 14. Graph Recommendation

交互构成 user-item graph。

NGCF / LightGCN 等通过邻域传播利用高阶协同信号。

## 15. Multi-Task Learning

推荐系统常同时优化：

- CTR；
- CVR；
- watch time；
- like；
- retention。

MMoE 思路：

```text
Shared Experts
→ Task-specific Gate
→ Task Head
```

目的是共享可迁移信息，同时降低任务干扰。

## 16. Bias

推荐训练数据并非 IID。

常见：

- exposure bias；
- position bias；
- selection bias；
- popularity bias。

模型只在“被展示的数据”上学习，会形成反馈环。

因此需要：

- random traffic；
- inverse propensity；
- counterfactual learning；
- debias sampling；
- online experiment。

## 17. 离线指标与在线指标

离线：

- AUC；
- GAUC/UAUC；
- LogLoss；
- NDCG；
- Recall@K。

在线：

- CTR；
- CVR；
- GMV；
- watch time；
- retention；
- long-term value。

离线提升不保证在线提升。

## 18. A/B Test

真正上线的推荐模型必须依赖随机实验判断增量。

至少注意：

- traffic randomization；
- sample ratio mismatch；
- novelty effect；
- experiment duration；
- interference；
- statistical significance。

## 19. 2025–2026 的新趋势

华校专近两年持续更新的论文显示，推荐系统正在明显吸收 LLM/Transformer scaling 思想：

- 更深/更大的 ranking backbone；
- long sequence；
- token mixing；
- sparse connectivity；
- MoE；
- generative recommendation；
- LLM-based recommendation；
- semantic ID；
- large-scale sequence modeling。

但推荐输入与语言不同：高维、稀疏、异构 feature field 的结构意味着“直接把 LLM 架构放大”并不一定有效。2026 年 SSRNet 等工作继续强调显式稀疏性与推荐数据结构之间的匹配问题。

## 20. 推荐系统阅读框架

看任何新模型时问：

1. 解决哪个阶段：recall/rank/rerank？
2. 输入是什么？
3. 如何建模 feature interaction？
4. 如何建模 sequence？
5. 是否针对 candidate？
6. 是否处理 bias？
7. serving complexity？
8. memory / FLOPs？
9. offline improvement 是否有 online A/B？
10. 是否能在规模放大后继续受益？

来源：华校专 CTR、传统推荐、深度推荐、序列推荐、多任务学习及 2025–2026 新增推荐论文。
