# Coding Agent 与通用 Agent

> 完整来源：[《深入理解 AI Agent》第 5 章](../05-来源保全/深入理解%20AI%20Agent/source/book/chapter5.md)

Coding Agent 是理解通用 Agent 工程的典型样本，因为代码同时是执行能力、验证手段和创造新工具的元能力。

## 典型闭环

理解任务 → 搜索与定位 → 形成计划 → 编辑 → 运行/测试 → 验证 → 失败恢复 → 继续迭代。

## Harness 工程关注点

- 搜索是否能找到正确上下文；
- 文件编辑是否精确、可验证；
- 命令执行是否受控；
- 能否从错误继续工作；
- 是否会提前宣布完成；
- 模型/供应商故障是否可回退；
- 权限与沙箱边界是否清晰。

## 代码作为元能力

代码可以作为思考工具、业务规则约束、多媒体生成器、系统适配器、生成式 UI 和新工具生成器，从而把 Agent 的动作空间扩展到固定工具集之外。

## 已吸收到

[工具使用](../01-核心章节/05-工具使用.md) ·
[规划](../01-核心章节/06-规划.md) ·
[异常处理和恢复](../01-核心章节/12-异常处理和恢复.md) ·
[推理技术](../01-核心章节/17-推理技术.md) ·
[安全模式](../01-核心章节/18-安全模式.md)


## 工程实践补充

关于项目规则文件、上下文分层、Plan/Edit/Test 闭环、权限、Git Diff、Subagent 和并行隔离的工程实践，参见：

- [AI 编码 Agent 工作法](../../AI%20%E7%AE%97%E6%B3%95%E5%9F%BA%E7%A1%80/15-AI%E7%BC%96%E7%A0%81Agent%E5%B7%A5%E4%BD%9C%E6%B3%95.md)

## 从“生成代码”到“拥有这段修改”

以修复列表平均值函数为例：先读调用者对空输入的约定 → 用最小输入复现 → 修改目标函数 → 运行一个能暴露旧错误的测试和一个正常回归 → 查看差异 → 解释为何不会引入新的边界错误。程序返回正确结果后，再改变一个条件，例如输入类型，判断当前方案是否仍成立。

如果 Agent 输出漂亮的解释但测试未运行，结果状态应为“代码已改，验证待执行”。如果测试本身按错误需求编写，全部通过也不能证明任务正确。因此需要把需求、测试和实现对应起来；测试不是数量竞赛。

**自检**：使用代码作为工具，是否意味着生成的代码天然可信？**核对**：不意味着。仍需审阅输入输出、副作用和执行边界；动态生成工具扩大能力，也扩大需要检查的程序范围。

更新：2026-10-02。入门练习见[附录 G](../02-附录/G-编码智能体.md)。

## 从证据到执行的工作台深化

2026-10-09增量：先修是能读函数、JSON、测试和Git差异；以下原理、题目和小程序由固定来源Phase14融合，原课编号仅用于追溯。模型或模板输出、人工fixture、实际运行与真实用户成果分别记录，原有效内容与历史代码保留。

## 工作台：把失败分解为可检查的职责

工作台（workbench/harness）是模型外面的执行环境。先修是能读一个函数、测试和Git差异。模型能提出代码，并不说明它拿到了正确需求、实际运行了测试或获准修改对象；模型本身也可能推理错误，不能把所有失败归咎于环境。七种职责分别是：指令说明怎样工作；状态说明做到哪里；范围限定能动什么；反馈提供实际观察；验证判断合同是否满足；审阅质疑是否解决了正确问题；交接让下一次工作继续。职责可以由同一系统承担，不要求恰好七个文件。

例如注册接口短密码必须返回规定错误。任务描述是输入；旧测试、调用者和仓库版本是事实；允许改动的接口与测试是范围；实际命令结果是反馈；正常与短密码回归是验证；“是否改变其他用户行为”是审阅问题；剩余失败及下一动作进入交接。把工具、worker、trigger、runtime、HTTP/RPC、queue、persistence、policy等基础机制对应到这些职责，能判断新术语到底增加了什么。MCP能力列表只说明可能调用什么，不授予动作权限；叫队列的JSON列表也不会自动得到可靠重放。

**原实验与源码的实际边界**：原Build要求同任务对比prompt-only与七职责工作台，Use要求识别宿主规则、框架状态与CI中的对应职责，Ship要求形成缺失/部分/健康审计。源码按surface名字直接设置成功布尔，没有修改FastAPI接口或运行测试。因此应交付逐职责的证据表和失败定位，不把原failure_modes.json视为实验收益。

**原五项练习：中文问题与参考判断**

1. **选择一个已获准检查的仓库，按七职责各打0/1/2分，哪项最弱？** 每分附具体版本、观察和失败反例；0缺失、1部分、2在适用场景有验证，分数不等实现。
2. **让prompt-only流程宣称假成功，验证器应如何识别？** 原stub已经声明成功；新增的是独立失败记录和不允许关闭任务的结果，不能只设置passing=True。
3. **为产品提出第八职责，为什么不能归入现有七项？** 说明独立输入、输出、失败责任和必要性；开放题允许结论“不需新增”。
4. **替换为会写额外文件的stub，谁先发现？** 执行前范围策略可预阻，真实差异核对可事后发现；按任务允许路径检查，不能硬编码两个文件。
5. **将前面失败分类映射到七职责，哪些对应？** 目标丢失靠目标/状态，越界靠范围，假成功靠反馈/验证，错误假设靠证据/审阅，恢复失败靠状态/交接；可跨多项，需说明观测点。

**原测验：中文问题与答案**

1. **真实任务失败的根因都在工作台吗？** 来源强调缺失工作台，但该二分过强；模型错误与环境错误要分别定位。
2. **七职责是什么？** 指令、状态、范围、反馈、验证、审阅、交接。
3. **哪项不是文中分布式系统基础机制？** 反向传播；它属于模型训练。
4. **Vercel成功率从80%到100%的题能当当前事实吗？** 不能，本批没有独立一手证据，不保留该数值结论。
5. **同一模型在Terminal Bench从30名外到第5能证明什么？** 原题量化未核；真实受控对比才可能分离harness影响，不能由预设stub证明。
6. **遇到新harness术语怎么办？** 先还原成函数、worker、触发、运行时、通信、队列、持久化、政策等机制，再决定采用。
7. **聊天与仓库谁是事实源？** 可持久文件有助续接，但文件仍须版本、证据和权限；聊天授权与实际系统状态各有作用。

## 最小入口、状态与任务板

一个短入口、一个当前状态和一个任务板，可以覆盖导航、恢复与调度的最小需求。课程分别用AGENTS.md、agent_state.json、task_board.json演示，名称不构成跨产品协议。入口只指向必要规则、命令和状态；状态保schema_version、revision、active_task、风险和下一动作；任务板保task_id、goal、allowed_paths、acceptance、status、owner。状态指向的任务必须实际存在，完成状态必须有同版本证据。

一次turn先载入并验证当前版本，再领取任务，执行获准动作，收集反馈，验收后更新状态。缺任务或效果未知时应进入核对状态，不能静默清空再领取下一项。JSON适合快照，JSONL适合追加事件；二者都需重复ID、字段和崩溃一致性策略。入口80行、状态24小时、12项任务都是课程政策，不是可靠性定律。

**原实验与源码的实际边界**：原Build创建三文件并演示续接，Use映射其他宿主，Ship生成项目入口/状态/任务板。源码只把app.py/test_app.py记入touched_files，再标done，未真改文件或验收；state与board分别写入也可能不一致。学习验收应检查引用可用、任务选择稳定、证据不足不得done及重启读取，宿主适配另查真实文档。

**原五项练习：中文问题与参考判断**

1. **增加last_run并在24小时后拒绝运行，如何设计？** 用带时区时间、版本和数据身份；24小时是题设。过期提示复核实际状态，不新增一概要求批准的门禁。
2. **增加priority并先取最高todo，如何避免重复领取？** 限定类型、稳定同分顺序、原子claim与owner；blocked/unknown不能被误重做。
3. **把任务板迁成JSONL怎样验收？** 保全部字段与UTF-8，重复ID拒绝，逐行校验并核记录数；仅换扩展名不算迁移。
4. **写lint检查80行和不存在引用，有何局限？** 阈值可调整，按实际相对目录解析引用；lint不能证明命令可运行或任务完成。
5. **丢失三文件中的哪个最严重？** 比较真实恢复成本与不可重建效果，无唯一答案；状态与板的一致性往往比文件名更关键。

**原测验：中文问题与答案**

1. **最小三文件是什么？** 规则导航入口、持久状态、任务队列；课程名字是AGENTS.md、agent_state.json、task_board.json。
2. **AGENTS.md应扮演什么角色？** 简短导航入口，指向更深规则与状态。
3. **好规则相当于升级某模型的说法可采用吗？** 未核定量，不采用；只能通过同任务对照评价规则质量。
4. **为何使用文件状态？** 便于跨会话回读；须避免覆盖、损坏与版本错配。
5. **冲突指令导致48.8%降到28%的题如何处理？** 未经本批一手核验，淘汰数值；保留检查矛盾与优先级的方法。
6. **跨工具symlink的目的与边界是什么？** 减少多份规范漂移，但每个宿主的实际支持、路径与读取规则须分别核实。
7. **嵌套AGENTS是否统一nearest-wins？** 不能泛化到全部产品；按当前宿主文档与显式任务规则处理。

