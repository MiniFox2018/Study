# 07｜Embedding 与检索模型训练

Embedding 模型把查询、文档或句子变成可比较的表示。训练目标是让正确候选相对错误候选更靠前；生成模型微调主要预测 token，两者不能混为一谈。先理解本篇的表示、损失和数据契约，再到 [12｜文本检索与 RAG 文档工程](12-文本检索与RAG文档工程.md) 学习召回、分块与问答；实验设计与评价在 [06](06-评测与实验管理.md)。

## 1. 表示有三种常见粒度

单向量稠密表示将整段文字压为一个 d 维向量，适合预计算和近邻索引。词表稀疏表示给 token/词表维度分配权重，可以利用倒排索引；学习型稀疏模型还能产生原文没有的相关词权重。多向量表示保留每个 token 的向量，通过晚交互如 MaxSim 评分，细粒度能力与存储/计算代价更高。

这些表示解决的困难不同：精确料号、同义表达、长文细节、跨语言或专业术语。BGE-M3 是同时提供稠密、稀疏与多向量功能的具体模型示例；支持多个功能不意味着每个任务都应全部启用，也不意味着一定优于当地语料上的更小模型。其官方说明不要求沿用旧 BGE 的查询指令前缀；前缀应按所用模型训练契约确定。[BGE-M3 模型卡](https://huggingface.co/BAAI/bge-m3)

## 2. 编码契约决定向量能不能比较

建库和查询必须固定模型/修订、tokenizer、截断、池化、投影、归一化、距离度量和输入角色。查询与文档可以按模型设计使用不同前缀或编码路径，但必须处于**配套训练的相似度空间**。两模型维度同为 768，不代表坐标含义相同；换模型或池化方式后必须重建文档向量与索引。

均值池化需排除 padding，有些模型采用 CLS、末 token 或专门池化头，不能随意互换。长文被截断时要知道丢了什么；声称支持长窗口不等于每个位置都能被一个向量有效表示。

余弦相似度为 `q·d/(||q||||d||)`，两边单位归一化后等于点积。归一化不是所有距离训练目标的通用默认；若模型本来用向量长度表达信息，随意归一化会改变任务。零向量没有余弦定义，应拒绝、回退或记录失败，不把零向量排序的并列首名当有效检索。

```python
import math

def normalize(v):
    if not v or not all(math.isfinite(x) for x in v):
        raise ValueError("向量不能为空且必须有限")
    norm = math.sqrt(sum(x*x for x in v))
    if norm == 0:
        raise ValueError("零向量没有余弦方向")
    return [x / norm for x in v]

def cosine(a, b):
    if len(a) != len(b):
        raise ValueError("维度不匹配，不能截到较短的一侧")
    return sum(x*y for x, y in zip(normalize(a), normalize(b)))

assert abs(cosine([3, 4], [6, 8]) - 1) < 1e-12
assert abs(cosine([1, 0], [0, 1])) < 1e-12
for a, b in (([0, 0], [1, 0]), ([1, 0], [1, 0, 0]), ([math.nan], [1])):
    try:
        cosine(a, b)
    except ValueError:
        pass
    else:
        raise AssertionError("输入错误应拒绝")
print("余弦：同方向、正交、零向量、维度及有限值检查通过")
```

## 3. 训练数据：查询、正例、负例

一个样本通常包括 `query、positive、negative`。正例应能回答这个查询，而非只是主题相似。随机负例容易；难负例看起来相关却不满足条件，例如查询“可报销的交通费”而候选讨论“不可报销的私人出行”。它们促使模型学会边界，但标签更容易出错。

常见来源是 BM25、已有向量模型或混合召回的高排名候选，经规则、人工或可信标注流程筛掉误负例，再在独立验证集评价。不能从测试查询矿难负例后再用同一测试集报告泛化效果。去重近似问答、同文档改写、同实体模板；按来源/时间/文档族分组切分，避免同一事实泄漏到训练和测试。

批内负例把其他样本的正例也作为当前查询的负例。它高效，却可能出现同一答案的副本、语义等价段落或一个查询有多条有效答案。多正例应明确标注或屏蔽误负例；不然更大 batch 可能放大错误监督。

## 4. 对比学习：相对排序的交叉熵

令查询矩阵 `Q` 为 `[B,d]`，文档矩阵 `P` 为 `[B,d]`，正例对齐在对角线，温度为 τ：

$$S=QP^\top/\tau,\qquad
\mathcal L=-\frac1B\sum_i\log\frac{\exp S_{ii}}{\sum_j\exp S_{ij}}.$$

每行是在该批候选中的相对分类。模型不是给“这段资料在现实世界中为真”的概率。τ 越小，分布越尖，难负例的相对差异更显著，错误标签和训练不稳定的影响也可能增加；不能把更小 τ 当单向改进。

若矩阵为 `[[2,0],[1,3]]`，两行正例比负例都高 2，正确项概率均为 `1/(1+exp(-2))≈0.881`，损失均约 0.127。把某行所有分数加同一常数，softmax 与损失不变。

### 4.1 稳定损失与解析梯度核对

本例只使用 NumPy，验证打分矩阵层面的梯度和多正例标签，未训练预训练文本编码器。`target` 每行表示正例概率质量；多正例可采用均匀目标。本实现对应“平均正例对数概率”损失，与“先将所有正例概率相加再取 log”的另一多正例目标不同，使用时必须写清。

```python
import numpy as np

def contrastive(scores, positive_mask):
    scores = np.asarray(scores, dtype=float)
    mask = np.asarray(positive_mask, dtype=bool)
    if scores.ndim != 2 or scores.shape != mask.shape or not np.isfinite(scores).all():
        raise ValueError("分数和正例 mask 必须同形状且有限")
    if scores.shape[0] == 0 or scores.shape[1] == 0 or not mask.any(axis=1).all():
        raise ValueError("每个查询必须至少有一个正例")
    target = mask / mask.sum(axis=1, keepdims=True)
    shifted = scores - scores.max(axis=1, keepdims=True)
    log_probs = shifted - np.log(np.exp(shifted).sum(axis=1, keepdims=True))
    probs = np.exp(log_probs)
    loss = -(target * log_probs).sum() / len(scores)
    grad = (probs - target) / len(scores)
    return float(loss), grad

s = np.array([[2., 0.], [1., 3.]])
mask = np.eye(2, dtype=bool)
loss, grad = contrastive(s, mask)
assert abs(loss - np.log1p(np.exp(-2))) < 1e-12
assert abs(contrastive(s + 10000, mask)[0] - loss) < 1e-12
numeric = np.zeros_like(s)
eps = 1e-5
for i in range(2):
    for j in range(2):
        plus, minus = s.copy(), s.copy()
        plus[i, j] += eps; minus[i, j] -= eps
        numeric[i, j] = (contrastive(plus, mask)[0] - contrastive(minus, mask)[0]) / (2 * eps)
assert np.allclose(numeric, grad, atol=1e-9)
# 若同一行两个候选都有效，均匀目标不应把第二个强行当负例。
assert np.allclose(contrastive([[0., 0.]], [[True, True]])[1], 0)
print("对比损失", round(loss, 6), "；解析梯度、多正例、平移稳定性通过")
```

打分来自 `Q@P.T/τ` 时，未归一化表示的梯度为 `dQ=(dS@P)/τ`、`dP=(dS.T@Q)/τ`；加入单位归一化还需对归一化反传。编码器参数则通过链式法则继续更新。训练框架通常自动完成这些步骤，理解梯度可帮助发现 detach、错误标签轴或不匹配的正例顺序。

## 5. Batch、缓存和难负例的实际边界

梯度累积把多个 microbatch 的梯度相加，未自动让每个查询看到所有 microbatch 的文档作为负例。要实现跨批大候选集，需要明确的特征缓存、梯度缓存或分布式 gather，并确定远端特征是否保留梯度。已 detach 的队列还能提供负例，但编码器更新后表示会陈旧；batch 大小不等于候选数不等于有效负例数。

训练记录 batch/microbatch、梯度累积、每查询候选数、误负例处理、温度、学习率、截断、采样分布、难负例来源和刷新时间。检查训练损失下降、验证排名是否改善、不同领域是否退化，以及嵌入范数、重复文本和全零表示。

一个基本训练流程是：固定数据切分 → 编码 q/p/n → 按已知正负关系构建分数与 mask → 稳定交叉熵 → 反传/优化 → 定期用完整候选库检索验证 → 保存编码契约与最优 checkpoint。验证只在小 batch 候选中分类正确，不能替代在完整库检索。

## 6. Matryoshka：前缀维度需要训练支持

Matryoshka Representation Learning 在一组维度 D 上共同优化前 d 维：

$$\mathcal L_{\mathrm{MRL}}=\sum_{d\in D}\lambda_d\mathcal L(\operatorname{norm}(q_{:d}),\operatorname{norm}(p_{:d})).$$

这样短前缀也有监督，部署时才可以选择不同维度以折中体积和质量。普通向量任意截断、随机哈希桶截断都不因此变成 MRL；不能假定所有 BGE 或 Sentence-BERT 模型都支持它。每个维度要独立归一化和验证，前 d 维可能全零。

```python
import numpy as np

def prefix_unit(vectors, dim):
    x = np.asarray(vectors, dtype=float)
    if x.ndim != 2 or type(dim) is not int or not 0 < dim <= x.shape[1] or not np.isfinite(x).all():
        raise ValueError("维度、形状或有限值无效")
    y = x[:, :dim].copy()
    norms = np.linalg.norm(y, axis=1, keepdims=True)
    if np.any(norms == 0):
        raise ValueError("截断前缀出现零向量")
    return y / norms

# 这组不是 MRL 训练表示，专门展示截断能改变排序。
q = np.array([[1., 1., 0., 10.]])
docs = np.array([[1., 1., 0., 0.], [0.5, 0.5, 0., 10.]])
rank_full = np.argsort(-(prefix_unit(q, 4) @ prefix_unit(docs, 4).T)[0]).tolist()
short_scores = (prefix_unit(q, 2) @ prefix_unit(docs, 2).T)[0]
assert rank_full[0] == 1 and np.allclose(short_scores, [1., 1.])
assert not np.shares_memory(prefix_unit(docs, 2), docs)
print("完整首名", rank_full[0], "；短前缀得分", short_scores.tolist(), "；截断并不无损")
```

两阶段检索可先用短向量召回，再用完整向量或多向量重排；若短层漏掉正确文档，后层同样无法恢复。每阶段应记录 Recall、延迟、候选数和额外向量存储。3072 维 float32 的原始单向量为 `3072*4=12288` 字节，即 12 KiB；一亿条原始向量约 1.2288 TB（十进制）。这是数组体积，未含 ANN、元数据、副本和压缩，不能直接换成固定云价格。

## 7. 评价：损失好看不等于检索有用

采用独立 query→相关集合，计算 Recall@k、MRR、nDCG，具体实现见 12。比较稠密、稀疏、多向量、混合方案时保持数据、预处理、gold 粒度和预算一致。多语言、长度、编号、否定、表格、时间条件和无答案要分切片；再观察 RAG 最终支持率和任务成功率。

MTEB 等基准提供不同任务和协议，排行榜总体分数不能代替当前业务数据；固定基准版本、任务子集、split、语料与指标定义。编码延迟、索引时间、内存和 P95/P99 也要在相同硬件、batch、输入长度与并发下测试。源资料中的“模型 X 是生产默认、总榜第一、固定损失 1%”不作为稳定知识。

## 8. 可复现的训练与更新记录

保存模型/代码 revision、数据 hash、预处理与切分规则、训练配置、随机种子、tokenizer/pooling/归一化/距离、验证集、最佳 checkpoint、索引与服务版本。数据新增要检查近重复和误负例；模型更新时用同一验证协议比较，然后重建索引和缓存。不是模型文件保存成功就代表可部署。

原有 self-llm 中 BGE-M3 微调知识在这里统一维护：query/positive/negative、批内负例、对比目标、难负例与训练后检索验证继续有效；具体库命令和模型前缀按当前版本核验，避免另起一份按来源组织的训练章节。

## 9. 练习与参考答案

1. `[[2,0],[1,3]]` 的损失约 0.126928；整体加 10000 不改变 softmax。其概率针对这两条候选，不是事实真值。
2. 两个查询问同一规则，各自正例可互相回答：将对方当负例会出现错误梯度；改为多正例、屏蔽或去重，并记录策略。
3. 将 microbatch 从 8 改为梯度累积 4 次，普通实现每查询仍只见 8 个批内候选，不会自动变成 32。
4. 任意 4 维向量截到 2 维，代码中排名区分消失，不能称无损。MRL 也需要按任务验证质量代价。
5. 切换同为 768 维的新模型不能复用旧文档空间。相同 tokenizer 也不保证池化、投影和角色契约相同。
6. 稀疏得分好、最终 QA 差：先查候选是否覆盖必需事实，再查重排、证据装配、版本和回答器，不盲目继续训练 embedding。
7. 设计 hard-negative 数据：BM25 高分但条件不符的候选，经核验确认不能回答当前查询；不能把另一个合理答案当负例。
8. 在自定义任务中比较不同 prefix dimension：保持相同文档、query、gold 与候选预算，报告 Recall、nDCG、内存和 P95，同时测短层漏召回。

## 来源与核验

- 原仓库已有 [self-llm BGE-M3 微调资料](https://github.com/datawhalechina/self-llm/tree/master/examples/BGE-M3-Finetune) 的有效原理保留并融合。
- 增量：[AI Engineering from Scratch](https://github.com/rohitg00/ai-engineering-from-scratch/tree/3be078b37ffd8f0c04953c0678e48f5c6d0c7775)，提交 `3be078b37ffd8f0c04953c0678e48f5c6d0c7775`，Phase 05 第 14、22、23 课；整理 2026-10-04。模型功能与输入说明按 [BGE-M3 作者模型卡](https://huggingface.co/BAAI/bge-m3) 核验；MRL 原理参见 [原论文](https://arxiv.org/abs/2205.13147) 及 [Sentence Transformers 文档](https://sbert.net/docs/package_reference/sentence_transformer/losses.html#matryoshkaloss)。
- 本篇例子用合成向量实测数学和边界，未下载模型、未微调 BGE-M3、未运行 MTEB 或真实 ANN 服务；源课哈希向量不能作为模型质量实验。
