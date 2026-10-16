# 第 14 章：知识检索（RAG）

> 来源：<https://adp.xindoo.xyz/chapters/>  
> 整理语言：中文  
> 整理更新：2026-10-02；含原理、教学例子与自检。示例不是生产部署验收。

## 本章定位

通过检索外部知识并注入上下文，提高回答的事实性、时效性与领域覆盖。

## 最小 RAG 闭环

RAG 是“检索证据后生成”，不是保证正确的开关。最低结构为：文档及版本 → 可追溯分块 → 检索候选 → 必要的重排与权限过滤 → 带来源的上下文 → 回答与引用核对。即使没有向量数据库，全文搜索或 BM25 加生成也可以构成 RAG。

## 具体例子：两份版本相反的制度

文档 A（已失效）写“每次上限 100”，文档 B（当前有效）写“每次上限 120”。问题问现行标准，语义相似度可能把 A 排在前面。因此索引还需保存生效日期、有效状态和权限；生成前确定采用的版本，并引用支持 120 的具体段落。只有 A 可访问时，应说明版本限制，不能假装已确认现行数值。

用三类问题验收：答案在单段中、需要跨段组合、库中无答案。逐题保存期望证据 ID、实际检索 ID、最终答案和引文。没有证据时允许回答“现有资料不足”；HyDE 生成的假设文本用于找文档，不能自己变成引用证据。

## 自检与核对

**问题**：答案错时，应先增大 top-k 还是换模型？

**核对**：先看正确证据是否被解析和索引、是否进入上下文、模型是否正确使用。漏召回才针对检索改进；证据已经足够则检查生成和冲突处理。盲目增大 top-k 可能引入旧版噪声并增加成本。

## 来自《深入理解 AI Agent》的增量吸收

- RAG 管道包含文档分块、稠密检索、稀疏检索、混合检索和结果注入，不应只等同于“向量数据库”。
- 知识组织可从扁平文本扩展到结构化索引、文件系统范式和知识图谱。
- **Agentic RAG** 将检索变成 Agent 可主动调用和迭代的工具，使其能判断何时检索、检索什么、是否需要再次检索。
- 进一步可加入上下文感知检索、知识更新机制、用户记忆融合和深度知识抽取。

完整来源：[第 3 章 用户记忆和知识库](../05-来源保全/深入理解%20AI%20Agent/source/book/chapter3.md)

## 来自《动手学大模型应用开发》的增量吸收

### 数据进入知识库前

- **区分结构化与非结构化数据**：CSV、数据库表、Markdown、PDF、PPT、Word 等应根据自身结构选择解析方式，同时保留有用的 metadata，避免把所有文件先粗暴转成一段纯文本。
- **先清洗再索引**：去除重复、无意义噪声和解析残留；涉及用户或业务数据时，在进入向量化和日志链路前完成必要的敏感信息脱敏。
- **索引、检索、生成分层**：把文档处理与建索引、Query 检索、基于证据生成答案视为三个可独立调试的阶段。

### 分块不是固定参数

常见方法包括固定长度、字符/递归字符、按文档结构、按 Token 约束和语义分块。没有一种方法天然最好：

1. 分块首先不能超过所用 Embedding 模型的有效输入范围；
2. 一个块尽量保持语义完整，避免同时混入多个无关主题；
3. `chunk_size`、重叠量和分块方法必须在自己的语料与问题集上测试；
4. 评估应关注召回表现，而不是凭经验固定使用某个长度。

**结论：分块策略本身是需要评估的检索参数。**

### Embedding 模型怎么选

不要只看某个排行榜名次。至少同时考虑：

- 目标语言与业务领域；
- 检索任务上的表现，而不是只看综合分；
- 最大输入长度与向量维度；
- 本地算力、时延与吞吐；
- 数据是否允许发送到外部 API；
- 成本与部署维护复杂度。

MTEB 等公开基准适合做初筛，但最终仍应在自己的检索集上验证；公开榜单不能替代领域评估。

### Query 对齐

用户原始问题未必是好的检索 Query。可按失败类型选择：

- **Query 改写**：把口语、错别字、含糊表达或多轮指代改成独立、明确的检索问题；
- **Multi-Query / 子查询**：对模糊或多维问题生成多个检索视角，提高覆盖；
- **HyDE**：先生成“假设性答案/文档”再做向量检索，用于 Query 与文档表述差异较大的场景；
- **Step-Back**：先抽象出更高层问题，再结合原问题检索，适合部分复杂推理场景。

