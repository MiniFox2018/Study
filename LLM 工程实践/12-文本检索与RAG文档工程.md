# 12｜文本检索与 RAG 文档工程

检索增强生成先找证据，再组织答案。检索器、文档处理和回答器分别会出错，必须分别验证。本篇承接 [Embedding 训练](07-Embedding与检索模型训练.md)，与 [Agent 中的知识检索](../Agentic%20Design%20Patterns/01-核心章节/14-知识检索-RAG.md) 分工：这里维护检索公式、分块实现、证据定位和问答评价，后者维护 Agent 工作流及工具边界。

## 1. 从问题到有出处的答案

一个最小系统有六个环节：原文和版本 → 清洗与分块 → 建立索引 → 候选召回 → 重排与上下文装配 → 有证据的回答。索引是原文的派生表示，不能代替原文。检索得到的旧制度、重复副本或越权文档，分数再高也不能直接成为有效证据。

每块至少记录 `document_id、revision、chunk_id、start、end、section、access_scope`；扫描 PDF 还应记录页码、OCR 状态；表格保存表头及单位，代码保存语言和所属函数。`start/end` 是对**约定版本原文**的半开字符区间 `[start,end)`。若清洗改了文本，须同时保存清洗版本和原文映射，否则引用会指错位置。

例如“旧版额度 100；新版额度 120”不应当简单拼成两个同等可信的块。查询有日期时按有效期选证据；日期不明时指出版本差异。用户看不到新版时，不能越权检索新版，也不能把旧版答案伪装成当前结论。

| 方法 | 返回什么 | 适合的问题 | 主要风险 |
|---|---|---|---|
| 抽取式 QA | 原文中的起止跨度 | 单段中有直接答案 | 选错跨度、文档不相关、原文本身错误 |
| 检索式 FAQ | 已审核的问答条目 | 稳定流程、固定口径 | 相似问题被误匹配、答案过期 |
| 生成式 QA | 新组织的文本 | 多段解释、比较、汇总 | 无证据补全、忽略否定、引用不支持结论 |
| RAG QA | 检索证据支撑的生成或抽取 | 文档持续变化、私有知识 | 候选漏召回、版本权限错误、回答误用证据 |

生成式不等于闭卷；生成器也可以读检索结果。抽取式保证答案是输入中的文本跨度，**不能保证它回答了问题或事实正确**。无答案问题需要单独的拒答机制，不能强迫每段都输出跨度。

## 2. BM25：为什么词重复和文档长度都影响分数

对语料库的 `N` 篇文档，词 `t` 出现在 `df(t)` 篇中。一种常用非负 IDF 定义为：

$$
\operatorname{IDF}(t)=\log\left(1+\frac{N-df(t)+0.5}{df(t)+0.5}\right).
$$

查询词集合 `Q` 的 BM25 分数为：

$$
\operatorname{BM25}(q,d)=\sum_{t\in Q}\operatorname{IDF}(t)
\frac{f(t,d)(k_1+1)}{f(t,d)+k_1(1-b+b|d|/\overline{|d|})}.
$$

`f` 是文档词频，`|d|` 是词项数，平均长度来自整个索引。词频增加会饱和，避免重复几十次就无限得分；`b` 控制长度归一化，`b=0` 不校正文档长度，`b=1` 使用完整长度比例；`k1` 控制饱和速度。不同引擎可能采用不同 IDF、查询词频、字段加权和长度统计，不应把跨引擎原始分数直接比较。

假设 `N=3, df=1`，IDF 是 `log(1+2.5/1.5)≈0.981`。若文档长等于平均长度、`k1=1.2`，词频 1 的乘子为 1，词频 2 为 `4.4/3.2=1.375`，而不是翻倍。

### 2.1 完整 BM25、RRF 与排序指标

以下示例仅用标准库。中文演示按单字切分以保证不会丢光中文；真实系统应固定适合领域的分词器和词典版本，同样用于建库和查询。单字切分不是最佳中文检索方案。

