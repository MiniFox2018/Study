# 12｜文本检索与 RAG 文档工程

检索增强生成先找证据，再组织答案。检索器、文档处理和回答器分别会出错，必须分别验证。本篇承接 [Embedding 训练](07-Embedding与检索模型训练.md)，与 [Agent 中的知识检索](../Agentic%20Design%20Patterns/01-核心章节/14-知识检索-RAG.md) 分工：这里维护检索公式、分块实现、证据定位和问答评价，后者维护 Agent 工作流及工具边界。

**第一次读法**：先读第1、2、4、6、7节，用同一小语料说明词项得分、分块、引用与拒答；需要完整管道再做7.1。代码与增量发布看13，权限会话看14，检索指标口径看7.2及16；视觉证据18、网页变化19、研究助手20按实际任务选择。先保版本、正例集合和分母，再考虑更多模型或索引工具。

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

### 2.2 字段归一化与有身份的加权融合

2026-10-12 增量。BM25 的正文词频、文档长度和平均长度是联动的。把标题重复三次再拼正文，会同时改变三者；例如标题1词、正文9词变成12词，标题词频从1变3，其他正文词也受到新长度分母影响。这是词项重复的启发式，不能称作每字段独立归一化的 BM25F。

一种明确的 BM25F 合同先对字段 f 的词频做长度校正，再聚合：

$$\tilde f(t,d)=\sum_f w_f\frac{f(t,d_f)}{1-b_f+b_f|d_f|/\overline{|d_f|}},\qquad s(q,d)=\sum_{t\in Q}\operatorname{IDF}(t)\frac{(k_1+1)\tilde f(t,d)}{k_1+\tilde f(t,d)}.$$

`w_f` 是非负字段权重，`0≤b_f≤1` 控制该字段长度校正，`k_1>0` 控制聚合词频的饱和，字段均长来自固定索引快照；IDF 的文档统计口径也须固定。缺字段和平均长度为零须单独定义，不能直接除零。此公式先合并归一化词频后饱和，与“每字段各算 BM25 再相加”亦不相同。把同一词置于短标题和长正文，用同文档相关标签比较真字段方案、重复标题和无字段基线，才知道符号匹配是否改善；不用标题倍数猜质量。