## 规则从愿望变为执行约束

“小心修改”是愿望；“改支付函数后，指定回归在候选版本上exit=0，且禁止目录无差异”才有可检查对象。课程把规则分启动、禁止、完成、不确定性、批准五类。每条还需要稳定ID、适用范围、风险理由、check白名单、severity和owner。block是硬失败，warn是已定义可接受警告，info仅报告；不能把授权越界放进可抵消的警告预算。

规则文本说明合同，执行器才真正阻断；事后checker只发现已经发生的违反。规则解析时缺check、未知类别、重复ID不可静默跳过。Markdown可以作维护源，JSON可以作缓存，但缓存必须绑定源摘要并检查过期。规则到期是复审提示，长期没有失败可能恰好说明它有效，并非自动删除依据。

**原实验与源码的实际边界**：原Build解析规则并打分，Use建议CI/guardrails/interrupts集成，Ship生成规则和checker脚手架。实际TurnTrace为人工fixture，坏例五条全违而非文案两条；布尔False与整数0混用会误判测试成功。新增集成需真实采集、明确执行前/后位置及版本，输出checker stub不等运行控制。

**原五项练习：中文问题与参考判断**

1. **产品需要第六类规则吗？** 给独立失败和责任证据；能归入五类就不增加。
2. **增加block/warn/info如何聚合？** 闭合枚举，未知与缺检查不能默认通过；硬权限不被分数抵消。
3. **接入CI后何时失败构建？** 独立采集同revision的真实运行，任一必要block失败或缺证据则拒；此处未部署CI。
4. **90天未失败的expiry规则如何处理？** 触发owner复审，核风险、预阻次数与替代控制，不自动解除。
5. **把真实AGENTS逐句改写为五类怎样评？** 区分可机械检查、需判断与解释性规则；无机器check并不等于无价值，不自动删用户规则。

**原测验：中文问题与答案**

1. **愿望规则与操作规则差别？** 后者指定可检查输入、检查函数与失败处理。
2. **五类是什么？** 启动、禁止、完成定义、不确定性、批准。
3. **block是否总要新问操作者？** 必须阻断未满足的硬约束；豁免依真实权限与合同，复用已有同事项授权。
4. **为什么预先标severity？** 在压力出现前说明风险依据，避免为了赶进度弱化门禁。
5. **Markdown源/JSON缓存有什么作用？** 便于人维护和快速加载，但摘要、白名单与同步必须正确。
6. **规则到期意味着什么？** 复审，不是到期自动失效；90天仅题设。
7. **规则和框架guardrails是什么关系？** 规则是合同，guardrails在其实际支持的调用边界执行一部分检查。

## 持久状态、并发与未知效果

持久状态保存续接真正需要的信息：任务身份、schema版本、候选版本、依赖、风险、下一动作和结果回执。大量工件单独保存，状态只存受控路径、摘要和归属；不保存秘密或逐字私人推理。三个月后有无用处只是保留启发式，复现需要的数据/模型版本也可能必须保存。

同目录临时文件→写入→fsync→os.replace能避免读到半个文件；它不阻止两个writer都读revision=6后各写revision=7，从而丢更新。state与board分别rename也非一个事务。可用锁/CAS或SQLite事务统一状态、板与receipt。schema_version不匹配先迁移，迁移保原数据、未结束效果并可重复验证。

call_id先记录仅能说明“准备执行”；不能说明副作用已提交。pending之后崩溃，重试须查外部状态或业务幂等合同。confirmed receipt才允许返回已知结果；unknown必须留待核对，不能跳过或重发。事件日志需要稳定序列、去重和状态版本；重放决策事件不等于重新执行副作用。


### 完整离线例：保存状态、schema迁移、CAS与未知效果

程序只在自身临时目录写SQLite；schema、task和effect都是人工fixture。迁移用deepcopy保原快照；布尔/小数版本拒绝。pending说明无法判断外部效果，假设独立查询后得到的fixture receipt才转known；没有发送或重放实际外部动作。

```python
import json
from copy import deepcopy
import sqlite3
from pathlib import Path
from tempfile import TemporaryDirectory

class Store:
    def __init__(self, path):
        self.db = sqlite3.connect(path)
        self.db.execute('CREATE TABLE IF NOT EXISTS state(id INTEGER PRIMARY KEY, revision INTEGER, payload TEXT)')
        self.db.execute('CREATE TABLE IF NOT EXISTS effect(key TEXT PRIMARY KEY, status TEXT, receipt TEXT)')
        self.db.commit()

    def load(self):
        row = self.db.execute('SELECT revision,payload FROM state WHERE id=1').fetchone()
        return (row[0], json.loads(row[1])) if row else None

    def save(self, expected, payload):
        if (type(expected) is not int or expected < 0 or type(payload) is not dict
            or type(payload.get('schema_version')) is not int or payload['schema_version'] != 2):
            raise ValueError('版本')
        with self.db:
            if expected == 0:
                self.db.execute('INSERT INTO state VALUES(1,1,?)', (json.dumps(payload, allow_nan=False),))
            else:
                cursor = self.db.execute('UPDATE state SET revision=revision+1,payload=? WHERE id=1 AND revision=?',
                                         (json.dumps(payload, allow_nan=False), expected))
                if cursor.rowcount != 1:
                    raise RuntimeError('revision冲突，重读后合并')

    def reserve(self, key):
        with self.db:
            self.db.execute('INSERT INTO effect VALUES(?,?,?)', (key, 'pending', None))

    def recover(self, key):
        row = self.db.execute('SELECT status,receipt FROM effect WHERE key=?', (key,)).fetchone()
        if row is None:
            return 'not-dispatched', None
        if row[0] == 'committed':
            return 'known', row[1]
        return 'reconcile-required', None

    def confirm(self, key, receipt):
        if not receipt:
            raise ValueError('缺回执')
        with self.db:
            cursor = self.db.execute("UPDATE effect SET status='committed',receipt=? WHERE key=? AND status='pending'",
                                     (receipt, key))
            if cursor.rowcount != 1:
                raise RuntimeError('不是待核效果')

    def close(self):
        self.db.close()

def migrate(payload):
    if type(payload) is not dict or type(payload.get('schema_version')) is not int:
        raise ValueError('schema版本须为整数对象字段')
    version = payload['schema_version']
    if version == 2:
        if 'blockers' in payload or type(payload.get('risks')) is not list:
            raise ValueError('v2字段矛盾或缺失')
        return deepcopy(payload)
    if version != 1 or 'risks' in payload or 'blockers' not in payload:
        raise ValueError('不支持或矛盾schema')
    if type(payload['blockers']) is not list:
        raise ValueError('v1 blockers类型')
    result = deepcopy(payload)
    result['schema_version'] = 2
    result['risks'] = result.pop('blockers')
    return result

with TemporaryDirectory() as directory:
    path = Path(directory) / 'fixture.sqlite'
    a, b = Store(path), Store(path)
    old = {'schema_version': 1, 'task': 'T1', 'blockers': ['effect unknown']}
    new = migrate(old)
    assert old['schema_version'] == 1 and migrate(new) == new
    migrated_copy = migrate(old);migrated_copy['risks'].append('modified-copy')
    assert old['blockers'] == ['effect unknown']
    for bad_version in (True, 1.0):
        try:migrate({**old, 'schema_version':bad_version})
        except ValueError:pass
        else:raise AssertionError('伪整数schema版本')
    a.save(0, new)
    rev_a, payload_a = a.load()
    rev_b, payload_b = b.load()
    a.save(rev_a, {**payload_a, 'next_action': '核回执'})
    try:
        b.save(rev_b, {**payload_b, 'next_action': '错误覆盖'})
    except RuntimeError:
        pass
    else:
        raise AssertionError('lost update未阻止')
    a.reserve('op-1')
    a.close()
    c = Store(path)
    assert c.recover('op-1') == ('reconcile-required', None)
    # receipt是假设外部查询后得到的fixture，程序没有执行外部动作。
    c.confirm('op-1', 'fixture-receipt-a')
    assert c.recover('op-1') == ('known', 'fixture-receipt-a')
    assert c.load()[1]['next_action'] == '核回执'
    b.close()
    c.close()
print('state: 迁移保原；并发旧revision拒绝；重开后pending仍待核，confirmed回读')
```

**原实验与源码的实际边界**：原Build要求schema、StateManager、持久回读，Use提及框架checkpointer与session，Ship生成迁移脚手架。源码有子集validator和atomic commit，未实现完整update/migration；main重置初始数据，不能用于续接。其“发现call_id便跳过”会把pending误作完成。下面SQLite教学程序演示CAS、统一事务和unknown保留，不接任何外部工具。

**原五项练习：中文问题与参考判断**

1. **增加last_human_touch，五秒内禁止写怎样改？** 时间只是题设；真正比较revision并锁定/合并，保留用户修改与授权。
2. **支持oneOf有什么判据？** 恰好一个分支匹配；未知schema关键词在使用前拒绝，不把子集validator称完整JSON Schema。
3. **v1 blockers改为v2 risks怎样迁移？** 识别旧版、保全部字段和未知效果、备份并幂等；未知版本拒绝。
4. **改SQLite但API不变需补什么？** 统一state/board/receipt事务、CAS/锁与owner；重开连接验证回读，不等于多机或掉电测试。
5. **两个writer相差50ms，rename能救什么？** 防半写，不能防lost update；测试同旧revision提交一方应冲突，时间差不是必要条件。