```python
import math
import re
from collections import Counter

def tokenize(text):
    return re.findall(r"[a-z0-9]+|[\u4e00-\u9fff]", text.lower())

class BM25:
    def __init__(self, docs, k1=1.2, b=0.75):
        if not docs or not math.isfinite(k1) or k1 <= 0:
            raise ValueError("语料不能为空，k1 必须为正数")
        if not math.isfinite(b) or not 0 <= b <= 1:
            raise ValueError("b 必须在 [0,1] 内")
        self.docs = {key: Counter(tokenize(text)) for key, text in docs.items()}
        self.length = {key: sum(tf.values()) for key, tf in self.docs.items()}
        self.avg = sum(self.length.values()) / len(docs)
        self.df = Counter(t for tf in self.docs.values() for t in tf)
        self.k1, self.b, self.n = k1, b, len(docs)

    def search(self, query, top_k=10):
        if type(top_k) is not int or top_k < 0:
            raise ValueError("top_k 必须为非负整数")
        terms = set(tokenize(query))  # 本实现每个查询词计一次。
        scored = []
        for key, tf in self.docs.items():
            score = 0.0
            for t in terms:
                f = tf[t]
                if f == 0 or self.avg == 0:
                    continue
                idf = math.log1p((self.n - self.df[t] + 0.5) / (self.df[t] + 0.5))
                norm = self.k1 * (1 - self.b + self.b * self.length[key] / self.avg)
                score += idf * f * (self.k1 + 1) / (f + norm)
            scored.append((key, score))
        return sorted(scored, key=lambda x: (-x[1], x[0]))[:top_k]

def rrf(rank_lists, c=60):
    if not math.isfinite(c) or c < 0:
        raise ValueError("融合常数必须有限且非负")
    scores = Counter()
    for ranking in rank_lists:
        seen = set()
        for rank, key in enumerate(dict.fromkeys(ranking), 1):
            if key not in seen:  # 单个检索器的重复副本不能重复投票。
                scores[key] += 1 / (c + rank)
                seen.add(key)
    return sorted(scores.items(), key=lambda x: (-x[1], x[0]))

def ranking_metrics(ranking, relevant, grades, k):
    if type(k) is not int or k <= 0 or not relevant:
        raise ValueError("k 要为正整数，相关集合不能空；无答案查询另行评价")
    if len(set(ranking)) != len(ranking):
        raise ValueError("先去重，再计算排名")
    if any(not math.isfinite(g) or g < 0 for g in grades.values()):
        raise ValueError("相关等级必须有限且非负")
    retrieved = ranking[:k]
    hits = set(retrieved) & relevant
    recall = len(hits) / len(relevant)
    hit = float(bool(hits))
    rr = next((1 / i for i, key in enumerate(retrieved, 1) if key in relevant), 0)
    dcg = sum((2 ** grades.get(key, 0) - 1) / math.log2(i + 1)
              for i, key in enumerate(retrieved, 1))
    ideal = sorted(grades.values(), reverse=True)[:k]
    idcg = sum((2 ** g - 1) / math.log2(i + 1) for i, g in enumerate(ideal, 1))
    return recall, hit, rr, dcg / idcg if idcg else 0.0

docs = {"a": "refund policy refund window", "b": "shipping policy", "c": "账户退款条件"}
index = BM25(docs)
assert index.search("refund")[0][0] == "a"
assert index.search("退款")[0][0] == "c"
assert all(score == 0 for _, score in BM25({"empty": ""}).search("x"))
fused = rrf([["a", "a", "b"], ["b", "c", "a"]], c=0)
assert fused[0][0] == "b"  # a=1+1/3，b=1/2+1。
recall, hit, rr, ndcg = ranking_metrics(["x", "a", "b"], {"a", "b"}, {"a": 2, "b": 1}, 2)
assert (recall, hit, rr) == (0.5, 1.0, 0.5)
print("BM25 中文/空文档、RRF 去重、多证据指标均通过；nDCG", round(ndcg, 6))
```

此例同时检查中文不为空、全空文档分数为零、RRF 单列表去重和多个相关文档的指标。零分结果仍可能出现在排序中；业务需决定它是否进入候选，不应把首名自动当可靠证据。

## 3. 稠密、稀疏和多向量检索如何组合

稠密双编码器分别编码查询和文档，再用点积或余弦找近邻。文档向量可提前建立 ANN 索引，查询不需要逐篇跑联合编码。但它可能不敏感于罕见编号、精确数字、否定或权限条件。BM25 对精确词有效，却可能错过“费用报销”和“垫付申请”的语义对应。

