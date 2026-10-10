# 附录 C：智能体框架选型检查

框架通常封装模型调用、工具调度、状态、图/循环编排、持久化与追踪。先实现能描述清楚的最小流程，再判断哪些能力值得交给框架；框架名字和下载量不能保证适合任务。

| 需求 | 应检查的能力 | 最小验收 |
|---|---|---|
| 固定流程 | 条件分支、类型约束 | 错误分支不继续执行 |
| 长任务 | 检查点、恢复、任务状态 | 中断后从已确认位置继续 |
| 工具调用 | 参数校验、权限、结果关联 | 错参数被拦截且可定位 |
| 多 Agent | 隔离、消息、合并 | 不覆盖彼此结果 |
| 生产维护 | 日志、版本、导出、测试 | 能重放一次失败 |

选型试验只需一个真实小任务：两步处理、一次工具失败、一次人工补充。比较自写简单程序与候选框架在可解释性、代码量、状态恢复、成本和依赖复杂度上的差异。若没有实际收益，简单程序可以是最终方案。

**自检**：框架声称支持 memory，是否自动解决隐私、过期与冲突？**核对**：通常只提供存储/读取机制，记忆策略仍需设计，参见[记忆管理](../01-核心章节/08-记忆管理.md)。

更新：2026-10-02。保留原附录路径；不列未经本任务实测的品牌排名，具体框架 API 应按选定版本核验。


## 用机制清单替代品牌决策树

先记录是否需要运行时schema、typed state、session memory、持久恢复、人工输入、并行合并、取消/deadline、副作用幂等、trace/export与数据边界，再用相同mock model/tool尝试。单agent也可能需要持久状态，两次调用也可能处理长等待/批准；角色或对话只是表达方式，不是厂商独占能力。源码first tiny branch遗漏has_typed_state/needs_session_memory，使“1call但有状态”仍被说成no state；没有最少node/用户数/固定framework overhead适用于所有负载。

下面脚本输出**应验收的能力**而非未测试品牌排名，接口字段含源八项，拒绝bool冒充call数/负数/遗漏未知字段。两个不同描述可有相同能力要求；具体框架是否通过这些要求由独立适配/故障试验判断。

```python
FIELDS={'has_typed_state','has_roles','has_dialogue','has_parallel_fanout','needs_resume','needs_human_interrupt','total_llm_calls','needs_session_memory'}
def requirements(p):
    if type(p) is not dict or set(p)!=FIELDS:raise ValueError('完整任务描述')
    if type(p['total_llm_calls']) is not int or p['total_llm_calls']<1 or any(type(p[k]) is not bool for k in FIELDS-{'total_llm_calls'}):raise ValueError('bool能力/正整数调用数')
    need={'schema_and_failures'}
    if p['has_typed_state']:need.add('validated_state')
    if p['needs_session_memory']:need.add('scoped_session_store')
    if p['needs_resume']:need.update({'durable_checkpoint','idempotent_effects'})
    if p['needs_human_interrupt']:need.update({'approval_version_binding','durable_checkpoint'})
    if p['has_parallel_fanout']:need.update({'parallel_merge_contract','cancel_and_deadline'})
    if p['has_roles'] or p['has_dialogue']:need.add('message_and_result_correlation')
    simple=p['total_llm_calls']<=2 and need=={'schema_and_failures'}
    return {'prototype':'普通函数链' if simple else '显式状态与适配层','acceptance':sorted(need)}
base={k:False for k in FIELDS-{'total_llm_calls'}};base['total_llm_calls']=1
assert requirements(base)['prototype']=='普通函数链'
for flag,cap in [('has_typed_state','validated_state'),('needs_session_memory','scoped_session_store'),('needs_resume','durable_checkpoint'),('needs_human_interrupt','approval_version_binding'),('has_parallel_fanout','parallel_merge_contract'),('has_dialogue','message_and_result_correlation')]:
    chosen=requirements(dict(base,**{flag:True}));assert chosen['prototype']!='普通函数链' and cap in chosen['acceptance'];print(flag,chosen)
for count in [True,-1,0]:
    try:requirements(dict(base,total_llm_calls=count))
    except ValueError:pass
    else:raise AssertionError('非法calls')
print('七个独立任务形状及typed_state/session_memory漏判反例通过；未测任何框架性能')
```

## 同任务对照与来源练习

