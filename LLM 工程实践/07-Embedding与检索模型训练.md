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


### 2.1 三种距离何时给同一排名

非零向量分别归一化到单位长度后，q·d=cos(q,d)，且 ||q−d||²=2−2q·d，因此点积/余弦降序与 L2 升序等价；平方根单调，不改变排序。零向量、不同维度或非有限值应先拒绝。未归一化时点积受长度影响，换度量可能改名次；不能仅因文本长短就认定某一种必然最好。动态图 cosine-similarity 精确展示角度余弦，但0.7等“相似”标签没有文本任务校准，负余弦也不是语言否定的可靠检测器。

```python
import math

def unit(v):
    if not v or not all(math.isfinite(x) for x in v):raise ValueError('非空有限向量')
    norm=math.sqrt(sum(x*x for x in v))
    if norm==0:raise ValueError('零向量')
    return [x/norm for x in v]
def dot(a,b):
    if len(a)!=len(b):raise ValueError('维度不同')
    return sum(x*y for x,y in zip(a,b))
def squared_l2(a,b):
    if len(a)!=len(b):raise ValueError('维度不同')
    return sum((x-y)**2 for x,y in zip(a,b))
q=unit([1.,0.]);docs=list(map(unit,[[3.,4.],[1.,0.],[-1.,0.],[0.,1.]]))
scores=[dot(q,d) for d in docs];dist=[squared_l2(q,d) for d in docs]
assert all(math.isclose(v,2-2*s,abs_tol=1e-12) for s,v in zip(scores,dist))
assert sorted(range(4),key=lambda i:(-scores[i],i))==sorted(range(4),key=lambda i:(dist[i],i))==[1,0,3,2]
a,b=[.9,.1],[3.,4.]
assert dot(q,unit(a))>dot(q,unit(b)) and dot(q,a)<dot(q,b)
print('单位向量cos/dot/L2排名',scores,dist,'；未归一化点积可换名次')
```