学习型稀疏检索把文本映射到词表维度的权重，包括潜在词扩展；SPLADE 等方法并不等于“使用神经网络调出一组 BM25 参数”。晚交互模型为每个 token 留下向量，ColBERT 风格分数为：

$$s(q,d)=\sum_i\max_j q_i^\top d_j.$$

查询每个 token 在文档中找最匹配 token，再求和，比单向量保留更多细节，也提高存储和交互代价。交叉编码器则把 `query + document` 一起送入模型，能看到双方的细粒度交互；其成本随候选数上升，适合召回后重排，不能恢复候选集中根本没有的证据。

RRF 将各列表中的名次转成 `1/(c+rank)` 后相加，适合不同检索器分数尺度不可比的情况。`c` 大时头部优势更平缓，小时更偏向首位。它忽略原始分数差距，不保证胜过经过校准的分数融合。两个检索器返回同一个文档，这是跨检索器共同投票；同一列表的重复 chunk 则应先明确去重粒度。

典型流程是 BM25 和向量各召回一批 → 以文档版本和 chunk ID 去重 → RRF → 交叉编码器重排 → 证据块装配。候选数、最终块数和长度预算应通过真实查询评价决定，不能把“召回 30、取 5 块”当定律。权限最好在召回前过滤，重排和装配还应再次检查。

## 4. 分块的目标是保留能回答问题的证据单位

固定长度容易控制预算，却可能切开定义、条件或表格。递归分块优先选大边界，超长部分继续尝试更细边界，最后才按长度硬切。按句子或语义转折分块需要保留短但完整的独立事实，同时处理单句超长；不能为凑“最短 100 token”把互不相关的段落黏在一起。

大小单位必须写清：Python `len(str)` 计 Unicode 码点，JavaScript 字符串长度通常计 UTF-16 代码单元，都不是模型 token 数。上线使用模型对应 tokenizer，并在标题、生成的说明和引用标签加入后重新计量。标点和空白不能随手丢掉，它们承载原文位置和段落语义。

### 4.1 有出处、可检查覆盖的固定与递归分块

下面按字符预算演示机制，保留半开区间，所有原文字符至少覆盖一次。固定块的 overlap 必须小于 size，避免不前进；递归块无重叠，分隔符归入左块，空白不丢弃。生产中的 token 预算要替换长度函数和相应区间切分器，不能把此例宣称为 token splitter。

```python
from dataclasses import dataclass
import hashlib

@dataclass(frozen=True)
class Chunk:
    id: str
    document: str
    revision: str
    start: int
    end: int
    text: str

def chunk_of(text, doc, start, end):
    revision = hashlib.sha256(text.encode()).hexdigest()
    key = f"{doc}:{revision}:{start}:{end}"
    return Chunk(hashlib.sha256(key.encode()).hexdigest()[:16], doc, revision,
                 start, end, text[start:end])

def fixed_chunks(text, doc, size=80, overlap=10):
    if type(size) is not int or type(overlap) is not int or not 0 <= overlap < size:
        raise ValueError("必须满足整数 0 <= overlap < size")
    result, start = [], 0
    while start < len(text):
        end = min(start + size, len(text))
        result.append(chunk_of(text, doc, start, end))
        if end == len(text):
            break
        start = end - overlap
    return result

def recursive_chunks(text, doc, size=80, separators=("\n\n", "\n", "。", "；", " ")):
    if type(size) is not int or size <= 0 or any(not s for s in separators):
        raise ValueError("size 必须为正整数，分隔符不能空")
    spans = []
    def split(start, end, seps):
        if end - start <= size:
            if start < end:
                spans.append((start, end))
            return
        for i, sep in enumerate(seps):
            bounds, cursor = [start], start
            while True:
                pos = text.find(sep, cursor, end)
                if pos < 0:
                    break
                cursor = pos + len(sep)
                if cursor < end:
                    bounds.append(cursor)
            if len(bounds) > 1:
                bounds.append(end)
                # 先合并不超预算的邻段，再递归处理超长段。
                a, b = bounds[0], bounds[1]
                for nxt in bounds[2:]:
                    if nxt - a <= size:
                        b = nxt
                    else:
                        split(a, b, seps[i + 1:])
                        a, b = b, nxt
                split(a, b, seps[i + 1:])
                return
        for a in range(start, end, size):
            spans.append((a, min(a + size, end)))
    split(0, len(text), separators)
    return [chunk_of(text, doc, a, b) for a, b in spans]

text = "退款条件。\n\n凭证必须完整；" + "很长的无分隔文本" * 8 + "\n申请时间。"
for chunks in (fixed_chunks(text, "policy", 24, 5), recursive_chunks(text, "policy", 24)):
    covered = set()
    for c in chunks:
        assert c.text == text[c.start:c.end] and 0 < len(c.text) <= 24
        covered.update(range(c.start, c.end))
    assert covered == set(range(len(text)))
assert "".join(c.text for c in recursive_chunks(text, "policy", 24)) == text
assert recursive_chunks("", "empty", 24) == []
assert len({c.id for c in fixed_chunks(text, "policy", 24, 5)}) == len(fixed_chunks(text, "policy", 24, 5))
print("固定块和递归块：长度、出处、覆盖、无分隔回退均通过")
```