先比较普通函数链与显式状态机：同样三条fake tool结果、一次瞬态失败、一个人工拒绝、进程重启和并行同key冲突；再接候选框架，用其当前SDK测试checkpoint、schema、访问/删除、事件关联和已完成task重放。外部token成本、框架CPU时间、尾延迟、状态大小与维护依赖分别量，代码行数不等可靠性。LangGraph的reducers/Send/checkpointer机制见[人机协同](../01-核心章节/13-人机协同.md)，memory治理仍接原主章；框架抽象不能代替权限、安全与生命周期。

源第17课三练习：①LangGraph/CrewAI同任务brief的真实token账单和行数未测；②AutoGen/Agno四框架成本/恢复/approval排行未测，官方能力介绍只作候选实现入口；③八字段决策树上面给完整替代和七种形状，不预设LangGraph唯一拥有fanout/durable、Agno最多四worker或任何固定DAU门槛。AutoGen旧ConversableAgent/GroupChat与Microsoft新包接口须分版本，AG2不是随意换名；不得直接复制旧install/API流程。

原五quiz的长期答案：恢复+批准+fanout要找并验证这些机制，品牌不是唯一；LLM路由只有实际增加planner调用时才多那笔token费，显式路由也有工程成本；proposer/critic可用消息协议实现，非某框架独占；session memory需实测scope/持久化/删除而非存储驱动名单；tiny任务可优先普通程序，但typed state/memory/权限不能因调用少就删掉。`framework-matrix`静态图与`l5-framework-fit`动态图四个固定graph/orgchart/chat/agent面板及6秒fade是人工对照，未测框架能力、overhead或成本，不作独占性结论。

增量source固定3be078b Phase11第17课，原完整阅读2026-10-06、判断程序执行2026-10-07。没有安装四框架/调用模型/跑框架性能，旧2026-10-02检查表与学习边界保留。更新时先记录任务变化，再核选定官方版本与故障验收，不按宣传排行追加依赖。

## 状态图、Actor、角色团队与托管循环怎样承担不同责任

以下补充第一来源 Phase14 第13–18课。先修是工具参数合同、状态更新、错误处理和[人机协同](../01-核心章节/13-人机协同.md)。同一个“研究→写作→审核”任务可以使用图、消息或角色团队表达；比较时要问谁拥有下一步、失败怎样传播、哪个状态能恢复、谁检查外部副作用，而不是比较角色名称。

### 第13课：有状态图的执行与恢复

图由状态、节点和边组成。状态保存本次任务需要的业务事实；节点读取状态并返回更新；普通边描述固定后继，条件边根据当前状态选择后继。类型提示帮助编写与检查代码，运行时还要校验输入和更新。节点可以执行模型或工具，不能把“节点都是纯函数”当框架强制保证。

以工单为例，分类写入 `route`，对应分支生成草案，人工门禁读取草案与版本，发送节点执行已获授权的内容。低置信度应转为 `waiting_for_human`，保存待审对象，再由人工补充路线。直接走 END 后重新开始一个任务，与恢复原待审任务的状态语义不同。多个节点并行写 `messages` 时，需要明确 reducer 是追加、去重还是冲突拒绝；两个分支都把 `status` 覆盖为自己的结果，不能仅靠 typed state 避免丢失更新。