**原测验：中文问题与答案**

1. **什么信息值得进repo memory？** 按恢复、复现、权限与保留期限判断；三个月是启发式。
2. **哪个字段记录合同版本？** schema_version；另用revision区分状态更新。
3. **atomic write怎样做？** 同目录临时写、flush/fsync、replace；并发及目录耐久另处理。
4. **为何非幂等调用需key？** 避免未知重试重复效果，但预先记录key不证明执行；必须查receipt/状态。
5. **大工件放哪？** 独立受控存储，状态保身份、路径与摘要。
6. **事件+快照买到什么？** 可审计和续接；需顺序/版本/去重，不声称能逐字重放推理或exactly-once。
7. **schema不匹配怎么办？** 拒绝错误版本，显式迁移并回读核验。

## 初始化：可缓存的事实与必须重核的条件

初始化把反复探索运行时、依赖、路径、验收命令、必要环境变量、当前状态的工作集中到一个可定位报告。必要条件失败应清楚失败；可选能力缺失可以降级并保边界。找到python命令不等于pytest可执行，find_spec不证明依赖版本或完整可用，报告不得回显秘密值。

缓存只有在输入身份匹配时有用：依赖清单内容、真实解释器/版本、测试配置、仓库revision和状态schema均可能相关。权限与外部效果等条件仍须在动作前重核。last-known-good必须由真实验收产生，写入当前HEAD不使它自动“good”；差异应包括工作区和未跟踪对象。用单调钟测时，软告警与真正超时分开。自动安装会改变执行与访问范围，不由“初始化”一词授予。

**原实验与源码的实际边界**：原Build写init_report，Use建议hook/CI/entrypoint，Ship生成项目探测器。源码实际六probe，lock只指纹硬编码名字，fresh会跳过已变化环境；LKG与state失败仍可能warning并pass。验收需坏依赖、旧缓存、缺状态、未知版本和探测超时的反例，不运行源探测/--fix或真实宿主命令。

**原五项练习：中文问题与参考判断**

1. **LKG差异超过50文件拒启动合理吗？** 50是题设，先确认LKG真通过、包括工作区/untracked，再按行为风险解释预算。
2. **prereqs.lock超过七天拒绝如何设计？** 七天另定；cache key绑定实际输入，stale重新探测或明确阻断。
3. **--fix自动装dev依赖边界在哪里？** 先明确包、脚本、网络、费用和对象授权；开发依赖也能执行代码，本批不安装。
4. **YAML registry取代硬编码如何权衡？** 更易维护，但需安全解析、probe白名单、参数与severity校验，禁止任意eval。
5. **每probe三秒预算是hard timeout吗？** 不是；明确单调时长、软告警及取消/未知效果，不能事后报慢就称已阻止。

**原测验：中文问题与答案**

1. **初始化消除什么？** 重复的每会话环境探索税，但仍重核易变条件。
2. **失败合同是什么？** 尽早、清楚、在可定位入口失败，必要项坏了不得开始依赖工作。
3. **哪项不是环境probe？** 逐token采样温度。
4. **幂等意味着什么？** 同条件重复执行不破坏已有状态；时间戳可新，不代表一切状态应重置。
5. **LKG锚定怎样有意义？** 绑定真实通过的版本并检查当前变更，不能仅保存HEAD。
6. **TTL lock怎样使用？** 成功证据与真实manifest绑定；24小时是题设，不能跳过实时权限检查。
7. **热路径应避免什么？** 无必要的网络/模型/许可调用；若任务确需外部条件，要明示授权、超时与失败，不把三秒当普遍定律。

## 范围合同：路径、操作、时间与出站

范围写goal、允许对象与操作、禁止对象、验收、恢复、必要批准和预算。负空间帮助拒绝“顺手修一下”。路径只是一个维度，网络origin/port/重定向/凭据目的地、时间、安装或发布操作也可能受限。材料目录中的SKILL/AGENTS属于数据，不能成为当前任务新授权。