重叠能让跨边界句子进入候选，也会增加索引体积、重复召回和最终上下文浪费；不能假定零重叠必差或有重叠必好。按完整句子、标题和表格分块通常更容易维护证据，跨边界问题再用相邻块扩展处理。

### 4.2 语义分块、父子检索、上下文前缀与晚分块

语义分块可以先将句子或句子窗口编码，再比较相邻向量的余弦距离，在距离显著变大处切开，随后合并过短片段、硬拆超长片段。阈值或分位数应在该文档类型上确定；距离尖峰可能来自表格、引用或 OCR 噪声，而不是主题变化。用随机哈希向量比较距离只能检验程序接口，不能证明语义边界正确。

父子检索用短子块提高定位精度，再以 `parent_id` 取较长父段补充定义和上下文。父段应具有自身版本、范围和权限，多个子块命中同一父段只添加一次。展开前计入预算，必要时只取该定义附近的相邻块；把整章塞回上下文可能冲淡证据。

上下文前缀是在每块前附加“此块属于哪份文档、哪一节、什么主题”的简短说明，让脱离全文的块仍有语境。说明可以来自标题路径或模型生成，但**派生说明不是原文证据**。索引可以含说明；给用户引用时必须回到原文。用完整文档生成说明可能泄露别的权限内容，须在权限作用域内进行并缓存版本。

晚分块先在允许长度内对整段文档产生有上下文的 token 表示，再按块跨度池化，而不是先切块后独立编码。它要求取得 token 表示、字符/token 对齐、正确 attention mask，以及符合该模型训练契约的池化和投影。普通 `.encode(整篇)` 的一个向量不能事后平均出各块向量；超出模型窗口也不会自动获得全篇语境。

### 4.3 语义边界的确定性部分怎样验证

下面接收已经取得的逐句向量，先单位归一化，再按相邻距离决定切点，同时执行最大字符预算。向量 fixture 是手工指定，验证的是阈值、合并与超长回退；真实语义能力取决于外部编码器和人工边界评价。这个演示不复用原课随机哈希来假装语义模型。

```python
import numpy as np

def semantic_groups(sentences, vectors, distance_threshold=0.5, max_chars=40):
    x = np.asarray(vectors, dtype=float)
    if (not sentences or x.ndim != 2 or x.shape[0] != len(sentences) or x.shape[1] == 0
            or not np.isfinite(x).all() or not 0 <= distance_threshold <= 2
            or type(max_chars) is not int or max_chars <= 0 or any(not s for s in sentences)):
        raise ValueError("输入或预算无效")
    norms = np.linalg.norm(x, axis=1, keepdims=True)
    if np.any(norms == 0):
        raise ValueError("不能对零向量求余弦")
    unit = x / norms
    distances = 1 - np.clip(np.sum(unit[:-1] * unit[1:], axis=1), -1, 1)
    groups, current = [], ""
    for i, sentence in enumerate(sentences):
        boundary = i > 0 and distances[i-1] > distance_threshold
        if current and (boundary or len(current)+len(sentence) > max_chars):
            groups.append(current); current = ""
        # 超长单句硬拆，并保留所有字符。
        while len(sentence) > max_chars:
            groups.append(sentence[:max_chars]); sentence = sentence[max_chars:]
        current += sentence
    if current:
        groups.append(current)
    return groups, distances.tolist()

sentences = ["退款规则。", "凭证要求。", "配送说明。", "无分隔长句" * 12]
vectors = [[1,0], [0.99,0.01], [0,1], [0,1]]
groups, distances = semantic_groups(sentences, vectors, 0.5, 20)
assert groups[0] == "退款规则。凭证要求。"
assert distances[0] < 0.01 and distances[1] > 0.9
assert "".join(groups) == "".join(sentences) and max(map(len, groups)) <= 20
print("语义切点 fixture", [round(x, 4) for x in distances], "；所有字符和长度边界通过")
```