OpenAI 的官方说明对其单位归一化 Embedding 给出同样的排名关系，并提供 text-embedding-3 的 dimensions 参数；手工截取后需重新归一化。这是指定模型契约，不推广到所有编码器；API 并未在此调用。[官方 Embeddings](https://developers.openai.com/api/docs/guides/embeddings)。

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


### 6.1 打包一 bit、Hamming 与候选漏召回

符号量化将正数映射1、非正数映射0，按约定的位顺序打包后载荷为 ceil(d/8) 字节；未打包的 int8/Uint8Array 仍是 d 字节。来源的 TF-IDF 非负，取符号仅变成词是否出现，不构成稠密语义表示。下例用明确有正负值的人工向量测试实际 bytes、尾部位、维度和 Hamming，未训练编码器。

压缩可以先召回再用原向量重评分，但原向量若仍驻留/保存在别处，必须计入总存储。短向量或二值层漏掉正确候选后，重评分无法补回；更少体积与真实检索质量需要一起验证。

```python
import math, struct

def pack_sign(v):
    if not v or not all(math.isfinite(x) for x in v):raise ValueError('非空有限向量')
    payload=bytearray((len(v)+7)//8)
    for i,x in enumerate(v):
        if x>0:payload[i//8]|=1<<(i%8)
    return len(v),bytes(payload)
def validate_packed(p):
    d,raw=p
    if type(d) is not int or d<=0 or not isinstance(raw,bytes) or len(raw)!=(d+7)//8:raise ValueError('打包合同')
    if d%8 and raw[-1]>>(d%8):raise ValueError('尾部未使用位必须为0')
    return d,raw
def hamming(a,b):
    da,aa=validate_packed(a);db,bb=validate_packed(b)
    if da!=db:raise ValueError('维度不同')
    return sum((x^y).bit_count() for x,y in zip(aa,bb))
def cosine(a,b):
    if len(a)!=len(b) or not a or not all(math.isfinite(x) for x in a+b):raise ValueError('向量合同')
    na=math.sqrt(sum(x*x for x in a));nb=math.sqrt(sum(x*x for x in b))
    if not na or not nb:raise ValueError('零向量')
    return sum(x*y for x,y in zip(a,b))/(na*nb)
v=[1,-1,0,2,-2,3,-3,0,4];p=pack_sign(v)
assert len(p[1])==2 and p[1]==bytes([41,1]) and hamming(p,p)==0
assert len(struct.pack('<9f',*v))==36
try:hamming(p,(9,bytes([41,129])))
except ValueError:pass
else:raise AssertionError('尾部污染须拒绝')
try:hamming(p,pack_sign(v[:-1]))
except ValueError:pass
else:raise AssertionError('不能截到短维度')
q=[1.,.01];docs=[[1.,100.],[1.,-.0001]]
full=sorted(range(2),key=lambda i:(-cosine(q,docs[i]),i))
binary=sorted(range(2),key=lambda i:(hamming(pack_sign(q),pack_sign(docs[i])),i))
pool=binary[:1];rescored=sorted(pool,key=lambda i:-cosine(q,docs[i]))
assert full[0]==1 and pool==[0] and rescored==[0]
print('实际打包载荷',p[1].hex(),'字节',len(p[1]),'对照float32字节',36)
print('精确余弦首名',full[0],'二值候选/重评首名',pool[0],rescored[0],'；漏召回无法恢复')
```

正式比较要锁定原模型、归一化、同一查询/gold和候选预算，报告精确全文库排名、压缩层 Recall@k、重评后的 nDCG/支持答案率、载荷/索引/原向量总内存及延迟。ANN 的近似损失与压缩损失还应分开：HNSW 的 M、efConstruction、efSearch 和过滤方法会改变折中；它没有每个数据分布都保证的 O(log n)/95%召回或固定数据库容量。本批未构建真实 ANN。

MRL 需在多个前缀维度施加训练目标，第6节的多尺度目标继续有效；按词表前缀切 TF-IDF 或随机向量，只能作为任意截断反例。本例的 bit packing 也未证明二值化普遍只损失5%–10%。

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

## 10. 向量接口与压缩练习的可核对落点

来源五项练习应分别核对：同单位向量的三种度量排名必相同，出现不同先查归一化/零向量/维度；改chunk大小以有出处的相关块集合和预算评价，不能把最高相似度当检索质量；普通词表前缀截断不构成MRL；binary对照既报top-k集合重叠，又用独立gold报Recall/nDCG，排名与集合不同，不能以overlap代替正确性；句子边界不保证语义最佳，超长句、标点、小数和中文必须保留原位置并对照。

来源SimpleEmbedder对同义但无同词的付款例产生正交向量，不能验证语义匹配。重复index_documents还会在refit词表后附加旧空间向量；模型/词表/归一化变更应重建同快照，不能凭同维数复用。TS把不同维度截到较短侧的做法由本篇的严格拒绝替代。来源模型排名/固定精度损失/通用0.7阈值和HNSW容量表未作为事实收录。

增量来源：固定AI Engineering from Scratch 3be078b37ffd8f0c04953c0678e48f5c6d0c7775，Phase11第04课，2026-10-07完整阅读与新增几何/打包探针执行；原2026-10-04对比训练/MRL/编码契约与程序证据保留。


## 11. 页面多向量与MaxSim的输入合同

ColPali将页面图像的上下文化视觉表示投影为矩阵 `P∈R^(N_p×d)`，查询编码成配套的 `Q∈R^(N_q×d)`；晚交互是在预计算表示上评分，不是查询时把全页和问题重新送同一cross-encoder。ColBERT对文本token采用类似机制；视觉patch、文本token和实际输出向量数量由具体processor/模型决定，不能固定所有checkpoint为729/128。[ColPali作者资料](https://github.com/illuin-tech/colpali/blob/97487f8871ff4d5d2284411fe61bdcd2cfe99894/README.md)

$$s(q,p)=\sum_{i\in\mathrm{validQuery}}\max_{j\in\mathrm{validPage}}q_i^\top p_j.$$

当每行单位归一化时点积是余弦；否则应遵循模型训练的距离合同。query padding不进入sum，page padding要在max前排除或赋负无穷。合法相似度全负时，0 padding会虚增分数。空有效查询/页、非有限值、有效零/近零向量、维度或encoder/preprocess revision不同，必须拒绝、明确empty或走定义过的fallback，不能zip到短维或自动得零分。

MaxSim保留每个查询token的最好局部匹配，平均所有patch相似度可能稀释局部证据；但它允许多个query token匹配同一patch，不是严格一对一、更不是业务条件全部满足。对**已给定**page向量集合换顺序不改max/sum；真实上下文encoder若换原图布局，其向量可能改变，不能由评分不变推出整个系统不感知布局。得分受查询token数量影响，不同query的总分不能直接作同一正确率阈值。

### 11.1 完整mask、负分与revision反例

本例用人工二维向量，只验证MaxSim数学与数据合同；无页面encoder、神经检索训练、ANN或真实ViDoRe成绩。`Space`保存配套编码空间和预处理revision，而非只检查d相等。

```python
import math
from dataclasses import dataclass, replace

@dataclass(frozen=True)
class Space:
    encoder_revision: str='synthetic-pair-r1'
    preprocess_revision: str='query-text+page-grid-r1'
    dim: int=2
    normalization: str='unit'

def active_unit(vectors,valid,space):
    if not vectors or len(vectors)!=len(valid) or any(type(x) is not bool for x in valid): raise ValueError('非空矩阵/boolean mask')
    if space.dim<1 or space.normalization!='unit': raise ValueError('本例契约限定unit cosine')
    out=[]
    for vec,keep in zip(vectors,valid):
        if len(vec)!=space.dim or any(type(x) not in (int,float) or not math.isfinite(x) for x in vec):
            raise ValueError('维度/finite错误，不能zip截断')
        if keep:
            norm=math.hypot(*vec)  # 稳定缩放，避免有限大数平方溢出。
            if not math.isfinite(norm) or norm<1e-300:
                raise ValueError('有效零/近零向量或范数非有限，不能返回伪零方向')
            out.append([x/norm for x in vec])
    if not out: raise ValueError('有效token为空；另设empty状态')
    return out

def maxsim(q,qmask,d,dmask,qspace,dspace):
    if qspace!=dspace: raise ValueError('encoder/preprocess/revision空间不配套')
    qs=active_unit(q,qmask,qspace);ds=active_unit(d,dmask,dspace)
    # 先过滤document padding，再max；query padding不进入sum。
    similarity=[[sum(a*b for a,b in zip(x,y)) for y in ds] for x in qs]
    return sum(max(row) for row in similarity),similarity

space=Space(); q=[[1.,0.],[0.,1.],[0.,0.]]; qm=[True,True,False]
d=[[1.,0.],[0.,1.],[0.,0.]];dm=[True,True,False]
score,matrix=maxsim(q,qm,d,dm,space,space);assert score==2.
assert maxsim(q,qm,d[::-1],dm[::-1],space,space)[0]==score
negative=maxsim([[1.,0.]],[True],[[-1.,0.],[0.,0.]],[True,False],space,space)[0]
assert negative==-1 and max(-1.,0.)==0.  # 把0 padding留在max里就伪增为0。
assert maxsim([[1.,0.],[1.,0.]],[True,True],[[1.,0.]],[True],space,space)[0]==2.
for args in [([[0.,0.]],[True],space),([[1.,0.]],[False],space),([[math.nan,0.]],[True],space),([[1.],[1.,0.]],[True,True],space)]:
    try:active_unit(*args)
    except ValueError:pass
    else:raise AssertionError('无效向量/有效mask须拒绝')
try:maxsim(q,qm,d,dm,space,replace(space,encoder_revision='r2'))
except ValueError:pass
else:raise AssertionError('同维不同revision须重编码')
large=maxsim([[1e308,0.]],[True],[[1e308,0.]],[True],space,space)[0]
large_negative=maxsim([[1e308,0.]],[True],[[-1e308,0.]],[True],space,space)[0]
large_diagonal=maxsim([[1e308,1e308]],[True],[[1e308,1e308]],[True],space,space)[0]
assert large==1. and large_negative==-1. and math.isclose(large_diagonal,1.,abs_tol=1e-12)
for extreme in [[1e-310,0.],[1.79e308,1.79e308]]:
    try:active_unit([extreme],[True],space)
    except ValueError:pass
    else:raise AssertionError('近零或不可表示的非有限范数须明确拒绝')
raw=200*729*128*4; hypothetical=raw/8
assert raw==74649600 and hypothetical==9331200
million=1000000*729*128*4
print('MaxSim',score,'pairmatrix',matrix,'padding负分反例',negative,'vs faulty 0')
print('200页float32载荷B/MiB',raw,round(raw/2**20,4),'假设8x载荷',hypothetical)
print('百万页原始向量B/GiB',million,round(million/2**30,4),'未含ANN/metadata/副本')
print('大有限向量same/opposite/diagonal',large,large_negative,large_diagonal,'近零/非finite norm拒绝')
```

归一化用稳定`math.hypot`，避免`sum(x*x)`在`1e308`这样的有限输入上溢出并把方向错误变成零。示例的大同向/反向仍为1/−1；近零范数阈值`1e-300`仅是本例的数值合同，范数非有限也显式拒绝，不能据伪零分继续检索。真实encoder可采用稳健max-scale归一化，并按其dtype/精度约定处理极端输入。

压缩降低维度精度的PQ/OPQ、减少向量数量的pooling和单向量候选层是不同改变。需同gold页/区域、候选预算比较Recall、nDCG、存储、检索延迟和回答支持率；粗层漏召回后，完整MaxSim重排无法恢复。热区可帮助回页找依据，但不会把retrieval score变成字段抽取证据。

2026-10-08作者README明确 `colpali-engine` 已deprecated，新项目指向Sentence Transformers的MultiVectorEncoder；旧代码用于研究复现或存量项目。这里保留多向量原则与版本迁移检查，不给旧SDK安装/当前API承诺，也未安装或调用任一SDK。页面级索引、证据装配与问答维护在[12｜页面与跨模态RAG](12-文本检索与RAG文档工程.md)，不再复制另一套回答管道。

## 12. 多向量三题的可评判参考

### 多向量练习 1：200页存储与压缩

题设200×729×128×4=`74,649,600` bytes，约71.1914 MiB；假定8倍载荷压缩为`9,331,200` bytes，约8.8989 MiB。这是题设数组算术，程序未实施PQ；codebook、索引、page metadata、原图、原向量重排存储与副本都另计。50页多向量与50个768维float32向量的原始数组比是121.5倍，源“约30倍”不符合它给定的参数。

### 多向量练习 2：MaxSim比平均捕捉什么

对每个有效query token选最好page token再sum，保留局部相关位置；平均所有pair可能把高匹配淹没。代码的单位正交矩阵score2；合法doc负余弦−1加padding若不mask会错成0。两相同query向量都可选同patch并得2，说明不是逻辑AND。比较算法应看同候选集合的gold排名与代价，而非因为sum数值大于mean就宣称召回更好。

### 多向量练习 3：patch与word级索引的交换

word级需可靠文本/OCR及word-position合同，适合精准编号/数字和可抽取文字；patch级可保视觉与布局条件，但resize/crop仍可能丢小字且多向量载荷大。不能说图像路径保留所有信息或文字RAG只存一整页向量。对同页集分别标文本、图表、表格、版式、多页证据，固定预算看Recall/nDCG与最终引用支持；可保双路径互补，不以材料含一张图为理由禁用文本索引。

增量来源：第1来源固定3be078b，Phase12/23，2026-10-08新增本地MaxSim合同程序执行；旧代码块、SHA与2026-10-04/07日期保留。原课随机Gaussian+bias不读页面或真实query；MaxSim/mean总分、固定PQ和速度表未成为检索质量/性能结论。

## 13. 联合编码重排的学习计算与训练目标

2026-10-12 增量。先读本篇第2–5节的编码/标签/负例契约，再看联合编码器。双编码器分别把query与doc编码成向量，可以离线缓存doc表示；cross-encoder则把每个 `(query,doc)` 一起打包，通过同一token序列的self-attention让双方直接交互，再得一个相关性scalar。它不要求另建名为CrossAttention的模块。预存一个doc向量不能替代对新query的联合计算，候选N对可以batch，不能把N对计算写成必然N次独立Python forward。

### 13.1 从输入到scalar的逐步过程

输入为 `query tokens + SEP + doc tokens + padding`，可按模型训练合同加CLS、token type/segment与位置。批张量IDs形状 `[B,L]`；有效mask形状 `[B,L]`，词/位置嵌入得到 `[B,L,d]`。每头生成Q/K/V，注意力logits为 `QKᵀ/√d_head`，形状 `[B,L,L]`，在softmax前把padding key屏蔽为负无穷。query位置可关注doc位置，doc也能关注query；这是和两塔独立编码不同的关键。后接残差、层归一化和FFN，得到联合上下文states。

masked mean pool为 `h=Σ_i m_i H_i / Σ_i m_i`，形状 `[B,d]`；scalar头 `s=wᵀh+b` 得 `[B]`。padding不进入mean，SEP/CLS是否进入pool按明确合同选择。mask全空应拒绝，截断要保两侧输入且记录丢掉的doc部分；长度16/96等只是例子的预算，没有通用最优值。CLS头与mean头不同，训练/验证必须保持配套，不能只换推理池化就复用旧head。相同文本加尾部PAD应不改变scalar（在本例无dropout的eval模式和相同有效位置下）。

### 13.2 标签、损失与多负例

标签先问“当前文档能否满足这个查询及其条件”。同主题但错实体/否定/数值/时期是负例；一个查询有多个正确证据时标多正例，避免把别的有效答案当hard negative。每query可有多个不同困难的负例，训练记录随机/难负例来源、误负例审核、采样比和权重；一个查询复制十个简单负例不是十份独立能力证据。按doc-family/实体/事实与近改写分组切分，避免训练与验证共享答案事实；同query字符串不重复还不够。

MSE回归目标为 `L=(1/B)Σ(s_i−y_i)²`，把连续等级当数值距离；若y是0/1，它仍只是回归，scalar可小于0或大于1，原始分数不是概率。BCEWithLogits为 `L=(1/B)Σ[softplus(s_i)−y_i s_i]`，y∈[0,1]且通常二元，用稳定logit目标，不能先sigmoid再当logit传入。sigmoid(s)在这份训练协议下有二元分类解释，但部署概率还需独立校准，不能自动代表“整库无答案”的概率。pairwise可优化正例比负例高，listwise可对每query候选集合归一化；它们的采样/多正例与规模合同不同，不能把任何一个低损失直接叫检索成功。

训练流程是固定labels/split→打包与mask→联合前向→损失→反传/优化→在独立query-doc-family的候选库验证→选checkpoint→冻结最终测试。训练score margin上升只证明拟合监督，更高epochs也可恶化held-out。候选budget N与保留K一起记录：N=K时能重排、提高MRR/Hit@1，但保留整个集合的Recall@K不变；gold从未进N时纯重排无法恢复。3×K或20–50的“拐点”是待测范围，八篇文档库里N≥8饱和只是候选耗尽。

### 13.3 完整自写CPU例：联合attention、训练与独立分组

以下是完整可运行教学程序，2026-10-12已用既有本地runtime实际执行；没有导入来源程序、下载权重、调用服务或使用GPU。词表固定、随机初始化、单头attention，四个人工doc-family中train_a/train_b仅训练，held_c/held_d仅验证；预定义词表包括验证family名，但没有使用它们的标签训练。每query一个正例、错状态与错实体两个负例，标签是人工任务真值，模型不是预训练语义检索器。BCE训练101步，训练前记录一次两数据集的基线；完成1、11、51、101次更新后，用同一参数快照同时评估训练集与留出集，评估不更新参数。最后的N=K排序是单独手工fixture，与神经模型held-out结果明确分开。


```python
import hashlib, json, math
import torch
from torch import nn

torch.set_num_threads(1)
torch.manual_seed(23)
FAMILIES = ('train_a', 'train_b', 'held_c', 'held_d')
VOCAB = {word: i for i, word in enumerate(('[PAD]', '[SEP]', 'allow', 'deny') + FAMILIES)}
PAD, SEP = VOCAB['[PAD]'], VOCAB['[SEP]']

def encode_pairs(pairs, extra_pad=0):
    if type(pairs) not in (list, tuple) or not pairs or type(extra_pad) is not int or extra_pad < 0:
        raise ValueError('nonempty pairs and integer padding')
    sequences = []
    for pair in pairs:
        if type(pair) is not tuple or len(pair) != 2 or any(type(t) is not str for t in pair):
            raise ValueError('each pair is exactly two text strings')
        q, d = pair
        qs, ds = q.split(), d.split()
        if not qs or not ds or any(w not in VOCAB or w in ('[PAD]', '[SEP]') for w in qs + ds):
            raise ValueError('nonempty known-token query/document')
        sequences.append([VOCAB[w] for w in qs] + [SEP] + [VOCAB[w] for w in ds])
    length = max(map(len, sequences)) + extra_pad
    if length > 16:
        raise ValueError('explicit length limit; no silent truncation')
    ids = torch.tensor([s + [PAD] * (length - len(s)) for s in sequences], dtype=torch.long)
    return ids, ids.ne(PAD)

class JointScorer(nn.Module):
    def __init__(self):
        super().__init__()
        self.word = nn.Embedding(len(VOCAB), 16, padding_idx=PAD)
        self.pos = nn.Embedding(16, 16)
        self.qkv = nn.Linear(16, 48)
        self.norm1 = nn.LayerNorm(16)
        self.ff = nn.Sequential(nn.Linear(16, 32), nn.GELU(), nn.Linear(32, 16))
        self.norm2 = nn.LayerNorm(16)
        self.head = nn.Linear(16, 1)

    def forward(self, ids, valid):
        if not isinstance(ids, torch.Tensor) or not isinstance(valid, torch.Tensor):
            raise ValueError('CPU tensor inputs required')
        if (ids.device.type != 'cpu' or valid.device.type != 'cpu' or ids.dtype != torch.long
                or ids.ndim != 2 or ids.shape[0] < 1 or not 1 <= ids.shape[1] <= 16
                or valid.shape != ids.shape or valid.dtype != torch.bool):
            raise ValueError('CPU Long IDs, bounded batch/length and boolean mask contract')
        if bool((ids < 0).any()) or bool((ids >= len(VOCAB)).any()):
            raise ValueError('IDs outside frozen vocabulary')
        if not torch.equal(valid, ids.ne(PAD)):
            raise ValueError('this toy mask must exactly mark non-PAD positions')
        if not valid.any(dim=1).all():
            raise ValueError('each pair requires valid tokens')
        x = self.word(ids) + self.pos(torch.arange(ids.shape[1]))[None, :, :]
        q, k, v = self.qkv(x).chunk(3, dim=-1)
        logits = (q @ k.transpose(1, 2)) / math.sqrt(16)
        logits = logits.masked_fill(~valid[:, None, :], float('-inf'))
        weights = torch.softmax(logits, dim=-1)  # query and doc tokens share one attention matrix
        x = self.norm1(x + weights @ v)
        x = self.norm2(x + self.ff(x))
        pooled = (x * valid[:, :, None]).sum(dim=1) / valid.sum(dim=1, keepdim=True)
        return self.head(pooled).squeeze(-1)

def examples(families):
    rows = []
    for family in families:
        other = next(x for x in families if x != family)
        for status in ('allow', 'deny'):
            opposite = 'deny' if status == 'allow' else 'allow'
            query = f'{family} {status}'
            # One positive; wrong status and wrong entity are two distinct negatives.
            for doc, label in ((f'{family} {status}', 1.),
                               (f'{family} {opposite}', 0.),
                               (f'{other} {status}', 0.)):
                rows.append({'query': query, 'doc': doc, 'label': label, 'family': family})
    return rows

train = examples(FAMILIES[:2])
held = examples(FAMILIES[2:])
assert set(r['family'] for r in train).isdisjoint(r['family'] for r in held)
assert set(r['query'] for r in train).isdisjoint(r['query'] for r in held)
train_ids, train_mask = encode_pairs([(r['query'], r['doc']) for r in train])
held_ids, held_mask = encode_pairs([(r['query'], r['doc']) for r in held])
y = torch.tensor([r['label'] for r in train])
y_held = torch.tensor([r['label'] for r in held])
model = JointScorer().cpu()
optimizer = torch.optim.Adam(model.parameters(), lr=.01)
objective = nn.BCEWithLogitsLoss()  # raw scalar logits; no extra sigmoid before stable loss
curve = []
def record(update):
    model.eval()
    with torch.no_grad():
        train_loss = objective(model(train_ids, train_mask), y).item()
        held_loss = objective(model(held_ids, held_mask), y_held).item()
    curve.append([update, round(train_loss, 6), round(held_loss, 6)])

record(0)  # Same untrained state for both datasets.
for update in range(1, 102):
    model.train()
    optimizer.zero_grad()
    scores = model(train_ids, train_mask)
    loss = objective(scores, y)
    loss.backward()
    assert model.qkv.weight.grad is not None and torch.isfinite(model.qkv.weight.grad).all()
    optimizer.step()
    if update in (1, 11, 51, 101):
        record(update)  # Both losses use this same post-update snapshot.

model.eval()
query = 'held_c allow'
docs = {'c-yes': 'held_c allow', 'c-no': 'held_c deny', 'd-yes': 'held_d allow'}
pairs = [(query, text) for text in docs.values()]
ids, mask = encode_pairs(pairs)
padded, padded_mask = encode_pairs(pairs, extra_pad=3)
with torch.no_grad():
    scores = model(ids, mask)
    assert torch.allclose(scores, model(padded, padded_mask), atol=1e-6)
by_id = dict(zip(docs, scores.tolist()))
ranking = sorted(docs, key=lambda identity: (-by_id[identity], identity))
assert set(ranking) == set(docs)
# Independent deterministic ranking fixture: K=N can change RR without changing retained Recall.
original, reranked, gold = ['bad-1', 'bad-2', 'bad-3', 'good'], ['good', 'bad-1', 'bad-2', 'bad-3'], {'good'}
def rr(items):
    return next((1 / rank for rank, identity in enumerate(items, 1) if identity in gold), 0.)
assert set(original) == set(reranked) and rr(original) == .25 and rr(reranked) == 1.
# Rejected inputs cannot mutate the trained parameters.
before = {name: value.detach().clone() for name, value in model.state_dict().items()}
def rejects(call):
    try:
        call()
    except ValueError:
        pass
    else:
        raise AssertionError('invalid input accepted')
    assert all(torch.equal(before[name], value) for name, value in model.state_dict().items())
for bad in (None, {}, [], [('held_c allow',)], [(True, 'held_c allow')],
            [('[PAD]', 'held_c allow')], [('held_c allow', '[SEP]')], [('', 'held_c allow')]):
    rejects(lambda: encode_pairs(bad))
rejects(lambda: encode_pairs(pairs, extra_pad=True))
rejects(lambda: model(ids.float(), mask))
rejects(lambda: model(ids, mask.long()))
rejects(lambda: model(ids, ~mask))
rejects(lambda: model(torch.full_like(ids, len(VOCAB)), mask))
rejects(lambda: model(torch.zeros((1, 17), dtype=torch.long), torch.zeros((1, 17), dtype=torch.bool)))
rejects(lambda: model(torch.zeros((1, 2), dtype=torch.long), torch.zeros((1, 2), dtype=torch.bool)))
recipe = {'families': FAMILIES, 'rows': train + held, 'vocab': VOCAB, 'seed': 23, 'objective': 'BCE', 'steps': 101}
print('environment', json.dumps({'torch': torch.__version__, 'device': 'cpu', 'threads': 1}, sort_keys=True))
print('data_sha256', hashlib.sha256(json.dumps(recipe, sort_keys=True).encode()).hexdigest())
print('curve [completed_updates, same_snapshot_train_BCE, same_snapshot_held_family_BCE]', curve)
print('held_candidate_scores', json.dumps(by_id, sort_keys=True), 'ranking', ranking)
print('padding invariance passed; joint qkv gradients finite; disjoint document families')
print('independent K=N fixture RR 0.25 -> 1.0; retained Recall@4 1.0 -> 1.0')
print('invalid pair/control token/dtype/ID/mask/length rejected; trained parameters unchanged')
print('synthetic CPU only; held scores are observations, no pretrained semantic or deployment claim')
```

实测环境为Python 3.12.13、PyTorch 2.14.1、NumPy 2.4.6，CPU单线程、seed23；NumPy仅核现有runtime版本，本程序不用它。以训练前step0为共同基线，train BCE从0.783081降到完成101次更新后的0.023439，独立family BCE从0.706742升到1.430310。两个值在每个检查点均由同一参数快照测量；完成1、11、51次更新时分别为train/held 0.670288/0.653764、0.629878/0.636993、0.197411/0.862626。可见训练拟合与留出退化；过拟合、未覆盖的family或分布差异都可能参与，单条曲线不能唯一归因，也不能报告为泛化成功。一次held_c allow候选得分c-yes=2.252125、d-yes=2.085031、c-no=−5.995965，首名恰正确仍不能推翻整体验证退化；d-yes为错实体却高分也暴露边界。PAD不变性、qkv梯度finite、分组不重叠、非法pair/控制token/dtype/ID/mask/长度拒绝后参数不变，以及独立N=K fixture断言通过；fixture RR从.25到1，集合Recall@4始终1。

真实66源课具有联合Torch模型（64维、4头、1层、MSE、14人工triples、默认60epochs），不是词重叠算法；demo query复用训练query，所以仅静读可确认计算路径，未运行或取得泛化成绩。69复制另一48维CE、17triples/80epochs，再加词法blend；68的title bonus stand-in没有接66。模型输入、pool/head、data hash、seed、objective、checkpoint、候选身份/revision与pipeline stage都要保存；不以模型文件存在或raw score过阈证明可以发布。

### 13.4 训练练习怎样回到实际检索

更换召回模型先锁相同语料/ID与N，分别评价candidate Recall@N、CE排序MRR/nDCG和最终证据集合覆盖；召回改动不能仅看top1 raw score。比较1/10/40/60等epoch时同时记录train loss/positive-negative margin与held-out排名，源练习说“十轮代替一轮”不符合原默认60。替mean为CLS须同split/seed/参数预算并验证mask；加answerability第二head须标有答案/无答案，分开ranking与拒答损失、权重及校准集。推理阈值与缓存都绑定model/tokenizer/pool/length/doc revision/权限，不同query的raw scalar不能当同一概率阈值。

本节来源是第1来源固定提交3be078b37ffd8f0c04953c0678e48f5c6d0c7775的Phase19/66与69只读冻结记录；六课的练习、原题与stage关系由[12第15节](12-文本检索与RAG文档工程.md#15-分块融合重排与评价的练习和测验)统一维护。原有代码块与2026-10-04/07/08日期保留。未核当前模型卡/部署SDK/厂商参数，也未把来源型号、固定速度、memory估计或score阈值写为当前生产推荐。


## CLIP练习：双向分母和零损失的含义

本章第4节的单向对比目标可扩为CLIP式双向目标：图文embedding先L2归一，S=I@T.T/temperature，正例在对角线。图→文按行交叉熵、文→图按列交叉熵各占1/2，对S的梯度为(P_row+P_col-2*Identity)/(2N)。P_col必须按列归一；做两遍行softmax不是双向目标。

全相等logit时loss=logN；N=1时loss和对S梯度都是0，只因没有可区分负例，不证明学会检索。N增大还带来N²score、跨设备通信与假负例，沿第3/6节核多正例、分组切分和候选集合，而不是只比较训练loss大小。


2026-10-25增量：基于[固定3f9715c的计算练习](https://github.com/rohitg00/ai-engineering-from-scratch/tree/3f9715c62a3bedcffb68a260f1a65ee2dd9cc10a/practice)，源截止2026-10-23。已读题目/参考/提示并按知识去重复用，未运行来源练习、测试或训练；反例仅自写标准库核算，旧程序及原成功日期不变。51题落点、710路径读取层级与本批正文验证见[11记录](../维护/来源更新/2026-10-24/11-算法练习纠偏与训练路径融合.json)。