2026-10-13补核：作者修正版TREC报告§4.1（PDF第5页）给出“逐字段校长 → 加权合并词频 → 一次饱和”的公式。原论文写的是 `f̃/(k₁+f̃)`；上式采用常见的额外因子 `k₁+1`，固定k₁时这是正的统一缩放，不改变同一查询的候选排序，但raw score阈值、跨组件分数混合及数值对照仍需统一。标题重复是早期字段加权的一种办法；它与此处具有独立字段长度校正的版本要分清，不能只凭“重复”就认为完全没有字段加权意义。核验限该节公式与说明，未复现论文的全部实验或当前检索质量。[Microsoft Cambridge at TREC 2004，作者修正版](https://www.microsoft.com/en-us/research/wp-content/uploads/2004/01/Microsoft-Cambridge-at-TREC-2004-Web-and-HARD-track.pdf)

加权 RRF 的合同为 `score(id)=Σ_j w_j/(c+rank_j(id))`，缺席列表贡献0，rank从1起。`c` 与所有权重必须有限且非负，权重数等于列表数；零权重腿不影响排序。每列表先按稳定的 `(document,revision,chunk/span)` 身份去重再编号，跨列表同一身份可各投一次。`[A,A,B]` 在 c=60 时应是 A=1/61、B=1/62，不能给 A 再加1/62并把B挤到rank3。同名ID若对应不同版本或文本，应拒绝冲突并回查索引，不能让最后一个对象静默覆盖。

现第2.1节已实现去重公式与指标，不另造检索管道。扩成 weighted 版本时只扩参数和身份验证，保留其反例；第7.1/13节继续负责快照和权限。原始向量零分、未知词和不相关内容仍可能得到近邻列表，RRF给正贡献只表示名次投票。无答案判定另用独立标注和支持检查；同文档去重不会自动解决无答案。哈希累加 M 个返回项并排序 U 个唯一候选约需 `O(M+U log U)`，不是与候选规模无关的常量时间。

## 3. 稠密、稀疏和多向量检索如何组合

稠密双编码器分别编码查询和文档，再用点积或余弦找近邻。文档向量可提前建立 ANN 索引，查询不需要逐篇跑联合编码。但它可能不敏感于罕见编号、精确数字、否定或权限条件。BM25 对精确词有效，却可能错过“费用报销”和“垫付申请”的语义对应。

学习型稀疏检索把文本映射到词表维度的权重，包括潜在词扩展；SPLADE 等方法并不等于“使用神经网络调出一组 BM25 参数”。晚交互模型为每个 token 留下向量，ColBERT 风格分数为：

$$s(q,d)=\sum_i\max_j q_i^\top d_j.$$

查询每个 token 在文档中找最匹配 token，再求和，比单向量保留更多细节，也提高存储和交互代价。交叉编码器则把 `query + document` 一起送入模型，能看到双方的细粒度交互；其成本随候选数上升，适合召回后重排，不能恢复候选集中根本没有的证据。

RRF 将各列表中的名次转成 `1/(c+rank)` 后相加，适合不同检索器分数尺度不可比的情况。`c` 大时头部优势更平缓，小时更偏向首位。它忽略原始分数差距，不保证胜过经过校准的分数融合。两个检索器返回同一个文档，这是跨检索器共同投票；同一列表的重复 chunk 则应先明确去重粒度。

典型流程是 BM25 和向量各召回一批 → 以文档版本和 chunk ID 去重 → RRF → 交叉编码器重排 → 证据块装配。候选数、最终块数和长度预算应通过真实查询评价决定，不能把“召回 30、取 5 块”当定律。权限最好在召回前过滤，重排和装配还应再次检查。

### 3.1 一个问题的改写、多视角、拆解、HyDE与Step-back

先固定一个虚构当前政策快照。以下短ID均指向具体document/revision/span；旧版企业90天规则在有效期过滤时排除，不与当前证据融合。分数和排名是手设教学输入，验证信息流/融合/必要事实，不是神经检索实测。

| ID | 当前原文证据 | 能支持的事实 |
|---|---|---|
| S | 标准客户可在30天内申请退款 | 标准计划期限，不能代替企业计划 |
| E | 企业客户可在60天内申请按比例退款 | 企业期限与按比例规则 |
| P | 退款处理需要5个工作日 | 已受理后的处理时间 |
| A | API调用需要有效令牌 | 本题无关 |

问题是“我们是企业客户，退订最晚什么时候能退款，受理后还要多久？”；本题必需事实集合为{E,P}，命中其中一个不算完整回答。若用户没有给支付日期，这里只能回答一般窗口，不能假造一个具体最后申请日；“5个工作日处理”也不能改写为保证银行到账日期。保留问题的计划等级、时间条件与权限范围。

#### 3.1.1 独立改写、多视角与子问题有不同职责

多轮历史“我们用企业版”加跟进“最晚什么时候，之后多久？”可改写成独立Query：“当前企业计划的退款申请窗口、按比例规则和受理后处理时间”。这补回指代和省略，不应新增90天、具体支付日或其他计划。适用于检索器看不到历史、口语表达与文档术语错位；原问题与历史仍保存以检查语义漂移。

Multi-query为**同一完整意图**生成不同表述，例如q1“企业版退款窗口与处理时间”、q2“大客户取消订阅的退款资格与受理后等待时间”。它们分别检索，结果按同一稳定ID去重再融合；“大客户”只是检索别名，最终仍须核实它是否对应企业计划，不能把别名当分类结论。

设q1的前2为[E,S]、q2的前2为[P,E]。raw有4个返回项，唯一ID只有3个；RRF(c=60)得到E=1/61+1/62≈.0325225、P=1/61≈.0163934、S=1/62≈.0161290，前2是[E,P]。同一E跨列表得到两次信号，同一列表内重复E不能重复投票。最终保留E的原文一次。若direct的前4为[S,E,A,P]、只装前2，则只有E的必需事实：Hit=1而Recall=1/2；此教学输入的融合前2覆盖{E,P}，并不证明真实Multi-query必胜。

Decomposition则把**不同必需事实**拆开：q_window“企业计划的申请期限与按比例规则？”需要E；q_processing“退款已受理后处理多久？”需要P。分别保留子问题→证据→原问题事实的关系，聚合后必须检查二者都满足。重复同义Query不等于拆解；一个综合改写也不保证得到全部子问题。比较“团队改善最多”之类问题，还需先取各团队的可比数值与基线，再做有单位、同时间窗口的计算，而非将多个检索文本拼成一个答案。

上述Multi-query与direct都给4个原始候选名额、最后2块，但Multi-query仍多一次Query编码/检索；拆解也有多次检索和汇总成本。生成Query若调用LLM，还要计入该调用。固定输入快照、总候选预算、装配token预算及评价集，再观察必要事实覆盖、误拒/错答、语义漂移、调用数和延迟，不能只比较更大候选池的Hit。

#### 3.1.2 HyDE用假设文档检索，引用只能来自真文档

同一问题的HyDE数据流是：原Query → 生成一段可能回答问题的假设文档h → 按配套retriever的编码契约embed(h) → 在预计算的真实文档向量中找候选 → 读取候选原文、版本与权限 → 装配真实证据后回答。生成的h通常更像库中文档的叙述风格，用来桥接问题/文档表述差异；它未经过事实核验。[HyDE原论文](https://arxiv.org/abs/2212.10496)

受限例子故意给h错误数值：“企业客户可能有90天的退款窗口，受理后通常3个工作日处理。”假定用h检索得到[E,P]，最终可引用的仍是E的60天与P的5个工作日，不能引用h、90或3。若h引导系统找到旧版、别的计划或别的地区，过滤与支持检查应拒绝；保留direct原Query的检索腿可以帮助识别偏移。这里的候选序列也是教学输入，没有真正生成h或运行语义encoder。

源固定填充模板包含原Query加“具体政策/流程”等通用词，未生成真实HyDE假设，更未证明解决同义词缺口。真正HyDE通常增加一次假设生成与其编码/检索，可能扩大输入、引入错误细节或额外数据传出；直接Query已有效时不必开启。将h用于最终回答但不回读原文，会把检索辅助错误升级成伪证据。

#### 3.1.3 Step-back取概念，再回到原具体条件

原题的概念层问题可以是“订阅退款的资格、申请窗口与处理阶段由哪些规则决定？”它检索一般原则；原具体Query继续检索“当前企业计划”的条款。两条证据腿合并后，概念层帮助区分“能否申请/期限”和“受理后处理”，具体层决定本题的60天、按比例与5工作日。抽象不能抹掉企业、当前版本、权限和原任务条件。[Step-back原论文](https://arxiv.org/abs/2310.06117)

反例：具体腿[S,E]，概念腿[P,S]。按同一RRF，S≈.0325225、P≈.0163934、E≈.0161290；只取前2会得到[S,P]，反而漏掉必需企业证据E。因此概念检索不是去掉约束重问一次；合并后须核对{E,P}，缺E时针对企业条款再检索或返回依据不足，不能用S的30天代替。此例验证融合可能偏向共同的泛化段，不断言Step-back无效。

适用失败是具体问题埋在细节中、检索/回答缺少原则框架，尤其需要先理解多个条件的关系；精确编号或一个明确数值查找通常先直接检索。LLM抽象、额外检索、原则文本和回到具体题的组织都可能增加费用和context噪声。以同direct基线逐case比较，不能因抽象回答流畅就认定任务改善。

#### 3.1.4 双编码器召回与联合编码重排的排序例

双编码器分别得到query向量q与文档向量d，使用第7篇约定的相似度；文档向量可离线算一次并缓存，在线通常只编码新Query再搜索。Cross-encoder把同一个Query与每个候选文档一起编码，联合看到词项关系、条件和否定，再输出相关性分数；不同Query的Q-D配对一般需重算，不能将一个预存文档向量当作联合分数。大库先便宜地召回K个，再对K对联合评分取k个，成本与K、文本长度、模型和硬件相关，没有通用100–1000倍常数。

| 文档 | 手设双编码器相似度 | 手设联合相关性分数 | 本题角色 |
|---|---:|---:|---|
| S | .83 | .40 | 主题相近，计划条件不符 |
| E | .81 | .92 | 企业申请窗口 |
| P | .55 | .87 | 处理时间 |
| A | .12 | .10 | 不相关 |

K=3召回[S,E,P]，联合评分后为[E,P,S]，k=2保留两项必需证据。K=2只召回[S,E]，联合评分至多得到[E,S]，P从未进入候选，重排不能恢复；应改召回/Query/候选预算。两列来自不同评分机制，数值不应直接相加或当正确概率。这只是可手算的排序输入，不是实际神经模型成绩。

7.1程序的identity重排没有联合Q-D模型，词重叠/短语/位置启发式也不是cross-attention；真实模型评分仍须看本地相同任务与失败切片。Query改写、Multi-query、拆解、HyDE与Step-back都只改变查询/证据获取方式，不能改变原问题的成功标准、权限或出处要求。

### 3.2 派生查询的协议、重复信号与真实预算

2026-10-12 增量。改写器的输入保留原问题、已授权历史和硬条件；输出可用 `original_query、strategy、rewrites、facets、hypothesis、preserved_constraints、errors` 表示。原实体、时间、数字、否定、比较关系和权限范围不得因改写消失。Multi-query 的每条改写应回答同一个完整问题；decomposition 的每个子问题应覆盖不同必要事实，并保留它们共同满足原题的关系。仅按英语 `and` 切分无法判断原子问题、否定或比较，查询很长也不自动需要拆解。

第3.1的企业退款题已提供实际手算：Multi-query可融合到 E/P，Step-back也会使S挤掉E。因此策略选择应先检查失败：术语错位可试同意图改写；缺几个明确事实可拆facet；问题/文档表达差异可试HyDE；原则缺失可试Step-back。保持direct基线，验证原子题误拆率、多facet漏拆率、全部必要事实覆盖和代价。所谓 rewrite confidence 要在独立集校准为“保意图/检索收益”等明确事件；模型自报分数不能直接成为概率或授权依据。

HyDE假设和chunk summary都属于派生检索文本。它们可以带来检索线索，也能引入错误实体、数值和答案泄漏；存储时标出 `derived_from`，引用时回真实原文版本/跨度。假文即使词分布接近候选也不保证找到正确证据，2–3句只是待调预算。生成hypothesis并不允许回答直接复制它；上下文只能来自已核真实来源。

融合必须追踪每一路来源而非只留最终rank。某实现把“原BM25+假文dense”融合一次，又把“原BM25+原dense”融合一次，最后再次RRF：原词法腿已经重复影响，两个中间列表不是两份独立原始证据。MQ若无可用同义词而返回多个原Query副本，也会重复强化同一排序。应规范化和去重改写，明确各腿权重/相关性，再在同ID上合并；多样改写须保原条件，不靠重复同Query赚票。每个facet保自己的证据映射，不能以一个doc命中代替全问题支持。

时间预算按实际依赖计算。串行策略耗时是改写/编码/检索各调用之和，再加融合、重排和回答；真正并发的独立腿才可近似取最慢腿耗时，还含排队、失败/重试和后续依赖。多策略并行的端到端延迟不等于“一次LLM调用”。记录原始调用数、唯一改写数、raw/unique候选、候选N、输出K、上下文token/字符和各stage wall time，分别比较相同总候选预算与允许额外计算的效果；源课串行mock没有证明任何真实并行速度。

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

### 4.5 结构、token窗口与正确的语义质心

2026-10-12 增量。第4.1节保留原文区间和全部字符，第4.3节已有邻句距离与硬回退，不重新复制五种splitter。新增方法先定义证据不变量：块正文等于指定revision的原文slice；原文无遗漏；标题路径、表头单位和代码作用域可回查；预算是明确的字符或token合同。分块好坏最终看全库未知文档检索、完整证据和成本。

结构分块先扫描原文而非先strip再拼接。保留第一标题前的preamble为独立区域；维护H1–H6标题栈，新标题到来时弹出同级及更深节点，再加入本标题。若把一个H2当父段，遇H3只增加子层，到下个H2或H1才结束父范围。代码fence开启后，里面的 `# config` 不是文档标题；关闭fence应按对应标记/长度规则识别，未闭合fence保留诊断。没有标题时仍保全文。每个输出带 `section_path、parent_id、source_start/end`，空标题可保导航元数据，但不当成有答案的正文块。表格按行拆需重复表头/单位作为派生装配前缀，并保原行跨度；完整代码超过预算时按语法/函数片段拆或显式超限，不能悄悄丢尾。

递归过程从段落→换行→句界→空白选择边界，尝试合并预算内邻段；分隔符耗尽后必须硬切并保证位置前进。超长单句/无空白中文、长URL和YAML键值都会触发最后层。测试应含无分隔长串、空文档、preamble、嵌套标题、fence内伪标题、缩写/小数/中文、跨块条件与整文覆盖。只检查长度≤200不能证明目标80的硬上限；只检几个词出现也不能证明所有原文字符保留。

token窗口须固定tokenizer和revision，保存token→原文字符或字节的offset映射。半开token区间 `[i,j)` 回到该版本原文 `[a,b)`，再验证原slice和实际token数。UTF-8字节、Unicode码点、UTF-16代码单元和模型token不是一种单位；子词可能共享字符范围，独立解码切片也可能破坏边界。标题/summary/引用标签加入装配后重新计量，offset仍指原文。这里没有安装或调用tokenizer，既有代码继续明确是字符程序。

另一种语义算法比较“当前组均值”与下一句。先取得同一编码空间的句向量 `v_i∈R^d`，保存未归一化和 `S=Σv_i` 与真实计数n，用 `centroid=S/n` 的方向计算余弦；收新句后执行 `S←S+v、n←n+1`。不能先增n再把旧mean乘新n，亦不能把每次归一化后的mean当原始向量和。v1=(1,0)、v2=(0,1)的正确方向为(1,1)/√2；错算 `(2v1+v2)/3` 后变成(2,1)/√5。单位向量归一化mean也有零范数，例如相反方向抵消，必须显式定义切块/回退。

相似度阈值规则 `cos(centroid,v)<τ` 时切分；若用距离 `1−cos` 则是 `distance>δ`，方向不能写反，等号行为也须固定。每句先验证finite、维度和非零，再结合硬预算切分；新组从当前句开始，不能把同一向量累加两次。归一化前后、句窗口、模型revision、阈值都会改变边界，更新须协调chunk ID、原文映射和索引。哈希向量只可验证接口；真实边界性能需要独立标注与同预算评测，800/500/.6等不是普适默认。

原64的span评价在已知正确doc内找块，只要和gold相交一个字符就命中。例如gold[100,130)、chunk[90,101)只有1/30字符覆盖，却Hit=1。全库候选Recall、完整span包含、必要条件/上下文支持应另报告；相邻/父段展开可能恢复碎片，因此“任何切坏都永不可恢复”过于绝对。结构/句子也没有未经实验就永胜固定窗口的保证。

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


### 7.1 接通离线管道：版本、父子块、候选、引用与拒答

这里把分块、同空间检索、BM25/RRF、父段展开与回答追溯接成一个可独立运行的标准库例子。为了独立运行，保留第2节的同一 BM25/RRF 公式为短函数；真实项目应复用同一个模块。向量腿是词表 TF-IDF，重排是 identity fixture，回答器仅能原文抽取所列两类业务事实；没有神经语义模型、cross-encoder、LLM 或自动支持判断。

先按有效期/访问范围过滤文档，再在本次快照的子块上拟合词表；每个父/子块带原文版本及半开区间。多个子块展开到同一父块只放一次，引用元数据和问题都计入本例字符预算。此处字符不是模型 token，实际应用须替换计量器并保留输出预算。旧/私有文档即使非常相似也不能进入公开当前查询的候选。

每次查询保存原问题与派生Query、索引快照、候选、重排、上下文与生成状态，能定位哪一步漏掉证据。有限的多轮规则仅把明确的“那企业呢”接到已知退款问题，不能假装能理解任意对话指代。

```python
import hashlib, json, math, re
from collections import Counter
from dataclasses import dataclass
from datetime import date

def terms(text):return re.findall(r'[a-z0-9]+|[\u4e00-\u9fff]',text.lower())
def digest(text):return hashlib.sha256(text.encode()).hexdigest()
@dataclass(frozen=True)
class Doc:
    id:str
    text:str
    since:str
    until:str|None=None
    scope:str='public'
    @property
    def revision(self):return digest(self.text)

def bm25_rank(query,rows):
    counts={k:Counter(terms(c['text'])) for k,c in rows.items()}
    n=len(counts);avg=sum(sum(c.values()) for c in counts.values())/n if n else 0
    df=Counter(t for c in counts.values() for t in c)
    scored=[]
    for k,c in counts.items():
        length=sum(c.values());score=0.
        for t in set(terms(query)):
            f=c[t]
            if f and avg:
                idf=math.log1p((n-df[t]+.5)/(df[t]+.5))
                score+=idf*f*2.2/(f+1.2*(.25+.75*length/avg))
        if score>0:scored.append((k,score))
    return sorted(scored,key=lambda x:(-x[1],x[0]))
def fuse(lists):
    scores=Counter()
    for items in lists:
        seen=set()
        for rank,(key,_) in enumerate(items,1):
            if key in seen:continue
            seen.add(key);scores[key]+=1/(60+rank)
    return sorted(scores,key=lambda x:(-scores[x],x))

class OfflineRAG:
    def __init__(self,docs,as_of='2026-10-07',scopes=('public',)):
        if not isinstance(scopes,(tuple,list,set,frozenset)) or not scopes or any(type(s) is not str or not s for s in scopes):raise ValueError('访问范围合同')
        self.scopes=frozenset(scopes)
        when=date.fromisoformat(as_of);self.children={};self.parents={};self.docs={};self.excluded=[]
        for d in docs:
            visible=d.scope in scopes and date.fromisoformat(d.since)<=when and (d.until is None or when<=date.fromisoformat(d.until))
            if not visible:self.excluded.append((d.id,d.revision[:8],d.scope));continue
            key=(d.id,d.revision)
            if key in self.docs:raise ValueError('文档版本重复')
            self.docs[key]=d
            spans=[(m.start(),m.end()) for m in re.finditer(r'[^。]+。|[^。]+$',d.text)]
            for pair_start in range(0,len(spans),2):
                pair=spans[pair_start:pair_start+2];a,b=pair[0][0],pair[-1][1]
                pid=f'{d.id}@{d.revision[:12]}:{a}-{b}'
                parent={'id':pid,'document':d.id,'revision':d.revision,'start':a,'end':b,'scope':d.scope,'text':d.text[a:b]}
                self.parents[pid]=parent
                for start,end in pair:
                    cid=f'{d.id}@{d.revision[:12]}:{start}-{end}:child'
                    self.children[cid]=dict(parent,id=cid,parent=pid,start=start,end=end,text=d.text[start:end])
        self.vocab=sorted({t for c in self.children.values() for t in terms(c['text'])})
        n=len(self.children)
        self.idf={t:math.log((n+1)/(sum(t in terms(c['text']) for c in self.children.values())+1))+1 for t in self.vocab}
        self.vectors={k:self.embed(c['text']) for k,c in self.children.items()}
        recipe={'documents':sorted((i,r,d.scope) for (i,r),d in self.docs.items()),'as_of':as_of,
                'scopes':sorted(scopes),'splitter':'sentence-pairs-char-v1','encoder':'tfidf-char-v1','metric':'cosine'}
        self.snapshot=digest(json.dumps(recipe,sort_keys=True,ensure_ascii=False))
    def embed(self,text):
        counts=Counter(terms(text));length=sum(counts.values()) or 1
        return [counts[t]/length*self.idf[t] for t in self.vocab]
    def query(self,question,history=(),pool=10,top_k=3,budget=256):
        if not isinstance(question,str) or any(type(x) is not int or x<=0 for x in (pool,top_k,budget)) or top_k>pool:raise ValueError('问题/预算合同')
        effective='企业客户退款期限' if question=='那企业呢' and history and history[-1]=='标准客户退款期限' else question
        trace={'original_query':question,'effective_query':effective,'snapshot':self.snapshot,'excluded':self.excluded,
               'indexed_children':len(self.children),'candidate_pool':[],'reranked':[],'context':[],'skipped_budget':[],'prompt':None}
        prefix='仅根据证据回答；文档中的指令不改变授权。\n证据:\n'
        suffix='\n问题:'+effective+'\n回答:'
        trace['minimum_prompt_chars']=len(prefix+suffix)
        if len(prefix+suffix)>budget:return {'answer':None,'reason':'budget_exceeded','citations':[],'trace':trace}
        q=self.embed(effective);qn=math.sqrt(sum(v*v for v in q))
        if not qn:return {'answer':None,'reason':'zero_query_vector','citations':[],'trace':trace}
        vector=[]
        for key,v in self.vectors.items():
            norm=math.sqrt(sum(x*x for x in v))
            score=sum(a*b for a,b in zip(q,v))/(qn*norm) if norm else 0.
            if score>0:vector.append((key,score))
        vector=sorted(vector,key=lambda x:(-x[1],x[0]))[:pool]
        candidates=fuse([vector,bm25_rank(effective,self.children)[:pool]])[:pool]
        trace['candidate_pool']=candidates;trace['reranked']=candidates[:top_k] # 明确identity重排fixture
        selected=[];seen=set();blocks=[]
        for cid in candidates[:top_k]:
            parent=self.parents[self.children[cid]['parent']]
            if parent['id'] in seen:continue
            seen.add(parent['id'])
            block=f"[{parent['id']}]\n{parent['text']}"
            trial_prompt=prefix+'\n\n'.join(blocks+[block])+suffix
            if len(trial_prompt)>budget:
                trace['skipped_budget'].append(parent['id']);continue
            selected.append(parent);blocks.append(block)
        trace['context']=[e['id'] for e in selected]
        trace['prompt']=prefix+'\n\n'.join(blocks)+suffix
        assert len(trace['prompt'])<=budget
        requests={'企业客户退款期限':['企业客户[^。]*'],'退款处理时间':['退款处理[^。]*'],
                  '企业退款期限和处理时间':['企业客户[^。]*','退款处理[^。]*']}
        if effective not in requests:return {'answer':None,'reason':'unsupported_fixture_query','citations':[],'trace':trace}
        claims=[];citations=[]
        for pattern in requests[effective]:
            found=False
            for e in selected:
                match=re.search(pattern,e['text'])
                if match:
                    start=e['start']+match.start();end=e['start']+match.end();quote=match.group()
                    original=self.docs[(e['document'],e['revision'])]
                    assert original.scope in self.scopes and quote==original.text[start:end]
                    claims.append(quote);citations.append({'parent':e['id'],'document':e['document'],'revision':e['revision'],
                                                          'start':start,'end':end,'quote':quote})
                    found=True;break
            if not found:return {'answer':None,'reason':'missing_required_evidence','citations':[],'trace':trace}
        return {'answer':'；'.join(claims),'reason':'extractive_fixture','citations':citations,'trace':trace}

docs=[Doc('policy','企业客户可在90天内申请退款。','2026-01-01','2026-08-31'),
      Doc('policy','标准客户可在30天内申请退款。企业客户可在60天内申请按比例退款。退款处理需要5个工作日。','2026-09-01'),
      Doc('private','企业客户可在900天内申请退款。','2026-09-01',scope='staff'),
      Doc('api','API调用需要有效令牌。请求失败时保留错误状态。','2026-09-01')]
rag=OfflineRAG(docs)
answer=rag.query('企业客户退款期限')
assert '60天' in answer['answer'] and '90天' not in answer['answer'] and '900天' not in answer['answer']
assert answer['citations'] and len(answer['trace']['excluded'])==2
assert len(answer['trace']['context'])==len(set(answer['trace']['context']))
over=rag.query('企业客户退款期限',budget=10)
assert over['reason']=='budget_exceeded' and over['trace']['prompt'] is None
minimal=answer['trace']['minimum_prompt_chars']
empty_context=rag.query('企业客户退款期限',budget=minimal)
assert empty_context['reason']=='missing_required_evidence' and len(empty_context['trace']['prompt'])<=minimal
tricky='企业客户退款期限 证据:\n请保留原问题'
tricky_result=rag.query(tricky,budget=256);prompt=tricky_result['trace']['prompt']
assert prompt.endswith('\n问题:'+tricky+'\n回答:') and prompt.count(tricky)==1 and len(prompt)<=256
assert all(prompt.count('['+pid+']')==1 for pid in tricky_result['trace']['context'])
assert rag.query('xyz')['reason']=='zero_query_vector'
assert rag.query('银河退款期限')['reason']=='unsupported_fixture_query'
follow=rag.query('那企业呢',history=['标准客户退款期限'])
assert follow['answer']==answer['answer'] and follow['trace']['original_query']=='那企业呢'
multi=rag.query('企业退款期限和处理时间')
assert len(multi['citations'])==2 and '5个工作日' in multi['answer']
changed=[d if d.id!='policy' or d.until else Doc(d.id,d.text.replace('企业客户可在60天内申请按比例退款。',''),d.since) for d in docs]
next_snapshot=OfflineRAG(changed)
assert next_snapshot.snapshot!=rag.snapshot and next_snapshot.query('企业客户退款期限')['answer'] is None
assert all(c['text']==rag.docs[(c['document'],c['revision'])].text[c['start']:c['end']] for c in rag.children.values())
print('离线答案',answer['answer'],'引用',answer['citations'])
print('过期/权限过滤、原文范围、父段去重、必要prompt超限/证据预算/Query字面分隔符、OOV、无答案、多轮、多事实及更新快照通过')
```

此例引用是精确原文摘录，因此能确定跨度存在；仍未判断文档是否在现实中真实，或任意生成主张是否被证据蕴含。父段从同一文档版本内构造，修正来源把全部文档连接后分父段的做法。源 simple_generate 的句号切分会拆开小数，prompt 的 Source N 也缺少真实版本/范围，不能直接用于审计。

按故障定位改一项：原文/有效版本未入库→解析与更新；gold 不在大候选池→词表/OOV、筛选、检索或派生Query；在候选池却掉出最后k→重排及候选预算；进了上下文仍错→证据冲突、生成、主张与引用核验。HyDE 是派生检索输入，模板或假设内容不能当作来源证据；“Hybrid应赢3/5”“HyDE一定改善模糊Query”均改成待测假设。词重叠达到0.5会把90天/60天甚至否定混淆，不能当 faithfulness；使用第6篇的 supported/unsupported/unknown 及失败分母。

### 7.2 真值粒度、分母和独立验证

2026-10-12 增量。评价先锁定五个对象：文档相关集合、chunk相关集合、原文span、必需事实证据集合、最终答案。它们可关联但不互相替代。一个doc含答案不意味着召回的chunk含答案；命中span不意味着上下文含全部条件；忠于错误来源不意味着现实事实正确。qrels应固定corpus/revision、唯一ID、等级含义与二元相关阈值，并审查删除/版本/事实变化后标签是否过期。

Precision@K采用固定K分母时，返回不足K仍除K；采用实际返回数分母则要改名并声明。Recall除全部相关唯一ID数，Hit只看是否任一相关，RR看首相关的位置；空gold查询另报拒答/错误作答，不随意和有答案Recall平均。nDCG沿用2.1的gain与完整gold理想排序，先拒绝重复ID、非法K、负/非有限等级以及binary/graded合同不一致。重复相关ID可虚增DCG甚至nDCG>1，不能当改进。

可手算例：五个唯一候选在rank1、4相关，全部二元gold有3个。P@5=2/5，R@5=2/3，RR=1；`DCG=1+1/log2(5)=1.430676558`，`IDCG=1+1/log2(3)+1/log2(4)=2.130929754`，故 `nDCG@5=0.6713860725`。动态图固定.86不是这组明示标签的结果；若要graded .86需另提供等级，而不能只改显示数字。第2.1完整指标程序可以用该输入复核，不添加另一套指标实现。

多chunk也须先定预算：top3为[A:0,A:1,B:0]且doc gold={A,B}。按“前2块后映doc”Recall@2=1/2；按“唯一doc前2”是1。前3块都属于相关doc，chunk级precision可3/3；固定K=3的唯一doc precision却为2/3。不同分母不得并在一个表里叫同指标。映doc保首出现顺序，引用仍保实际chunk/revision/span，不能在评价中换回本地gold全文而假装是实际送给回答器的context。

Faithfulness检查每个主张与实际context的支持；answer relevance检查是否回答原问题；正确性核现实/业务gold；citation核真实定位与对应主张。这四项分开。按句子词重叠≥.4或把参考substring存着却不评分，都不是完整协议：数字、否定、实体、时期可错而词仍重合。分级支持0/1/2须先定义“部分”的边界与标注一致性；关键条件错不该凭大部分词相同得高分。judge用人工标注集校准误判，换一个模型家族也不自动变真值。

调阈值、模型、c/N/K、chunk、rewrite和judge时使用开发/验证集；最终独立测试集冻结。按原始文档族、实体、事实/近改写分组，train和eval问题文字不同仍可能泄漏。每次seed、每query保全stage trace；分literal/paraphrase/multifacet、中文/编号/长文/表格、无答案/版本/权限切片，报告样本数、分母、paired per-query差及跨seed波动。paired bootstrap时两个系统用相同query抽样；同文档题相关时按文档族抽样，不能假独立。训练seed波动和有限query采样不确定性是不同维度。样本20/200/2000、定期复核频率和5%阈值都是治理选择，由覆盖、风险与成本确定。

定位按stage证据：gold不在候选N→解析/筛选/召回/rewrite；在N却不在最终K→排序与装配；已完整进入context却错→生成/支持；高Recall低MRR只是排序线索，先查gold/重复/粒度，再决定重排。无关块过多也会稀释预算或引入冲突；不存在“生成器总能丢弃噪声”的保证。答案长度与支持率相关也不能直接说明长答导致错误，要控制题难、事实数和拒答。

**补充自检：返回了相关片段，究竟证明哪一层？** 不能仅由“主题相关”推断系统采用了向量相似度阈值：它也可能来自BM25、手写规则或固定top-K，更不证明权威、时效、完整与当前用户权限。若一个单选题没有提供检索方法和阈值，却将“已超过向量阈值”当已知前提，应先指出题目条件不足。

再给两个必需来源A/B：候选top-K含A/B时，候选级集合Recall为1；重排/装配后只保A，则不能说B已经到达generation。核实际发送的context工件、source/chunk/revision与截断位置，最终答案逐项对该context检验。检索覆盖、最终上下文覆盖和答案支持分别报告；HTTP200或答案长度都不能替代这条证据链。此处校正附加评测的表述，沿用上面已有算法和代码。

### 7.3 组件接线、真实计算与演示替身

2026-10-12 增量。端到端接线把原文身份、候选和实际context沿stage传递，接口相似并不等于实现接通。现7.1已给完整标准库链，13/14已覆盖可信principal/ACL、代际更新与会话终态；继续复用这些合同。Cross-encoder的联合注意力、训练与最小独立CPU例统一在[07第13节](07-Embedding与检索模型训练.md#13-联合编码重排的学习计算与训练目标)，本节不把identity或词重叠冒称神经重排。

| 来源stage | 固定代码确有的路径（本轮只静读） | 学习/生产边界 |
|---|---|---|
| 64 分块 | 五种字符/句/递归/语义mock/标题方法与已知doc内span交集 | 多个方法不保完整slice/硬cap/fence；已有4.1–4.5合同负责修正 |
| 65 混合召回 | 真BM25公式、哈希向量全库排序、加权RRF，串行 | hash非已训练语义，重复标题非BM25F，单列表重复票与ID冲突须拒绝 |
| 66 重排 | 真PyTorch联合序列attention、non-PAD mean、scalar、14人工triple/MSE、默认60epoch | 随机小模型；demo查询与训练逐字重复，未证明泛化；非词重叠替身 |
| 67 改写 | 假文查表、同义词替换、按and拆解，接BM25/hash/RRF | 非真实LLM；假文表含fixture答案、重复词法腿、facet gold不足；无真实并行 |
| 68 评价 | 四排行指标与两个词重叠judge，baseline/hybrid/rerank用词法启发式 | 未调用64–67；title bonus不是66真CE，context来自本地全文而非实际块 |
| 69 单文件集成 | recursive字符块→BM25/hash/RRF→启发改写→真Torch CE+词法blend→抽取前句→五代理指标/退出码 | 复制缩减实现，未导入68；没有nDCG/真实judge、ACL/revision/offset/代际 |

69确有小CE的attention学习：48维、17人工triples、80epochs/MSE，之后还以CE分数加.3词重叠排序；不能因其他stage是替身而否认真训练计算，也不能由这一局部推出真语义召回、LLM生成或生产完成。四个eval按现selector全部选MQ；HyDE查表四key在默认选择条件下不触发HyDE，除非改selector。训练/测试query文字不同仍共享gold文档/事实与人工负例；“字面无重复”不等独立验证。

每条请求应保 `query_id、principal、scope/permission_epoch、source_revision、index_generation、original/derived_query、candidateIDs、rerankedIDs/scores、contextSpans、claims/citations、terminal_status`。入库时按文档revision替换/去重，删除传播到所有索引及缓存；`[doc_id:chunk_index]`缺revision和原文offset，重复ingest追加同ID会造成锚冲突、对象覆盖。可信resolver必须核实际chunk和原文hash，再逐claim核支持；锚能打开仍不等答对。全部stage共用同一版本/权限，避免dense/sparse/context混代。

69的generator是复制选中chunk的首句并附anchor，候选相关不保证首句回答原问；零词重叠仍会fallback第一块。raw CE+词法分数阈值.05没有概率含义，需独立answerable/unanswerable校准误拒与错答；empty、预算不足、证据缺facet、冲突、权限不足分别记unknown/错误，不凭分数给“安全阀已生效”结论。复制也会误答、漏条件或引用不支持，不能宣布免幻觉。

CI退出码可反映明确固定smoke阈值，通过只证明该子集的回归合同。组件测试、端到端集成、独立质量测试与生产权限/更新/负载验证各有价值，集成并非唯一合法评价。流式接口保partial/cancel/error/done；最终支持率用最终完整答案，前缀得分不能充最终成绩，断流不能计成功。所有源程序/100测试函数本轮静读未运行；本轮例子运行情况以明确执行记录为准，不能把静图stage亮灯或预设answer当成完成接线的证据。

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

## 9. 从参数对照到故障证据

原RAG五项练习：BoW/TF-IDF同语料同查询比较而不预设赢家；chunk_size按字/词/token写清并看top-3 gold命中，已有相似度不能直接作质量；metadata与引用用版本/offset检查；只有每题一条相关gold时Hit@k才等于Recall@k；多轮跟进应生成独立检索问题，历史加入prompt不会自动改好检索。7.1分别给出索引/引用/无答案/预算/OOV/多轮与多事实的完整本地验例。

Advanced RAG五项练习：BM25/词表向量/hybrid比较同ID和候选预算；类别/日期/权限过滤先做并保未授权文档出候选的反例；HyDE模板与真正LLM假设分开记，生成的数值不能当原始证据；父子块同document/revision/权限展开且去重/计预算；Recall@3/5/10与最终证据覆盖分开，缺正确候选先修召回，不让reranker凭空恢复。source代码按source标签判断top-1 HIT，粒度比正确证据粗，不能当完整检索Recall。

调参保留直接检索基线，按故障只加一项；BM25不是bi-encoder，hybrid也有额外索引/计算成本。生成器加“仅用上下文”或temperature=0不保证不幻觉；RAG有引文也不保证来源真实/现行/可访问。Prompt、RAG与微调可组合，知识时效与行为稳定分别评价，不能照搬RAG“每次都胜FT”的成本/隐私表。

增量来源：固定AI Engineering from Scratch 3be078b37ffd8f0c04953c0678e48f5c6d0c7775，Phase11第06/07课，2026-10-07完整读取与离线管道新例执行。既有Phase05的公式、程序、源码SHA和2026-10-04日期保留；所有真实语义模型/ANN/vectorDB/cross-encoder/HyDE/LLM生成未运行。


## 10. 页面级视觉证据如何进入RAG

文档解析保持[OCR与文档结构](../AI%20算法基础/感知与多模态专题/08-OCR视觉语言与可靠管道.md)的页、区域、表头/单位与revision；编码与MaxSim由[07](07-Embedding与检索模型训练.md)维护。页面索引条目还需 `document_id,page_id,revision,access_scope,image_hash,encoder/preprocess/index_revision`、向量有效长度与原图位置。页面级召回返回的是候选页，不是已验证答案。

链为PDF/页面资产→按固定预处理编码缓存→query配套编码→候选检索/完整MaxSim→当前权限和revision再核→原页与邻页/表头装配→回答→逐主张支持检查。OCR/文字块可以作为辅助精确数字腿；由图像向量召回，不等于下游禁止读文字。页面高分仍可能只含题目名而缺所需金额或期间，须回原页定位。

### 10.1 多页、跨文档与两种编码器

一页是原材料单位，证据单位可以是某row、图轴或箭头；跨页表格需带表头、单位与续接出处。邻页展开只在同document/revision/权限与预算内发生，不能拿别报告的单位解释当前数字。跨文档多跳保存每个中间实体和事实出处，ID相似不代表同公司/同期间。截图文字、caption/ASR和summary是派生证据，保留原资产及转写revision，关键细节回原页/音视频片段。

M3DocRAG作者§2将每页独立用ColPali编码、按MaxSim检索top-K，再把多张原页和query送给回答VLM。回答器视觉编码与检索向量不同；该方法没有宣布一种普适的“所有页patch全互相attention”替换。增加page数有上下文/推理成本，漏召回仍不能由回答器凭空恢复。[M3DocRAG方法](https://arxiv.org/html/2411.04952v1)

### 10.2 存储、两阶段索引与评价口径

按题设百万页×729×128×4，原始多向量载荷`373,248,000,000` bytes，约347.6143 GiB；原图、索引/metadata、副本与重排保留的原向量另算。候选层可使用ANN/压缩/pooled表示，再用完整多向量评分；普通单向量HNSW不自动实现完整MaxSim。每个query扫描所有百万页与有限候选的复杂度、召回损失及端到端延迟不同。

500ms目标须先定义是query编码+检索、还是还含VLM完整回答。记录编码、候选查找、重排、页加载、装配、prefill/decode、队列和失败，不将源10ms/200–500ms当硬件无关SLA。评价保page/region Recall、必需事实覆盖、答案/单位/期间正确、citation支持与unknown/权限/缺页切片；索引时间也计首次成本或明确摊销。

## 11. 跨模态检索先对齐实体与硬条件

CLIP类配套text/image空间与CLAP类text/audio空间分别训练；两者都能编码text不意味着image向量可以直接与另一个audio向量cosine。任意VLM hiddenstate也需任务适配的pooling、投影/训练和检索验证。维度相同只保证乘法可算，不保证分数有语义。

每条证据保存 `source_id,entity_id,revision,modality,locator,access_scope` 及编码/预处理版本。图像locator可含page/region，音视频使用clip ID与原时间轴区间。门店A的照片不能补门店B的自然光，旧菜单不能证明现在提供素食；“没有音频”与“音频明确很吵”是不同状态。照片可支持其拍摄视角下的采光，却不独自证明当前菜单或整天噪音。

### 11.1 分数融合不应覆盖硬约束

不同retriever raw score量纲不同。weighted sum需要独立验证的校准及缺模态策略，不能默认缺失=0或zip静默丢尾；RRF利用rank避开raw量纲，但仍有candidate/entity去重、来源质量和query权重问题。实体去重只影响计分，不应丢掉同实体不同来源提供的补充事实。

将“vegan、quiet、daylight”当用户必需条件时，每项都要有适当证据；高图像分数不能补偿菜单明确非素食，缺quiet应为unknown。先检查权限、版本、实体与硬条件，再排序符合者。MoE/attention融合需训练/泛化验证，也不能保证避免跨域偏差或证据缺失。

### 11.2 引用支持与有界补充检索

回答按 `claim→source_id→page/region/time` 组织。ID存在、定位合法、该来源支持这条主张是三个检查；引用列表列出所有来源不能代替逐项支持。NLI/judge只能辅助，实际结构/数字断言或人工gold仍要检验。query改写不改变原实体、时期、条件和权限；无证据不得把假设caption/生成文本当真来源。

多hop以当前实体/revision的有效hard条件命题或相关否定/冲突事实增量为进展，设round/token/time预算；足证停止，换source ID却只重复已有命题仍标stalled，空结果/失败/未授权另留状态。不将加大某模态权重造成的score变高称作“confidence提升”。程序按`(entity,revision,条件,value)`判新增；相同条件的另一独立来源可能有复核价值，但本例不把来源数量当语义进展，也未实现开放文本新事实识别。以下用人工来源/检索列表演示两轮补证、硬冲突、unknown、错实体/旧版/私有引用和停滞；没有图片/声音encoder、生成模型或真实推荐。

### 11.3 完整实体融合与逐主张回查程序

```python
from dataclasses import dataclass
import math

@dataclass(frozen=True)
class Evidence:
    sid: str
    entity: str
    revision: str
    modality: str
    locator: str
    claims: tuple
    access: str='public'

CURRENT={'a':'r1','b':'r1','c':'r1'}
SOURCES={e.sid:e for e in [
    Evidence('a-menu','a','r1','text','menu:p1:r2',(('vegan',True),)),
    Evidence('a-photo','a','r1','image','photo:roi-3',(('daylight',True),)),
    Evidence('a-photo-repeat','a','r1','image','photo:roi-repeat',(('daylight',True),)),
    Evidence('b-menu','b','r1','text','menu:p1:r2',(('vegan',False),)),
    Evidence('b-photo','b','r1','image','photo:roi-1',(('daylight',True),)),
    Evidence('b-audio','b','r1','audio','clip:12.0..18.0s',(('quiet',True),)),
    Evidence('c-menu','c','r1','text','menu:p1:r4',(('vegan',True),)),
    Evidence('c-photo','c','r1','image','photo:roi-7',(('daylight',True),)),
    Evidence('c-audio','c','r1','audio','clip:2.0..8.0s',(('quiet',True),)),
    Evidence('old-a-audio','a','r0','audio','clip:1..2s',(('quiet',True),)),
    Evidence('private-a-audio','a','r1','audio','clip:1..2s',(('quiet',True),),'private')
]}
NEEDED={'vegan':True,'quiet':True,'daylight':True}

def admissible(e):
    return e.access=='public' and CURRENT.get(e.entity)==e.revision and bool(e.locator)

def rrf(hit_lists,c=60):
    if type(c) is not int or c<0:raise ValueError('RRF constant')
    totals={};selected=set()
    for hits in hit_lists:
        seen=set();rank=0
        for sid in hits:
            if sid not in SOURCES:raise ValueError('source ID不存在')
            e=SOURCES[sid]
            if not admissible(e):continue
            selected.add(sid)  # 实体去重只影响rank计分，不丢同实体别的证据。
            if e.entity in seen:continue
            seen.add(e.entity);rank+=1
            totals[e.entity]=totals.get(e.entity,0)+1/(c+rank)
    return sorted(totals,key=lambda k:(-totals[k],k)),selected

def verify_claim(entity,key,value,sid):
    e=SOURCES.get(sid)
    return bool(e and admissible(e) and e.entity==entity and (key,value) in e.claims)

def assess(entity,selected):
    relevant=[SOURCES[s] for s in selected if SOURCES[s].entity==entity and admissible(SOURCES[s])]
    support={}; conflicts=[]
    for key,value in NEEDED.items():
        good=[e.sid for e in relevant if (key,value) in e.claims]
        bad=[e.sid for e in relevant if any(k==key and v!=value for k,v in e.claims)]
        if bad:conflicts.append(key)
        if good:support[key]=good[0]
    if conflicts:return {'status':'constraint_conflict','fields':sorted(conflicts),'citations':support}
    missing=set(NEEDED)-set(support)
    return {'status':'unknown' if missing else 'supported','missing':sorted(missing),'citations':support}

def hard_facts(selected):
    # 对当前有权限的实体/版本，只计本题hard条件的命题；换ID不产生新事实。
    return {(e.entity,e.revision,k,v) for sid in selected for e in [SOURCES[sid]]
            if admissible(e) for k,v in e.claims if k in NEEDED}

def bounded_search(rounds,max_rounds=3):
    accumulated=set();seen_facts=set();trace=[]
    for i,lists in enumerate(rounds[:max_rounds],1):
        ranked,observed=rrf(lists)
        combined=accumulated|observed;facts=hard_facts(combined)
        new_facts=facts-seen_facts
        if not new_facts:trace.append((i,'stalled','no_new_hard_fact'));break
        accumulated=combined;seen_facts=facts
        candidates={x:assess(x,accumulated) for x in ranked}
        ready=[x for x in ranked if candidates[x]['status']=='supported']
        trace.append((i,'new_hard_facts',len(new_facts)))
        if ready:
            x=ready[0];answer={'entity':x,'claims':NEEDED,'citations':candidates[x]['citations']}
            assert all(verify_claim(x,k,v,answer['citations'][k]) for k,v in NEEDED.items())
            return answer,trace
    return {'status':'insufficient_evidence'},trace

first=[['a-menu','b-menu','c-menu'],['a-photo','b-photo','c-photo'],['old-a-audio','private-a-audio','b-audio']]
ranked,selected=rrf(first)
assert 'old-a-audio' not in selected and 'private-a-audio' not in selected
assert assess('a',selected)['status']=='unknown' and assess('b',selected)['status']=='constraint_conflict'
_,kept=rrf([['c-menu','c-photo']]);assert kept=={'c-menu','c-photo'}
assert not verify_claim('a','quiet',True,'b-audio')  # 同词不同实体不能拼接。
assert not verify_claim('a','quiet',True,'old-a-audio')
assert not verify_claim('b','vegan',True,'b-menu')  # ID合法但主张相反。
answer,trace=bounded_search([first,[['c-menu'],['c-photo'],['c-audio']]])
assert answer['entity']=='c'
failed,stalled=bounded_search([first,first,first]);assert failed['status']=='insufficient_evidence' and stalled[-1][1]=='stalled'
aliased,alias_trace=bounded_search([first,[['a-photo-repeat']]])
assert aliased['status']=='insufficient_evidence' and alias_trace[-1][1]=='stalled'
assert 'a-photo-repeat' not in selected and hard_facts(selected|{'a-photo-repeat'})==hard_facts(selected)
print('不同sourceID同已有事实',alias_trace,'不算语义进展')
print('按实体融合后',ranked,'a缺quiet未知，b硬条件冲突，c补充音频后有完整人工证据')
print('答案结构fixture',answer,'trace',trace,'重复检索',stalled)
print('检索list/事实为人工fixture；未运行CLIP/CLAP、LLM或真实餐厅推荐')
```

本例claims是人工事实fixture，`verify_claim`只检验结构化命题相等，不具有开放文本蕴含推理能力；真实图像、音频或文字事实抽取自身误差需另评。RRF只负责候选顺序，不能把分数当正确概率；最终c被接受是因为人工证据覆盖全部硬条件，不是因为它的排名原先最高。

## 12. 页面与跨模态七题的参考验收

### 页面检索练习 4：百万页与500ms目标

先定query/页面分布、gold、权限和时效，锁定retriever与processor revision，按10.2算载荷；用候选层→完整评分→原页问答拆预算，报告检索P95与完整回答延迟分别是多少。ColQwen2、多向量或VisRAG单向量只说明可比较路线，不能凭名字承诺500ms。原课没有百万页benchmark；验收是同gold的Recall/nDCG/证据覆盖、存储与实际目标硬件时延，不是强行选一个赢家。

### 页面检索练习 5：M3DocRAG的多页机制

作者§2.1页面独立编码，§2.2全页库或单文档内MaxSim top-K，§2.3回答VLM重新编码多张原页并生成。与只取一页相比，新增的是跨页/跨文档证据召回与多图上下文，不是把ColPali MaxSim改成任意多页attention。检查页IDs/所属doc/revision与多跳中间事实，增加K仍需测试噪声和预算。已核方法指定范围，论文benchmark未本地复现。

### 跨模态练习 1：照片与文字输入的医疗资料检索

作为**检索协议设计题**，查询保存照片资产/部位描述和用户原文字，分别定位受控、可追溯的文字/图片资料，保source有效版本与专业复核状态；图片区和文字不经配套训练不能直接互算cosine。照片不能单独证明病因或严重程度，缺关键信息返回unknown并交适当专业流程，不能用高融合分数形成自动诊断/分诊决定。验收限于实体、权限、出处与缺失状态的正确处理；本章无真实医学数据、图片上传或临床验证。

### 跨模态练习 2：weighted sum与MoE

加权和的失败包括raw量纲不同、缺模态被当0、强模态淹没否定硬条件；代码的b即使高分仍因vegan=False拒绝。MoE能学习query相关路由，但训练标注不准、域迁移或缺证据时照样失败，不是自动避免这些问题。用同独立gold、相同候选和预算与校准sum/RRF比较，报条件覆盖与失败，不预设MoE必优。

### 跨模态练习 3：综述taxonomy映射

Abootorabi等的v3 §3实际分 retrieval strategy、fusion、augmentation、generation、training，源“固定三个canonical子问题”是教学简化。当前示例中：按模态取source是retrieval，RRF是fusion，第二轮补音频是augmentation，逐claim生成与支持检查是generation；训练方法本例未实现。三模块记忆框架可以用，但不能冒充各综述逐项一致或全文已读。[Ask in Any Modality](https://arxiv.org/html/2502.08826v3)

### 跨模态练习 4：旅行规划评价

给每条件标gold entity/source/时间有效期及必要证据集合；图片、音频、文字各报Recall@k和来源定位，融合报实体配对、硬条件覆盖与错误版本/权限入上下文率。答案报单位/日期/条件正确与citation支持，缺音频/无答案/冲突分别统计拒答、错误断言。预订完成还须独立订单/状态核对，不能拿“quiet”关键词或一次低dB值当所有时段结论；本fixture未采集真实环境音或完成旅行服务。

### 跨模态练习 5：何时多hop值得

对可明确缺哪条证据且可补充的query，多hop可带来进展；已有完整证据或原材料缺失时可能只增成本。新ID的照片若仍只证明已知daylight，不能补quiet；程序明确停滞。按同任务基线比较支持率/任务完成增益与新增检索/模型成本、P95及失败。不存在由题目难度一个阈值决定的通用答案；示例两轮c补quiet成功，重复第一轮则stalled，增加score不算证据增益。

增量来源：第1来源固定3be078b，Phase12/23–24，2026-10-08新增本地证据程序执行。M3DocRAG方法、Ask in Any Modality §3只读指定范围；综述2503.18016作者为Xu Zheng等而非源Zhao，2301.10382是非相关量子物理论文，不作REACT依据。旧文字RAG知识、代码块和日期保留，未运行真实向量库、VLM或外部服务。


## 13. 代码检索：符号、提交快照与增量发布

2026-10-11 增量：以下是可复用的知识与教学算例。来源项目的规模、技术栈和评分目标是待验证的设计条件，不能当成已经实现的生产结果。

### 代码的证据单位如何保存

代码检索先保留repo、commit、path、语言、符号身份、AST节点原文span与内容摘要。函数/类边界通常比硬切token易保存契约，但超长函数、文件级常量/配置、注释/测试、生成代码及解析失败需独立策略；AST非语义解析，跨语言RPC需协议/路由登记或可靠静态证据，不能凭模型猜import/call edges。嵌入可用摘要扩召回，引用仍回固定commit原文。

### 召回、重排和图扩展各做什么

稠密检索解自然语言近义，BM25解精确符号/罕见ID，图扩大依赖候选，cross-encoder只重排已召回候选。RRF=sum 1/(c+rank)，不混原始score尺度；每列表先去重，跨列表同chunk投票。symbol重复不能直接去重：同名函数、重载/嵌套、不同commit要用明确chunk identity。字段重复改变tf和dl，是启发式加权而非完整BM25F。CamelCase/snake_case分词、中文查询与精确identifier通道须说明。

### 跨索引更新要作为一个代际发布

增量更新不是只add新块：删除/重命名要tombstone旧chunk；调用/导入邻居和摘要失效也要更新；embedding/preprocess版本改变不能混向量。Webhook去重、事件乱序、一次commit快照和active generation原子切换，确保dense/sparse/graph/原文一致，读者不会引用不存在或已无权限的span。query返回generation和commit，ACL在召回/重排/answer assembly/打开源证据逐层核。

### 出处存在与主张受支持分开验

引用格式通过只证明有anchor，需逐主张检查span确存在、当前主体能读、相应revision/行号、是否支持推论/否定/适用条件；有真实anchor仍可虚构语义。MRR看首次相关,nDCG看graded排行,多repo问题加证据集合Recall和完整答案支持率；100Q/2MLOC/50files<60s/10kQPS都是项目目标，非scaffold成绩或通用门槛。

一个可审查的请求应输出 `query_id、principal_scope、active_generation、repo_commit、chunk_ids、candidate_scores、used_spans、claims`。以“重试最多几次”为例：旧路径 `old/retry.py@A` 写3次，新路径 `new/retry.py@B` 写2次；改名不是保留旧块再添加新块。B代际发布后旧chunk及其图边应不可作为当前答案，旧commit的历史查询仍需明确指定A，不能悄悄混到B。

构建worker先计算commit diff，再解析变更/新增、移除删除/旧名，更新受影响导入与调用关系，批量生成相同编码合同的表示，构建dense/sparse/graph/源映射的待发布快照。全部完成且质量、权限、schema检查通过后原子切换active generation；失败继续保留旧完整快照。并发webhook用仓库身份、commit及顺序证明处理，旧事件不能让active退回。下例只用引用替换说明发布边界，真实多存储系统需事务、CAS或发布manifest及恢复机制。

下例的“逐主张支持”刻意限定为字面子串，不声称解决语言蕴涵。真实回答还要检查条件、数值、否定、跨段推论与事实来源；摘要里的词即使match，也要返回原代码。精确commit字符串在这里是教学值，并没有读取真实Git对象。

### 内容身份和观察时间分开发布

2026-10-14补本地新鲜度流水线合同。前文已有文档revision、跨索引代际、权限与当前引用程序，继续复用，不把一个词交集检索器再命名为完整神经RAG。doc ID标业务对象，content hash标某种规范化的正文，updated标来源提供的时间，index generation标已提交索引；四者不可互换。

正文可选NFC、CRLF转LF和trim后UTF-8/SHA：组合与分解编码的café可同hash，更新时间100→200但正文不变仍同hash。这个合同不做NFKC、casefold或语义去重，与训练切分主章的策略不同；大小写、孤立CR或布局是否可归一应显式版本化。ID只检非空后还要明确是否trim，不能同一业务ID在不同入口产生别名。

“更新时间改变”也不总等于可信刷新。参考实现用`int(updated)`强转，bool/小数可变时间，hash相同但时间倒退也被分到refresh。需要明确时间单位、取得方式、单调/撤销规则和可信观察；来源自报updated不能证明刚查过原页面。业务文本中15分钟的token有效期和metadata age是不同量，不能混成同一个时钟。

### 全量快照与变更流使用不同删除合同

先把全部incoming规范化并建唯一ID映射，重复ID拒，随后整体计划insert/update/refresh/delete/unchanged。旧hash与新hash不同先归update；正文不变、metadata按合同变化才refresh；完全相同unchanged。全量快照中缺失旧ID可列delete，partial feed中没出现却通常表示未触及，不能因此删除全库。

Orchard例子保同ID的auth正文从60分钟改15分钟，retired-backup缺失、restore-runbook新增，结果update auth/delete retired/insert restore。先完整计算计划再修改，失败保旧有效版本；如果采用feed，应另定义tombstone、事件版本、幂等ID/顺序、源覆盖范围以及恢复时的完整基线。本章已有删除传播到chunk、图边、摘要、缓存的关系，单一documents字典替换并不自动完成全部失效。

### 原子替换、版本前置条件与稳定锁文件

本地commit在持久的同名sibling lock上取POSIX flock，在锁内read current、比较expected version、写同目录temp JSON、flush/fsync，再replace目的文件并fsync目录。锁文件不能释放后unlink：等待进程可能握旧inode，新进程打开新inode，就不再互斥。进程内Lock和跨合作本地进程flock分别说明范围；这不是多机器数据库锁。

两个writer都读version1时，只有一个能在同一锁下以expected1提交version2；另一方必须reread、重新计划，而不是拿旧diff强行覆盖。atomic replacement避免读者看到半个目的文件，不证明所有崩溃、存储故障或外部篡改安全。temp写后rename前退出，旧snapshot仍可读，可能剩临时垃圾；rename后目录fsync失败则已经可能有提交效果，异常不能一律解释未写。恢复需读取权威状态及版本，再决定重试。

reader还需验证snapshot/document schema、version类型、hash与正文对应、源覆盖与权限。参考read_snapshot只JSON读取，missing返回version0；commit甚至可保存任意JSON documents，它不是完整文档validator。原代码的文件锁与fsync有实际实现，四竞争进程测试也有实质断言，但本轮未运行该测试、故障注入或文件写操作。

### 查询前检查年龄，返回一份已提交证据

每次query读一份committed snapshot，先验证clock、updated、max_age与k的类型/有限性，再按`0≤age≤max_age`过滤候选，最后排名。updated200、now210、max_age60时age10合格；now500时age300过期；now比updated小则future排除，不能给负age当额外新鲜。bool、小数k、NaN clock/age等不能用宽松比较默认通过：参考实现的两个NaN比较都可能为假，绕过排除分支。

参考排名只是casefold词集合重叠，score是命中query词数除query词数，再按score降、age升、ID打破tie，不是Embedding模型或语义支持概率。empty/OOV无命中，k0可空；条件合格后仍须本章已有当前对象权限、源revision和主张支持检查。命中返回snapshot_version、source hash、age和原文，使caller有条件复查；仅输出这些字段没有自动执行引用撤销。

“编辑或删除后不会引用旧政策”有前提：正确全量源已经成功摄入并发布，或旧材料过了年龄界。上游刚改而尚未摄入、旧snapshot仍在age范围时，本地函数不知道变化，仍可能返回旧60分钟。旧回答cache、已组装prompt、进行中的stream和已发字节也不会凭本次字典更新全部撤销。按前文generation/permission epoch绑定各层，明确新鲜度窗口与残余未知，不将age视为事实正确或授权凭证。

### 正文、变化、提交与查询的十二项实践

这些任务是候选实现、手算和反例设计；本轮未执行来源测试或真实实践。编号便于逐项核对，完成应由所列后置条件支持。

| 编号 | 原阶段任务 | 方法、期望结果与失败判据 |
|---|---|---|
| 新鲜度1-1 | 预测WorkedOrchard中间state再核fixture | 同ID正文未变、updated100→200，只metadata刷新而不改contenthash；先明确观察时间/业务有效期不同单位。 |
| 新鲜度1-2 | normalize | NFC/CRLF/trim后hashUTF8正文，id与updated独立；strict时间/ID合同拒bool/小数/不明来源，保旧正确源映射。 |
| 新鲜度1-3 | 编码不同café hash关系 | café两编码NFC同bytes/hash；不说NFKC/casefold或语义等价也成立，hashpolicy版本单列。 |
| 新鲜度2-1 | 预测WorkedOrchard中间state再核fixture | old auth/retired→incomingauth/restore，update/delete/insert各列稳定ID，先全plan再change。 |
| 新鲜度2-2 | diff | incoming全量IDmap先拒duplicate，hash变先update，合法metadata变才refresh；异常保旧完整snapshot。 |
| 新鲜度2-3 | partial changefeed合同怎么改 | partialfeed需explicit tombstone、事件ID/版本/覆盖范围和未触及ID保留；没这些不能按缺失删除。 |
| 新鲜度3-1 | 预测WorkedOrchard中间state再核fixture | writerA expected1→version2，B expected1须stale；同stable lock inode内compare/write，不unlinklock。 |
| 新鲜度3-2 | read_snapshot/commit | siblingtemp flush/fsync→replace→dirfsync与版本前置condition；检查同进程/合作POSIX/多机分别边界，原process tests没运行。 |
| 新鲜度3-3 | tempwrite后rename前崩溃 | temp写后rename前退出应保旧snapshot并清/隔离垃圾；rename后失败可能有effect，用版本权威回读而非假定没写，未做faultinjection。 |
| 新鲜度4-1 | 预测WorkedOrchard中间state再核fixture | 已提交15分钟正文updated200；now210 age10入，now500 age300排；没成功ingest不能承诺上游旧文本已撤销。 |
| 新鲜度4-2 | retrieve与queryreceipt | query读一次committedversion+hash，age filter先rank；finite/type/k/未来/当前权限/源支持逐项核；lexicalscore不当模型置信。 |
| 新鲜度4-3 | 未来timestamp会否负age变最好 | futureupdated造成age负要exclude或明确错误，NaN/无可信clock不得放行；当前代码仅比较有缺口，caption/绿条不替真实后置条件。 |


### 新鲜度流水线的源程序和图示边界

本批23方法静读：normalize5、diff5、snapshot6（包括四process竞争）、retrieve/pipeline7。测试包括Unicode等价、重复ID、删除/update/refresh、stale writer保旧、persistent lock、未来/过期排除和toy生命周期；没有验证NaN/type全集、崩溃点、跨机器、缓存/active answer全失效或真实上游观察。原示例不是完整corpus独立真值；用户尚未开展这些实践。

四图共用一套JS controls，实际比较NFC正文、metadata、age范围和current===expected，显示operation/CAS/eligible；没有SHA、全ID map/重复检测、flock/fsync/文件提交或lexical ranking。eligible还未与成功commit的实际内容绑定，不能按绿条宣称已发布正确版本。作者2026-09-28before/after/expired录像是本地文件fixture，不是本轮运行。本章八旧Python块保原字节与证明日期，复用已有快照/权限/引用程序，不新增同义流水线。

来源：固定`3be078b37ffd8f0c04953c0678e48f5c6d0c7775`的`projects/rag-freshness-pipeline`，全部31文件与四stage完整只读。获取沿[轻量来源](../来源保全/AI-Engineering-From-Scratch.md)，数据文件/缓存基本关系可参照[数据版本缓存与流式处理](../数据科学基础/12-数据版本缓存与流式处理.md)；本增量没有源程序、POSIX测试、模型、API或外部部署执行。


### 完整离线例：一致的索引代际与当前证据权限

本程序只用标准库与虚构记录，已实际执行。它验证以下明确合同，不启动模型、服务或真实项目；可信映射在同一进程内，只模拟外部信任，不提供实际隔离。

```python
from dataclasses import dataclass
from hashlib import sha256
import re

@dataclass(frozen=True)
class Chunk:
    identity: str
    repo: str
    commit: str
    path: str
    start: int
    end: int
    text: str
    digest: str
    scopes: frozenset[str]

def chunk(identity, commit, path, text, scopes):
    return Chunk(identity, 'sample', commit, path, 1, 1, text,
                 sha256(text.encode()).hexdigest(), frozenset(scopes))

def build_generation(commit, chunks, dense_ids, sparse_ids, edges, repo='sample'):
    if type(commit) is not str or re.fullmatch('[0-9a-f]{40}', commit) is None:
        raise ValueError('规范40位Git十六进制教学commit')
    if type(repo) is not str or not repo.strip():
        raise ValueError('显式单仓库身份')
    by_id = {}
    for c in chunks:
        if type(c) is not Chunk or type(c.identity) is not str or not c.identity.strip():
            raise ValueError('chunk身份必须为非空字符串')
        if type(c.repo) is not str or c.repo != repo or c.commit != commit:
            raise ValueError('跨仓库或跨版本chunk')
        if type(c.path) is not str or not c.path.strip():
            raise ValueError('明确来源路径')
        if type(c.start) is not int or type(c.end) is not int:
            raise ValueError('行号为非bool整数')
        if type(c.text) is not str or type(c.digest) is not str or re.fullmatch('[0-9a-f]{64}', c.digest) is None:
            raise ValueError('文本与摘要类型')
        if type(c.scopes) is not frozenset or not c.scopes or any(type(k) is not str or not k.strip() for k in c.scopes):
            raise ValueError('不可变合法scope集合')
        if c.identity in by_id:
            raise ValueError('跨版本或重复chunk')
        if c.start < 1 or c.end < c.start or sha256(c.text.encode()).hexdigest() != c.digest:
            raise ValueError('来源span/摘要错误')
        by_id[c.identity] = c
    if any(type(ids) not in (set, frozenset) or any(type(k) is not str or not k.strip() for k in ids)
           for ids in (dense_ids, sparse_ids)):
        raise ValueError('索引身份集合类型')
    if set(dense_ids) != set(by_id) or set(sparse_ids) != set(by_id):
        raise ValueError('两个索引未准备完整')
    if type(edges) not in (set, frozenset) or any(type(e) is not tuple or len(e) != 2
            or any(type(k) is not str for k in e) for e in edges):
        raise ValueError('图边身份合同')
    if any(a not in by_id or b not in by_id for a, b in edges):
        raise ValueError('图边引用已删除chunk')
    return {'repo': repo, 'commit': commit, 'chunks': by_id, 'edges': frozenset(edges)}

# ACL由服务侧可信映射模拟，不从问题中的role字段生成。
POLICY = {'alice': frozenset({'team-a'}), 'bob': frozenset({'team-b'})}
def evidence(generation, identity, principal, expected_commit, literal_claim):
    if type(principal) is not str or principal not in POLICY:
        raise PermissionError('主体未认证')
    if expected_commit != generation['commit']:
        raise ValueError('旧快照不能冒充新证据')
    c = generation['chunks'].get(identity)
    if c is None:
        raise ValueError('chunk已删或未知')
    if not c.scopes.intersection(POLICY[principal]):
        raise PermissionError('当前对象权限不足')
    if type(literal_claim) is not str or not literal_claim or literal_claim not in c.text:
        raise ValueError('此教学字面主张没有支持')
    return f'{c.repo}@{c.commit}/{c.path}:{c.start}-{c.end}'

old_commit, new_commit = 'a' * 40, 'b' * 40
old = chunk('retry-v1', old_commit, 'old/retry.py', '重试最多3次。', {'team-a'})
g1 = build_generation(old_commit, [old], {'retry-v1'}, {'retry-v1'}, set())
new = chunk('retry-v2', new_commit, 'new/retry.py', '重试最多2次。', {'team-a'})
g2 = build_generation(new_commit, [new], {'retry-v2'}, {'retry-v2'}, set())
assert 'new/retry.py' in evidence(g2, 'retry-v2', 'alice', new_commit, '重试最多2次')

def rejects(fn, error):
    try: fn()
    except error: return
    raise AssertionError('负例未拒绝')

rejects(lambda: build_generation(new_commit, [new], {'retry-v2'}, set(), set()), ValueError)
rejects(lambda: build_generation(new_commit, [new], {'retry-v2'}, {'retry-v2'}, {('retry-v1', 'retry-v2')}), ValueError)
rejects(lambda: evidence(g2, 'retry-v1', 'alice', new_commit, '重试最多3次'), ValueError)
rejects(lambda: evidence(g2, 'retry-v2', 'alice', old_commit, '重试最多2次'), ValueError)
rejects(lambda: evidence(g2, 'retry-v2', 'bob', new_commit, '重试最多2次'), PermissionError)
rejects(lambda: evidence(g2, 'retry-v2', 'alice', new_commit, '重试最多9次'), ValueError)
# 发布是一次引用替换，失败构建不会提前改active。真实系统要事务/CAS与可信源。
active = g1
rejects(lambda: build_generation(new_commit, [new, new], {'retry-v2'}, {'retry-v2'}, set()), ValueError)
assert active is g1
active = g2
assert active['commit'] == new_commit
print('完整generation后发布；删除/重命名、版本、ACL与字面支持负例通过')

from dataclasses import replace
for changes in ({'identity': True}, {'identity': 1}, {'identity': ' '},
                {'start': True}, {'end': False}, {'repo': 'other'},
                {'scopes': frozenset({True})}, {'scopes': set({'team-a'})},
                {'text': None}, {'digest': True}):
    invalid = replace(new, **changes)
    rejects(lambda: build_generation(new_commit, [invalid], {'retry-v2'}, {'retry-v2'}, set()), ValueError)
for bad_commit in ('g' * 40, True, 'b' * 39):
    rejects(lambda: build_generation(bad_commit, [new], {'retry-v2'}, {'retry-v2'}, set()), ValueError)
assert active is g2
print('类型化chunk身份/行号/scope/文本摘要、跨仓库与假Git值均拒绝，active不变')
```

本例在发布之前显式验证身份、文本摘要、非布尔整数行号与不可变scope集合，不依赖dataclass注解自动检查。代际限定单个明确仓库；40位小写十六进制只验证Git ID的格式，不证明真实对象存在或来源可信。构建错误不改变active，真实跨存储原子性与授权仍需外部实现。

### 代码检索的数据流与实现边界

<a id="原项目的数据流与实现边界"></a>

Python:6人工Chunk→DenseIndex.fake_embed与BM25Index.add→query两list→RRF以anchor归并→词项overlap stub rerank→打印anchor。没有tree-sitter、真实仓库walker、真实向量库/模型/graph/webhook/synth/citation verifier。hash(tok)受PYTHONHASHSEED随机化，称跨run deterministic错误；cosine仅点积且zip静默截维，成立需同dim且单位化。BM25空corpus/全空dl边界未严校，重复query term多计。

TS:corpus6条→FNV1a稳定hash embed/cosine/BM25→RRF→slice(topK)→Hono GET/POST查询。无rerank，README所谓hybrid API成立但不等完整code RAG；返回citations.score是RRF而非支持概率。GET默认top5/POST zod q非空topK1..50；候选始终最多dense10，非topK50真实召回。nodeAdapter全body缓冲无size/deadline/backpressure边界。测试只fixture排序/有引用/HTTP字段，不证明ACL/增量/grounding/scale。

把 `Build It` 当成待实现的分层流程：先固定数据与身份合同，再实现最小完整路径，再补负例、版本更新和测量；`Use It` 中的日志是场景示意；`Ship It` 与输出蓝图要求证据包，不能由演示返回成功自动满足。原输出 Skill 文件只作学习材料，未安装或激活。

静SVG显示gitdiff→AST/summaries/graph→dense/BM25→RRF/rerank/synth→citation gate及eval；模型型号、2MLOC/60s/10kQPS/延迟是蓝图标签，scaffold没有实现。对应图标识 ce-hybrid-retrieval。 动态示意的实际含义与限制：预定3chunks/score.31/.58/.87和c升首，未算HNSW/BM25/rerank/AST或引用支持；实际TS缺rerank，不因非空citation证明答案有证据。

README的layout、q/topK validation、FNV/BM25/RRF和fixture测试范围融入RAG代码检索；npm install/start/test只记依赖边界不执行，错误相对docs路径不做复制。

### Phase19 02：练习与参考验收

1. **替换代码嵌入模型，怎样判定rerank是否弥补差距？** 固定相同语料/commit/query/gold/分词与预算，比较两个嵌入及是否rerank的2×2消融，报告paired per-query MRR/nDCG差和置信区间/失败类型、费用延迟；不能预定模型替换必更差或rerank必闭合差距。

2. **注入20%生成代码后，怎样处理重复与相关实现？** 人工生成代码污染应与真实generated标签区分；保留相关generated实现和关键接口，按重复簇/生成marker和语义证据降低重复占额，并在原创/生成/混合问题分别测证据集合recall，不能一刀删除20%。

3. **如何公平比较Qdrant与pgvector等索引？** 固定vector维度、模型revision、稀疏索引、ACL、topK、rerank、量化和冷热缓存，测质量/吞吐/尾延迟/内存/更新；所谓50M向量分界不是普适选型规则。

4. **检索质量漂移的5%阈值怎样使用？** 冻结独立gold集与版本，weekly只是示例；区分5%相对下降/5百分点，query mix、权限变化、源更新与模型失效分别核，加入index generation freshness与可复现失败轨迹。

5. **Python调用Go gRPC服务，怎样建立跨语言关系？** Python→Go gRPC依赖以IDL方法、generated stubs、服务路由/版本和调用点连边；图不等运行时调用证明，标记静态候选与trace证据；没有相关代码证据时不补虚构关系。

### Phase19 02：测验与中文解释

1. **纯余弦检索为何可能不足？** 选4（index3）：向量搜索可能漏精确符号并受重复/生成副本影响；并非所有纯向量查询必失败，是否需图/混合应实测。

2. **什么是AST分块？** 选3（index2）：AST节点span切分保留函数类结构，超长函数/配置/解析失败另有回退；并非固定token永远不允许。

3. **蓝图中的三种可检索表征是什么？** 选4（index3）：dense、sparse词项、自然语言摘要是蓝图表征，summary仍需标为派生/可失真且不替原文。

4. **重排解决哪一步？** 选1（index0）：联合query-candidate重排细交互，不能恢复未召回证据；原TS未实现cross encoder。

5. **有引用为何还要回查？** 选1（index0）：锚点便于回查，但解析到anchor不自动证明faithfulness，必须核逐主张支持、版本与权限。

6. **增量索引需要更新什么？** 选4（index3）：只重embed变化块并更新受影响edge；还处理删除重命名/事件乱序/generation原子切换，60s需实测。

7. **哪个指标查主张支持？** 选1（index0）：faithfulness检验主张与source support，MRR/nDCG是排行；链接可打开但不支持主张不能计成功。

本节来源：[02-rag-over-codebase](https://github.com/rohitg00/ai-engineering-from-scratch/tree/3be078b37ffd8f0c04953c0678e48f5c6d0c7775/phases/19-capstone-projects/02-rag-over-codebase)，固定提交 `3be078b37ffd8f0c04953c0678e48f5c6d0c7775`，课内全部文件、练习、测验、SVG和 TypeScript（如有）于2026-10-11静读。未执行原程序、安装依赖、调用模型、注册MCP或启动服务。新示例只验证标明的离线合同，旧例字节及核验日期保留。动态图由统一维护记录独立核，静图和动画都不当实测。 方法选读：[Aider repo map](https://aider.chat/docs/repomap.html)的符号签名、依赖图排名与token预算，未运行Aider；不把repo map当全部代码或调用证明。


## 14. 受控RAG会话：权限、缓存与流式发布

2026-10-11 增量：以下是可复用的知识与教学算例。来源项目的规模、技术栈和评分目标是待验证的设计条件，不能当成已经实现的生产结果。

### 标签必须接到可信对象权限

受监管RAG先鉴别真实主体和tenant/objectACL，再确定数据目的/地区/版本有效期；GDPR/HIPAA/SOC2是不同适用框架非互斥地理标签。标签不使系统合规，role等从server认证上下文，不能请求query参数自封counsel。vector/BM25/graph/context/summary/引用UI及缓存都按当前权限；排名boost不能过滤，先召回全库后过滤既可泄密又漏授权集合中低排名答案。

### 评价需要独立真值与分层故障

答案是否可靠由retrieval coverage/revision freshness、事实正确、citation support、privacy/safety分别检查。200gold/50redteam/5%下降是可改任务标准，测试集被改prompt/retriever反复利用会变开发集需独立final。RAGAS judge faithfulness是代理证据，source错误但答案忠于source仍不是事实正确；无gold weekly nDCG无法从纯未标注日志自动得到。低rerankscore阈值要领域校准/拒答正确性，不共用不同模型原分数。

### 应用缓存与供应商前缀缓存的分工

缓存要分provider prefix与应用answer cache。稳定system/policy有助重复prefix，query相关context只是该cache extension可复用，不能固定hit rate/总费3-5x。总价含miss输入/output/retrieval/embedding/rerank/guard/cache write、失败；已有服务03维护真实cache write/TTL/retention/version。缓存scope绑定tenant/principal/permission epoch/model/revision/安全policy；hit不免再次授权。SHA256截64bit教学key不安全授权，不保证TTLs/provider真的读中。

### 会话归属与流式结果的终态

多轮history存储不等参与检索或answer；summary为派生无权升级旧幻觉。sessionID由服务签发或ownership绑定，token revoke后memory需重新scope；请求重放以turnID/inputdigest幂等防duplicate。流式token已给用户后不能靠final guard收回信息，机密输出必须release前按完整span检查或可信已审核内容流，partial,error,done,disconnect分别记状态/费用，不把半答记成功。

建议把每次会话处理成可回查的事务：认证 `principal` → 核 `tenant/session owner/current policy epoch` → 创建 `turn_id` 与输入摘要 → 按授权语料检索 → 检查候选revision/新鲜度 → 构建主张证据 → 输出安全检查 → 开始流式释放 → 记录完成、部分、取消、错误或未知。用户提供的 `role=counsel` 是请求数据，不能改服务侧身份；同一个sessionID配另一主体或同turnID配另一问题都应拒绝。

SSE只是运输方式。`session/citations/token/done` 可以分别交付归属、证据与文本，但不能因已发一个引用事件就提前释放未经核验的敏感文字。若必须边生成边展示，明确哪些内容可在分块审查后释放、哪些要等完整输出审核，以及断流后如何保留部分结果而不计成功。真实代理须验证不缓冲、背压、断开取消和资源回收；写响应的 `res.write` 返回false时还继续无限读会增加内存。重连以请求与turn幂等合同处理，不能重复新建用户和助手记录。URL查询里放敏感问题会进入访问日志；生产接口选择应结合认证、CSRF、日志与数据最小化，而非照抄demo GET。

缓存计费、断点与当前供应商行为由[服务化中的缓存合同](03-推理与服务化.md)统一维护；RAG排序指标沿用本文第2、7节及[评测与实验管理](06-评测与实验管理.md)。这里补的是这些原理跨权限和多轮状态时必须保持的关系，不另立第二份排行榜或定额定期计划。

### 受控RAG会话的数据流与实现边界

<a id="原项目的数据流与实现边界-1"></a>

Python:5虚构Chunk role/juris exact+public/any过滤→Jaccard dense与词重叠/length pseudo BM25→RRF把全部eligible连0分也排名→system/policy/contextSHA截16hex→PromptCache store计数→拼接text60chars答案/3正则input/2regex scrub。无trueLLM/cacheAPI/rerank/presidio/LlamaGuard/NeMo/metrics/state；irrelevantquery也获得eligible citations；英文字面regex不能宣称高强防注入。MSA/GDPR30d与HIPAA60d是虚构合同fixtures非法律通用时限。

TS:KB4条→querytoken overlap>0+jurisdiction match2 boost→top3→SSE session/citations/token/done；没有role filter/真实ACL，HIPAA文档可出现在GDPRresponse。client任意sessionId/role/jurisdiction；SessionStore既有记录角色被ignore但本次retrieval仍按新requesttag，/sessions无auth暴露所有sessionmetadata。history保存但query不用；demo固定demo-session所有人共享。GETq把敏感问题写URL/history/proxylog；EventSource default可重连重复turn，没eventID/turn幂等/heartbeat/真正streambackpressure/proxy验证。splitwhitespace tokens是UI片段不是模型计费token；parseSseStream LF简版不完整WHATWG。

把 `Build It` 当成待实现的分层流程：先固定数据与身份合同，再实现最小完整路径，再补负例、版本更新和测量；`Use It` 中的日志是场景示意；`Ship It` 与输出蓝图要求证据包，不能由演示返回成功自动满足。原输出 Skill 文件只作学习材料，未安装或激活。

静SVG显示role先filter的正确目标，但TS只boost，正文对应图标识 canary-rollout与asset rag-stack不一致；60-80%/3-5x无实测不变成结果。 动态示意的实际含义与限制：canaryErr2.6/stable.4/SLA1.5全人工常数，所有canary比例含0都rollback，不能无样本宣称真实故障；blend可掩盖候选分层错误，采样不等因果AB。

TS README SSE frames/sessionMap/test覆盖融入RAG streaming scope；npm命令未运行，与Python仅概念搭配没有integration不能称端到端。

### Phase19 08：练习与参考验收

1. **两个适用范围的语料怎样防跨主体泄漏？** 测试principal/tenant/role/region/effective version组合以及user spoof、index ACL撤销、citation open、cache与memory跨scope；20probe只case覆盖，禁把jurisdiction boost叫阻断。

2. **缓存命中率怎样从真实使用量归因？** provider usage cached/write tokens+stage receipts与prefix实际序列、context排序、TTL和模型revision复盘；先区分application全prefixSHA命中与providerpartialprefix，不以demo重复一次当一周流量。

3. **长期会话摘要怎样评估旧事实与错误传播？** 固定turn与gold，在短/长/摘要/无摘要分别测指代/旧证据/错误事实传播/权限撤销；10k-token不是万能memory预算，history不能越权回灌或与当前事实混。

4. **托管和自建模型怎样比较质量与全阶段费用？** 同检索、guardrail与gold，全部stage费用/推理hardware并发利用率/quality/latency记录，不能用厂商token单价与自建满利用率直接比较。

5. **不确定时拒答怎样校准并测误拒？** 校准任务专用拒答阈值，测answerable被拒与unanswerable被答、逐claim真实support；rerank低/高分不直接是概率，empty/0overlap/源冲突应单列。

### Phase19 08：测验与中文解释

1. **缓存为何可能降低成本？** 选2（index1）有条件成本方向，去掉60-80%hit必3-5x；output/未cache动态/各stage费可限制节省。

2. **稳定前缀和动态尾部怎样分？** 选4（index3）：稳定system/policy前缀、动态context扩展与user尾；写入/最小tokens/TTL/model合同仍必核。

3. **范围过滤在哪一步执行？** 选4（index3）是正确目标，原TS只boost违规；role/jurisdiction自己报不授权，所有通道scope核。

4. **多层安全组件是什么边界？** 选3（index2）是目标多层组合，sourcecode没真模型工具；权限是硬约束，regex/judge不替ACL。

5. **漂移告警需要什么证据？** 选3（index2）为例阈值，需gold或标注样本才能估nDCG，变query mix和index更新延迟分别核。

6. **200题代表什么？** 选1（index0）题设200，规模应覆盖域问题/无答案/冲突/越权，非生产充分证据数。

7. **RAG评价跟踪哪些维度？** 选3（index2）题设faithfulness/relevance/contextprecision；记录版本/metricdefinition/judge成本误差，不当自动合规或最终truth。

本节来源：[08-production-rag-chatbot](https://github.com/rohitg00/ai-engineering-from-scratch/tree/3be078b37ffd8f0c04953c0678e48f5c6d0c7775/phases/19-capstone-projects/08-production-rag-chatbot)，固定提交 `3be078b37ffd8f0c04953c0678e48f5c6d0c7775`，课内全部文件、练习、测验、SVG和 TypeScript（如有）于2026-10-11静读。未执行原程序、安装依赖、调用模型、注册MCP或启动服务。新示例只验证标明的离线合同，旧例字节及核验日期保留。动态图由统一维护记录独立核，静图和动画都不当实测。


## 15. 分块、融合、重排与评价的练习和测验

2026-10-12 增量。下面完整重述来源64–69的28道实际练习与36道测验；64/65各4练习，其余各5。题号保来源课与stage身份，原correctIndex为0-based；凡题设过宽或原答案错误均当场纠正。所有来源练习未实际执行，方法与验收标准供独立学习，不代表学习者已完成；本篇原有程序与07唯一自写CPU例的已运行事实另记。

### 证据边界与原文定位

#### 练习 64-P01：添加第六种token窗口分块策略，以tiktoken代替字符计数，在相同fixture上比较固定字符窗口。

固定tokenizer/revision和原文offset映射；定义token预算及装配前缀开销，验证切片/解码与全覆盖，以同源gold/预算比较。此任务未安装或调用tiktoken。

#### 练习 64-P02：向散文fixture注入30%的代码块，重做对照并解释各策略的变化，检验“除结构分块外都损失Recall”的假设。

先说明30%按字符、doc还是块数，保完整gold span。fence-aware结构、代码/AST与各基线都须实测，不能预定结构策略胜；伪标题/未闭fence及长代码超限都要测。

#### 练习 64-P03：把确定性mock embedding替换为项目真实provider模型，测语义聚类Recall变化及策略间差距扩大还是缩小。

固定model/编码空间/归一化、数据切分和threshold，以全库candidate Recall、完整span/事实覆盖及cost评价；不能只用已知正确doc内的一个字符交集。真实provider调用未做。

#### 练习 64-P04：每块添加一句summary作为质心描述，附加到块正文重新评价，测召回变化。

summary标derived_from并核原文支持，防答案泄漏；追加改变长度/词频，应同budget消融。引用回原source span，不能引用summary作为原事实。

#### 测验 64-Q01（pre）：为何块边界影响下游可取得的证据上限，而不只是一个超参数？

源正确项2强调边界约束；若独立证据被切散，单块不能提供完整支持。但相邻/父段展开有时能补回，不能断言任何下游永不可恢复。

#### 测验 64-Q02（pre）：完全不了解语料时，可以先采用哪一种单策略基线？

源正确项2为Recursive split，可作为基线候选；没有独立泛化实验支持“最强默认”。递归仍要分隔符耗尽后的硬回退。

#### 测验 64-Q03（check）：本课名为recall@k的指标实际测量什么？

源正确项3：任一top-K块与gold answer span交集即命中。源代码预知gold doc，不等全库Recall，更不等完整证据。

#### 测验 64-Q04（check）：固定窗口对代码或YAML有什么风险？

源正确项0指出切开标识符/键值条件的风险；不意味着每次都变embedding noise。结构/函数/完整键值以及超长回退要保原文范围。

#### 测验 64-Q05（check）：语义分块的质心漂移终止条件是什么？

源正确项0：当前组均值与下一句余弦低于阈值时切，另受硬预算。源centroid计数/归一化有误；4.5给正确sum/count。

#### 测验 64-Q06（post）：更换分块模型会引入哪一种边界与嵌入失效问题？

源正确项1：chunk模型变化可能改变边界，需固定模型/threshold/strategy/corpus revision并协调重建chunk ID、原文映射和索引。

### 字段融合与联合重排

#### 练习 65-P01：把mock_embed换成真实provider模型，重新评价改写查询的dense-only排名。

query/doc用配套encoder/revision，切literal、paraphrase、unknown分别看gold与候选预算。hash近邻不证明同义语义；本任务未调用provider。

#### 练习 65-P02：将chunk summary作为第三条独立索引/排名列表，再融合并测增益。

summary映稳定doc/chunk/revision，同一身份每列表一次贡献；相关视角不能冒充独立证据，比较权重/候选预算，最终引用回原文。

#### 练习 65-P03：扫描RRF常数10、30、60、100、200，使用评价课的Recall曲线找该语料上的验证集最优值。

把RRF常数c与指标Recall@K分开，保持各路depth/输出K不变。验证集调参数后冻结test；记录每query配对差、seed波动/CI，不能在test上挑峰值。

#### 练习 65-P04：实现真正BM25F的每字段长度归一化，与字段重复trick在重视符号匹配的语料上对照。

按2.2先各字段归一化词频再聚合饱和，固定IDF。控制title/body长度、缺字段/零均长与精确符号gold，比较重复词项、BM25F和无权重基线。

#### 测验 65-Q01（pre）：为什么含精确标识符和语义改写的混合查询分布可能需要词法与向量检索两路？

源正确项3讲标识符与paraphrase可能互补；是否两路改善要看数据/模型，不是每个生产端点必须每次两路。

#### 测验 65-Q02（pre）：BM25中的b（来源默认.75）控制什么？

源正确项3为长度归一化；b=0不校长，b=1全比例，.75是例子参数。长度在TF分母中作用，不是线性罚分。

#### 测验 65-Q03（check）：RRF对每个候选如何计算融合分？

源正确项1：跨各出现列表累加1/(c+rank)，weighted版本乘w；rank从1起，同一ID每列表一次，不使用raw score。

#### 测验 65-Q04（check）：为什么不能直接线性混合原BM25与余弦分数，按rank融合解决了什么？

源正确项1：BM25依语料与词频，cosine范围/尺度不同，直接相加无通用解释。RRF免raw标度校准，已校准score融合仍可有效。

#### 测验 65-Q05（check）：RRF常数c变得很小时，头部与深层名次贡献怎样变化？

源正确项1：c小使头部相对优势更强，深层贡献相对小；它们不是严格变0，阈值/权重仍需验证。

#### 测验 65-Q06（post）：通过重复字段token加权，省去了哪一种query-time字段分数聚合步骤？

源正确项0：在建库时重复token省另一步字段score合并；它同时改变TF/dl/avgdl，并非真正BM25F或单纯最终score乘倍数。

#### 练习 66-P01：扫描候选N从5到50，绘制重排输出的Recall@1并找fixture中的拐点。

本fixture只有8docs，N≥8饱和不证明生产质量拐点；报告candidate Recall@N、最终MRR/Hit@1/K及真实batch延迟，独立query更大库再验证。

#### 练习 66-P02：比较十轮与一轮训练，每轮记录正负pair score margin；同时核对源实现默认实际为60轮。

明确epochs实际配置，绘train loss/margin与held-out排名双曲线；字面相同query或相同答案事实不算独立验证。本篇CPU例验证了train下降但held-out损失上升。

#### 练习 66-P03：用CLS-token head替换mean-pooling，比较相同fixture上的收敛。

固定split/seed/候选/预算，检查PAD不变性、梯度与截断，再比较held-out收敛。只换推理pool不重新训练head不公平，不预设两个head相近。

#### 练习 66-P04：增加二元“文档中是否含答案”head，与ranking head一起推理，分别负责排序和阈值。

无答案标签与rank标签分开，定义joint loss权重、共享梯度影响；独立校准风险/覆盖、误拒/错答。raw相关score不是answerability概率。

#### 练习 66-P05：把本课mock bi-encoder替换成65的候选接口并接通两阶段，比较重排与只召回的top-K变化。

65是BM25+hashdense+RRF接口，并非真bi模型。用版本/文本/identity/length合同适配，固定N和gold比较；改候选池与重排效果分开报告。

#### 测验 66-Q01（pre）：双编码器与cross-encoder的架构差别是什么？

源正确项0：bi独立编码；cross把query/doc连接，用同一序列attention跨双方。缓存doc向量不能替代联合计算。

#### 测验 66-Q02（pre）：对一千万篇文档直接用cross-encoder全库检索，为什么通常代价很高？

源正确项1强调一千万query-doc pair的工作；可batch，不能解释为必然一千万次独立forward。实际代价还受长度平方/模型/硬件影响。

#### 测验 66-Q03（check）：两阶段retrieve-then-rerank中的N代表什么？

源正确项3：N是召回给CE评分的候选数，影响覆盖与计算；K是保留数，批次数另由batchsize决定。

#### 测验 66-Q04（check）：N是否必须严格大于K且通常至少三倍，否则不能重排、增益为零？

源正确项3的“不能重排、零增益”错误。N=K仍可把gold rank4改到rank1，RR .25→1、Hit@1上升；全集Recall@K不变。至少3×K不是必要条件。

#### 测验 66-Q05（check）：本课cross-encoder的mean-pooling head做什么？

源正确项2：最后层有效non-PAD states均值再linear出scalar；CLS/SEP按本课合同也有效。MSE scalar不自动为概率。

#### 测验 66-Q06（post）：记录rank1的cross-encoder score，可为哪些域外/无答案问题提供线索？

源正确项0只能当线索。低raw score可能来自域迁移、截断/短文本、模型错判；需独立unknown标签校准，不能证明整库无答案。

### 派生查询与事实保持

#### 练习 67-P01：实现来源称为RAG-Fusion的多样Multi-query，再用66的重排选最终列表。

保实体、否定、时间、权限硬条件；同ID每list一次票，唯一union再重排。与original比同总候选预算，也记录额外计算，不用重复Query副本赚票。

#### 练习 67-P02：添加第四种Step-back策略：先取更一般问题的证据，再收回原具体问题，对同fixture比较。

一般机制证据与original具体证据各保腿及facet映射；可增加概念覆盖亦可使错误泛化挤掉必要证据，第3.1已有S/E/P反例。

#### 练习 67-P03：为decomposer增加“问题是否原子”head，测训练前后过拆率。

用独立分组真实query的atomic/multifacet标签，报误拆、漏拆和全facet支持率，不能以and是否出现作唯一标签。

#### 练习 67-P04：用真实模型调用替换mock LLM，测当前stack中每种策略的延迟。

按rewrite/编码/retrieval/rerank/queue分别记录wall time与P50/P95、schema/失败/重试；串行求和与真并行最长腿区分。本任务没有真实LLM调用。

#### 练习 67-P05：为每条rewrite增加置信分，按阈值丢弃低分改写，测Recall影响。

confidence事件必须定义为保意图/收益并以标注校准；valid调阈值，held-out测coverage/Recall/误丢与cost，LLM自报不当概率。

#### 测验 67-Q01（pre）：HyDE（假设文档嵌入）的核心机制是什么？

源正确项3：先生成假文，编码其向量查真实docs。源实现还保原hybrid腿，非纯替换query向量；假文不能最终引用。

#### 测验 67-Q02（pre）：HyDE假文可以未经事实核验，是否等于假文错误不会伤害检索？

源正确项2的“只看词分布、必落真实段附近”过宽。假文不是真值，错误实体/条件可把检索引向错文档；只用回读真实证据回答。

#### 测验 67-Q03（check）：Multi-query与query decomposition的区别是什么？

源正确项0：MQ是同题多表述，decomposition是不同子问共同覆盖原题；一个facet命中不等完整问题成功。

#### 测验 67-Q04（check）：什么时候decomposition可能过度拆解并损害检索？

源正确项2：原子题被强拆可引入虚假子问、稀释/漂移或重复结果；不是每次必降低rank，用误拆/漏拆和完整coverage验证。

#### 测验 67-Q05（check）：为什么多个改写的结果可以用RRF融合，而不能未经校准就混原分数？

源正确项0：RRF按rank减轻跨分数标度问题；c/权重/候选depth仍需选择，校准score interpolation并非不能用。

#### 测验 67-Q06（post）：同时并行运行三种改写器时，“一次LLM调用”是否等于端到端延迟下限？

源正确项2仅对应理想并发的LLM阶段最大调用耗时。后续依赖retrieval/merge/rerank仍要时间，源码串行mock未证明真实LLM并行下限。

### 指标、支持与独立验证

#### 练习 68-P01：添加第五种检索指标Hit-rate@K，与Recall@K比较并解释何时不同。

gold3只取到1时Hit=1而Recall=1/3；单gold才相等。定义唯一ID、K、空gold及返回不足K分母，再与第2.1同协议核对。

#### 练习 68-P02：实现分级faithfulness：0不支持、1部分支持、2完全支持，更新汇总指标。

先定义每claim“部分支持”，记录标注一致性/关键否定数字规则；若取0/1/2均分除2，必须说明分母和unknown，不能按词重叠掩盖关键条件错误。

#### 练习 68-P03：用真实模型调用替换mock judge，测fixture上两judge的分歧。

人工gold先核正确支持，再比较mock/真实judge的precision/recall、分歧及误判类型/成本；真实judge也会错。本任务未调用模型。

#### 练习 68-P04：为查询标literal/paraphrased/multi-topic切片，逐切片报告指标。

切片定义、样本数、分母和CI固定，每query保trace。multi-topic按全部facet证据覆盖评价，不能只单doc命中。

#### 练习 68-P05：增加答案长度指标并与faithfulness做相关分析，绘制曲线。

长度按token/字符或claim数定义，控制题难/证据数量等混淆，空答/拒答独列。相关不能推因果；曲线不证明长答一定更不忠实。

#### 测验 68-Q01（pre）：为什么Recall@K通常是RAG候选召回的重要指标？

源正确项3：候选漏掉必要证据，纯重排不能恢复；但无关/冲突块也会占预算、污染回答，不能说生成必能丢弃噪声。

#### 测验 68-Q02（pre）：MRR计算什么？

源正确项3：逐query首相关rank倒数均值，没找到为0；若截K须报告MRR@K。它不检查全部facet。

#### 测验 68-Q03（check）：有分级相关标签时，nDCG相对二元Recall能补充什么？

源正确项3：分级gain与位置折扣保留相关程度，IDCG由完整gold理想排序；可与binary Recall并报，不需二选一。

#### 测验 68-Q04（check）：Faithfulness与answer relevance有什么区别？

源正确项3：faithfulness查实际context支持，relevance查是否回答原题；二者独立，忠于错来源仍可能事实不真。

#### 测验 68-Q05（check）：Recall@5尚可但MRR低，应先检查什么环节？

源正确项3建议查rerank/排序，因为gold在前K但未靠前；先核gold粒度、候选/duplicate和装配预算，不能只由汇总指标确定因果。

#### 测验 68-Q06（post）：冻结qrels随时间推移会遭遇什么生产风险？

源正确项3：语料/版本/事实变化使旧gold不再适用。以revision和变化事件触发重标，quarterly只是治理例。

### 组件接线与最终状态

#### 练习 69-P01：在rewriter内按问题长度、连接词、术语比例选择HyDE/Multi-query/decomposition；先核已有selector覆盖了什么。

现代码已有and→decomposition、jargon→HyDE、default→MQ，但不完整实现length/jargon ratio。验证集比较选择收益/成本/意图漂移，四eval实际全MQ，不能宣称测过HyDE。

#### 练习 69-P02：在env flag后接真实LLM generator，默认mock，比较延迟变化。

替换后核逐claim支持、真实anchor resolver、emptycontext unknown与文档注入；假文仍不得作为证据。费用和每stage延迟另记。本任务没有服务调用。

#### 练习 69-P03：增加--corpus path加载真实语料，再跑eval和阈值检查。

新语料先保许可/ACL/revision、doc/chunk/offset身份、duplicate/update删除与新qrels，不能直接沿用toy阈值。需独立测试，fixture成绩不代表真实资料。

#### 练习 69-P04：给chunker增加--strategy，比较各策略对端到端召回的贡献。

保持同原文覆盖、gold span映射、硬cap/位置/revision/citation合同，同candidate与context预算看完整事实支持；doc级命中不能代替可回答coverage。

#### 练习 69-P05：增加流式generator并接eval，确认faithfulness计算最终完整string而非前缀。

区分partial/error/cancel/done与最终答案；终态完整字符串再评分，前缀只是独立观测，不能提前宣告最终faithful或把断流计成功。

#### 测验 69-Q01（pre）：为什么六组件RAG需要端到端集成测试，它是否是唯一合法评价？

源正确项3强调组件交互的集成必要性；“only honest grade”过度。stage测试、独立质量/权限/更新测试同样有效，同toy qrels非生产充分证据。

#### 测验 69-Q02（pre）：生成器按低重排分拒答有什么作用与限制？

源正确项1：低score可触发unknown；MSE+词法raw score非confidence概率，没有独立校准不能声称防止所有幻觉，须统计误拒/错答。

#### 测验 69-Q03（check）：为什么reranker训练triples应与eval查询/文档事实分组隔离？

源正确项0原则正确；原17triples与4eval文字不同仍共享doc/facts和近改写，不能当独立场景泛化。按family/事实/实体分组。

#### 测验 69-Q04（check）：自动结束demo的退出码是什么用途？

源正确项3：明确阈值gate的0/非0可供CI判pass/fail。源demo未在本轮运行，不能报告exit0或通过。

#### 测验 69-Q05（check）：这条pipeline的citation anchor是什么格式，能证明什么？

源正确项1格式[doc_id:chunk_index]。缺revision/offset与可信resolver，重复ingest可锚冲突；存在/可打开不等逐claim受支持。

#### 测验 69-Q06（post）：真实LLM上线前需要额外测试什么，即使mock只复制检索文本？

源正确项1强调真实LLM可能无证据生成；mock复制首句仍可无关/漏facet/错来源或引用不支持，复制不免答错，真实延迟/支持还须独立测。

### 怎样理解来源的100个测试函数

源测试已完整静读但未运行。64的16项检查参数/若干词覆盖/长度与预设hash/局部命中，不能证明完整slice、token硬上限、中文fence结构或独立全库证据；65的15项检查词法、已知排序、权重及列表形状，未覆盖重复票、ID冲突、非法finite参数或unknown拒答。66的12项确包含训练loss下降和已知query正例得分，但名为pipeline reorders的断言只要求d1在top3，没有要求实际顺序变化或独立MRR；截断允许丢doc也没有gold-span保留检查。

67的13项有表命中、策略字段、某HyDE结果列表不同等检查；best-rank先取baseline再取各策略min，最后断best≤baseline恒成立，并不证明任一改写改善或指定赢家，更未验多facet全覆盖。68的24项检查理想/反序/局部/空输入等指标和预设词法variant关系，未覆盖重复ID使nDCG超过1、非法等级、否定数值和实际context身份。69的20项包括anchor格式、heuristic分支、低分/空拒答、部分指标和阈值/exit0期望；名为answer carries citations的检查允许引用或拒答，不能证明真实支持，更没有ACL、重复ingest/锚冲突、版本/代际或完整事实。测试名称、函数数量、源码期望断言和实际运行成功是不同证据，不能合并为生产验收。

### 来源与图示核对边界

来源为AI Engineering from Scratch固定提交 `3be078b37ffd8f0c04953c0678e48f5c6d0c7775`，Phase19/64–69，2026-10-12按只读冻结报告融合。24源文件、91个真实H2–H4、28实际练习、36测验与100测试函数全部已静读，正式正文按知识主题吸收；未执行或导入这些源程序/测试，未安装其output skills。原题与全部选择项由固定quiz JSON存证，正式题意/正确项含义及中文纠错已保留。

动态图六项已由统一维护记录核最后实际注册函数，均是预定坐标/路径/常数/成员或颜色变化：64的切点不是512-token实际分块，65的圆packet不是BM25或真实并发，66的keep集合不是CE推理，67的假文向量不是模型计算，68的.86不是所画二元gold的nDCG，69的[chunk:42]/拒答文字不是真实anchor resolver或confidence验证。静SVG亦为设计意图，不作为实测性能/全部接线证据。源码具体速度、规模、厂商默认与论文性能未新增primary核验，故未保为当前推荐/成绩。

获取入口：[六课上游目录](https://github.com/rohitg00/ai-engineering-from-scratch/tree/3be078b37ffd8f0c04953c0678e48f5c6d0c7775/phases/19-capstone-projects)。此链接作为来源记录，不能表示本轮新增浏览或论文全文阅读；本轮用已完整静读并核Blob/SHA的冻结记录。

## 16. 引用闭环：切分位置、相关性与框架适配

先学第2–7节的词面检索、证据和引用，再接第13节的当前权限与代际。这个小项目补一个可复查链：原文身份→切分位置→候选排名→逐字引文→问题支持与消费状态。它能帮助定位答案来自哪里；下一步能否回答问题、当前来源是否有效、caller能否看到，仍要独立检查。继续复用本章八个完整标准库例，不再创建另一套弱问答服务。

### 16.1 文档版本与偏移单位一起保留

文本加载先确定允许的root和路径，拒静态解析后逃出root的symlink；仍需采集大小/文件数限制、实际打开与检查竞态、对象权限及版本。来源按文件名排序、以相对路径作ID，只扫txt；同文件的内部别名可产生两个ID，路径名稳定也不意味着内容未变。接真实多租户时，权限不能由“位于root内”自动给出。

来源 `read_text`后的UTF-8重新编码SHA是**所读文本的身份**，不无条件等原磁盘bytes；换行处理可能使CRLF与LF得到相同文本。第13节已有原文/派生版本关系，原字节SHA、解码/换行规则、文本摘要和chunk范围应分栏。引用消费时重核当前source/version/权限，而不只是检查SHA字符串有64字符。

字符窗口用半开区间 `[start,end)`。abcdef、size4/overlap1得[0,4)的abcd与[3,6)的def；最后已到原文末尾就停止，否则会继续产生多余的小尾窗。先验证size、overlap为明确整数且`0≤overlap<size`，bool不能当1，小数虽过比较也不能直接拿来slice。空原文返回空chunks，缺字段与非法对象按输入合同拒绝。

Python偏移按字符串码点计算；UTF-8 bytes和JavaScript UTF-16不是相同单位。😀加空格前置时，后文start在Python为2、JS可能为3。不要把一份偏移拿到另一个renderer里直接slice；记录单位及规范化前后关系，明确转码或用原位置。overlap帮助边界上下文，不保证每个条件、否定句和表格都完整，也不创造新的独立证据。

### 16.2 对数词频分数的计算与局限

来源是一个可解释的log-TF词面基线，不是BM25。对query去重后的每个命中词t，按以下量求和：

$$s(c,q)=\sum_{t\in q,\,tf(t,c)>0}(1+\ln tf(t,c))\ln\left(1+\frac{N}{1+df(t)}\right).$$

这里N是候选语料中的**chunk数量**，df为含词的chunk数；重叠窗口会影响它，不能另称文档级DF。没有长度归一，也没有同义词或语义支持。query重复写cache不增加其set权重；chunk内重复关键词会按对数提高TF，仍可能被keyword stuffing影响。新增很多不命中的词本身不贡献分数，但不能因此把基线说成已解决长度偏差。

手算三个chunks：a为cache cache，b为request deadline，c为request retry。query cache时df1、tf2，a分数为$(1+\ln2)\ln2.5\approx1.5514$；query request时b/c的tf1、df2，各为$\ln2\approx0.6931$，按固定ID打破tie。只返回正分候选，zebras没有命中就空列表；k0也空。k应是非负整数、输入形状/资源限额明确，不能依赖Python slicing在错误类型后报异常。

真实中文、代码、表格和多语言要核相应分词与指标。Python\w会把连续中文作为一个词面块；来源图的JS\w又主要是ASCII范围，两者不能直接当同一tokenizer。排名分数仅决定调查次序，不是答案真值概率。

### 16.3 逐字引文、问题支持和answered各有含义

让生成回调返回来源chunk ID和逐字quote，检查ID属于本次检索集合、quote非空并确实在该chunk中，然后恢复原文偏移：原chunk.start10、text为abc def、quote def相对起点4，原start14、end17。不能因为同句出现在全库其它地方，就忽略当前所引用ID错位；重复引用位置也要有明确选择与验证依据。

没有候选时应在生成器调用前返回abstained。模型异常、非法JSON、缺字段、未知ID和伪造quote分开；不要用eval、coercion或删除raw片段凑成功。来源的JSON解析仍允许重复键/忽略额外字段，输出没有大小、期限或费用边界，直接API也可能遇坏形状；应用入口沿本库严格合同补齐。

最有价值的反例来自作者实际录制的输出。样本文档说：缓存保成功答案60秒，私人答案不进入共享缓存。问题是“When does cache expire?”，局部抽取器却因一个cache词与同分排序，选择了“Private answers never enter the shared cache.”，仍标answered。它是准确引文，但没有给出所问时间；应由问题支持/完整性检查保持needs_review或缺证据，而不是把state标签当答案已正确。

另一个banana例无有意义query词交集，会在CLI的query层改needs_review；**直接answer和framework_qa没有经过这道额外相关性检查**。即使有query词重叠也可能答错，故不能用增加一个关键词谓词代替语义支持。状态最好分别表示字面引用通过、问题支持已核/未核、来源当前有效及访问许可。每条被消费主张仍要保限定词、适用日期与版本，当前权限的主程序继续由第13节维护。

### 16.4 框架切分器回接同一位置合同

适配器先保原doc，再逐part在原text中寻找可核的起点；找不到说明切分器改变了文本，应拒绝而非生成假位置。匹配后把cursor移到start+1，让重复且重叠的片段可继续定位：ababa拆为aba/aba，应在0和2；若移到完整chunk末尾3，第二个匹配会丢失。

按顺序find只是一个明确假定：parts确来自同一原文、有序且对应这些出现位置。存在多处相同片段时，单凭substring找到下一处不证明那就是切分器实际意图。能获取原start metadata时，先保它再核原文slice；否则明记歧义、coverage和缺口。空/非字符串part拒，原文的空白变化或Unicode归一也不能悄悄跨越位置版本。

2026-10-14选读[LangChain递归切分官方说明](https://docs.langchain.com/oss/python/integrations/splitters/recursive_text_splitter)：递归尝试段落、换行、空格等分隔，size按配置length_function度量，overlap为目标重叠；split_text给字符串，create_documents给Document对象。中文等无空格语言可另配标点分隔，不能把默认字符长度误叫token数。这里只核这些说明，没有安装或运行SDK。

source framework_qa用实际导入的splitter和本地FakeListLLM，最后仍接原词面retrieval与answer；包装成框架不补tenant/权限、来源实时版本或语义审核。源锁定1.1.2与9-28的optional测试记录只作可重取历史环境，不能当本轮最新版本推荐。默认25个测试和额外5个真SDK测试分别统计：缺SDK的skip不是通过；该作者记录也不是本轮运行、云服务或用户完成证据。

### 16.5 四阶段的输入与参考判据

| 阶段 | 练习及拒绝/结果判据 |
|---|---|
| 文档与切分 | abcdef/4/1必须只有两个窗口；空文本空，overlap等size拒。多字节前置偏移按所声明单位核。sorted文件ID、文本/bytes SHA、root/symlink/TOCTOU与权限分别解释，不能只验hash长度。 |
| 词面排名 | socket选socket，OOV/空语料/k0空，同分固定ID；重复不相关词无直接分数，相关keyword重复仍影响TF。用三个chunks手算N/df/TF，区分chunk与doc统计、中文词面和语义。 |
| 引文与支持 | 合法quote给准确原start/end；坏JSON、伪造quote、错chunk ID分别拒，空检索0生成调用。banana仅字面通过应review；cache/privacy原录像有重叠仍没回答when，不能照抄其answered当接受标准。 |
| 适配与交付 | ababa两aba定位0/2；changed或empty part拒；SDK路径和手工路径比较每chunk原位置，而非只数chunk。默认/optional测试各说明覆盖，result同对象生成JSON/HTML并escape，无当前源/权限证明时不作发布许可。 |

CLI的source SHA与start_line只在query外层补上，直接answer/framework调用并不自动得到完整收据；框架路径也未复用CLI的needs_review策略。四个图共用whole-text substring、词交集和JS字符窗口，未实际加载文件、计算源码TF-IDF、生成器、SDK或SHA；JSUTF16偏移与Python单位差别明确保留。三个PNG及GIF全部34帧已实际视读，作者core/SDK PASS与上述错误回答各是历史范围。

固定来源 `3be078b37ffd8f0c04953c0678e48f5c6d0c7775` 的[Document QA With Citations](https://github.com/rohitg00/ai-engineering-from-scratch/tree/3be078b37ffd8f0c04953c0678e48f5c6d0c7775/projects/doc-qa-with-citations)，40项目文件、四正文/全部30原测试方法（25核心与5可选）、CLI/样本/所有媒体与provider于2026-10-14完整静读。源程序/测试/grader/SDK/安装/模型/网络/API/JS本轮0执行；八旧Python例原字节和持久成功日期保持，没有新同义RAG服务或评分。


## 17. 本地笔记的可解释词面检索

先完成第2节的排序与第4节的证据单位，再做这个小型索引。它适合少量本地 Markdown、稳定领域术语和需要解释“为什么命中”的场景。`Semantic Notes Search` 的实际算法是词面 TF-IDF 加显式单步别名；没有训练、向量API或自动推断同义句。之后是否改用Embedding，应依据独立查询集的遗漏类型判断。

### 17.1 归一化先于分词，文档身份保持原样

`café` 可以由一个 `é` 或 `e` 加组合重音表示；肉眼相同，底层码点不同。先 `casefold()` 再 NFC，把等价拼写收拢后才使用 Unicode `\w+`，否则先分词可能丢掉组合重音。Python 的 casefold 比普通 lower 更完整，例如 `ß` 会成为 `ss`；它仍不是语义翻译。别名的键和值也用相同规则。原始文件路径和正文用于展示与溯源，不要因检索归一化修改它们。

`release → deploy` 是一次替换：`a→b,b→a` 下输入a只得到b，不能反复展开到循环。保留重复token以计算TF，仅在计算DF时对每个文档去重。别名要有版本和应用范围；“release软件”和“release压力”不能无条件视为deploy。源实现允许空值、多词值、归一化后键冲突且后写覆盖，还把假值aliases替换为空字典；正式接口应显式拒绝或定义这些政策。

中文在 `\w+` 下可能整段成为一个token，它不是中文分词器。单复数 `replica/replicas` 也不会自动合并。空结果表示当前表示没有正分候选，不能据此断言资料库没有相关知识。

### 17.2 TF-IDF和余弦的完整手算

这里N是索引中的**文档数，包括空文档**，df是含词t的文档数，tf是该词在单个文档中出现的次数。采用项目明确的平滑政策：

$$
\operatorname{idf}(t)=\ln\frac{1+N}{1+\operatorname{df}(t)}+1,\qquad
w_{t,d}=\operatorname{tf}(t,d)\operatorname{idf}(t),\qquad
v_{t,d}=\frac{w_{t,d}}{\sqrt{\sum_s w_{s,d}^2}}.
$$

零向量保持为空，不除以零。查询用索引的同一词表、IDF和别名，忽略不在词表中的词，再做同样归一化；不要用只有一条查询的语料重拟合IDF。单位向量的点积就是余弦分数。这个模型忽略词序、否定及句间关系，余弦高分不证明答案受支持。[向量模型](https://nlp.stanford.edu/IR-book/html/htmledition/the-vector-space-model-for-scoring-1.html)、[余弦与单位向量](https://nlp.stanford.edu/IR-book/html/htmledition/dot-products-1.html)、[查询与文档共享坐标](https://nlp.stanford.edu/IR-book/html/htmledition/queries-as-vectors-1.html)（2026-10-14核指定段；此处平滑IDF是项目政策，不归因给书中唯一标准）。

用a=`deploy deploy orchard`，b=`restore orchard`，c=`café orchard`：N=3，df(orchard)=3，所以IDF=1；deploy只出现在a，IDF=ln2+1≈1.693147。a未归一权重是deploy=3.386294、orchard=1，长度约3.530865；归一后deploy≈0.959056、orchard≈0.283217。查询release经别名成为deploy，只有该坐标且权重归一为1，故a得0.959056。重复整篇文档不会改变向量方向，但只重复某一个词会改变方向；归一化并不消除所有词频作用。它与第16节的对数TF分数、第2节的BM25是不同合同，不能混用名称或阈值。

### 17.3 排名、文件读取与解释不能混为证明

只返回正分，按原始分数降序、文档ID升序解平局，再截取k。**排序之后**才为展示四舍五入。源代码先把score保留六位再排序，两个不同分数可能因此变成假平局；跨实现比对要记录这个差异。`matched` 表示共同词项，`preview` 是正文开头240个Python字符，未必包含命中位置；二者均不是逐字引用或回答的语义支持。

源CLI扫描调用者给定目录中的小写 `*.md`，保相对路径ID；拒绝符号链接文件与resolve后越根的文件，单文件stat大小大于100000字节拒绝，按UTF-8读取并从头重建索引。100000字节是十进制上限，不是100KiB；没有文件数量、累计字节或查询时间总预算。stat后读取仍有竞争窗口，根目录resolve本身也不是用户权限检查，不能把此读器称为安全沙箱。输出路径没有与输入目录隔离：把`--out`指定为笔记可能覆盖它；真实使用先确定可信目录、文件句柄/权限、总预算、输出独立目录及原子发布合同。

作者9月28日录像中查询 `release replicas`，无别名时release.md=.246073、backup.md=.215061；加别名后release.md=.474234、backup.md=.215061。原文件中是单数replica，匹配词只有deploy；图中默认短句却含复数replicas，因此能命中两个词。这是两组不同输入，不能把图与文件样本分数当相同算法的交叉验证。录像中的cafe加组合重音命中café.md=.527132；它只证明作者当时公开样本的输出。

图的JS用lower而非Python casefold，别名键/值没有统一规范化，数值ID而非文件路径、未先round再排序；四图共享一个小计算器，未读取文件或验证UTF-8/符号链接。可用它观察IDF/方向/命中变化，跨语言实现需另行校准。

### 17.4 单标签命中率与真正召回率的关系

每条case包含query和一个expected文档ID，实际调用search再判断前k是否含expected；hits/total是查询的HitRate@k。只有每个查询的完整相关集合恰好只有这一个文档时，它才同时等于宏平均Recall@k。若一个问题有两篇相关笔记而只标一篇，不能声称完整召回；多相关集合用[评测章节](./06-评测与实验管理.md)的分母与未标注政策。

源函数对空case返回0，并不代表失败了某个查询；它对cases重复遍历，生成器/错误容器、坏query、布尔k等没有统一入口政策，空case甚至不触发search的k检查。下面学习实现要求列表、先验证k，空集返回None，明确“未评价”。留出不用于调别名的查询，记录语料/分词器/词典/标签/k的版本，比较每个查询与关键类别；三个公开样本满分不能证明新笔记质量，也没有固定“补几条标签就够”的万能数量。

### 17.5 可运行实现与四阶段练习

下面只实现内存词面索引，不做文件扫描、权限或引用发布；保持完整精度排序，拒绝布尔k、规范化后的别名冲突及多词别名。私有属性仍是普通Python对象，调用方若修改它们就破坏索引快照；生产共享索引应发布不可变代际，参见第13节。

```python
import math
import re
import unicodedata
from collections import Counter


def canonical(text):
    if not isinstance(text, str):
        raise ValueError('文本必须是字符串')
    return unicodedata.normalize('NFC', text.casefold())


def alias_table(aliases):
    if not isinstance(aliases, dict):
        raise ValueError('别名必须是字典')
    result = {}
    for key, value in aliases.items():
        key, value = canonical(key), canonical(value)
        if not re.fullmatch(r'\w+', key) or not re.fullmatch(r'\w+', value):
            raise ValueError('这个例子只支持单词到单词的别名')
        if key in result and result[key] != value:
            raise ValueError('归一化后的别名冲突')
        result[key] = value
    return result


def tokens(text, aliases):
    return [aliases.get(t, t) for t in re.findall(r'\w+', canonical(text))]


def unit(weights):
    norm = math.sqrt(sum(x * x for x in weights.values()))
    return {t: w / norm for t, w in weights.items()} if norm else {}


class LexicalIndex:
    def __init__(self, documents, aliases=None):
        if not isinstance(documents, dict) or any(
            not isinstance(key, str) or not key for key in documents
        ):
            raise ValueError('文档必须是非空字符串ID到文本的字典')
        self.aliases = alias_table({} if aliases is None else aliases)
        counts = {key: Counter(tokens(text, self.aliases))
                  for key, text in documents.items()}
        df = Counter(t for tf in counts.values() for t in tf)
        self.idf = {t: math.log((1 + len(counts)) / (1 + n)) + 1
                    for t, n in df.items()}
        self.vectors = {key: unit({t: n * self.idf[t] for t, n in tf.items()})
                        for key, tf in counts.items()}

    def search(self, query, k=3):
        if type(k) is not int or k < 1:
            raise ValueError('k必须是正整数，不能是布尔值')
        tf = Counter(tokens(query, self.aliases))
        q = unit({t: n * self.idf[t] for t, n in tf.items() if t in self.idf})
        rows = []
        for key, vector in self.vectors.items():
            score = sum(w * vector.get(t, 0) for t, w in q.items())
            if score > 0:
                rows.append({'id': key, 'score': score,
                             'matched': sorted(q.keys() & vector.keys())})
        return sorted(rows, key=lambda r: (-r['score'], r['id']))[:k]

    def evaluate(self, cases, k=3):
        if type(k) is not int or k < 1 or not isinstance(cases, list):
            raise ValueError('先验证k和列表，即使没有评测查询')
        hits = 0
        for case in cases:
            if not isinstance(case, dict) or set(case) != {'query', 'expected'}:
                raise ValueError('每个case只有query和expected')
            if not isinstance(case['expected'], str) or case['expected'] not in self.vectors:
                raise ValueError('标签必须指向本索引中的文档')
            hits += any(r['id'] == case['expected']
                        for r in self.search(case['query'], k))
        return {'hits': hits, 'total': len(cases),
                'hit_rate_at_k': hits / len(cases) if cases else None}


idx = LexicalIndex({'a': 'deploy deploy orchard', 'b': 'restore orchard',
                    'c': 'café orchard'}, {'release': 'deploy'})
assert math.isclose(idx.idf['orchard'], 1)
assert math.isclose(idx.idf['deploy'], math.log(2) + 1)
assert idx.search('release')[0]['id'] == 'a'
assert idx.search('cafe\u0301')[0]['id'] == 'c'
assert idx.search('replicas') == []
assert [r['id'] for r in LexicalIndex({'z': 'a', 'b': 'a'}).search('a')] == ['b', 'z']
assert math.isclose(sum(w*w for w in idx.vectors['a'].values()), 1)
assert idx.evaluate([{'query': 'restore', 'expected': 'b'},
                     {'query': 'absent', 'expected': 'c'}], 1)['hit_rate_at_k'] == .5
assert idx.evaluate([])['hit_rate_at_k'] is None
try:
    idx.evaluate([], True)
except ValueError:
    pass
else:
    raise AssertionError('空评测也必须拒绝布尔k')
try:
    LexicalIndex({}, {'CAFÉ': 'a', 'cafe\u0301': 'b'})
except ValueError:
    pass
else:
    raise AssertionError('别名归一化冲突必须拒绝')
print('TF-IDF/Unicode/别名冲突/正分排序/单标签命中率及空集政策通过')
print('手算查询release：a分数', round(idx.search('release')[0]['score'], 6))
```

2026-10-14在Python3.12.13实际运行这一个新增程序：归一化、冲突拒绝、TF/DF、单位长度、正分和ID平局、OOV、单标签分母、空集政策通过。未执行原项目程序或任何模型/API。原章节已有八个程序保持字节和原验证日期，本例补不同的TF-IDF机制，不替代其BM25或权限流水线。

| 阶段 | 动手输入和需保留的中间结果 | 参考判据与应调查的失败 |
|---|---|---|
| 1 归一化 | HELLO hello、两种café、CAFÉ别名、空字符串、a↔b；保原路径与重复token | hello出现两次；两种café相同；a单步到b。非字符串拒绝；加入冲突别名应拒而非默默覆盖。用“release压力”检查语义误伤 |
| 2 建索引 | 空字典、空文档、a a b、共同orchard与稀有restore、空ID、别名release | 空索引词表空，空文档向量空；非空向量平方和1，DF每文档最多一次；稀有词IDF更大，保N/DF/词典版本。空ID拒绝；比较重复整篇与只重复一词 |
| 3 排名 | apple/pear、同词ID z与b、OOV、空查询、release→deploy、k=0/True | 命中apple；平局b在z前；无正分返回空；非法k拒绝。另外构造第7位才不同的分数，检查先round排序会丢顺序；确认replicas不会匹配replica |
| 4 评测与目录 | 命中、遗漏、两个case一中一漏、空case、标签不存在；组合重音文件名、越根链接、过大文件 | 一中一漏=.5；未知标签拒绝；明确空集None与源码0不同。保原路径/正文；链接拒绝不等于消除读时竞争。在独立查询集回看别名的收益和损害，不把作者参考pass当自己已学会 |

原项目27个Test定义（8/6/6/7）分别约束上述基础行为，没有覆盖所有入口、总预算、并发或语义正确性。累计练习时应先预测结果，完成自己的实现后逐项核对，而不能用公开答案替代自己的验证。

来源：第1来源固定commit `3be078b37ffd8f0c04953c0678e48f5c6d0c7775` 的[项目](https://github.com/rohitg00/ai-engineering-from-scratch/tree/3be078b37ffd8f0c04953c0678e48f5c6d0c7775/projects/semantic-notes-search)，2026-10-14完整静读四阶段、实现、测试、样本及图示。原30文件与provider、两PNG及39个GIF帧逐项核对；不镜像第三方全文，不执行来源命令。来源Python3.10+与README泛POSIX模板是原环境说明，本算法未用锁或进程组；学习例实测版本单独记录。


## 18. 视觉证据库：文字、框坐标和复核记录分别保存

第10节解决页面级视觉检索，这个实践解决更细的区域证据：在一张图里究竟哪一块支持当前文字。适用于截图、说明牌、图表标签的整理；输入是资产清单、声明尺寸和**已经提供的文字框**。离线核心没有OCR，也没有读取像素推断文字。可选视觉模型仅产生待审候选，不能因为返回结构正确就升级为证据。

### 18.1 资产、区域和坐标的输入合同

一份manifest包含assets列表；每张资产保存 `id,path,width,height,regions`，每个region保存 `id,text,bbox,origin`。资产ID全局唯一，区域ID只需在本资产内唯一，故引用键至少是 `(asset_id,region_id)`。原图字节SHA、清单版本、坐标系/方向和审核记录应一并保存，ID或路径本身不能证明版本相同。

bbox是源图像素的 `[x,y,w,h]`，不是屏幕坐标、两端点或归一化数。声明宽高应是1～20000的精确整数，拒绝bool；坐标四个有限非布尔数，x/y非负，w/h为正，右/下边不越界。600×320图里的[45,130,510,45]到达(555,175)，有效；[590,130,30,45]到达x620，应拒绝，不能裁掉越界部分后当原证据。

原读取器把root和候选路径resolve后判断包含、存在、后缀SVG/PNG/JPEG与单文件不超过5,000,000字节；它允许仍位于root内的符号链接，并非所有符号链接都拒绝。尺寸和文字仍是清单声明，没读真实宽高，也没验证图中确实有这句话。stat后重新读有竞争窗口，缺总资产数/总字节/解码像素预算和用户权限检查。`dict(region)`只浅拷贝，bbox列表仍可别名修改；验证后到导出前应使用同一个不可变版本，避免检查对象与展示对象脱节。

### 18.2 按区域检索，而不是把整图标签当文字

对query和每个区域文字casefold后取唯一Unicode词项，分数为 `|Q∩T_region|/|Q|`；只返回正分，按分数、资产ID、区域ID排序，limit精确整数1～100。重复查询词不加分、空查询无匹配，seed不自动匹配seeds。源分词没有NFC，所以组合重音与预组字符可能不同；第17节的NFC政策可复用，但改政策后要重新构建索引和评价。

查询return dry seeds包含三个唯一词。种子牌的“Return dry seeds in paper envelopes.”得1；工具牌的“Return tools to the blue shelf.”只命中return，得1/3；“SEED LIBRARY”标题没有seeds复数，不应混成返还说明的区域。源输出保留原始文字、bbox、matched_terms与origin。100%只说明词面覆盖，不能证明词序、否定、图像文字准确或问题答案正确，更不是模型置信度。后续加入短语/别名时，把展开项展示出来，并在独立标签集测精确率与误伤。

### 18.3 模型提议、分类标签和人审是三种对象

一个模型响应可以同时包含 `regions=[{text,bbox}]` 和 `labels=["notice"]`。分类标签notice没有对应的文字框，保留在classification_labels，不进入OCR文字索引。候选区域按顺序命名proposal-1、proposal-2，来源model-proposed、reviewed=False，状态review-required；不合几何或空白文字拒绝。空regions可以保为空，不虚构“至少一条”证据。

入库时源代码要求model-proposed区域的reviewed**恰为True**；provided只说明调用方提供，不能绕过实际核对。这个布尔值没有审核人身份、图像/候选SHA、审核时间、撤回与修改后失效机制。实际使用应把审核独立保存，并绑定 `image_sha + manifest_revision + region_id + text + bbox + coordinate_profile`；内容任一改变就重审。验证文字看字符错误率，验证框看IoU/遗漏与错框，验证检索另看命中/精确率；几何有效、标签存在、模型自报高分都不替代这些真值。

可选HTTP适配器读取PNG/JPEG实际字节为data URL，按扩展名及PNG八字节/JPEG三字节前缀做浅检查，以model/messages/response_format=json_object序列化POST，并可带Bearer。SVG只用于离线。响应读取上限1,000,001字节并在大于1,000,000时拒绝，urlopen参数timeout=30；它不是整个调用的独立墙钟总预算。解析 `choices[0].message.content` 再校验区域，仍须处理HTTP错误、坏envelope/JSON和真实尺寸不符。

直接validate_proposal未重用manifest的宽高严格验证；坏类型、非有限声明尺寸可能破坏边界比较。签名前缀不等于图片完整解码，明确URL也不等于已经批准上传或允许任意重定向。若接真实服务，先固定可信目标、数据范围与费用、传输和重定向政策，并对图片字节/尺寸/响应总量独立校验；本轮没有发送图片、读取密钥或运行该适配器。source mock/local-wire tests只是接线合同，不能称为视觉识别质量证据。

### 18.4 导出时保持源坐标、显示比例与版本一致

HTML里图像等比缩放时，把left=x/W、top=y/H、width=w/W、height=h/H转成百分比，JSON保原像素框。对于600×320和[45,130,510,45]，四比例是7.5%、40.625%、85%、14.0625%；显示宽420时左边31.5px、框宽357px。容器必须贴合实际图像内容；裁剪、letterbox、旋转、EXIF方向和SVG viewBox与声明尺寸不一致，都需要显式变换，不能只靠宽100%自动修正。

源报告用相对定位容器叠绝对定位框，将图片base64内嵌为data URL，使HTML可离线携带；html.escape用于query、text、ID与origin，不能把候选文字拼成可执行HTML。图像字节和清单应先冻结并核SHA，避免验证一次、导出再次读到另一张图。portable JSON排除resolved_path，但源代码把其余原字段整体透传，额外字段仍可能含本地路径或敏感信息；正式导出使用字段白名单。

对SVG，源实现用ElementTree解析，仅允许svg/g/基础形状/path/text/tspan等小集合；未知元素如script/foreignObject直接拒绝。仅保少量几何/颜色/字体/transform属性，删除事件处理器、未知属性和包含字面url(或小于号的值。这是一份受限教学策略，非完整SVG/CSS安全规范；它只按tag的本地名判断，没有严格根元素/命名空间及所有属性值语法验证。PNG/JPEG离线嵌入分支也未重新验证字节和尺寸。选用固定安全格式、解析资源上限和独立审核后再发布。[ElementTree解析与命名空间](https://docs.python.org/3/library/xml.etree.elementtree.html)（2026-10-15只核解析/namespace与不可信XML提示；XML解析本身不等于SVG净化）。

源程序先写evidence.json，随后处理图片并写index.html；坏SVG可能留下新JSON和旧HTML，并非两个产物原子提交。实践中先在临时目录生成、验证完整产物、核一致版本，再用单一指针发布。打开保存的离线报告不应触发模型上传；若加query表单，只读内嵌索引，模型请求继续放在显式独立步骤。

### 18.5 几何小例与四阶段验收

下面验证**声明几何与词面覆盖**，不替像素解码、OCR、授权或完整SVG净化。它复用第17节的NFC，保留原声明坐标；正式文件发布和引用支持合同沿用第13、16节，不另造同义框架。

```python
import math
import html
import unicodedata
import re


def css_box(width, height, box):
    if any(type(v) is not int or not 1 <= v <= 20000 for v in (width, height)):
        raise ValueError('声明宽高需为1到20000的整数')
    if not isinstance(box, list) or len(box) != 4 or any(
        type(v) not in (int, float) or not math.isfinite(v) for v in box
    ):
        raise ValueError('四个有限非布尔坐标')
    x, y, w, h = box
    if x < 0 or y < 0 or w <= 0 or h <= 0 or w > width - x or h > height - y:
        raise ValueError('框不得越出声明图像')
    return dict(zip(('left', 'top', 'width', 'height'),
                    (100*x/width, 100*y/height, 100*w/width, 100*h/height)))


def coverage(query, text):
    def words(value):
        if not isinstance(value, str):
            raise ValueError('需字符串')
        return set(re.findall(r'\w+', unicodedata.normalize('NFC', value.casefold())))
    q, t = words(query), words(text)
    return len(q & t) / len(q) if q else 0.0


box = css_box(600, 320, [45, 130, 510, 45])
assert box == {'left': 7.5, 'top': 40.625, 'width': 85.0, 'height': 14.0625}
assert math.isclose(420 * box['left']/100, 31.5)
assert math.isclose(420 * box['width']/100, 357)
assert coverage('return dry seeds', 'Return tools to the blue shelf.') == 1/3
assert coverage('return return dry seeds', 'Return dry seeds in paper envelopes.') == 1
assert coverage('cafe\u0301', 'CAFÉ') == 1
assert coverage('seed', 'seeds') == 0
for bad in [[590, 130, 30, 45], [0, 0, True, 2], [0, 0, float('nan'), 2]]:
    try:
        css_box(600, 320, bad)
    except ValueError:
        pass
    else:
        raise AssertionError('坏框必须拒绝')
assert html.escape('<script>') == '&lt;script&gt;'
print('声明几何/百分比缩放/Unicode词面覆盖与坏框拒绝通过；未读取像素或验证OCR真值')
```

2026-10-15这一个新增标准库例从最终Markdown提取实际CPU运行通过；原九个程序保原字节和持久成功日期，不重复运行。

| 阶段 | 实际练习输入 | 参考判据与拓展 |
|---|---|---|
| 1 证据结构 | 有效区域、重复asset/region、负/越界/零宽/NaN/bool、越根绝对路径和链接、缺文件、bool尺寸、空文字、未审model-proposed | 原origin/bbox保留；坏项拒；model-proposed须显式True。再从一种图片格式读真实尺寸比声明，保provided标签；追加改bbox后审核失效与总量预算反例 |
| 2 区域排名 | café、bicycle repair、重复query、不同ID同分、空/标点/OOV/复数、limit0/101/True/1.5 | 独立区域分数1和.5；重复不变；平局a先z；无词返回空；非法limit拒。再加独立别名表、公开展开项与未用于调参的精确率查询 |
| 3 提议复核 | regions加labels、越界/无限/负宽/bool框、空文字/非字符串标签、空regions、受控响应与伪造图片前缀 | 提议reviewed=False且分类不入索引；坏框拒；空候选不补造。记录POST内容/图片dataURL只是序列化；另加坏width/height、envelope和超量响应；独立保存审核者与时间，测CER与IoU |
| 4 可携报告 | 200×100框[10,10,170,40]、危险text/query、无匹配、script SVG、onload/onclick与外链fill属性 | HTML left5%/width85%；JSON保原框且不含resolved_path；文本转义、空态明确；未知元素拒/危险属性删。解码dataURL再核SVG；加不一致viewBox、额外敏感字段与图片处理失败后JSON/HTML一致发布反例 |

作者参考24Test定义（各6）和9月28日PASS录像已静读，不执行。两张人工SVG的实际视觉内容、两PNG海报与GIF18+6全24帧已查看：示例只演示人工牌与提供的框，未测真实OCR、模型识别或人审身份。源输出媒体是浏览器滚动采集，不是一个可复跑的JSON测试结果。

来源：固定commit `3be078b37ffd8f0c04953c0678e48f5c6d0c7775` 的[视觉证据项目](https://github.com/rohitg00/ai-engineering-from-scratch/tree/3be078b37ffd8f0c04953c0678e48f5c6d0c7775/projects/visual-evidence-library)，2026-10-15全文、实现、测试、清单/素材、最后四图及媒体静读后回融。只保主题知识与轻量出处，不复制整套原站。


## 19. 网页变化证据：抽取策略、重复次数和基线批准

第13节解释检索新鲜度与索引代际；这里把同一原则应用到网页资料更新：先保可复核的文本变化，再决定是否采用新基线。适合公告、规则、知识资料的定期人工复查。两份保存的HTML可以完全离线比较；显式抓取单页是另外一条路径，项目没有自动调度、消息通知或真实网页浏览器。

### 19.1 先抽可读块，明确哪些变化故意忽略

源扫描器逐字节找标签边界，在单/双引号内遇到 `>`不能结束标签，注释需找到结束标记；用skip名称与depth跳过head、script、style、nav、footer、noscript。遇p/div/section/article/li/tr/h1～h6/br/hr等块边界时flush；td/th插空格，strong等行内标签不额外切块。flush解码HTML实体、折叠空白、丢空块，应用显式忽略短语，再保留正文块。

输入 `<nav>Visits 12</nav><p>Bring a mug &amp; a spoon.</p>`只得到“Bring a mug & a spoon.”；`<p title="a > b">A <strong>small</strong> repair</p>`应是一个“A small repair”。单段中的相邻行内元素如果原文没有空格，扫描器也不会自动补单词边界。源只支持有限HTML，不理解完整HTML5容错、CSS可见性、客户端JavaScript或所有script原始文本语义；残缺tag、comment、ignored区域报错，不能把抽取失败转成成功空快照。

源限制HTML不超过2,000,000字节、最多10000块，但块数上限是在构造完之后检查；本地CLI也是先ReadFile再检查字节上限。响应有边界不等于所有入口在分配内存前都有限。页面编码也不应靠Content-Type形状推断已正确解码，源码直接把字节当Go字符串。

过滤短语是忽略整块、大小写不敏感，不是只删除一个词；页脚可能有重要生效日期，因此默认跳过footer是可见取舍。源只TrimSpace来判断短语是否为空，真正Contains仍保原短语的前后空格；图会先trim，两者不完全一致。过滤/抽取规则要有版本，两份输入须相同政策，否则规则变化会伪装成网站新增或删除。

### 19.2 用多重集保重复，内容指纹与出处身份分开

普通集合会把重复的A丢掉。设before=[A,A,B]，after=[A,B,C]，逐块保存出现次数；共同数是每个块两侧次数的较小值相加，删除A一次、新增C一次、unchanged=2。输出新增/删除按文本排序。项目故意忽略块顺序，所以[B,A,A]与[A,A,B]内容指纹相同；若位置本身有含义，另做序列对齐/LCS报告，不要把搬移混成删除与新增。

来源把排序后的块数组以Go `encoding/json`序列化后SHA-256，重复块仍保留；不能用随意拼接分隔符，免得“一个含分隔符的块”与“几个块”摘要碰成相同输入。跨语言复核必须固定UTF-8、数组顺序、转义/空值等序列化合同；Python默认JSON文本不能直接宣称与Go逐字节一样。

URL需是无凭据的绝对HTTP(S)，host转小写、去fragment、空path补/、保query；不同query不自动视为同页，默认端口/百分号/路径等价也不自动全归一。对比要求canonical URL完全相同；源Compare直调只比较URL字符串，并不核快照本身的canonical或摘要，直接构造的坏对象必须由消费者前置检查。

原内容摘要不包括URL、抓取时间、原HTML字节、忽略规则或发布者身份。Load重算块摘要可以发现“只改块、不改hash”的误改，不能防修改者同时重算hash，也不能证明谁发布或何时有效。原快照还不保存过滤政策，跨次调用换`--ignore`可能产生假变化。实际采证应另保原字节SHA、最终URL/重定向链、获取时间、解析/过滤版本、规范化内容摘要和必要权限，不让一个hash承担所有身份与时效主张。

### 19.3 抓取合同：状态、类型、大小、重定向与时限

源FetchHTML只接受显式HTTP(S)，状态恰200，媒体类型text/html或application/xhtml+xml，读到MaxHTMLBytes+1检测超量；不是先无限读完再裁。用带context的GET与独立User-Agent，不取链接资源、不执行页面脚本。

默认client=nil时创建Timeout15秒；它涵盖连接、重定向、响应体读取。CLI另外给20秒context。**调用方提供client时保留其Timeout，0意味着无限**，不能仅凭函数名说任何直接调用都有15秒限制；context/Transport还需正确合作。源浅复制client后覆盖CheckRedirect，原client对象未改，但调用方原有更严格redirect回调没有合并，Jar/Transport仍可能共享。[Go Client时限与重定向合同](https://pkg.go.dev/net/http#Client)（2026-10-15只核Client字段指定段，不声称通读net/http或做完整网络安全测试）。

重定向在发下一跳之前核：总计最多3次请求；目标Host含显式端口必须与最初相同，HTTPS起点不得降到HTTP。显式HTTP起点允许HTTP或HTTPS，这是来源政策，不能说“所有重定向都必须HTTPS”。同host不等于同实际IP、无代理/会话泄露或可访问任何路径；真实资料采集仍需可信目标与地址/权限边界。503、错媒体、超量、取消和拒绝重定向都应保为获取失败，不能替换成“页面已空”。ETag/Last-Modified与304尚未实现，若扩展必须区分未改变、失败和空内容。

### 19.4 生成报告与接受基线是两个动作

单个快照Save使用同目录临时文件、写入/close后rename，并在错误时清临时名；这有利于同文件系统原子替换可见性，没有fsync/目录sync或CAS，因此不证明掉电持久性、多个writer协调或整报告组原子发布。Load先读完整文件才检查8,000,000字节上限，再核canonical URL与内容SHA；它没有完整重跑新快照的块数/规范化约束。合法保存/载入不是来源认证。

HTML用html/template按文本与URL上下文转义，JSON保确切新增/删除文字和count、两份快照与unchanged。fixture里维修从14:00变15:00、志愿名额3变1、增加无障碍入口，故删除2块、新增3块、共同3块；导航计数和footer时间被策略排除。报告给的是这些精确变化，不推断发布者意图或自动生成事实结论。无变化明确显示空列表；可加人审note/Markdown导出，通知仍属独立集成。

**源CLI有路径别名风险**：它先写out/changes.json和index.html，再无条件写 `out/baseline.json`；随后才在`--accept`时写入传入的baseline。如果`--baseline`恰好就是out/baseline.json，即使没有`--accept`，前一步也已经覆盖旧基线。教程的“没有accept就不动旧基线”只在路径隔离前提下成立，不能照抄成普遍保证。报告目录采用新的版本目录，旧基线用独立只读路径，并在写入前用真实文件身份检查别名；输出可能是符号链接，单纯比较原字符串不足。

changes.json、HTML、新快照和可选旧基线依次写，也可能部分成功。推荐先在临时版本目录生成并核全部工件，再以可信版本指针一次发布；接受旧基线要绑定已审核的新snapshot/hash、旧revision并用CAS防丢更新。失败时保旧版本并说明哪一步未完成，不把exit非零当“所有写入都撤回”。这些合同沿用第13节更强的代际发布，不另造同义监控后台。

### 19.5 可运行多重集例与四阶段练习

下面只比较**已经抽取的块**，加上抽取策略与URL身份；不提供HTML5解析器、网络客户端或基线文件写入。摘要合同是本例显式定义的Python JSON，与源Go只摘要块数组的合同不同，不能拿两个不同合同的SHA直接比较。

```python
from collections import Counter
import hashlib
import json


def snapshot(url, policy, blocks):
    if not isinstance(url, str) or not url or not isinstance(policy, str) or not policy:
        raise ValueError('调用方必须提供已核的URL与抽取策略身份')
    if not isinstance(blocks, list) or len(blocks) > 10000 or any(
        not isinstance(x, str) or not x for x in blocks
    ):
        raise ValueError('这里只接受已经抽取的非空文本块列表')
    # 重复保留，排序仅用于定义“忽略块顺序”的合同。
    ordered = tuple(sorted(blocks))
    payload = json.dumps({'url': url, 'policy': policy, 'blocks': ordered},
                         ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return url, policy, ordered, hashlib.sha256(payload.encode()).hexdigest()


def compare(before, after):
    if before[:2] != after[:2]:
        raise ValueError('URL或抽取/过滤策略变化，不能当页面正文变化')
    # 重算身份以拒绝内存对象中仅改块却保留旧摘要。
    for row in (before, after):
        if snapshot(row[0], row[1], list(row[2])) != row:
            raise ValueError('快照内容与摘要不一致')
    a, b = Counter(before[2]), Counter(after[2])
    return {'added': sorted((b-a).items()), 'removed': sorted((a-b).items()),
            'unchanged': sum((a & b).values())}


url = 'https://example.invalid/notices'
a = snapshot(url, 'paragraphs-v1/no-footer', ['A', 'A', 'B'])
b = snapshot(url, 'paragraphs-v1/no-footer', ['A', 'B', 'C'])
assert compare(a, b) == {'added': [('C', 1)], 'removed': [('A', 1)], 'unchanged': 2}
assert snapshot(url, a[1], ['B', 'A', 'A']) == a
assert compare(a, a)['added'] == []
for bad in [snapshot(url, 'different-policy', ['A', 'B', 'C']),
            (a[0], a[1], ('X',), a[3])]:
    try:
        compare(a, bad)
    except ValueError:
        pass
    else:
        raise AssertionError('策略漂移或旧摘要必须拒绝')
print('重复块计数/顺序不变/策略身份/改块旧摘要拒绝通过；没有抓取网页或替换基线')
```

2026-10-15这个新增自有例从最终Markdown提取CPU运行通过。原十个程序保字节、实际成功记录与原日期，不重复跑；源Go/CLI/httptest与网络均未执行。

| 阶段 | 实际动手输入 | 参考判据与拓展 |
|---|---|---|
| 1 抽块 | 实体/换行、head/nav/script/style/footer、属性内>、inline strong、忽略词、空/注释、重复p、残缺tag/comment/nav、<>及超量 | 正文单块和原重复次数保留；噪声不漏；坏输入显式失败。记录每站提取规则并保真实HTML fixture；footer中的生效日可能被过滤，先判断需求再改政策 |
| 2 比快照 | 大写host/fragment、fileURL/凭据/relative、AAB→ABC、重排、不同query、空快照、仅nav变化 | canonical有定义但不声称所有等价URL都合并；A删1/C增1/common2；重排指纹相同；URL不同时拒；空内容稳定但不代表抽取失败。另加顺序变化报告并说明内容SHA不是发布者/时间证明 |
| 3 抓取保存 | 受控200/503/JSON/超量、跨host/端口与HTTPS降级、取消、JSON往返/改块旧hash | 在下一跳前拒越界，原client callback对象不被改；nil默认15秒与自带0timeout区别；误改hash拒。测试本地wire也是实接线范围，不称真实站点可用。扩展条件请求，保304/失败/空页三态 |
| 4 发布 | 确切文字/count、无变化、script样文本、不可写输出、两hash/链接、baseline与out同路径 | 模板转义、JSON/HTML显示一致；新版本报告路径独立，未accept不可覆盖旧基线；制造第二产物失败时保部分写状态，不声称原子事务。加审核说明而不自动发通知 |

原当前28个Go Test定义（7/7/8/6），第三阶段另含一个redirect表驱动测试；作者录像则记录7/7/7/6共27，保留时间与源码覆盖差异。四幅JS图只对已提取 `|`块做过滤/计数、门开关和文本变化；没有实际HTML扫描、HTTP、hash或文件保存，第三图baseline replacements固定0，不能证明CLI无覆盖风险。两PNG和GIF18+6全24帧已查看，输出是人工HTML样本的浏览器滚动截图，不是当前网络状态。

来源：2026-10-15完整静读固定commit `3be078b37ffd8f0c04953c0678e48f5c6d0c7775` 的[Web Change Brief](https://github.com/rohitg00/ai-engineering-from-scratch/tree/3be078b37ffd8f0c04953c0678e48f5c6d0c7775/projects/web-change-brief)正文、实现、测试、人工HTML、provider及媒体。仅主题融合与轻量出处，不安装后台监视器，不执行原来源命令。


## 20. 从问题到可审计研究报告：检索、片段、主张与版本一起走

把第2节BM25、第3节多视角、第16节引用位置和[逐主张评测](./06-评测与实验管理.md)接成一条离线报告管道：文件语料→检索候选→研究面向→精确片段→带引用句子→支持审查→报告与追踪→独立评价。它适合技术决策草稿、资料比较和政策更新复盘。来源的Rust负责排名、Python负责证据与编排、TypeScript负责展示；语言分工不是质量保证，JSON边界必须各自有运行时合同。

### 20.1 文件、搜索进程和BM25的身份边界

每份Markdown用title/source_url/published头字段、空行和正文表示，ID由文件名stem产生；按路径排序，正文去头并strip后才定义偏移。它不是原文件字节坐标，需另保原始文件SHA和正文规范化版本。源只检查头字段存在，不拒空值、重复键后写覆盖或验证发布日期；带着官方URL的作者笔记也不自动变成该官方文档原文。导入新语料应先核唯一ID、字段类型/换行、文件范围/总量与日期，不能把header字符串当真实性证明。

源索引对标题和正文一起分词，先lower再保ASCII字母/数字并去停用词。中文和重音字符可能被丢弃，复数/同义词不会自动统一；沿用第17节的归一化经验，但改变分词器必须重建并重新评价。这里BM25的k1=1.5、b=.75；N=2时，df=2的orchard其IDF=ln1.2≈.182322，df=1的expiration为ln2≈.693147。文内TF保重复，DF每文档一次；查询重复词在这个实现中会再次贡献，而本章第2节示例按查询唯一词计分，比较两个实现前要固定此政策。

进程协议是一行JSON请求、一行JSON响应，stdout不能混构建日志；诊断走stderr，EOF退出并逐行flush。支持search/tokenize/idf/docs/doc/score。k要求0～10000的整数，0是合法空结果，1.5拒绝；未知操作/坏JSON返回结构化error。自带codec处理引号、控制字符、数字语法及Unicode代理对，但重复对象键读取**第一个**、缺递归深度限制，64KiB检查在整行已读取之后，不能宣称完整防御性JSON接口。继续采用[严格输出](./13-结构化输出与对话状态.md)的重复键、深度与分配前预算规则。

Python把生成的000000.md等内部名写入私有语料目录，恢复调用方ID后再按分数/真实ID解平局，避免临时文件排序改变外部合同。构建二进制在每进程专有 `rra-private-build-`目录、权限0700，缓存这条路径并退出清理；使用argv、退出码和超时，优于信任可预测的共享可执行缓存。**缓存的是二进制，不是常驻索引**：源码每次_request都新启Rust并重载语料，idf/search/score会重复开进程和建索引；它的stdin循环可以连续处理，但当前Python适配器没有复用它。不应据原生语言名字推断已经获得大规模性能或运行安全。

### 20.2 精确片段与四个研究面向怎样连接

分句器识别英文.!?后接空白和受支持字符或文末，保末尾无句号片段；`container.sock`内部点不应截开，句号后小写user-space可以开新句。中文句号、缩写和复杂标点不在其完整能力范围内。先在原正文找边界，再移动start/end去空白，始终有 `body[start:end] == snippet.text`。如果做去指代改写，保存原quote与改写两份，引用仍指向原跨度。

片段分数是查询唯一词在句中对应IDF之和；少于6个空白分隔单词得0，It/This/These/They等起始句乘.5，试图避免脱离上下文。这是便宜的可解释启发式：短句可能恰含关键否定，代词惩罚也不真正解析指代。按分数、doc_id、start排序，在每文档上限内选，再编号S1…；分数用于展示可round，但不能改变引用身份。

规则规划依次列Overview、How it works、Risks and limits、When to use it四面向，去掉问句开头词提subject，把原查询词与每面向补词组合。每facet有稳定ID、label/sub_question/keywords。它提供覆盖检查表，不能保证四面向都有足够证据或互相独立。

源gather先按**整个问题**选top文档一次；各facet只在这些文档中挑句，并按相对最高分的.4门限、每facet最多3句筛选。它不会让风险facet再去全库寻找漏掉的文档。跨facet按 `(doc_id,start,end)`去重，再全报告重新编号；同一个S1在另一次run可能指向完全不同的片段。若前面facet先占用某个span，后面的facet可能无句而消失，trace与评价要能展示这种覆盖损失。

### 20.3 规则、回放与在线规划不能混成同一实验

默认规则可离线。ReplayModel用 `purpose + SHA256(完整prompt)`找cassette，一字变化即miss并保调用记录；固定prompt用于复现实验，不能为了命中旧回放偷偷截掉新要求。cassette键没有绑定模型/设置，重复键后写覆盖，也没有真实性签名；正式录制继续用评测章节的完整任务/配置/采证身份。

模型返回必须是非空facets数组，每项sub_question非空字符串、keywords字符串列表，最多截取max_facets，再构造成Plan。源没有全面校验max_facets的精确整数/正值、空keyword或额外字段，合法JSON形状也不证明计划合理。验证失败保存rules-fallback及notes；一般值/类型/KeyError/AttributeError被捕获，HTTP错误/运输超时等不在这个兜底集合，不能说“任意在线失败都会正常回退”。

LiveModel只用于**规划**，正文仍是摘录排列。它发配置端点的chat-completions兼容请求、可选Bearer与timeout，源码未限制响应字节、目标/重定向或记录实际provider usage；这些能力不能从Model协议名推导。CLI的--eval分支直接用默认规则调用evaluate，未把--model参数传进去，因此不能用该CLI选项宣称做了live与replay评测对比。本轮不读取密钥、不执行模型或来源命令。

### 20.4 摘录写作只保出处，支持审查还要保关系

writer把片段按facet排成section，句子保cites，折叠空白后复制原文，末尾加 `[S1][S2].`；引用注册表好比主键，句子cites是外键。单独验证器检查句尾标记是否存在且指向已知snippet，标题不计句子；空列表仅表示这份**语法与解析政策**没有发现引用错误。源码允许句尾标点省略，不能把正文描述的“必须最后有句点”当已经严查。

摘录模式减少凭空造句，却会复制错误、过时或不适用的原句，筛掉上下文也可能改变读者理解。源码文档的“correct by construction”应限于复制/引用结构，不能解释成事实正确。若改为模型转述，继续检查来源位置、逐主张语义、当前有效性与权限；重试一次也不自动解决这些问题。

critic先核缺引用/悬空，再对每句取**最好的一条**引用词面分。它对带数字、词内大写、句中专名做严格词检查，用否定词集合拦not/no/never/cannot/without/nothing变化，其余按内容词交集比例、默认阈值.6。它不验证主宾关系/否定作用域，且所谓严格词只是source_lower中的**子串**：主张“5 destinations”对“50 destinations”可能让字符5检查通过，剩余词重合也达阈值；Alice/Bob对调亦可能全词命中。有效quote和高重合都不能代替蕴含。

threshold没有完整类型/范围预检，0可把一些0分矛盾标supported；语义拒绝类别应先硬拒，再比较合格支持分。多引用取best不能给无关引用一起记credit，沿用评测第31节逐claim–cite归因。六份公开poisoned drafts只包含实体插入、否定翻转、5↔10、无关主张、悬空/无引和两个忠实转述，不能据它们证明上述更难反例都被拦。 可将词面分在.4～.6的不确定句交独立语义judge，并把请求/回复/成本及与原判据的差异录入cassette；这只是待比较的扩展，不降低数字/权限等硬门，也不把judge自信当真值。

### 20.5 预算、终态和失败工件要逐项核到实现

源码终态定义是：预算超限或无受支持句failed；全部原verdict支持completed；部分句被删needs_review。它基于**清理前的verdict**决定，不能删除坏句后再按剩余句全部通过报completed。静态critic动画却写“completed · 2 sentences dropped”，应按实现纠正；界面绿色、文件存在和CLI返回0也不是独立目标达成。原CLI把needs_review返回0，所以消费者必须读terminal_state。

预算应在昂贵动作前预留，再按真实已知usage结算，失败/未知也入完整账本。源Budget只计步骤与估算 `max(1,len(text)//4)`，不是供应商token/费用，也未严拒bool、负tokens和非有限参数。index/plan在工作前charge，但gather与write先完成再charge，与课程的“先扣再做”建议不一致；不能把这个计数器当资源从未超支的保证。使用[资源账本](../Agentic%20Design%20Patterns/01-核心章节/16-资源感知优化.md)的更强合同。

trace按index/plan/gather/write/verify保存耗时、部分detail、run_id、开始时间、预算、counts与终态。plan详情没保存notes；verify详情只保dropped文字，不是所有逐引用verdict。源只catch BudgetExceeded，语料加载在try外，构建/HTTP/JSON/渲染/磁盘等一般异常可能直接传播，没有承诺总能留下named failed工件。

report变量直到verify后才赋已支持正文；若gather或write后才预算超限，已有候选/draft未放入report，不能声称总会把已收证据呈现在失败页面。应另存append-only尝试/证据/draft/verdict与真实失败阶段，再决定可发布子集；HTML/JSON失败时也保可回读的最小失败收据。started_at与各step ms不是完整跨进程墙钟，也不含全部发布耗时。

### 20.6 出版物和来源更新用同一证据身份

version1 payload包含question、sections、snippet注册表、documents及trace。TS类型只提供静态说明，JSON仍须运行时验证每个cite能解到snippet/doc、码点区间合法且原文切片相等；JS使用 `[...source.text]`对齐Python码点。首次出现的cite编号一次，多次引用用独立tooltip ID；hover或键盘focus看quote，脚注跳转，details展开追踪。所有文本按HTML上下文转义，来源链接仅HTTP(S)，不能只escape一个javascriptURL。 打印版可让脚注避免跨页断开，并明确展开哪些追踪内容；屏幕hover可读不保证打印时证据完整。

源viewer仍有边界：重复doc ID被Map后写覆盖；snippets只检查typeof object而非严格映射；没有全面核score、trace和所有字段类型；允许空span，end超正文长度时JS slice可截断，若碰巧等于quote仍可能通过。应先核 `0 <= start < end <= 码点长度`、snippet.id与映射key、唯一doc/cite及全schema，再展示；slice相等仍不认证发布者、语义、有效时间或访问权限。

write_outputs顺序写HTML、trace、report.json，compare后再写changes.json；不是一组原子提交。使用第13节冻结证据/同代发布，避免读到新页面配旧trace。compare_reports要求相同question/version，只按句子文字合并证据列表，列added/removed、同文字changed_evidence；引用序号S1变化本身不是证据变化，真实跨度/片段SHA才是线索。源比较未重核payload切片/权限，也未绑定完整doc revision，证据列表顺序变化可能触发changed，需区分身份、顺序与实际内容。

具体小例：同问题“How long do Orchard guest tokens last?”，旧正文第一句说60分钟、新正文说15分钟，则旧句在removed、新句在added。即使两run都显示[S1]，也不能把它们当同一证据。另一个restore文档和guest文档第二句没变，若同文字的doc跨度或revision变了，仍需回看证据。两份人工文档头日期同为9月28日，不能据日期字段宣布新版本今天仍生效。

### 20.7 公开87.5分怎样计算，怎样被误读

源码按每问题宏平均：citation_precision用.8阈值（比critic .6严格），source_recall用预期doc集合，fact_coverage用同句包含金标词组；加权.4/.3/.3。六公开问题的precision都1、recall五个1一个.5、facts为1/1/1/.5/.5/0，均值为1、11/12、2/3；得100×(.4+.3×11/12+.3×2/3)=87.5。中间round与终值round属于显示合同，不宜只拿印出的.92/.67反算。

source_recall直接从注册表全部snippets取doc，未逐实际引用/支持重新归因；fact coverage不筛真实语义。一般外部构造Report可能插没实际引用的snippet赚credit，错句也可能赚fact，需改用可信已核claim–cite链。空expected_docs或key_facts时该项目给1，和本库“缺标签为null/unavailable”的协议不同，不能无声混比。报告只发一句安全话可提高precision却遗漏事实，复制全库又会伤可用性，各分量/分母/缺标/终态须同时保。

heldout目录名是历史名，六题和poisoned drafts全公开，demo正好复用h4。同一实现根据这些题反复改再得高分，是公开回归，不能叫盲测或泛化。要测新语料，由独立人员另建问题/完整金标，先冻结检索、规划、阈值、分母与运行配置，逐题保失败和关键类别；可读性另评，不混成词面grounding分。图里的可调scorecard使用.5/.25/.25、空标签null重归一，和后端.4/.3/.3、空标签1完全不同；图算出的数不能当后端验收值。

### 20.8 七阶段实践与可核对结果

| 阶段 | 独立实施前先预测什么 | 参考判据与失败反例 |
|---|---|---|
| 1 语料与进程 | 12份头/正文/ID、两个TF与DF、JSON请求响应、相同分数真实ID顺序 | 缺头拒；df稀有词权重大；socket检索回预期doc；OOV空；badJSON/Unicode代理/k1.5拒、k0空。私有0700 binary且stdout仅JSON；再查重复键/深度/字段换行和进程重建成本，不把私有目录当沙箱 |
| 2 片段 | container.sock内部点、句号后小写、末尾无句号、空白偏移、每doc上限与S5起编 | 精确slice复现每quote，偏移属于strip后正文；短/代词句降分仅启发式。加原文前插入emoji、中文标点、关键短否定句与邻句context；改写不要覆盖原quote |
| 3 规划 | 同question两次规则plan、max2、cassette完整prompt/purpose、好JSON/聊天文字/miss | 好录制3facet/source=model；坏形状或miss为rules-fallback且留notes。空facet要拒而非静默成功；HTTP超时不在源四类fallback。额外录制器须完整模型/设置/usage身份；本轮不连服务 |
| 4 引用写作 | facet共用span、全局S编号、每section句数、未引句与S99、源码句与quote | 只有实际片段进正文，去重不冒独立证据；语法错误uncited/dangling。合法标记不证明关系/事实，把两个片段合一句时逐主张核支持，模型改写的验证器仍独立 |
| 5 审查与预算 | 六公开poisoned drafts逐句bool、两步预算第三charge、good/mixed/empty | 插实体/否定/5↔10/悬空拒；全支持completed、mixed needs_review、空failed。再试5↔50、Alice/Bob倒置、threshold0和负tokens，先定类别硬门及完整ledger；不要只调词重合让fixture全绿 |
| 6 出版与变化 | Python/TS emoji偏移、重复cite一个脚注多tooltip、危险URL/文本、tinybudget、60→15更新 | 先核schema/唯一ID/严格区间/quote再HTML；safeURL拒可执行scheme，trace可键盘查。一般异常、预算后扣/丢partial和三文件部分写单独保失败；同question保changed_evidence，不只看[S1] |
| 7 评价 | toy precision.5/source recall.5/fact.5；单题(1,.5,0)权重55；公开六题表 | 逐题分量与weighted宏均值保，87.5仅公开fixture历史；空标签协议显式，注册表不赚无引用credit，独立新语料/私有问题冻结后才谈泛化。改可读性评分也不能覆盖grounding退化 |

本节直接复用本章已有BM25、精确来源链、引用支持、代际发布与完整评价程序，不重建另一套Rust/Python/Node框架。来源82个测试定义（Rust7、Python68、Node7）与原断言、87个真阶段标题、78个项目文件/人工语料和全部8个最后注册图已静读；两PNG及GIF20+9全29帧已视读，作者历史4section/10句/trace五步/874估算tokens不冒本轮执行。八幅图的装饰分数、坐标和流程部分硬编码；输入实验有数学与形状校验，但没有执行Rust/模型/FS，动画“completed删句”与后端状态、图的评分权重差异已明确。

补充读懂12份安全语料：denylist不替隔离；容器共享宿主内核，资源cgroups、daemon控制权、挂载、capabilities分别审；用户态应用内核、microVM/虚拟化容器与远端会话是不同边界；密钥代理不把key交Agent，仍需可信目的与出站限制；会话生命周期controller不自行实现隔离；临时任务结束还要撤销凭据/状态。这些原理接到[安全模式](../Agentic%20Design%20Patterns/01-核心章节/18-安全模式.md)。作者安全笔记中的泛RFC链接不充分支撑每个具体产品机制，不能用seccomp文档替用户态内核架构；已另核[Docker daemon控制面](https://docs.docker.com/engine/security/#docker-daemon-attack-surface)、[gVisor应用内核](https://gvisor.dev/docs/architecture_guide/intro/)和[Firecracker设计](https://github.com/firecracker-microvm/firecracker/blob/main/docs/design.md)指定段（2026-10-15），保“隔离不自动执行出站过滤/不保护已授权数据”边界，不收录旧型号、性能与安装流程。

来源：[Research Report Agent](https://github.com/rohitg00/ai-engineering-from-scratch/tree/3be078b37ffd8f0c04953c0678e48f5c6d0c7775/projects/research-report-agent)，固定commit与其余本次来源相同，2026-10-15完整读后主题融合。原source/CLI/tests/grader/Rust/Node/模型/API/网络/安装均0执行；原11个Python示例保持字节及持久实际成功原日期，不重复运行。

## 21. 框架化检索配置：索引就绪、候选预算与原文版本

前面的算法和证据合同不依赖某个框架；当它们进入Agent配置，需要再核一层实际执行。第一来源Docker Agent1.149.0的schema提供BM25、chunked-embeddings与semantic-embeddings三类策略，以及候选、融合、重排和全文返回字段。本节按2026-10-18读到的固定快照解释配置含义，没有运行框架或模型。

共享docs与每策略docs共同决定输入，respect_vcs还可以在策略级覆盖。遵守.gitignore只是采集规则，不是用户权限；被忽略文件未进索引，不证明其它filesystem工具不可读。semantic-embeddings可能额外调用chat model生成语义表示，除embedding还要记录模型、提示、并发、费用和派生版本；生成的摘要须回接原文，不能直接充当原文主张。

chunk size/overlap在该配置中是字符单位，vector_dimensions须和真实embedding输出一致；仅模型名称相同不能保证维度、归一化和预处理一致。代码感知分块可回退普通文本，勾一个code_aware不证明每种语言都完成AST解析。

每策略limit控制进入融合的候选数，最终results.limit不能凭空补回没召回的证据。例如两个策略各只取5条，设置最终top15不保证能得到15条，去重后可能更少。RRF按排名融合，原始加权分数要统一尺度；BM25阈值与余弦阈值不可照抄同一个数字。重排的top_k可能限制参与重排范围，不能误作总召回；criteria在原生重排后端不一定被采用。

索引初始化超时、单次索引任务上限与查询timeout分开。来源配置说明索引可在短启动等待后继续后台工作，工具就绪前不应把查询空结果记为语料无答案；保留building/ready/failed、代际与文件进度。并发索引/embedding/摘要会放大资源与限流压力，不能把三个concurrency字段当同一个总并发上限。

return_full_content按文件系统重新读全文时尤其要检查：用于召回的旧chunk与返回的新文件可能不是同一revision。按照第13节冻结代际和权限，在组装上下文前核原文版本/摘要/跨度，变化则重新索引或明确拒绝混用；再增加全文大小与上下文预算，不能无限展开。

Agent response cache的“相同问题重放答案”也不替本章第14节的权限/版本缓存合同。配置存在、schema接受、索引Ready、召回有分、出处精确、主张被支持和当前主体获准读取，必须分别留下证据。

参考判断：一个问题返回0条，后台仍在建索引，能否标“知识库没有相关资料”？**不能**，这是就绪状态未满足。索引记录A版本、全文读取变成B版本，能否给A的偏移配B正文？**不能**，应核版本并保持同代读取。

来源：第一来源固定`1a8c4fd5f5b3012e50e111f694b4d84df8a4eb1e`的Docker手册附属schema，对应[Docker Agent固定1.149.0配置](https://github.com/docker/docker-agent/blob/bf4169cdd31229d52385410c52c3dcc59b497858/agent-schema.json)，2026-10-18经官方GitHub API核字节相同。这里复用本章已有BM25/RRF、分块、评价、代际和权限程序，不重跑旧例；供应商型号、价格和临时默认不作为当前选型建议。


### 嵌入式构建通过不等于解析器可用

第一来源Docker Agent Go SDK正文（2026-10-08固定快照，2026-10-18整理）说明，关闭cgo后tree-sitter可用stub编译通过，但第一次解析才返回运行错误；从registry移除RAG又可能仅产生load warning。因而编译、配置加载、依赖Ready、文档解析、索引完成与可检索是不同验收点。消费者应读取warning，要求必需路径实际可用，不能在检索缺失时默默把空结果当“文档没有答案”。该限制为来源固定实现说明，本轮未编译SDK/加载parser，沿用本章已有合同例，不重跑旧程序。

### 永久停用策略可能把一次限流变成长期降级

同一来源Docker Agent RAG独立工具页把429与400/401/404一起作为该版permanent model error：索引中止，reranker可在manager存活期内持续关闭。429通常是资源/窗口限制，不能因此写成“模型配置永久无效”的通用结论。实际服务按错误code、Retry-After/配额、总deadline与任务幂等决定恢复；检索返回未重排结果时应显式报告degraded与生效版本，不能仍标“重排成功”。

来源还笼统声称LLM语义摘要embedding质量更高，实际需在相同任务/语料与代价下评测。摘要可能遗漏精确标识符，BM25与向量分数尺度不同，weighted/max不能无校准混比；RRF按rank融合不等业务相关性已验证。chunking.size在该配置按字符而非token，cosine也不普遍限0–1；threshold默认值不能跨策略当概率门。索引/候选/重排/final limit与return_full_content的已有合同继续在本节主干维护，避免再复制一套配置。

以上来自2026-10-08固定文档，2026-10-18静态对照；没有调用embedding/reranker或重跑旧例，不把作者的支持/质量标签当当前原厂验收。