实际向量若按句子窗口编码，要说明窗口如何形成、切点对应哪个句末，并把输出组还原为原文区间。阈值太低会碎成小句，太高会合并跨主题内容。图示的三种切点是方法示意，不是同一语料上的最优分块实测。

### 4.4 从候选到上下文的预算规则

装配按重排顺序放证据，但先处理同版本重叠块、父段重复、标题和引用开销。对互相矛盾的块保留区别和时间条件，而不是盲目去重。预算应留出指令、问题、工具结果和预期输出空间。

可以将候选块视为区间，对同一文档版本中相邻或重叠区间合并，再回原文截取。不要仅凭向量近似判断“重复”：两个数值不同的制度段可能词语几乎相同，却必须保留差异。召回块不足以支持答案时返回“依据不足”，低相似分数阈值只能当经过验证的拒答特征，不能当通用真值概率。

## 5. 抽取式问答：起止头、无答案与原文偏移

起止头输出每个 token 是起点、终点的分数。选跨度时要满足 `end >= start`、最大答案长度、属于上下文而非问题或特殊 token；窗口切分后还要统一比较不同窗口候选。模型 tokenizer 的 offset mapping 把 token 跨度还原为字符跨度，中文、子词和标点尤其不能按单词拼接来重建原文。

```python
import math

def best_span(context, offsets, start_logits, end_logits, max_tokens=4, null_score=None, margin=0.0):
    n = len(offsets)
    if (n == 0 or len(start_logits) != n or len(end_logits) != n
            or type(max_tokens) is not int or max_tokens <= 0):
        raise ValueError("维度或长度参数无效")
    if not all(math.isfinite(x) for x in list(start_logits) + list(end_logits)):
        raise ValueError("分数必须有限")
    if not math.isfinite(margin) or (null_score is not None and not math.isfinite(null_score)):
        raise ValueError("null 分数及阈值必须有限")
    def valid(pair):
        a, b = pair
        return type(a) is int and type(b) is int and 0 <= a < b <= len(context)
    candidates = []
    for i, pair in enumerate(offsets):
        if not valid(pair):
            continue  # 本接口以无效区间标记 question/special/padding token。
        a, initial_end = pair
        previous = pair
        for j in range(i, min(n, i + max_tokens)):
            if not valid(offsets[j]):
                break  # 不能越过中间被屏蔽的 token 去拼成跨段答案。
            c, d = offsets[j]
            if c < previous[0] or d < previous[1] or d < initial_end:
                break  # offset 区域必须非递减；允许字节子词共享同一区间。
            previous = (c, d)
            candidates.append((start_logits[i] + end_logits[j], i, j, a, d))
    if not candidates:
        return None
    score, i, j, a, b = max(candidates, key=lambda x: (x[0], -x[1], -x[2]))
    if null_score is not None and null_score - score >= margin:
        return None
    return {"text": context[a:b], "start": a, "end": b, "score": score}

context = "新版退款期限为30天。"
offsets = [(0, 2), (2, 4), (4, 7), (7, 9), (9, 10), (10, 11)]
ans = best_span(context, offsets, [0, 0, 0, 4, 0, 0], [0, 0, 0, 0, 4, 0])
assert ans["text"] == "30天"
assert best_span(context, offsets, [0] * 6, [0] * 6, null_score=5) is None
# 两端分数最高，但中间是特殊 token，不得跨过它返回整个 abc。
cross = best_span("abc", [(0,1), (0,0), (2,3)], [8,-20,-20], [-20,-20,8])
assert cross["text"] != "abc" and cross["score"] == -12
backwards = best_span("abc", [(2,3), (1,2)], [5,-10], [-10,5])
assert backwards["text"] == "c" and backwards["score"] == -5
# UTF-8 字节级子词可能映射为同一字符区间，重复区间允许组合。
repeated = best_span("中", [(0,1), (0,1)], [5,-10], [-10,5], max_tokens=2)
assert repeated["text"] == "中" and repeated["score"] == 10
for invalid in (0, -1, 1.5, True):
    try:
        best_span(context, offsets, [0]*6, [0]*6, max_tokens=invalid)
    except ValueError:
        pass
    else:
        raise AssertionError("max_tokens 必须为正整数")
print(ans["text"], ans["start"], ans["end"], "；拒答、跨 mask、倒序、重复区间和整数边界通过")
```