同一虚构退款问题的独立改写、Multi-query与子问题拆解、HyDE错数值反例、Step-back双检索及Q-D重排例，见 [工程12第3.1节](../../LLM%20工程实践/12-文本检索与RAG文档工程.md#31-一个问题的改写多视角拆解hyde与step-back)。它们共享原问题的必需事实和权限边界。

这些方法都可能增加调用次数、时延和噪声，因此**不要默认全开**。先建立直接检索基线，再只针对已经测出的召回缺口启用对应策略，并保留原始 Query 以便回溯。

### 实用 RAG 调试顺序

```text
数据解析 → 清洗/脱敏 → 分块 → Embedding → 索引
                     ↓
用户 Query → Query 对齐 → 检索 →（必要时重排）→ 上下文 → 生成
                     ↓
                 独立评估
```

先定位是数据、分块、Query、检索还是生成阶段的问题，再做局部优化。

来源：<https://datawhalechina.github.io/llm-universe/#/>（仅吸收经时效审计后仍有效的 RAG 方法）

## 有界 Agentic RAG：动作、证据状态与终止

Agentic RAG 把改写、再检索、重排或父段扩展变成可选择的读操作。每项动作须保留原任务、查询及证据版本、权限和消耗，不能因为“回答还不够好”无限循环。动态图 agentic-rag-loop 只有固定6秒的轨道动画，代码没有检索、judge 或终止逻辑，不能当已实现系统。

下面使用明确的动作计划和检索表，不调用模型。support 标签是人工 fixture，验证的是控制流：证据有效/权限正确且主张支持才结束；重复无增益、动作/次数/调用预算耗尽或无证据都给明确状态；禁止动作在执行前拒绝。真实控制器需要独立核验标签来源及读操作实际范围，引用和最终答案仍按 [工程12](../../LLM%20工程实践/12-文本检索与RAG文档工程.md) 追溯。

```python
import hashlib, json

ALLOWED={'retrieve','rewrite','rerank','expand_parent'}
def bounded_rag(question,plan,tools,max_calls=4,budget_calls=4):
    if not isinstance(question,str) or any(type(n) is not int or n<=0 for n in (max_calls,budget_calls)):
        raise ValueError('任务和调用上限')
    query=question;evidence=[];seen=set();trace=[];calls=0
    for action in plan:
        if action not in ALLOWED or action not in tools:
            return {'status':'blocked_action','trace':trace,'calls':calls}
        if calls>=max_calls:return {'status':'call_limit','trace':trace,'calls':calls}
        if calls>=budget_calls:return {'status':'budget_limit','trace':trace,'calls':calls}
        # 本例scope由控制器固定，计划/来源文本不能修改。
        result=tools[action]({'original_question':question,'query':query,'scope':'public','evidence':evidence})
        calls+=1
        if not isinstance(result,dict) or set(result)-{'query','evidence','intent'}:raise ValueError('工具结果合同')
        if 'query' in result:
            if action!='rewrite' or result.get('intent')!='enterprise-refund':raise ValueError('本fixture只支持指定意图改写')
            query=result['query']
        if 'evidence' in result:
            evidence=result['evidence']
            if not isinstance(evidence,list) or any(set(e)!={'id','revision','scope','current','support'} or
                    type(e['current']) is not bool or e['support'] not in {'supported','unsupported','unknown'} for e in evidence):
                raise ValueError('证据结构')
            valid=[e for e in evidence if e['scope']=='public' and e['current']]
            fingerprint=hashlib.sha256(json.dumps(valid,sort_keys=True).encode()).hexdigest()
            if valid and all(e['support']=='supported' for e in valid):
                trace.append({'action':action,'query':query,'valid_evidence':valid})
                return {'status':'supported_fixture','evidence':valid,'trace':trace,'calls':calls}
            if fingerprint in seen:
                trace.append({'action':action,'query':query,'valid_evidence':valid})
                return {'status':'stalled','trace':trace,'calls':calls}
            seen.add(fingerprint)
        trace.append({'action':action,'query':query,'evidence_ids':[e['id'] for e in evidence]})
    return {'status':'plan_exhausted','trace':trace,'calls':calls}

def retrieve(state):
    if state['query']=='企业客户当前退款期限':
        return {'evidence':[{'id':'current','revision':'r2','scope':'public','current':True,'support':'supported'}]}
    return {'evidence':[{'id':'old','revision':'r1','scope':'public','current':False,'support':'unknown'}]}
def rewrite(state):
    if state['original_question']!='企业退款时间':raise ValueError('有限改写不处理其他任务')
    return {'query':'企业客户当前退款期限','intent':'enterprise-refund'}
def identity(state):return {'evidence':state['evidence']}
tools={'retrieve':retrieve,'rewrite':rewrite,'rerank':identity,'expand_parent':identity}
ok=bounded_rag('企业退款时间',['retrieve','rewrite','retrieve'],tools)
assert ok['status']=='supported_fixture' and ok['calls']==3
assert bounded_rag('企业退款时间',['retrieve','retrieve'],tools)['status']=='stalled'
assert bounded_rag('企业退款时间',['retrieve','rewrite','retrieve'],tools,budget_calls=2)['status']=='budget_limit'
assert bounded_rag('企业退款时间',['retrieve','rewrite','retrieve'],tools,max_calls=2)['status']=='call_limit'
assert bounded_rag('企业退款时间',['publish'],tools)['calls']==0
assert bounded_rag('企业退款时间',['retrieve'],tools)['status']=='plan_exhausted'
def private(state):return {'evidence':[{'id':'staff','revision':'r1','scope':'staff','current':True,'support':'supported'}]}
assert bounded_rag('企业退款时间',['retrieve'],dict(tools,retrieve=private))['status']=='plan_exhausted'
print('有界动作',ok['status'],'调用数',ok['calls'],'；停滞/预算/调用上限/权限与禁止写动作通过')
```

identity 重排/展开只演示允许的动作接口，没有实现实际 cross-encoder 或父段扩展算法；该算法由工程12维护。人工 supported 标签不能升级为真实自动 judge。真实多事实问题还须在控制器外锁定必需主张集合，逐项覆盖，不能因为“返回的一条证据受支持”就认为所有要求完成。

停止时保留原因：无可用证据、权限限制、上下文预算不足、反复同结果、判断未知或调用失败。基线一次检索已足够时不必循环；改写和HyDE可能引入偏差、费用和额外泄漏范围，保持原问题与证据快照。语义效果与真正模型调用本批未测试。

增量来源：AI Engineering from Scratch 固定提交 3be078b37ffd8f0c04953c0678e48f5c6d0c7775，Phase11第06/07课，完整阅读及本地控制流验证2026-10-07；上文2026-10-02的原有来源与边界保留。