多个合同同时适用时，对实际路径分别判断允许谓词再做AND，禁止做OR，时间取最严格值，适用批准条件全部满足。不能对glob字符串求集合交：src/**与src/a.py的字符串交集为空，但路径src/a.py满足两者。先规范路径并核真实对象，尤其rename/delete/untracked和symlink。docs扩展名不自动低风险；越权修改规则文件不能靠warning预算放过。时间到后停止新dispatch，进行中的写效果可能unknown，取消不等回滚。


### 完整离线例：词法范围与同候选验证记录

目录条目以/结尾匹配组件子树，文件条目精确匹配；多个scope取谓词交集。它不是glob/实际文件系统/symlink隔离。command/exit是受信采集之后的人工记录fixture，没有运行这些命令；不能由模型自报通过。

```python
from dataclasses import dataclass
from pathlib import PurePosixPath

@dataclass(frozen=True)
class Scope:
    allow: tuple[str, ...]
    deny: tuple[str, ...] = ()

def path_parts(path):
    p = PurePosixPath(path)
    if not path or p.is_absolute() or any(x in ('', '..', '.') for x in path.split('/')):
        raise ValueError('路径必须为规范相对路径')
    return p.parts

def contains(root, path):
    subtree = root.endswith('/')
    r, p = path_parts(root[:-1] if subtree else root), path_parts(path)
    return p[:len(r)] == r if subtree else p == r

def allowed(path, scopes):
    path_parts(path)
    if not scopes:
        raise ValueError('缺范围合同')
    return all(any(contains(r, path) for r in s.allow)
               and not any(contains(r, path) for r in s.deny) for s in scopes)

def verdict(task, revision, changes, scopes, required, records):
    if not task or not revision or not required:
        raise ValueError('缺任务身份或必要验收')
    if len(set(required)) != len(required):
        raise ValueError('验收ID重复')
    findings = []
    for path in changes:
        if not allowed(path, scopes):
            findings.append('范围:' + path)
    for command in required:
        matches = [r for r in records if r['task'] == task and r['revision'] == revision
                   and r['argv'] == command]
        if not matches:
            findings.append('缺验收:' + repr(command))
        elif not all(type(r['exit']) is int and r['exit'] == 0 for r in matches):
            findings.append('失败或未知:' + repr(command))
    return {'passed': not findings, 'findings': findings}

scopes = [Scope(('src/', 'tests/'), ('src/release/',)), Scope(('src/auth.py', 'tests/'))]
command = ('python', '-m', 'unittest')
record = {'task': 'T1', 'revision': 'candidate-a', 'argv': command, 'exit': 0}
assert allowed('src/auth.py', scopes)
assert not allowed('src/other.py', scopes)
assert not allowed('src/auth.py/child.py', scopes) # 文件条目不是目录子树。
assert not allowed('src/release/ship.py', scopes)
assert verdict('T1', 'candidate-a', ['src/auth.py'], scopes, [command], [record])['passed']
assert not verdict('T1', 'candidate-b', [], scopes, [command], [record])['passed']
for result in (False, None, 1):
    assert not verdict('T1', 'candidate-a', [], scopes, [command],
                       [{**record, 'exit': result}])['passed']
for invalid in ('../src/auth.py', '/src/auth.py', 'src/./auth.py'):
    try:
        allowed(invalid, scopes)
    except ValueError:
        pass
    else:
        raise AssertionError('不规范路径未拒绝')
try:
    verdict('T1', 'candidate-a', [], scopes, [], [])
except ValueError:
    pass
else:
    raise AssertionError('空验收未拒绝')
print('gate: 路径谓词交集正确；缺验收/旧版本/False/None/非零均拒绝')
```

**原实验与源码的实际边界**：原Build声称schema/diff parser/两次检查，Use建议scope/PR/interrupt，Ship生成checker。真实源码只检查人工RunSummary，验收只查命令字符串曾出现，网络只核host文本，均无真实执行预阻。下面gate演示合同谓词组合和同task/revision的反馈检查；正式执行器仍要独立采集和containment。

**原五项练习：中文问题与参考判断**

1. **增加network_egress如何证明拒未知host？** 源已有集合检查；需真实调用边界核origin、端口、重定向与目的地，不凭自报hosts。
2. **docs软、scripts硬是否合理？** 依据具体后果；禁止对象始终硬，文档可能是权限规则，不按后缀豁免。
3. **按goal静态生成allowed_files首个反例？** 同名函数、跨模块与重构；映射只建议，须仓库证据与原授权。
4. **time_budget到时如何停止？** 单调deadline、dispatch前检查、inflight取消和效果核对；事后elapsed不能证明限时。
5. **同一diff适用两个合同怎样合并？** 实际路径allow AND/deny OR、预算min、条件并用；None代表未指定，空集合代表拒绝全部，不能混淆。

**原测验：中文问题与答案**

1. **为何scope creep难察觉？** 每一步似有理由，合起来偏离已审目标。
2. **合同的一半是什么？** 负空间/forbidden对象。
3. **glob为什么有用、有什么风险？** 覆盖目录形态，但仍须明确匹配语义，重构后核对范围，不能自动合法。
4. **violation budget是什么？** 对明示可容忍警告的有限预算，绝不豁免硬权限或禁止路径。
5. **52%到21%的原题如何处理？** 未核一手，不作事实；保留同任务范围对照的实验问题。
6. **least privilege merge是什么？** 各允许谓词交、禁止并、预算最严格、条件全满足。
7. **为什么要时间与网络预算？** 墙钟和出站也是动作范围，文件范围不足以表达。

## 真实反馈进入下一轮

反馈记录提供下一轮决策所需的实际观察；telemetry用于跨任务运维，可共享采集器但有不同访问和保留策略。记录至少有task/run/command ID、parent ID、候选revision、argv、cwd、允许记录的环境摘要、单调时长、exit、错误类型和输出。None表示缺结果或未完成，非零表示这次命令失败；exit=0也只证明命令进程成功，任务合同另判。

记录前控制敏感采集与脱敏，再按字节限制/确定性head-tail截取。先截断多行private key会破坏识别，argv/note/error也可能含秘密。regex只是辅助，不是完整PII保证。限制单记录、当前文件及总retention；轮转、并发写和断裂JSON行都要有失败策略。重试保父子身份、失败、取消和unknown，检测循环与缺parent；不能只留下最后一次绿灯。

**原实验与源码的实际边界**：原Build runner/loader/成功失败慢命令，Use框架shell/CI，Ship项目反馈器。真实main是五命令且无slow，先删除历史，与跨run累积文案冲突；capture_output全缓冲、rotate无锁、loader全量读历史。此处不运行来源命令；教学gate用明确fixture记录，不能当真实stdout采集或安全脱敏部署。

**原五项练习：中文问题与参考判断**

1. **加cwd怎样区分相同命令？** 绝对路径加解释器/argv/env摘要/task/revision，命令字符串相同不等环境相同。
2. **脱敏Bearer/password怎样测？** 多行、截断边界、argv/note/error与变体反例；默认不采秘密，不只测试一行happy case。
3. **1MB并轮转怎样辩护？** 1MB是题设，核单记录字节、总保留、并发和崩溃；归档访问与热路径预算分开。
4. **parent_command_id怎样展示重试？** 唯一稳定ID、同任务、无环、缺parent标unknown；保失败链而非独立成功。
5. **TUI需要哪八项？** 可选task、argv、cwd、revision、exit/错误、时间、输出/截断脱敏、父子链接；评价是否定位问题，无唯一八项，源未实现TUI。

**原测验：中文问题与答案**

1. **反馈runner强迫什么？** 从实际记录反应，不能想象“测试通过”。
2. **feedback与telemetry如何区别？** 用途、访问与保留不同，不必物理上不同文件。
3. **每条必需哪个结果字段？** exit_code及明确unknown；非零也不能当success。
4. **怎样截大输出？** 确定性head+tail与截断标记，同时限制字节/单行。
5. **为何写前脱敏？** 读时隐藏不能消除磁盘已经泄漏的秘密。
6. **parent ID有什么用？** 联系失败与重试并保因果证据。
7. **为何轮转？** 有界热路径与保留历史；源loader读所有历史，未实现所声称“只读当前”。

## 验证器判断完成，缺证据不可绿灯

验证器是合同与可信工件的确定性函数。输入应闭合：候选身份、实际diff、规则结果、完整必要验收、时间/权限/预算状态。空scope、空rule list和空acceptance不能自动pass；要分格式有效、执行有结果、合同通过、实际目标满足。反馈argv必须同类型比较，exit要求type(x) is int以排除False==0；旧revision成功不得覆盖新候选。

coverage须有限且落在[0,1]，绑定报告版本、分母和测试变更；删失败测试可能提高覆盖率，覆盖率不能独立防作弊。pre-commit能绕过，独立CI/protection和动作前授权有不同职责。共享HMAC加调用者自报user_id不证明人类批准；豁免应有可信主体、确切finding/action、范围、期限与审计，不能自行签字。失败也应交接，才能正确恢复。

**原实验与源码的实际边界**：原Build clean/scope creep/missing acceptance，Use CI/pre-handoff/人工核查，Ship门禁接线。实际工件人工构造、空输入可过、coverage NaN可绕过、human60秒豁免可伪造，源override未参与verify。下方闭合教学gate会拒缺验收、旧版本、布尔exit及越界；它只证明局部纯函数，不是不可篡改CI。

**原五项练习：中文问题与参考判断**

1. **coverage_floor≥80%怎样验收？** 80%题设；有限值/分母/候选身份/报告真实性与测试删改审计共同检查。
2. **strict把warn升block何时适用？** 按真实风险预定，发布/故障复核可更严；不代替完整输入与授权。
3. **JSON之外MD摘要写什么？** 结果/失败/unknown、候选与证据定位、下一动作，不回显秘密；两格式同语义。
4. **人类60秒内编辑免off-scope是否成立？** 不成立，mtime/时间近不能证明主体或授权；应核实际批准范围。
5. **真实diff中多少真问题/噪声？** 按类别统计TP/FP/FN和严重漏报，真实运行另在授权范围执行；不能削弱硬门禁减少噪声。

**原测验：中文问题与答案**

1. **验证器回答什么？** 这个任务是否满足明确完成合同。
2. **为何确定性？** 同冻结证据应得同状态；定性问题由审阅补充，确定性不等语义正确。
3. **block如何override？** 需真实获准主体与绑定动作的记录；共享密钥签名本身不足。
4. **可验证回报与rubric怎样配合？** 测试/schema/exit核机械事实，审阅核问题匹配和意义，两者均有局限。
5. **分层门禁如何防御？** 动作前、CI、合并前各检查其层；pre-commit并非不可绕过。
6. **coverage floor防删测试吗？** 只能提供信号，必须同时审计测试分母/差异，80%和1pp不是普遍标准。
7. **strict应何时开启？** 预定高后果场景或合同要求；不随看结果临时改变标准。

## 独立审阅：目标匹配与证据质量

审阅读取冻结diff、规则、范围、状态、反馈和verdict，输出问题、证据、风险和建议。五维是问题匹配、范围纪律、假设、验证质量、交接可续性；每项0–2、总分7/5是课程示例，严重越权不能被其他项抵消。角色分离能减少自证偏差，同一模型也可换角色；独立权限和独立输入需实际实施，仅写read-only不够。

文件名含goal关键词不是解决问题的证据，记录假设不等验证假设，有next_action不等可恢复。先核独立gate，再按引用事实审阅，缺证据要请求具体补证或abstain。LLM judge可能有位置、冗长、自偏好、提示敏感等偏差；校准要可信gold、heldout、严重误判代价与版本，self-reported confidence不是概率。

**原实验与源码的实际边界**：原Build给clean与“测试对但问题错”打分，Use reviewer/handoff，Ship rubric接入。实际deterministic stub按关键词与非空字段给分，甚至忽略verdict.passed，未真运行LLM或权限隔离。练习应提交引用候选证据的审阅报告；0.6/80%只题设，不作真实性门槛。

**原五项练习：中文问题与参考判断**

1. **第六领域维度是什么？** 用实际domain失败、gold和证据论证独立性；硬安全不进可抵消评分。
2. **terse/verbose哪种人更愿读？** 冻结同工件和预算，只改变提示，分别量读者反馈与正确性；没读者测试不能下结论。
3. **最低维confidence<0.6拒报告如何改？** 不确定度需校准，允许补证/abstain；自报0.6不能作真实概率。
4. **10个历史close-out如何校准？** 可信版本/gold/负例/heldout，分TP/FP/FN和严重错判；十例是题设。
5. **请求更多证据怎样防循环？** 精确对象/动作/验证器，限重复、时间和费用；缺证据明确未完成，不越权外发。

**原测验：中文问题与答案**

1. **builder为何需第二视角？** 可能把自己的假设和较弱测试当正确；自检有用，角色分离也不保证正确。
2. **哪项非五维？** 推理延迟；性能需求可另设，但不是原rubric项。
3. **角色分离需什么？** 不同目标/输入/提示和真正限制修改能力，不能仅改角色名。
4. **Cloudflare七专家架构是现通用事实吗？** 本批未核一手，淘汰产品/数量主张；保留按风险分工并去重的原则。
5. **哪项不是judge偏差？** vector locality；位置、冗长、自偏好、提示敏感要用对照检验。
6. **校准集有什么用？** 核审阅对真实标签的误判并维护版本；10–20/80%仅课程政策。
7. **审阅报告放哪？** 与交接及验收证据关联，方便下一次复核，但不能替代真实工件。

## 跨会话交接：下一动作与未决效果

交接包保存目标、候选版本、branch、状态、实际改动、验收/审阅指针、失败与unknown、待验证假设、下一动作及启动前必读材料。最承重字段是next_action：要能指出具体命令/文件/待解决问题。MD与JSON可以从同快照生成，发生分歧先核原证据和版本，不因扩展名就认定真值。

压缩用于延长上下文，交接用于连续工作；没有通用50–75%预算必结束规则。摘要可保最近K条、失败和unknown的代表与原日志指针，避免无限倾倒全部失败。冻结输入、稳定排序和稳定ID保证生成幂等，Python object id不是跨会话身份。dirty/失败也要准确交接；不能为了“clean”擅自删除、stash或提交用户改动。

**原实验与源码的实际边界**：原Build收state/verdict/review/feedback写两格式，Use session-end/PR/跨产品，Ship生成器。main只用虚构snapshot，默认review=10隐藏未知，trim漏掉旧exit=None，指针可能不存在。验收应回读相同候选及证据、确认具体下一动作且unknown未丢，外发PR/消息仍需实际授权。

**原五项练习：中文问题与参考判断**

1. **assumptions_to_validate如何关联低分？** 逐假设ID、来源、review criterion和状态，未评分写unknown，不由总分推全部已核。
2. **失败与通过怎样不同裁剪？** 失败保因果与未知效果；通过也保回归历史，预算内摘要并链接完整受控日志。
3. **questions for human何时进包？** 缺信息影响目标/正确性/授权才问；给影响和独立可做事项，复用已有回答。
4. **两次生成同包要稳定什么？** 同输入snapshot/版本/IDs/顺序与观察时间，MD/JSON同语义。
5. **next-session prereqs列什么？** 真实规则、选定task、代码、状态版本、证据、权限与未决效果；不存在路径不作proof。

**原测验：中文问题与答案**

1. **关键字段是什么？** next_action，使状态报告成为可执行续接。
2. **为何生成而不是手写？** 减少遗漏，但手写有依据同样可用；生成器不能替未知工件造结论。
3. **两种形式是什么、谁胜？** MD与JSON同源；不一致时核原证据/版本，而非盲目JSON优先。
4. **compaction与handoff区别？** 前者压缩会话上下文，后者保存连续工作合同；都不自动关闭任务。
5. **何时结束会话？** 按有效上下文和恢复需要决定，50–75%是经验题设而非门禁。
6. **怎样裁剪反馈？** 最近条目+失败/取消/unknown的有界摘要与指针；不能仅非零exit。
7. **多会话需哪些协调元数据？** branch、LKG/候选revision、topic、active/superseded/archived及owner，避免误接旧任务。

## 真实仓库对照：工作台的收益也要受检验

评价工作台前冻结同任务、同基线revision、输入与授权、运行条件和验收，再比较真实改动与费用。可量任务接受率、范围越界、实际反馈完整性、交接可用性、返工/回滚，以及首次有意义修改的时间；最后一项须预先定义行为证据，敲字或mtime变化不算进展。

重复运行预设表不会产生独立证据。真实模型对比需要控制配置和预算、多次代表case与holdout、保失败/unknown/费用，并区分模型随机性和工作台差别。简单一行修正可能直接路径更有效；合理结果包括工作台应缩小、停止或换机制。把这类反例称为分类“false negative”容易误导，应说开销与负结果。

**原实验与源码的实际边界**：原Build两pipeline输出comparison/report，Use向怀疑者解释，Ship评价harness。源码两个函数返回预设结果，sample.signup仍未实现短密码422且无模型/测试。原1/5对5/5不是测量。因此交付的是可复现对照设计与实际记录边界，不引用预设数字证明业务收益。

**原五项练习：中文问题与参考判断**

1. **加time-to-first-meaningful-edit怎么测？** 预定goal子结果，用真实单调start、第一次候选diff与可验收行为关联。
2. **第二天真实任务数字为何可能变差？** 任务/依赖/权限变化与环境差别，冻结基线并独立收集；不复用preset。
3. **prompt-only更快还要保工作台吗？** 按风险与足够结果留最小控制，诚实记录开销，可缩小或停止。
4. **换真实LLM哪些更噪？** 成功、耗时、调用成本、路径选择；控制输入/config并保失败与unknown，本批未调用API。
5. **给非工程者的一页保什么？** 实际改变、对象范围、证据、代价、未知及继续/停止理由，不把教学表作ROI。

**原测验：中文问题与答案**

1. **同任务两流程的目的？** 可被核对的前后结果与代价。
2. **哪项不在原五结果？** model_perplexity，且原五项均预设。
3. **Terminal Bench名次变化可用吗？** 本批无独立一手核验，不作量化证明。
4. **88%企业项目失败可用吗？** 未核人口/方法/日期，淘汰统计结论。
5. **长上下文40–50%掉到10%可用吗？** 未核基准/条件，不泛化；可保目标丢失/循环作为待检失败类型。
6. **简单任务的反例是什么？** 事实查询、一行lint/format等可能工作台开销更高，要真实测而非先定赢家。
7. **何时引用此报告？** 真实复现并说明边界后才能支持流程取舍，源preset不能作可携带benchmark。

## 可复用包：版本、所有权与安全迁移

复用工作台有价值的单位是行为合同及其依赖：导航、schema、执行/验证脚本、必要模板、版本与拥有文件清单。课例包不是因为目录叫pack就成为可安装Skill；缺真实SKILL.md或宿主要求不能宣称兼容。单源规则适配到不同工具应核真实路径与支持，symlink不保证读取。

安装先dry-run列源/目标、冲突、摘要、文件mode与版本；只替换明确owned且内容仍匹配的对象。未知、用户改动和symlink保留审阅，state/board/output不当作包文件删除。迁移先快照→兼容检查→隔离候选验证→切换→回读→恢复演练；回滚需对应实际数据和效果，cp -r反复执行不等安全幂等。版本分类按实际兼容合同，文档变化也可能改变安全语义。

**原实验与源码的实际边界**：原Build组装七职责包，Use拷目录/template/SkillKit，Ship调优pack。已生成目录缺state/board/checker/reviewer/CI/uninstall，verify全缺仍可pass，runner缺脱敏，installer仅护AGENTS却覆其他同名文件。来源“重复安全、32工具兼容”不采；下方只讨论/验证owned清单，不安装、不删文件。

**原五项练习：中文问题与参考判断**

1. **第五可选doc该提升吗？** 有真实流程缺口、owner和维护价值才加入，已有入口足够就不增加。
2. **Python dry-run相对bash如何评？** 比较可读错误、路径安全、冲突清单、摘要和逆向计划；不用易用性掩盖覆盖风险。
3. **uninstall怎样定义非平凡history？** 以所有权与实际用户数据为准，不粗按计数；仅计划移除owned未修改字节，保未知和全部用户state/output。
4. **lint VERSION怎样防漂移？** 绑定schema/scripts/metadata摘要与required check存在；代码和已生成包都核，未接CI不能称CI通过。
5. **手写工作台迁入pack的顺序？** 快照/授权与范围→兼容/迁移dry-run→隔离验证→切换→回读/恢复，不声称零停机。

**原测验：中文问题与答案**

1. **capstone实际产物是什么？** 版本化教学目录；并未实现宣传的完整七职责运行。
2. **哪项不在包？** vendor_proprietary_weights。
3. **VERSION为何需要？** 追溯兼容与迁移；major/minor/patch须据实际合同，不能只看文件后缀。
4. **跨工具分发是什么？** 单一规范适配真实宿主，原symlink路径/统一读取主张未证。
5. **uninstaller怎样做？** 只处理owned且未改对象，保用户状态/输出和未知文件，不广删schemas/scripts/docs。
6. **包不应塞什么？** 项目特定任务、无必要SDK依赖和重复入职材料；其必要依赖与边界要清楚。
7. **一命令覆盖32 agent事实吗？** 未经当前一手验证，不保数量/安装命令或兼容结论。

## 改代码前形成任务框架

Task frame先记录要改变的行为，事实与receipt、最小允许对象、负空间、完成证明和unknown，再选择方案。事实应是当前版本实际代码/测试/观测，例如“重复请求测试在指定行期望409”；“应该加缓存”是推断。receipt需要真实path/行/版本和它支撑的claim，非空字符串不足。

未知可以靠读取发现、范围内自主决定、等待人类关键回答或暂缓。缺失信息改变公共行为、目标、授权或不可逆后果才暂停依赖部分；已授权可逆选择继续，不能因模板有checkpoint就重新询问。侦察充分是所有下一步决定都有证据、明确授权或显式unknown，不是必须读完整仓库。

**原实验与源码的实际边界**：原lab写task-frame，要求分别去goal、fact receipt、造allow/forbid冲突、去acceptance并得到不同拒绝原因。源码facts可空、glob冲突只字符串相等、人类unknown不影响READY。真实仓库Use六步应保行为目标/事实/最小范围/负空间/关闭观察/未获决定；一屏是压缩建议，不是正确性阈值。

**原五项练习：中文问题与参考判断**

1. **真实bug先不提方案怎样frame？** 写行为、证据、边界和unknown，不把假想练习称用户真实修复。
2. **发现一个假设怎样换证据？** 查真实path/line/revision或观察，不可证者保assumption。
3. **加一个改变公共合同的人类unknown何时问？** 答案实质影响正确性/目标/授权时，继续独立侦察。
4. **缩小宽泛allowed路径如何不漏依赖？** 沿真实调用/测试关系核最小集合与操作类型，不关键词猜权限。
5. **给验收增加scope receipt是什么？** 同候选真实diff/rename/delete/untracked与范围合同核对。

**原测验：中文问题与答案**

1. **可靠编码第一单位？** 有仓库证据的任务框架。
2. **什么是仓库事实？** 当前测试明确期望409且有可核行与版本。
3. **为何写禁止路径？** 定义修改负空间。
4. **人类unknown何时暂停？** 影响真实行为/风险/授权/不可逆代价，已有同事项回答复用。
5. **强验收证据是什么？** 具体命令/观察及它证明的claim，不只是“测试一下”。
6. **侦察何时足够？** 每个计划决定有证据、授权或显式unknown。

## 证据计划：依赖图而非长待办

工作项记录goal/change、scope、支撑证据、依赖、状态、产物和完成证明。共同合同先定，避免实现与文档各自发明返回语义；再实现/说明，最后整合验证。图中无依赖只是拓扑可同时开始，还须核写对象、设计决策、共享状态、限流和授权独立。

重复ID、未知依赖、循环、缺proof要在计算波次前拒绝。循环可能隐藏未定业务选择，也可能只是分解或ID错误；不能看到cycle就编造业务原因。两条proof若共同证明同一不可分行为可留一项，独立目标才拆。新事实出现应修计划并保依据；计划本身不代替执行。

**原实验与源码的实际边界**：原lab静态拓扑三波：合同→实现与文档→整合，写evidence-plan。七tests只检查结构，未验证真实并行完成。开放Use要求逐claim receipt、清晰proof、把昂贵/不可逆工作延后；原“先批准计划”不自动成为当前任务每步门禁。

**原五项练习：中文问题与参考判断**

1. **加需人类批准迁移项怎么写？** 真实schema/data/版本、备份/恢复和必要事项批准，不只needsapproval=True。
2. **造cycle背后是什么争议？** 列互相先决，查业务决定或纯分解错误。
3. **一项两proof要拆吗？** 共同证明一个不可分行为可保；两个独立成果再拆。
4. **第二wave加独立项怎样证明？** 依赖已完成且决策/写路径/状态/预算无冲突，拓扑并列不授予执行。
5. **MD计划以JSON为源怎样保持一致？** 同冻结版本投影，保unknown/失败/status；JSON非空不等事实真。

**原测验：中文问题与答案**

1. **计划与待办差别？** 有证据与proof的依赖图。
2. **为何先共同合同？** 避免依赖面行为冲突。
3. **循环通常揭示什么？** 未决选择或坏分解，还要证据判断。
4. **何时同wave？** 依赖完成且其他执行条件独立。
5. **每项为何带证据？** 说明修改理由并允许新事实修订。
6. **何谓可续接计划？** 小项有状态、工件、依赖和完成证明。

## 隔离委派：共同合同、对象归属与整合

只有已获委派授权且真实独立的工作才并行。隔离有三层：文件写对象归属、执行/状态隔离、共同设计合同。worktree隔离checkout，不提供OS沙箱或网络/秘密隔离；不同文件也可能共享API决定，先约定合同或串行。只读research可以共享阅读，输出事实表附来源版本/行和unknown。

每单元给目标、allowed read/write、owner、依赖、产物、proof与取消条件。integrator核最终实际diff并做跨单元验收，不能把各自绿灯相加。依赖版本失效时停止新dispatch，取消inflight仍保unknown效果与已有成果；取消不等回滚，不擅自清理。


### 完整离线例：依赖波次和并行写冲突

输入是人工Item与计划proof文字；输出是可并行波次。依赖先后不等实际任务已经完成，proof字段存在也不证明执行。相同波次的父子写对象冲突被拒绝，真实Git合并、撤权和运行恢复另验。

```python
from dataclasses import dataclass
from pathlib import PurePosixPath

@dataclass(frozen=True)
class Item:
    id: str
    dependencies: tuple[str, ...]
    writes: tuple[str, ...]
    proof: str

def canonical(path):
    p = PurePosixPath(path)
    if not path or p.is_absolute() or any(x in ('', '.', '..') for x in path.split('/')):
        raise ValueError('路径')
    return p.parts

def overlap(a, b):
    x, y = canonical(a), canonical(b)
    return x[:len(y)] == y or y[:len(x)] == x

def plan(items):
    ids = [i.id for i in items]
    if not items or any(not i.id or not i.proof.strip() for i in items) or len(set(ids)) != len(ids):
        raise ValueError('空项/重复ID/缺proof')
    lookup = {i.id: i for i in items}
    for item in items:
        if any(d not in lookup for d in item.dependencies):
            raise ValueError('未知依赖')
        for path in item.writes:
            canonical(path)
    done, waves = set(), []
    while len(done) != len(items):
        wave = sorted(i.id for i in items if i.id not in done and set(i.dependencies) <= done)
        if not wave:
            raise ValueError('依赖循环')
        for pos, a in enumerate(wave):
            for b in wave[pos + 1:]:
                if any(overlap(x, y) for x in lookup[a].writes for y in lookup[b].writes):
                    raise ValueError('同波写对象重叠')
        waves.append(wave)
        done.update(wave)
    return waves

items = [Item('contract', (), ('spec',), '合同例反例核对'),
         Item('api', ('contract',), ('app/auth.py',), '局部行为回归'),
         Item('docs', ('contract',), ('docs/auth.md',), '描述与合同一致'),
         Item('integrate', ('api', 'docs'), (), '全局范围与行为验收')]
assert plan(items) == [['contract'], ['api', 'docs'], ['integrate']]
invalids = [items + [items[0]], [Item('x', ('missing',), (), 'p')],
            [Item('a', ('b',), (), 'p'), Item('b', ('a',), (), 'p')],
            [Item('a', (), ('app',), 'p'), Item('b', (), ('app/auth.py',), 'p')],
            [Item('a', (), ('../app',), 'p')], [Item('a', (), (), ' ')]]
for invalid in invalids:
    try:
        plan(invalid)
    except ValueError:
        pass
    else:
        raise AssertionError('坏计划未拒绝')
print('plan: 三波；重复/未知依赖/循环/父子写冲突/坏路径/缺proof全部拒绝')
```

**原实验与源码的实际边界**：原lab检查路径重叠/deps/waves，把docs也声明app/应block。实际PurePosixPath未处理absolute/../symlink/glob，阻断后仍输出waves；没有真实worktree/worker/merge。教育练习不授予新agents或消息，需按当前明确授权执行。

**原五项练习：中文问题与参考判断**

1. **真实变更拆两单元与整合者怎么验？** 各自合同/写对象/owner/proof/取消，整合者另核全局，不能重复重写双方成果。
2. **看似独立实际共享什么？** 找API、设计、状态、依赖或限流，先解决共同决定。
3. **只读research worker能共读吗？** 可以，限制写；事实表保版本/range/unknown，不称已修复。
4. **merge gate核什么？** 实际rename/delete/untracked与各合同、权限、共同行为，不止路径计数。
5. **依赖失效如何取消？** 停止新动作、记录在途效果并查receipt、保未合成果，继续独立合法工作。

**原测验：中文问题与答案**

1. **何时值得并行？** 有真实决策、路径或等待独立，且已授权。
2. **文件系统隔离不保证什么？** 设计/写对象独占，也不提供OS/网络隔离。
3. **每单元为何proof？** 整合者能重现和核对。
4. **写对象重叠怎么办？** 阻断/重拆或明确串行归属；共享只读不是同类冲突。
5. **校准自主是什么？** 证据与恢复强处自主，高后果按真实权限设检查点。
6. **整合者最终责任？** 完整跨单元验收和范围核对。

## 把纠正变为有效控制

纠正先作为观察记录，区分症状、原因假设与反例，再找到最早能有效控制的一层：类型/测试、工具接口、执行权限、运行时、上下文、流程或人类决定。回归应进测试/评测，权限问题要在动作边界预阻；关键词含bug就分给test会错。一次严重事件也可值得控制，不能只按次数。

控制记录稳定ID、项目/对象/风险范围、全部观察、owner、变更、验证和复审/退役条件。fingerprint用于合并同cause证据，不能last-wins丢不同后果。零复发可能是控制有效；只有风险不适用或更强控制经负例证明，再按授权删旧规则。产品反馈与执行反馈合流方法见案例方法论“反馈棘轮”。

**原实验与源码的实际边界**：原lab分类/推广/fingerprint写feedback-ratchet，两句同cause应合并。源码用英文关键词、recurrence≥1全推广，去重丢观测且无owner/retirement；七tests只结构。需要交付“原因证据→实际控制→验证回执”，不是写一个Prevent cause句子。

**原五项练习：中文问题与参考判断**

1. **最近五次纠正怎样找真实owner？** 基于真实症状/证据/影响区分偏好、事实、回归、权限和工具控制，不编用户经历。
2. **一句prose换可执行test怎样验？** 保原范围，有正常/反例assert与实际结果，空checker名字不算。
3. **严重首次可立即推广吗？** 可以，按观察后果和长期维护代价；硬权限不被平均损失抵消。
4. **加owner与退役日有什么意义？** 真实责任、版本、复审事件和退役证据，日期不是自动解除。
5. **删旧指令先证明什么？** 更强控制实际负例、独立阻断与当前适用范围；本批不修改AGENTS。

**原测验：中文问题与答案**

1. **重复纠正揭示什么？** 可能缺少/弱控制，需要原因证据，不能直接断言模型或系统唯一根因。
2. **回归应沉淀哪里？** 测试/评测。
3. **为何先查根因？** 相同症状来自不同控制缺口。
4. **一次纠正何时永久化？** 复发或后果足以抵维护复杂度。
5. **为何fingerprint？** 合并重复而保不同对象、原因及所有证据。
6. **为何需退役复审？** 控制可能过时、冲突或被替代；零触发不等无价值。

来源：AI Engineering from Scratch固定`3be078b37ffd8f0c04953c0678e48f5c6d0c7775`的Phase1431–46；完整课内读取2026-10-08至2026-10-09，增量整理2026-10-09。[轻量来源与许可](../../来源保全/AI-Engineering-From-Scratch.md)。原AGENTS/SKILL/安装/部署/拒绝模板是教育材料，未激活为本任务规则。原定量宣传无相应一手证据不保为事实。上述完整程序只验证明确的标准库fixture与自己的临时文件，源程序、真实宿主/模型/API/服务、Git操作、访谈/试点与线上效果未运行。


## 工作台图示的可学习含义与证据边界

以下12幅最终注册动态图由figures-workbench.js绘制，2026-10-09实际只读全部builder及必要helper/挂载链；未运行browser/build。学习价值是职责、状态、反馈与交接之间的关系，预设动画和数字不能当软件已经执行的证据。

| 原课/图 | 重要关系与纠偏 |
|---|---|
| 31 | 七职责按6秒依次出现并令model边框稳定；没有真实task或收益测量，strip任一必失败是插图设定 |
| 32 | 5秒三文件读写预设运动，无真实文件、schema、taskboard一致性或durability |
| 33 | 4.4秒四rule与pass=[true,false,true,true]固定3/4，非artifact checker |
| 34 | 5秒rev6→rev7/schema菱形与下一session预设，无atomicwrite/fsync/CAS或存储 |
| 35 | 4.6秒四probe全部点亮并开gate，没有运行runtime/deps/tests；不是每任务必须新批准/安装 |
| 36 | 4.2秒固定allowed/forbidden与diff B反弹，未执行glob、path检查或rollback |
| 37 | 5秒预填exit1/stderr→exit0/412ms，无shell/runner或真实重试观察 |
| 38 | 4.6秒前三门开、acceptance never ran阻断，verdict预设，不是真gate计算 |
| 39 | 4.4秒builder→readonly reviewer画墙与报告，没有独立agent/评分/OS权限 |
| 40 | 5.2秒state/verdict/review与下轮first action移动，无实际序列化/恢复，也不保证减少固定分钟 |
| 41 | 4.8秒prompt-only固定1/5而workbench全5/5，没有同repo/模型/任务的实测对照 |
| 42 | 4.8秒文件copy与第二run skipped预设，未运行installer；skip不证明内容相同、安全幂等或可永久复用 |

实际实现分别进入本章的scope/gate、state/CAS与计划波次程序，以及[案例方法论](../../LLM%20工程实践/10-案例方法论.md)成果/指标例。状态程序以两连接手动交错模拟旧revision更新，不声称完成真实线程/多机/断电故障试验；本地receipt为人工假设，不自证外部动作。


## 编码 Agent：比较完整闭环，而不是品牌排名

编码 Agent 先读任务和仓库，再定位依赖、提出修改、编辑、运行可信测试、处理失败并交付 diff 与证据。**Scaffold/Harness** 是包围模型的检索、规划、工具、执行环境、验证和控制结构。换同一模型而改变这些机制，结果也会改变；但跨报告的两个分数不能自动归因于“只有 scaffold 改了”，还须固定任务、预算、模型配置、工具与评测器。

| 机制 | 解决的问题 | 要检查的证据 |
| --- | --- | --- |
| repo map、搜索与最小上下文 | 找错文件、漏调用者 | 正确定位率、未读取依赖导致的失败、敏感文件读取范围 |
| edit/test/feedback 闭环 | 一次生成的补丁可能不工作 | 指定版本实际 exit、失败测试、原回归、测试是否被弱化 |
| 执行环境 | 程序可以读写、联网、运行子进程 | mount、身份、出站、秘密、资源限制、退出后的残留 |
| 完成判据与交接 | 自称完成可能不符合目标 | 用户要求的行为、实际 diff、receipt、unknown 和下一动作 |

**JSON tool call 与 CodeAct 比的是动作表达及执行合同。** 前者把调用写成结构化名称/参数，由宿主校验、授权和执行；后者把若干步骤写成可执行代码，利用循环、变量和异常处理组合工具。JSON 接口也可以支持批处理、一次返回多个调用；CodeAct 的一次代码可能很小。不能把“一次 JSON 恰好改一文件”推广为所有 JSON 架构，也不能因 schema 合法称它安全。一个允许任意 shell 的 JSON 工具仍能产生大量副作用；代码执行环境同样需要真实隔离和出站约束。

OpenHands 的早期研究采用代码/命令/浏览器动作；2026-10-09 的[官方项目 README](https://github.com/OpenHands/OpenHands)还列出本地、Docker、VM 等不同后端，Docker 会话隔离并不把整个服务都放进沙箱。不要从产品名字推出固定安全能力。SWE-agent 的 ACI 关注适合模型的操作反馈；Aider 的修改与仓库上下文、Cline 的编辑器工具政策、托管开发环境及 Claude Code 的权限机制，都是可按上表拆解的设计选择。采用前查看选定版本实际实现与许可证；“最活跃”“最高分”没有固定时间和口径就没有教学价值。

**SWE-bench Pro 是另一个数据集，不能把 Verified 删掉短补丁当作 Pro。** [Pro v1 原论文](https://arxiv.org/html/2509.16941v1)第 1 节按其统计指出 Verified 的 500 题中有 161 题参考补丁只改 1–2 行；其 Pro 收集策略与仓库、访问分组、人工补充要求也改变了，平均参考修改 107.4 行、4.1 文件。短补丁不必然容易，长补丁不必然更真实；GPL 和私有数据可降低部分污染风险，不能证明绝无污染。该版本模型结果是历史实验，源课的 80.9%、43.2/59.8、23–59% 不作为当前排行或固定提升承诺。SWE-bench 最初论文在 2023 年出现，源“2022 原 SWE-bench 4%”时间线不沿用。

源第 09 课 Python 没有调用模型、执行 Python snippet 或运行真实测试，只按字符串内容判断并 `replace` 预定错误。静态推导两边均修好 **3/3**，JSON stub 用 3 次修改加 1 次 done 共 **4 turn**，CodeAct stub 用 1 次集中修改加 1 次 done 共 **2 turn**；“CodeAct 解更多题”与这个程序不符。已观察一次最多触及 1/3 文件，仅属于此 fixture。它适合解释组合性，不适合证明模型性能、沙箱安全或生产收益。

### Phase15 第 09 课练习参考

1. **比较 turns 与影响范围。** 上述 4/2 与 1/3 来自源控制流静态核对，本批未运行源代码；公平试验还须相同真实测试、预算与失败样本，统计整个任务而非只成功动作。
2. **CodeAct 的失效模式。** 已读取[OpenHands ICLR 2025 原论文](https://arxiv.org/pdf/2407.16741v3)§2.1/2.2和Appendix A–B，并视觉核对p18：作者明确旧版agent编辑长文件困难、复杂长任务可靠性不足；大型模块修改时，动作可组合也不能保证正确定位/完整编辑。扩大写入或出站影响是工程风险推断，不伪称论文报告了某个特定攻击。该文也支持将已有函数封装成JSON调用，并非CodeAct和JSON绝不共存。
3. **跨两文件任务的成功概率。** 没有本地任务测量不能给两种架构编造概率。冻结 bug、代码和工具，分别多次运行并保失败、费用、回归与越权，报告样本数和不确定性。
4. **排除短补丁重算。** 先冻结那 161 题的真实 ID；对剩余 339 题计算通过数/339，再按仓库与类型分层。没有逐题预测不能由总分推算新排名，也不能假装完成榜单重算。
5. **Verified 清理能解决什么？** 人工核任务可解、说明/测试一致性等，详解见[评测与实验管理](../../LLM%20工程实践/06-评测与实验管理.md)；仍不能覆盖所有实现、隐藏数据污染、真实上线授权或全部业务后果。

## 权限模式、规则与执行隔离是不同的层

先明确当前任务允许读写的对象、操作、时间和出站，再由执行器落实。权限模式决定哪些调用会走询问/自动审批，**不会凭空创建用户授权或 OS 沙箱**。动作 classifier、固定规则、真实凭据/网络/文件隔离与预算各自承担职责；这些原则也适用于其他工具，具体配置名称不可互换。

2026-10-09 按 [Claude Agent SDK 权限文档](https://platform.claude.com/docs/en/agent-sdk/permissions)与[Claude Code 模式文档](https://code.claude.com/docs/en/permission-modes)核对，以下是理解模型，使用时仍检查客户端、SDK/CLI 版本、组织政策和提供方：

| 模式 | 实际需要理解的合同 |
| --- | --- |
| `default`（界面可称 Manual） | 无模式层额外自动批准；需批准而无允许规则的调用走审批。只读命令等可直接执行，并非每个动作都提示 |
| `plan` | 用于探索和方案；SDK 中编辑不自动通过，走 `canUseTool`，只读仍可运行；CLI 与启用 bypass 的交互会话存在额外差异，不能称“每次读取都审批” |
| `acceptEdits` | 工作目录/额外目录内的文件编辑及部分文件系统命令可自动批准，包括某些 `mkdir/rm/mv/cp/sed`；范围外、保护路径和 critical path 有例外，并非所有 shell 都必须问 |
| `auto` | classifier 对进入该层的动作做允许/拒绝；不代表每个读取或已预批准调用都经相同分类，也不保证没有漏判 |
| `dontAsk` | 原本应弹出询问的调用改为拒绝；既有无需批准的读取/工具和预批准调用仍可执行，不是“只允许清单中工具” |
| `bypassPermissions` | 跳过许多提示，仍有 deny、hooks、明确 ask、交互与 critical-path 等例外；不自动提供外部隔离 |

`allowed_tools` 是**自动批准规则**，未列出的工具未必从能力集合消失；bare `disallowed_tools` 可移除某工具，模式和路径规则也会影响。官方 SDK 图的顺序是 hooks→deny→ask→mode→allow→callback；`canUseTool` 可能因前层已批准而不被调用，需要对全部调用施加硬 gate 时看 `PreToolUse` 及真实执行权限。不能用字符串子串匹配域名或含某命令就断言工具安全。更新可能改变默认模式；当前文档已有版本依赖的 auto 默认，笔记不固定“省略配置永久等于 default”。

源第 10 课“两阶段”仅是 keyword＋规则教学模拟，不是 Claude classifier 架构契约。其 Stage1 已检查连续 5 次相同调用，随后 Stage2 才拒绝；不存在默认样本中“Stage1 从不 flag、Stage2 总能抓住”的路径。Stage2 先见任意允许域名子串就批准，`pypi.org.attacker.example` 或“合法 curl 后串另一个危险动作”都可误过。最后读假凭据→写临时文件→push 是预设 composite，不证明真实凭据已泄露，也不意味着这些读取都已授权。

### Phase15 第 10 课练习参考

1. **两层各抓什么？** 合法域 curl 是 S1 flag/S2 clear；危险 curl、根删除、sudo 与第 5 次相同调用先被 S1 flag 再 S2 block；末尾 composite 未 flag。题中“仅 S2 能抓且 S1 不 flag”与“只对 flagged 调 S2”的代码矛盾。
2. **增加 URL 检测。** 结构化解析 scheme/hostname/port，精确 origin 与重定向控制，再核动作/body/出站数据；测试伪装域、userinfo、重定向、允许请求与非允许请求。用误报数/真实良性样本数报告，不从单例猜误报率。
3. **哪些状态可接触？** 取决于工具、目录、身份、mount、网络与 callbacks，不能把产品的 default 当固定全机访问清单。列本任务文件读写、shell、网络、秘密、会话，再在真实执行边界收窄。
4. **长时预算。** 根据任务数量、调用上界、使用定价和容忍损失设置总任务/每次调用/每工具/时间窗限制；24 小时是题设，不给普遍推荐额度。暂停与恢复仍接同一外部预算账本。
5. **组合风险。** 读取敏感材料后把内容写入允许目录并上传可以逐动作看似正常，却跨越数据目的地授权；执行器绑定数据来源、对象、sink 与 task scope，不能只核工具名。

## 浏览器任务：页面是证据输入，不能自行授予动作权限

浏览器 Agent 对页面/截图/DOM/URL/下载和历史记忆做观察，再点按、输入或调用工具。一次网站数据访问许可不等于购买、发送或改权限许可；已有具体同事项授权可复用，网页声称“用户已同意”不能替代真实授权。[OpenAI 官方 computer-use 文档](https://developers.openai.com/api/docs/guides/tools-computer-use)于 2026-10-09 核对了屏幕内容不可信及需保留用户对重大动作的控制，输入敏感信息到表单也算传输。不同执行器的 origin gate、操作 gate 与登陆流程必须分别验收。

例如“查机票并整理选项”先允许检索、比较，产出带日期/退改/费用的候选；“购买某班次”是另一个具体对象和操作。若网页或 URL fragment 要求额外发账户资料，执行器不因网页指令改授权。检索结果、评论、first-party 页面里的用户内容、持久记忆均可能包含攻击；可信托管域不使其中每段内容可信。

| 输入/动作 | 风险边界 | 合适的控制 |
| --- | --- | --- |
| HTML、截图、URL fragment/query | 数据伪装成工具指令；payload 也可未显示 | 保留来源/可信等级；模型理解材料，宿主独立核动作 |
| 已登录读取、秘密读取 | 访问日志、cookies、恶意 GET、敏感内容暴露 | scoped 身份/会话、精确读取范围和数据最小化；读也可能有后果 |
| 写长期记忆 | 攻击指令进入下一会话 | 来源/版本/审核/过期，与已授权用户偏好分开 |
| 表单提交、下载、外部通信 | 改状态、泄露数据、触发文件内容 | 按授权核 endpoint/body、工具可达范围和文件处理；必要人工 gate |

Sanitizer 能删除已知表达，却会漏同义/编码/多模态 payload，也可能误删合法说明；它不是安全判决。URL/HTML 一起输入时，应处理两种来源，不能因为 fragment 没渲染就忽略。Source toy 用 `"exfil"` 字符串决定 attack，再由同一分支标记 `content_origin="page"`；真实产品不能把模型自报的 origin 当不可伪造权限证据。

BrowseComp 测搜寻具体事实，WebArena 测模拟网站流程，OSWorld 测桌面动作；不能把一个分数换算成另一个业务成功率。版本、步数预算、身份和 scoring 不同都影响结果。源产品并购因果、SOTA 与袭击年份不保留为当前事实。WebArena-Verified当前发布README标Hard子集258题，早期论文检索片段则为137；不能在未锁定套件/论文版本时混用，也不把未全文核定的11.3%当普遍误判率。详细主库已有[交互与动作空间](03-交互与动作空间.md)与[安全模式](../01-核心章节/18-安全模式.md)，无需新建浏览器来源副本。

核对版本为ServiceNow/webarena-verified `6473f72db5dcefc97b5725b59e734504edc28a21`。[官方评价合同](https://github.com/ServiceNow/webarena-verified/blob/6473f72db5dcefc97b5725b59e734504edc28a21/docs/evaluation/index.md)给每题一个结构化回答评价器，并按任务配零到多个网络事件评价器，支持捕获HAR后的离线重评。比如用户要求取得数据，只有NAVIGATE而没有RETRIEVE结果就不应算完成；类型规范化应保语义，不能把不同实体压成同值。

[移除模型裁判的具体方法](https://github.com/ServiceNow/webarena-verified/blob/6473f72db5dcefc97b5725b59e734504edc28a21/docs/evaluation/removing_llm_based_evaluation.md)包含在意图中明确输出结构，以及把开放摘要改为可核对的检索，例如改问低评分评论的标题。后者改变了任务本身，比较新旧成绩时须记录；可重复的评价器也可能有错误，不能以确定性替代正确性或把HTTP200自动当业务已持久成功。本次只读合同，未安装环境或执行评价器。

### Phase15 第 11 课练习参考

1. **sanitize/RW 的差别。** 源可见注入被 sanitizer 移除；fragment 留在 URL 被漏掉；toy 的 origin gate 能拦两者。所以没有“sanitize 抓住而 RW 抓不住”的该源样本。本批只是静态审查，不执行网站。
2. **fragment 误报。** 合法 `#section-2`、编码片段、含可疑词的普通标题与真正越界动作都须覆盖。标记可疑片段不自动把合法导航禁止；最终仍核执行 sink。没有良性 corpus 不报告数值误报率。
3. **业务 read/write 清单。** 航班查询含页面/身份读取；加入订单、提交乘客信息、付款、发邮件均有不同后果。按用户已授权对象和真实规则设 gate，不把所有读取称零风险或所有可逆动作强制再问。
4. **评分可靠性。** 固定官方发布文档说明可将月份等数据按类型规范化后比较，避免文本表面差异；检索任务还要核task_type与取得的数据，不能只到正确网页就通过。对不可达任务使用明确错误状态，避免含糊的N/A。这里给出本次核对的官方实现机制，不冒作未读论文的逐页案例；逐题结果与真实最终效果仍需独立审核。
5. **记忆 canary。** 用无真实权限的 sentinel，放在正常任务不应读取/输出的独立受控对象，监控访问/回显并关联 task/call ID；告警器在 Agent 外。合法整理资料本来会读的条目不应被当攻击证据。

### 图示与新增自检的范围

第 09 静图和 `a5-scaffold-delta` 把固定 43.2/59.8 画成宽度，6 秒变化并非采样；第 10 权限阶梯忽略上面的例外，`autonomy-oversight` 的 10/30/55/75/92 是预设风险示意，未接 classifier；第 11 静图可解释输入→观察→sink，`injection-boundary` 的 3 次 bounce/1 次 slip 是动画，不是 75%防御率或真实攻击评测。图只能帮助找到控制层，不能替代授权、隔离或测试。

新增自检（源 09–11 **没有 quiz**）：①schema 合法是否安全？不，仍核对象/权限/副作用；②`allowed_tools` 是否删掉其他工具？不是；③`plan` 是否每个读取都问？不是；④被动读取是否必定无影响？不是；⑤相同模型两报告差 16.6 点是否证明只因 harness？须控制全部相关条件；⑥网页能否授权新增出站？不能；⑦来源图的防御比例可否拿来验收？不能。

以上吸收固定来源 Phase15 第 09–11 课，完整正文/代码/模板/SVG阅读与一手相关章节核验为 2026-10-09；原代码未执行，未登陆网站、跑模型、安装或启动 Agent。