本接口要求同一原文窗口的 context token；问题、特殊 token 和 padding 用无效区间屏蔽，连续候选中 offset 必须非递减。若输入包含多个不同窗口/段落，还须按 window/segment 分组调用，不能拼接 offset 重新开始的序列。字节子词映射到同一字符区间允许重复。此例实测的是跨度选择，分数是人工 fixture，未加载 QA 模型。真实 null score 的定义和跨窗口阈值要按训练模型确定，用有答案、无答案、错文档集合校准；此处的 margin 不是所有模型通用参数。

## 6. 生成式问答要逐主张检查证据

输入至少明确问题、证据 ID/版本、只按证据回答、证据不足允许返回未知，以及引用格式。证据中的指令按文档内容处理，不能改变系统授权。输出可组织为 `answer + citations + unsupported_parts`，但是结构合规仍不证明引用正确。

引用有三个检查层：ID 确实存在；引用跨度确实来自这个版本；跨度支持对应主张。“文件写了 30 天，答案写 60 天并引用该文件”能通过前两层，过不了第三层。支持判断可以由业务断言、人工审核、NLI 或 judge 辅助，但后两者也需要误差校准。多跳问题要求每个中间事实有出处，而不是一个引用 ID 覆盖整段推断。

EM 检查严格或规范化字符串一致，适合短答案；token F1 比较预测和参考 token 多重集合，适合不同跨度长度，但不能识别颠倒、否定或数字因果错误。中文需明确字符或分词评价，不能用 `[a-z]+` 分词后把所有中文答案变成空串并得到满分。无答案样本要分别统计拒答正确率、有答案误拒率与错误作答率。

### 6.1 EM 与 token F1 的完整小例子

令共同 token 多重集合大小为 C，预测 token 数为 P，参考数为 G，则 precision=C/P、recall=C/G，F1 为二者调和平均。下例中文按字符、英文和数字按连续串评价，明确保留否定词；这是一份教学协议，不宣称与 SQuAD 官方规范化脚本逐项相同。

```python
import re
from collections import Counter

def answer_tokens(text):
    return re.findall(r"[a-z0-9]+|[\u4e00-\u9fff]", text.lower())

def em_f1(prediction, reference):
    pred, gold = answer_tokens(prediction), answer_tokens(reference)
    em = float(pred == gold)
    if not pred or not gold:
        return em, float(not pred and not gold)
    common = sum((Counter(pred) & Counter(gold)).values())
    precision, recall = common/len(pred), common/len(gold)
    f1 = 2*precision*recall/(precision+recall) if common else 0.0
    return em, f1

assert em_f1("June 29, 2007", "June 29, 2007") == (1.0, 1.0)
assert abs(em_f1("June 29th, 2007", "June 29, 2007")[1] - 2/3) < 1e-12
assert em_f1("允许退款", "禁止退款")[0] == 0.0
assert em_f1("允许退款", "禁止退款")[1] == 0.5
assert em_f1("30天", "60天")[1] == 0.5  # 只共享“天”，并不表示部分事实正确。
assert em_f1("", "") == (1.0, 1.0)  # 双方都空，须由无答案任务语义确认。
print("EM/F1：英文跨度、中文差异、数字差异、空答案协议通过")
```