检查点保存可恢复状态及调度信息。LangGraph 的持久化按 **super-step** 形成检查点，并可记录已完成节点的 pending writes；恢复也可能从某个节点或 task 的起点重放。它不是“每个 Python 语句保存一次，永远从 N+1 精确继续”。节点内随机数、时间、外部读取及副作用要按运行时的 task/持久化合同处理，已提交外部动作仍需幂等键和回读。完整机制与本地重启例复用[人机协同](../01-核心章节/13-人机协同.md)，这里不复制第二套恢复实现。[官方持久化](https://docs.langchain.com/oss/python/langgraph/persistence)、[持久执行](https://docs.langchain.com/oss/python/langgraph/durable-execution)。

Supervisor 由中心决定下一位专家；swarm 让专家彼此移交；hierarchical 把子图组织为层级。选哪一种取决于路由变化、观察范围和失败责任。减少中心节点可能减少某次调度调用，也可能增加循环与协调成本，必须按同任务轨迹比较。Streaming 是运行中暴露消息、更新或事件，并不自动把每个流式 token 写成可恢复业务状态。

#### 第13课：构建、使用与交付

原 Build It 的 Python/TypeScript 用字典和内存副本演示 classify→branch→human gate→send。名称 `SQLiteCheckpointer` 不代表真正 SQLite；没有数据库序列化、进程重启、并行 reducer 或完整 stream。Use It 提供图与其他运行时的候选入口；Ship It 的生成蓝图可转换为状态、分支、持久化、权限和故障验收清单。`langgraph-state.svg` 与 `langgraph-state` 动态图解释分支和恢复位置，7个固定演示步骤没有调用真实 checkpointer；图中“逐节点精确恢复”按上面的 super-step 边界修正。

#### 第13课：五项练习与参考答案

1. **低置信度人工改路由**：设分类阈值后进入待审状态，保存 route 候选、草案版本与待审原因；人工设置 route 后校验枚举并恢复。答案要证明拒绝/超时不发送，不能只展示正常分支。
2. **换真正 SQLite 并量开销**：配置实际持久化后端，用独立进程恢复同一任务；分别测序列化、事务写入和总 super-step 时长。源内存副本不是这个实验，本轮未安装或运行 SDK。
3. **并行边与 reducer**：两分支返回独立更新，例如按证据 ID 合并而非后写覆盖；同 ID 不同内容应明确报冲突。不可变输入减少共享对象被修改的风险，但并不提供事务或副作用隔离。
4. **迁入 supervisor**：保持同样分类、人工门禁和失败场景，比较中心路由新增的模型调用、专家输入以及父子 trace。迁移验收是合同一致，不能只看 API 更短；本轮未做框架迁移。
5. **流式更新**：为事件附 run/node/sequence，区分临时进度与已提交状态；制造失败后检查最后已提交点。打印 delta 不等于恢复数据库已经持久化该 delta。

#### 第13课：七题自检与答案

1. **图把什么作为核心？** 状态与转换：有类型描述的状态、节点和条件边；运行时校验与节点纯度需要另行实现。
2. **持久执行解决什么？** 长流程中断后根据已保存进度恢复，减少从头重做；恢复粒度由运行时合同决定。
3. **哪项不是本课三种拓扑？** Gradient ring；本课讨论 supervisor、swarm、hierarchical。
4. **为什么处理未捕获的非确定性？** 同输入重放可能得到不同结果；随机、时间及外部结果应持久化或隔离到支持恢复的 task。
5. **条件边是什么？** 用状态计算后继；过多交叉条件会使停止与错误路径难审阅。
6. **检查点只存聊天有什么风险？** 工具结果、业务更新、待审对象及调度信息可能丢失；外部副作用还须单独回读。
7. **人工介入放在哪里？** 在关键动作前暂停，呈现当前对象和版本，接收修改/批准/拒绝，再按原任务恢复。

### 第14课：Actor 的消息合同与失败传播

Actor 的设计原则是让状态由对应实体管理，通过消息交互。消息至少区分 sender、recipient/topic、message ID、任务关联、payload schema、deadline 和处理结果。私有状态是设计约束，不是同进程 Python 对象自带的内存安全沙箱；把可变对象引用共享给多个 handler 仍会发生污染。异步 runtime 也不自动提供分布式传输、可靠投递、去重或重启恢复。

AutoGen Core 提供消息与 runtime，AgentChat 提供对话/团队编排，Extensions 提供模型、执行器等集成。Core 的 runtime 管理 Core agent 实例；直接创建的 AgentChat agent 如要接入 Core，需 wrapper。RoundRobin 固定轮换发言，Selector 根据当前任务选择发言者；Magentic-One 是浏览、代码和文件工作的一种参考团队，不是另一个基础模型。[官方 runtime](https://microsoft.github.io/autogen/stable/user-guide/core-user-guide/framework/agent-and-agent-runtime.html)。

两种发送语义不能混用。`await send_message(...)` 等待接收 handler 的返回值，handler 异常可传播回发送方；`await publish_message(...)` 等待调度发布，返回 None，订阅者处理异常记录后不回传给发布者。故障隔离取决于所选语义、异常策略及重试设计，不能将二者概括为“send 永远立刻返回，发送方从不受影响”。DLQ（死信队列）保存无法正常处理的消息及原因，重放前要检查重复副作用。[官方通信](https://microsoft.github.io/autogen/stable/user-guide/core-user-guide/framework/message-and-communication.html)。

#### 第14课：构建、使用与交付

源程序是同步全局 deque，`receive` 仍在同一执行栈内；不能据此宣称并发 actor 或分布式故障隔离。三条消息就宣布共识也缺少任务关联、重复票和截止时间。`actor-mailbox` 图显示 mailbox 与轮转，是调度意图，不是 transport 性能证据。Use It 的运行时名单用作候选：2026-10-09 官方 AutoGen README 明确 maintenance mode，并建议新项目考虑 Microsoft Agent Framework；源“只在 preview”不作为当前状态。Ship It 蓝图要补关联 ID、投递语义、取消、消息预算与 DLQ，而非只生成角色列表。[AutoGen 当前仓库说明](https://github.com/microsoft/autogen)。

#### 第14课：五项练习与参考答案

1. **DLQ**：记录消息 ID、关联任务、失败类型、尝试数和脱敏摘要；同时报告总投递/失败数。内存 DLQ 只能演示，handler 已发出的副作用不会因异常自动回滚。
2. **SelectorGroupChat**：显式定义选择输入、可选 agent 集、无候选与循环停止；对“专家连续拒绝”和“已完成专家被重复选择”给反例。
3. **分布式 transport**：设计 JSON schema、身份认证、确认/重试、去重、版本兼容和 deadline。换成 HTTP 并不实现可靠队列；本轮只保留方案，未起服务。
4. **每条消息一个观测**：关联 send/publish/process 的因果 ID，选适用 operation；用 NoOp 只能验证接口，不是 collector 成功。AutoGen 有原生 OTel 支持，但 exporter/SDK 仍需配置。[官方 telemetry](https://github.com/microsoft/autogen/blob/027ecf0a379bcc1d09956d46d12d44a3ad9cee14/python/packages/autogen-core/docs/src/user-guide/core-user-guide/framework/telemetry.md)。
5. **迁移真实 Core**：核 runtime 管实例、async handler、direct/publish 异常、取消与 message schema。源同步队列跳过的恰是这些合同；本轮未安装或迁移。

#### 第14课：七题自检与答案

1. **Actor 怎样交互？** 通过消息表达交互并由自己管理状态；同进程对象访问仍须程序约束，不能宣称物理上没有共享内存。
2. **三层 API？** Core、AgentChat、Extensions，分别承担运行机制、团队编排和集成。
3. **解耦为什么有助故障隔离？** runtime 可以隔离接收处理失败；direct request/reply 仍可能把异常传播给等待的发送者，publish 则有不同合同。
4. **哪个拓扑固定轮换？** RoundRobinGroupChat；SelectorGroupChat 根据选择器决定下一位。
5. **Magentic-One 是什么？** 参考多 Agent 团队，涉及浏览、代码执行和文件处理。
6. **AutoGen 当前维护状态？** 本次官方核验为维护模式；新项目选型还需核 Microsoft Agent Framework 当前版本，而非沿用源日期与 preview 标签。
7. **怎样接观测？** 原生支持 OTel，对 runtime、tool、AgentChat 有 instrumentation；必须配置 SDK/exporter并核接收结果，不能从“支持”推成每条消息已经导出。

### 第15课：角色团队负责产出，Flow 负责可审阅的控制

Agent 描述角色、目标、工具与上下文；Task 描述输入、依赖、期望产出和验证；Crew 集合参与者和任务；Process 定义它们怎样组织。Sequential 按任务依赖传递上下文，Hierarchical 增加 manager 做路由/审核。是否值得增加 manager 取决于动态决策收益、失败回合与成本，没有“至少四专家才能用”的通用定理。

Flow 把起点、监听、条件路由和状态放进代码：`@start` 标起点，`@listen` 在上游结果后触发，`or_` 对任一结果触发，`and_` 等待全部依赖，`@router` 选标签。显式流程让边更容易测试；其中的模型、外部服务和随机数仍可能变化，Flow 不等于确定性模型或自动精确重放。生产任务可以用 Flow 包裹一个 Crew：先取证→Crew 写草案→schema/证据审阅→授权→提交，每一步的结果合同应能单独检查。[官方 Flow](https://docs.crewai.com/en/concepts/flows)。

期望产出不是一句“写得好”：例如 brief 需要 title、summary、sections 及证据引用；参数 schema 只保证字段形状，还要检查章节数量、来源范围和是否保留未核事实。Backstory 可改变真实模型行为，源硬编码 mock 没有测出这个效果；保持必要角色背景并用同题对照，不能把200字当统一上限。记忆应按客户/项目 scope 写入与检索，处理来源、过期、冲突和删除；2026-10-09 核到官方 unified Memory，源“四种独立 memory store”不能当永久 API。[官方 Memory](https://docs.crewai.com/en/concepts/memory)。

#### 第15课：构建、使用与交付

源 Sequential/Hierarchical/Flow 三个教具使用固定字符串；memory 的随机向量不代表语义检索，两次 kickoff 同一对象不证明重启持久化。真实 Flow 的持久化可配置 `@persist`，resume 沿原 ID 续写，fork 由已有状态建立新 ID；仍须核不存在的 ID、并发写和副作用。`ae-crew-vs-flow` 图比较可变调度与显式路线，固定动画不能证明“Crew慢3倍”。Use It 先按控制要求挑表达，Ship It 蓝图取消 backstory长度/专家数量硬门槛，改为依赖、schema、最大回合、持久化及批准验收。

#### 第15课：七项练习与参考答案

1. **Sequential 转 Flow**：固定依赖、明确失败/结束标签并冻结每步合同；比较路由变化次数和理解成本。模型文本仍可变，不把固定边说成输出完全一致。
2. **客户实体记忆**：写入 customer ID、证据与有效期；测试同名客户不串数据、重启可读、撤销后不可读。源同对象缓存只证明内存存在。
3. **manager 拒绝不足三段草稿**：先定义“段”及空段处理，返回可定位验证错误，最多重试 N 次；每次记录原因。三段只是练习合同，不证明内容优质。
4. **BaseTool 与装饰器 mock 搜索**：同名、同 schema、同工具结果，核 trace中的调用/结果关联；两种声明风格不改变权限职责，本轮未运行 SDK。
5. **Brief 结构与畸形 JSON**：验证 title/summary/sections 字段和业务约束，注入一次错误记录实际修复/失败策略；重试 API 与默认次数须按选定版本核，源没有 Pydantic 实测。
6. **迁移真实 CrewAI**：核 task输出、工具注册、持久化、异步/取消与错误传播；不要把 mock 的 string拼接当这些机制已经通过。
7. **接入观测平台**：检查模型、工具、manager路由和异常 span以及导出回执；本轮只记录验收方案，没有登录、开服务或上传 trace。

#### 第15课：七题自检与答案

1. **四个原语？** Agent、Task、Crew、Process。
2. **生产入口怎样选择？** 可先用 Flow 表达可审阅流程，再把需要自主协作的 Crew 作为步骤；这是方法选择，不是所有任务唯一实现。
3. **Crew 与 Flow 的主要差异？** 前者描述角色协作，后者用事件、状态与代码明确控制；Flow 内部模型仍非确定性。
4. **Quantized 是 memory 类型吗？** 不是本课概念；源四存储分类仅作历史讲解，当前 unified Memory 要按 scope/检索合同核。
5. **Backstory 膨胀的影响？** 占上下文、引入无关角色偏置；保留与判断有关的信息并测试，而不是固定200字规则。
6. **何时值得用 Hierarchical？** 任务需要动态分工/审核且收益超过 manager 的延迟与成本；专家数不能独自决定。
7. **为什么需要控制边界？** 自主多次工具调用会增加调试与副作用风险，关键写操作应经过schema、权限、幂等和结果回读。

### 第16课：SDK 的循环、移交与护栏边界

OpenAI Agents SDK 把模型/工具循环与 Agent、handoff、guardrail、session、tracing 等机制组合。Handoff 转移当前会话控制给另一位专家；agent-as-tool 把专家当嵌套工具，结果回到管理者，管理者继续承担最终输出。二者改变的是控制权与输入/结果合同，不能只把专家名字替换一下。[固定 SDK handoff](https://github.com/openai/openai-agents-python/blob/26345c1e45ebede8e2fc9b0bc7341dedab5e01fc/docs/handoffs.md)。

模型通常看到 `transfer_to_<agent_name>` 工具。`input_type` 校验本次移交工具的参数并交给 `on_handoff`，不替换接收者的聊天历史，也不自动选择目的地；改变历史用 input_filter 或对应嵌套设置。`is_enabled` 在模型返回参数前决定工具可用性，无法核具体金额/对象参数；依字段授权应在 `on_handoff` 开头检查、失败 raise，成功返回后 SDK 才继续移交。过滤结构化工具项仍可能留下普通消息/摘要里的敏感内容，须一并核。

Input guardrail 只在链中首个 Agent 检查初始输入；output guardrail只在产生最终答案的 Agent 后检查。默认 parallel input guardrail 可能在拦截前已经耗 token并执行工具；blocking input guardrail先完成检查。Output 检查永远在产出之后，拒绝答案不撤回已完成工具副作用。Function-tool guardrails 检查被保护的 function调用；handoff、hosted tools及未配置 guardrail的 MCP/Computer/Shell 路径需独立政策。不能用函数护栏覆盖名单代替动作授权。[固定 guardrails](https://github.com/openai/openai-agents-python/blob/26345c1e45ebede8e2fc9b0bc7341dedab5e01fc/docs/guardrails.md)。

人工批准应保存中断对象与 RunState，批准/拒绝后恢复同一 run，并绑定当前参数、任务和版本；新发一条“approved”用户消息不是状态恢复证明。跳数只计 handoff，模型回合、工具调用、wall time和token budget分别限制，耗尽要明确 exhausted 状态，不能返回空字符串假称通过输出护栏。详细批准合同复用[人机协同](../01-核心章节/13-人机协同.md)。Native tracing的导出和敏感数据默认值见[评估和监控](../01-核心章节/19-评估和监控.md)。

#### 第16课：构建、使用与交付

源循环的固定字符串移交没有真实 session、tool guardrail、approval、parallel运行或exporter。`agents-handoff` 示意图保留管理者与移交关系；预设动画无法证明 history过滤或首/尾护栏已经生效。Use It 用官方固定接口做候选，Ship It 的 SDK生成蓝图需要补各路径的覆盖表、停止状态、会话留存与出口政策。SSN子串规则只是故障fixture，不能称 PII识别器。

#### 第16课：五项练习与参考答案

1. **移交跳数**：每次真正 transfer 前增加 hop，达到上限返回明确终止原因；工具调用另计预算。测试 A→B→A 循环和零/非法预算。
2. **嵌套历史**：记录接收者实际看到的消息与摘要，核被排除内容没被复制到摘要；`input_type`不是历史filter。服务端管理历史与本地filter的组合限制按固定官方说明处理。
3. **阻塞检查的延迟**：输入blocking先挡住执行，输出guardrail在产出之后；分别量通过/拒绝、token/工具副作用及端到端延迟，不能把输出检查叫“执行前”。本轮未测SDK延迟。
4. **JSON trace processor**：选择字段白名单、关联ID与独立导出边界。`add_trace_processor`保留默认出口；脱敏失败要由同一自有exporter阻断交付，详见监控章，未上传trace。
5. **迁移真实 SDK**：核移交历史、首/尾guardrail、tool覆盖、RunState批准、超限状态与tracing默认值；源教具没有验证这些合同。

#### 第16课：七题自检与答案

1. **本课五种机制？** Agent、Handoff、Guardrail、Session、Tracing；这是教学分类，不意味着SDK只有五个类型。
2. **模型怎样看到 handoff？** 通常为 `transfer_to_<agent_name>` 工具，可覆盖名字。
3. **三类护栏在哪触发？** 初始input、最终output、已配置function-tool调用，各有不同覆盖边界。
4. **Parallel与blocking的代价？** Parallel重叠检查和执行，拒绝时可能已耗资源/动工具；blocking先检查初始输入，增加正常路径等待。
5. **Trace 默认怎样？** SDK默认开启，敏感数据也默认True；应在运行前明确导出与内容策略，不能把OTel内容默认off推给此SDK。
6. **Handoff drift怎样控制？** 绑定任务关联与允许路线，设置handoff预算并记录循环原因，不能只靠提示“不要循环”。
7. **为何内建工具有覆盖缺口？** Function-tool guardrails不自动保护所有hosted/MCP/Computer/Shell或handoff，需独立执行政策。

### 第17课：托管循环、子任务上下文与会话生命周期

Anthropic Client SDK 接原始模型 API，调用者负责循环；Claude Agent SDK 使用预建 harness，管理工具、MCP、hooks、子任务及会话。省下循环代码也意味着要理解默认工具能力、工作目录、权限与生命周期。子任务可以隔离对话上下文并并行处理独立工作，隔离 prompt 不等于隔离文件系统、凭据或网络；授权与结果汇总还由调用者负责。

把20个独立小任务分成最多5个活跃worker，保留task ID、deadline、取消与结果schema；比较一任务一worker、分批和串行的实际总开销。父上下文不自动包含子任务全部轨迹，但结果仍要进入汇总或外部账本，不能把漏合并结果误判为上下文优化。`len(text.split())`只数单词，不是真token用量。

固定 Python SDK `f7b0b62c2a8d110d4da0eec0aa70cf795ec3afc4` 确实含 SessionStore 的 append/load/list_sessions/delete/list_subkeys及会话摘要相关能力。参考 InMemorySessionStore明确仅测试/开发，进程退出丢数据；load返回列表浅拷贝，内部对象的独立性仍须核。删除主session会级联子key，显式subpath则定向删除；配置session_store后CLI命令包含 `--session-mirror`。不能因为原教具是假store就断言官方不存在这些接口。[固定 SessionStore实现](https://github.com/anthropics/claude-agent-sdk-python/blob/f7b0b62c2a8d110d4da0eec0aa70cf795ec3afc4/src/claude_agent_sdk/_internal/session_store.py)。

同版本 subprocess transport 会尝试用 OTel propagator 注入context：需要可用的opentelemetry-api与有效active context；显式options.env优先，注入失败最佳努力继续connect。自动传播不是无条件完整trace，也不是已经配置exporter。hooks适合在PreToolUse检查权限/预算、在后置hook记录结果；后置日志不能替前置授权，异常、取消与SessionEnd清理要按实际生命周期保证。[固定 transport](https://github.com/anthropics/claude-agent-sdk-python/blob/f7b0b62c2a8d110d4da0eec0aa70cf795ec3afc4/src/claude_agent_sdk/_internal/transport/subprocess_cli.py)。

#### 第17课：构建、使用与交付

源 `spawn_subagents` 实际串行，store为内存且hook异常可能跳过end；`session-tree` 动态图展示树结构，不构成并发/持久化/trace传播实测。Use It在自托管harness与managed之间比较权限控制、执行位置、持久任务、数据留存、运营成本与恢复责任；不能只说“托管更可靠”。Ship It 的生成蓝图要列工具授权、子任务归属、session删除、hooks失败及可查询trace合同。本轮没有启动Claude CLI或调用模型。

#### 第17课：五项练习与参考答案

1. **20任务分批5worker**：固定相同输入与输出schema，限制活跃数、记录完整20个task结果；父上下文、账本大小及总耗时分别量。原serial循环未实现此实验。
2. **write_file每分钟5次**：PreToolUse按session与时间窗口原子计数，明确失败/取消是否占名额、并发竞争与时钟。只在PostToolUse计数会先写再发现超额。
3. **list_subkeys树**：用project/session/subpath标识归属，核重复显示、缺父、深层嵌套与级联删除；显示树不等权限隔离。
4. **迁移SDK注册工具**：核内建工具与自定义/MCP路径、权限回调和hook事件；配置参数按固定版本读，不能搬源mock函数后声称已接真实工具。
5. **何时考虑Managed Agents**：当持续任务与运营成本是主要问题，先核托管执行/数据/权限/恢复可见性；控制细节要求高或边界不能满足时继续自托管。本轮没有申请托管服务。

#### 第17课：七题自检与答案

1. **Client与Agent SDK区别？** 原始API客户端与预建执行harness；后者仍需要权限和生命周期治理。
2. **子任务两个用途？** 独立工作并行与上下文隔离；收益须计调度/汇总成本。
3. **compile_prompt是session store方法吗？** 不是本课列的store接口；append/load/list_sessions/delete/list_subkeys确实在固定SDK中存在。
4. **PreEmbedding是生命周期hook吗？** 不是本课这组hook；具体hook支持与payload按选定SDK版本核。
5. **CLI trace context怎样传播？** 同版本尝试由OTel propagator注入环境W3C字段，有依赖、active context、env优先及最佳努力条件；不能保证最终后端已收到。
6. **过度spawn是什么？** 很多小任务各开worker，使启动/协调成本超过收益；用有界并行和批处理实测。
7. **托管方案交换什么？** 执行控制细节与运营负担的不同分配，需同时评价数据、权限、任务恢复和费用。

### 第18课：语言生态、状态位置与许可证都是部署合同

Agno主要在Python生态，Mastra主要在TypeScript生态；语言决定现有类型、服务和依赖能否直接复用，不证明哪一个业务更快。输入schema（例如Zod）能检查字段与基本类型，仍需业务范围、NaN、未知字段和授权校验。Mastra的Agent、Tool、Workflow是常用组织方式，模型路由统一调用表面也不保证所有供应商支持同样工具、stream或usage。

请求scope与持久session分开：一个后端可以创建短生命周期执行对象，把会话、memory、任务快照放到配置存储；也可以有受控长活跃session。关键是避免多用户状态串用、并发覆盖和重启丢失，而非“一律每请求新对象”。Agno官方提供SDK、AgentOS runtime及外部DB存储候选；Mastra suspend/resume可通过配置storage保存snapshot，仍须故障验收。源重复复用同一对象不证明无状态架构。[Agno官方入口](https://github.com/agno-agi/agno)、[Mastra恢复说明](https://mastra.ai/docs/workflows/suspend-and-resume)。

微秒级对象创建成本只在调用路径大量创建对象且CPU开销成为瓶颈时有意义。先量对象创建、模型等待、tool I/O、序列化、并发与p95；源2μs/3.75KiB、路由模型数量、stars和下载量不作为2026-10-09性能或功能结论。

#### 第18课：构建、使用与交付

源Python/TypeScript都是本地loop/schema教具，没有AgentOS、真实Mastra、持久store或性能基准。`runtime-choice`图的语言/部署分叉仅是选择维度；固定动画与人为sleep不证明overhead。Use It以既有语言、观测、存储与权限需求列候选，Ship It需要记录迁移适配表与合同测试。Mastra根许可对ee目录作例外：本次缓存EE License v2.0（2026-09-22生效）只授自身开发/测试等特定权利，生产要求适用书面协议与有效license key，且限制再分发；不能从“根Apache2.0”推成全仓可任意fork。[根LICENSE](https://github.com/mastra-ai/mastra/blob/main/LICENSE)、[EE LICENSE](https://github.com/mastra-ai/mastra/blob/main/ee/LICENSE)。这是固定文本的范围说明，使用时再核实际组件与当时条款。

#### 第18课：五项练习与参考答案

1. **ReAct迁Agno**：对照模型/工具adapter、状态、停止条件、approval及usage。消失的循环代码可能转成runtime配置，权限与失败责任仍需保留；本轮未迁移。
2. **同loop迁Mastra**：核Zod参数与返回schema、async/取消、服务端状态；再注入合法类型但越业务范围参数。类型系统不能代替授权。
3. **量实例化成本**：预热后多次测同配置、报告环境/样本/分位数，与端到端总时长比较。源2μs只有原测法适用范围，不能换环境直接复用。
4. **CrewAI迁移设计**：逐项映射任务依赖、角色上下文、manager路由、memory scope、tool schema、trace、持久resume；不要只改imports。不同失败语义和session key必须单测。
5. **检查ee许可**：按实际目录和依赖判定组件，区分根Apache、EE及第三方条款；记录生产/再分发/托管限制，不能把source-available当开源授权。

#### 第18课：七题自检与答案

1. **语言配对？** Agno/Python、Mastra/TypeScript，先考虑已有服务与团队维护能力。
2. **session状态放哪里？** 请求执行对象与持久session可以分离，外置存储须核隔离、并发与恢复；短对象生命周期不是唯一合法架构。
3. **Mastra三个常用原语？** Agents、Tools、Workflows。
4. **实例化微秒数字怎样使用？** 视为源特定测法的性能主张，本轮未复现，决策用自己负载测量。
5. **统一路由带来什么？** 统一候选模型调用表面；具体能力、tool/stream/usage差异仍需adapter合同。
6. **何时性能宣传不该决定选型？** 对象开销在总耗时中很小，主要瓶颈是模型或I/O，且其他方案更可维护时。
7. **fork前看哪个许可范围？** 根LICENSE、所有ee目录及第三方组件；当前EE文本含生产和再分发条件，不能只读根许可标题。

本段框架机制与官方选读核验于2026-10-09；第1来源固定 `3be078b37ffd8f0c04953c0678e48f5c6d0c7775`。原74文件中的本课正文、双语言程序、SVG、输出蓝图和quiz已静态读取，源程序与SDK未执行。这里的Build/Use/Ship是可复用设计及验收解释，不是用户已完成实践；旧本地程序和原执行日期保留。
