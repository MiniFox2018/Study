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