F1 不足以判定事实：两答案只差一个否定词或数字，仍可能有较高词重叠。业务关键字段可增加精确数值/单位断言；公开基准比较必须使用该基准原评分协议，而不是用自定义分词得分冒充官方成绩。

## 7. 用评价找出故障，而不是只看一个命中率

`Recall@k=命中的相关文档数/全部相关文档数`；`Hit@k` 只问至少一条相关证据是否进入前 k；MRR 平均首条相关文档排名的倒数；nDCG 对高相关等级排得靠前给予更高分。只有每题恰好一个相关文档时，Recall 和 Hit 才相同。

完整检索评价须确定 gold 粒度：文档、块、精确证据跨度，还是一组必须共同出现的事实。一个问题需两条证据，命中一条的 Hit 为 1、Recall 为 1/2，但仍答不了完整问题。对父子展开分别记录子块召回与最终证据覆盖，不把父段包含参考字符串当成整个 QA 成功。

生成评价分别检查支持率、答案相关性、事实/业务正确性、引用准确性、拒答及实际任务完成；见 [评测与实验管理](06-评测与实验管理.md)。评测框架负责运行协议、收集记录和汇总，不天然提供正确性金标准。保留无答案、版本冲突、中文、编号、长文档、表格、权限不足等切片。

部署时记录文档数/块数、分块与分词版本、嵌入版本、索引时间、召回与重排配置、最终块 ID、延迟分解、失败原因。更新文档后失效旧块与缓存；换嵌入模型后重建空间；修正文档结构后重新比较相同测试集。

## 8. 练习与可核对答案

1. **RRF 手算。** 两列表 `[a,b]`、`[b,c,a]`，`c=0`：a 为 4/3、b 为 3/2、c 为 1/2，顺序 b,a,c。把第一列表改成 `[a,a,b]`，去重后结果相同。
2. **多相关证据。** gold 为 `{d1,d2}`，前 3 是 `[d3,d1,d4]`：Recall 为 1/2，Hit 为 1，RR 为 1/2。不能把这次检索称为完整证据召回。
3. **重叠边界。** `size=10, overlap=10` 必须拒绝；`overlap=-1` 也拒绝，避免步长错误和字符遗漏。修改块大小后字符覆盖与出处断言应仍成立。
4. **结构化文档。** 把标题、一个含单位表格、一段代码与正文混合。答案必须保留标题路径、表头/单位、代码完整性；超过预算时拆表行但重复表头，不能盲切成无单位数字。
5. **语义分块对照。** 固定原模型、查询与 token 总预算，只换 fixed/recursive/semantic/parent 策略；记录 Recall、必需事实覆盖、答案正确率和 P95。某方法在少数题更好不能推导成普遍默认值。
6. **错引用反例。** 答案“30 天”引用写“60 天”的有效来源：ID 检查通过、支持检查失败；抽取原文也不保证其针对当前问题或生效日期正确。
7. **缺失证据。** 人为从候选池移除正确段：reranker 无法恢复它，应先修召回；所有证据都缺失时回答“依据不足”，而不是用闭卷记忆补成有出处的结论。
8. **评价深度。** 一个字符串匹配为满分的回答是“不是 pineapple”：简单子串匹配会误判；应使用任务指定的精确答案或人工/可验证协议，长上下文反例见 06。

## 来源与核验

- 吸收来源：[AI Engineering from Scratch](https://github.com/rohitg00/ai-engineering-from-scratch/tree/3be078b37ffd8f0c04953c0678e48f5c6d0c7775)，固定提交 `3be078b37ffd8f0c04953c0678e48f5c6d0c7775`，Phase 05 第 13、14、22、23 课，整理日期 2026-10-04。原课 docs、Python/TypeScript、测验、SVG、动态图与输出建议均已阅读；输出 skill 只作为学习建议处理，不安装或执行。
- 核心原理为重新组织的中文说明与独立示例；原课简化词频、哈希向量、固定切块和子串命中不作为真实 BM25、语义模型、递归分块或正确性验证。模型训练维护入口为 07，评价维护入口为 06。
- 上述程序仅做本地合成数据验证；没有下载模型或语料、没有进行真实向量服务、重排器或 LLM 测试。
