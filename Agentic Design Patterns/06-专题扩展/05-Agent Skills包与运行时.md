# Agent Skills：目录包、运行时与可验证交付

Skill 把可重复的方法、分支知识、确定性脚本与输出合同组成一个可发现目录包。它适合“收集同一类证据、作判断、交付有验收标准的产物”，例如只读检查一个已经准备的发布候选。仅有“Kubernetes 技能”这样的主题名，还没有输入、触发边界或完成证据。先修是[工具调用合同](../01-核心章节/05-工具使用.md)、[结构验证](../../LLM%20工程实践/13-结构化输出与对话状态.md)与[安全模式](../01-核心章节/18-安全模式.md)。本页不要求安装宿主或执行来源包，三个完整标准库例子只处理自己创建的临时 fixture。

## 1. 按职责选择：一次提示还是可复用包

先问真实工作何时开始、相似但不该触发的任务是什么、证据从哪来、哪些判断随输入变化、哪些步骤可确定计算、产物怎样验收。把稳定的判断流程写进 Skill，把解析、计数和完整性检查交给普通代码；不要让模型手工模拟解析，也不要把主观架构判断隐藏成一个 opaque script。

| 需要 | 合适单元 | 必须另外解决 |
|---|---|---|
| 一次生成或改写 | Prompt | 本轮输出核对 |
| 仓库长期约定 | AGENTS.md | 适用目录、指令优先级 |
| 多次使用的任务方法 | Skill | 发现、调用资格、工具权限、产物验收 |
| 读取外部服务或执行 typed 操作 | 普通工具/MCP | 身份、对象范围、副作用、返回合同 |
| 每次事件必须发生的检查 | Hook/应用程序 | 事件时点、失败阻断、可靠执行 |
| 固定格式转换和验证 | 普通代码 | 输入边界、错误和测试 |
| 已授权的独立上下文或所有权 | Subagent | 委派范围、合并、消息和退出合同 |
| 分发复合能力 | Plugin | 安装、依赖、版本、目标宿主适配 |

这些单元可组合。发布检查 Skill 可以用 MCP 读取候选状态，用仓库约定找到测试入口，用 Hook 强制某事件检查，用普通程序核哈希；命名一个工具不创造能力，装一个 Skill 不创造权限。研究中的“学到的 skill library”常指成功轨迹、策略或环境程序，它与 authored `SKILL.md` 目录有不同创建、检索和评价合同，不能因为同名就共享效果结论。

## 2. 可移植核心、伴随资源与宿主扩展

```text
release-review/
  SKILL.md                    身份、触发、核心流程、分支与失败出口
  references/contract.md      所选分支的领域规则
  scripts/inspect.py          独立可测的确定性计算
  assets/report-template.md   产物材料
  evals/cases.json            包作者的评价用例，非通用必需目录
```

目录是部署、校验、升级和移除的单元。只复制入口、丢掉脚本和 reference 会使流程无法复现。可移植标准要求 frontmatter `name/description`，name 与父目录一致；optional license、compatibility、字符串 metadata、实验性 allowed-tools 各有自己的格式。正文没有统一模板限制，伴随文件和目录也不是只有上面几种。三级披露、入口少于500行和直接 reference 是组织建议；某课程的一层物理深度、suffix allowlist、10K字符或1MB限制是发布政策。[Agent Skills Specification](https://agentskills.io/specification)（2026-10-08 全文核对，未运行标准验证库）。

入口应让人加载后就能开始：范围、默认步骤、分支条件、直接资源路径、工具/脚本合同、输出与失败行为。不要为了缩短入口把核心流程藏进“相关 reference”。每个 resource 有明确加载条件，例如 Python 包才读 python-release，容器候选才读 container-release，公共报告模板由所有分支使用。reference 负责知识，script 负责计算，asset 负责产物材料；这些目录名不会自动产生执行能力。

前置元数据会在正文加载之前影响路由。把它当配置代码审查：模糊 description 可能过度触发，名字冲突造成误选，未知 extension 可能被忽略或拒绝。Claude Code 的 user-invocable 与 disable-model-invocation 是两个宿主维度，不是核心字段；前者 false 影响用户显式入口，后者 true 抑制模型调用。其它运行时不能自动继承意义。[Claude Code Skills](https://code.claude.com/docs/en/skills)（只核 frontmatter 与跨产品边界）。

2026-10-08 的 Codex 官方说明：CLI/IDE 用 `/skills` 或 `$` 明确选择，隐式由 description 匹配；项目发现从当前目录的 `.agents/skills` 向仓库根扫描，加用户、管理员和内置位置；同名不合并，支持 symlink 目录。`agents/openai.yaml` 的 allow_implicit_invocation false 仍保留显式调用。初始列表的2%预算与窗口未知时8000字符 fallback 是两种条件，且只约束目录，不约束选中正文。[OpenAI Build skills](https://learn.chatgpt.com/docs/build-skills) 本次仅核文档，不改当前配置；普通文本命名是否被当明确选择，仍应查看宿主可观察记录。

## 3. 发现、选择、执行和完成是不同状态

```mermaid
flowchart LR
    A[显式作用域] --> B[浅层候选与物理树检查]
    B --> C[身份/元数据与来源]
    C --> D[碰撞政策与目录预算]
    D --> E[按actor过滤资格]
    E --> F{相关性/阈值/领先差}
    F -->|无匹配| G[弃答或普通推理]
    F -->|有歧义| H[请求澄清]
    F -->|明确| I[加载入口与所需分支]
    I --> J[宿主能力/授权/隔离下执行]
    J --> K[产物与独立核验]
```

Discovery 找候选；validation 检身份、大小和树；catalog 把 name/description/scope/source 交给模型；selection 选相关方法；activation 只让正文进入上下文；execution 才涉及工具/模型工作；completed 要以输出合同核验。一个 `skill_used=true` 会遮蔽失败位置，不能用发现、激活或 fluent report 代替执行证据。

### 碰撞政策与两种上下文预算

同名可保留全部、用声明的作用域优先级选一、拒绝重复或用 source 限定身份。各有取舍：workspace override 可帮助定制，也可能影子覆盖可信包；保留全部有歧义；拒重会阻止合理覆盖。优先级不是标准规定，也不能由修改时间、目录遍历顺序或名字猜出。同优先级重复要报 ambiguous，shadowed/rejected 候选留诊断。浅发现不把包内 examples 的 SKILL.md 误当独立安装包。

令 `c_i` 是目录条目的实际序列化成本，`b_j` 是激活正文成本，`r_k` 是确实读入模型的资源成本：catalog=Σc_i，active=Σb_j+Σr_k。单位必须注明，不能把字符或 UTF-8 bytes 直接当 tokens。缩 description 可能删掉排除条件，缩目录不自动缩已激活900行正文；拆 reference 也只有按分支加载才省上下文。宿主为了校验读取文件与文件进入模型上下文是不同事件。

资源先检查相对规范路径，再查 root 内真实目标、regular file、symlink 政策与大小。`references/../../secret`、`./SKILL.md`、反斜线、绝对路径和通向外部的 symlink 不应混入同一可移植地址。先限读取，再验内容；stat 后 open 仍可能有竞态，强执行器需文件描述符绑定。路径在包内并不证明内容可信。加载日志记录 skill/resource/reason/bytes，不写秘密正文。

### 调用资格在相关性排名之前

人类可显式调用与模型可隐式选择组成2×2；application、skill composition、harness 有额外精确身份、caller、target allowlist 和深度合同。最高词面分数被禁用时应先移出集合，再选可用者。例：incident-triage=.90但禁 model，incident-review=.55且许可，应考虑后者。资格决定可选集，相关性决定集内排序，二者不能合成一个不透明分数。先独立验证阈值与margin政策；过滤后才读取、检查可用候选的分数。禁用项缺score或NaN不应阻止合法候选，全部禁用应直接返回 none_eligible。

阈值不足返回 abstain；第一和第二名差距不足返回 ask 或正常推理，不能靠字母顺序伪装明确结果。positive、paraphrase、clear negative、near miss、竞争技能和否定/引文任务分别测。问“为什么 build 失败”不应自动执行发布评估，即使含 package/release。英文词面 Jaccard 只是解释基线，不证明中文语义或模型路由效果。

调用另一个 Skill 是运行时依赖边，非语言 import。传 target identity、bounded task、输入路径、输出合同、fallback、visited chain 与最大深度；A→B→A 不会被“只禁止自己调自己”挡住。用户文字经 host parser/quoting、bound values、Skill 上下文，再到 typed tool argv，每跨一界都重新验证；文字不能插值成 shell 代码。中断后重读持久 artifact、重验候选版本和效果状态，不能因压缩忘记某外部写入已提交但结果未知。

### 完整离线例一：目录、预算、资格、歧义和路径

下面创建独立 `/tmp` fixture scope，项目与用户有同名包。解析器仅支持两个单行字符串字段，是明确的教学子集；正式 YAML 需安全解析库与类型/大小策略。目录预算按完整 JSON 的 UTF-8 字节计算。路由分数人工给定，host eligibility 人工政策；不能把输出当真实宿主或模型的选择记录。

```python
import json
import math
import re
import tempfile
from pathlib import Path, PurePosixPath

NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

def clean_relative(value):
    if type(value) is not str or not value or "\\" in value:
        raise ValueError("path_shape")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or path.as_posix() != value:
        raise ValueError("path_not_canonical")
    return path

def bounded_resource(bundle, relative, limit=4096):
    if type(limit) is not int or limit < 1:
        raise ValueError("size_policy")
    rel = clean_relative(relative)
    target = bundle
    for part in rel.parts:
        target /= part
        if target.is_symlink():
            raise ValueError("symlink")
    root, resolved = bundle.resolve(), target.resolve()
    if resolved == root or root not in resolved.parents or not target.is_file():
        raise ValueError("resource_boundary")
    if target.stat().st_size > limit:
        raise ValueError("resource_size")
    data = target.read_bytes()
    if len(data) > limit:
        raise ValueError("resource_size")
    return data

def discover(scopes):
    # scopes由调用方按高到低排序；这是课例政策，并非某产品默认。
    candidates, names_at_rank, ranks = [], set(), {}
    for scope, root in scopes:
        rank = ranks.setdefault(scope, len(ranks))
        if root.is_symlink() or not root.is_dir():
            raise ValueError("scope_boundary")
        for bundle in sorted(root.iterdir()):
            if bundle.is_symlink():
                raise ValueError("package_symlink")
            if not bundle.is_dir() or not (bundle / "SKILL.md").exists():
                continue
            text = bounded_resource(bundle, "SKILL.md").decode("utf-8")
            parts = text.split("---\n", 2)
            if len(parts) != 3 or parts[0] != "":
                raise ValueError("frontmatter")
            fields = {}
            # 此例只接收name/description单行字符串；不声称完整YAML解析。
            for line in parts[1].splitlines():
                key, sep, value = line.partition(": ")
                if not sep or key in fields or key not in {"name", "description"}:
                    raise ValueError("metadata")
                fields[key] = value
            name, desc = fields.get("name", ""), fields.get("description", "")
            if (not NAME.fullmatch(name) or len(name) > 64 or name != bundle.name
                    or not desc.strip() or len(desc) > 1024 or not parts[2].strip()):
                raise ValueError("identity")
            if (rank, name) in names_at_rank:
                raise ValueError("equal_precedence_duplicate")
            names_at_rank.add((rank, name))
            candidates.append({"name": name, "description": desc, "scope": scope,
                               "path": str(bundle), "rank": rank})
    return candidates

def catalog(candidates, max_entries=10, max_bytes=6000):
    if any(type(v) is not int or v < 1 for v in (max_entries, max_bytes)):
        raise ValueError("catalog_budget")
    winners, shadowed = {}, []
    for item in sorted(candidates, key=lambda x: (x["rank"], x["name"])):
        if item["name"] in winners:
            shadowed.append(item)
        else:
            winners[item["name"]] = item
    entries, omitted = [], []
    for item in winners.values():
        entry = {key: item[key] for key in ("name", "description", "scope", "path")}
        candidate = entries + [entry]
        size = len(json.dumps(candidate, ensure_ascii=False, separators=(",", ":")).encode())
        if len(candidate) > max_entries or size > max_bytes:
            omitted.append(item["name"])
        else:
            entries = candidate
    used = len(json.dumps(entries, ensure_ascii=False, separators=(",", ":")).encode())
    if used > max_bytes:
        raise ValueError("empty_catalog_does_not_fit")
    return {"entries": entries, "shadowed": shadowed, "omitted": omitted,
            "catalog_bytes": used, "unit": "UTF-8 bytes"}

def route(entries, eligibility, score_by_name, threshold=0.3, margin=0.1):
    # 分数是显式fixture；不是模型输出，不称生产分类准确率。
    if any(type(v) not in (int, float) or not math.isfinite(v) or not 0 <= v <= 1
           for v in (threshold, margin)):
        raise ValueError("score_policy")
    allowed = [e for e in entries if eligibility.get(e["name"]) is True]
    if not allowed:
        return {"status": "abstain", "reason": "none_eligible"}
    # 被禁项不读score：缺分数或NaN不能压住合法候选。
    scores = [score_by_name[e["name"]] for e in allowed]
    if any(type(v) not in (int, float) or not math.isfinite(v) or not 0 <= v <= 1 for v in scores):
        raise ValueError("score_policy")
    scored = sorted([(score_by_name[e["name"]], e) for e in allowed],
                    key=lambda x: (-x[0], x[1]["name"]))
    best, entry = scored[0]
    if best < threshold:
        return {"status": "abstain", "reason": "below_threshold"}
    if len(scored) > 1 and best - scored[1][0] < margin:
        return {"status": "ask", "reason": "ambiguous"}
    return {"status": "selected", "entry": entry}

def compose(caller, target, visited, maximum=2):
    return target != caller and target not in visited and len(visited) < maximum

def make(root, name, desc):
    bundle = root / name
    (bundle / "references").mkdir(parents=True)
    (bundle / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: {desc}\n---\n\nRead references/contract.md.\n")
    (bundle / "references" / "contract.md").write_text("只读检查；返回有证据的结论。\n")
    return bundle

with tempfile.TemporaryDirectory(prefix="study-skill-fixture-") as td:
    base = Path(td).resolve()  # 由本程序创建的可信临时根。
    project, user = base / "project", base / "user"
    make(project, "release-review", "核验已准备发布包；不处理构建失败。")
    make(user, "release-review", "通用发布检查。")
    other = make(user, "incident-review", "解释故障证据。")
    candidates = discover([("project", project), ("user", user)])
    cat = catalog(candidates)
    assert len(cat["shadowed"]) == 1
    assert next(e for e in cat["entries"] if e["name"] == "release-review")["scope"] == "project"
    try: discover([("project", project), ("project", project)])
    except ValueError as error: assert str(error) == "equal_precedence_duplicate"
    else: raise AssertionError("equal_rank")
    assert len(catalog(candidates, max_entries=1)["omitted"]) == 1
    assert cat["catalog_bytes"] <= 6000
    policy = {"release-review": False, "incident-review": True}
    chosen = route(cat["entries"], policy, {"release-review": .9, "incident-review": .55})
    assert chosen["entry"]["name"] == "incident-review"
    assert route(cat["entries"], policy, {"incident-review": .55})["entry"]["name"] == "incident-review"
    assert route(cat["entries"], policy, {"release-review": float("nan"), "incident-review": .55})["entry"]["name"] == "incident-review"
    assert route(cat["entries"], dict.fromkeys(policy, False), {}) == {"status": "abstain", "reason": "none_eligible"}
    try: route(cat["entries"], policy, {"incident-review": float("nan")})
    except ValueError as error: assert str(error) == "score_policy"
    else: raise AssertionError("eligible_score")
    try: route(cat["entries"], dict.fromkeys(policy, False), {}, threshold=float("nan"))
    except ValueError as error: assert str(error) == "score_policy"
    else: raise AssertionError("threshold_policy")
    assert route(cat["entries"], dict.fromkeys(policy, True),
                 {"release-review": .55, "incident-review": .52})["status"] == "ask"
    assert route(cat["entries"], policy,
                 {"release-review": .9, "incident-review": .1})["status"] == "abstain"
    assert not compose("a", "a", ["a"]) and not compose("b", "a", ["a", "b"])
    loaded = bounded_resource(other, "references/contract.md")
    assert len(loaded) > len(loaded.decode())  # 中文bytes和chars不等。
    for rel in ("../secret", "./SKILL.md", "references/../SKILL.md", "/etc/passwd"):
        try: bounded_resource(other, rel)
        except ValueError: pass
        else: raise AssertionError("escape_or_noncanonical")
    (other / "references" / "linked.md").symlink_to(other / "SKILL.md")
    try: bounded_resource(other, "references/linked.md")
    except ValueError as error: assert str(error) == "symlink"
    else: raise AssertionError("symlink")
    try: bounded_resource(other, "references/contract.md", limit=1)
    except ValueError as error: assert str(error) == "resource_size"
    else: raise AssertionError("size")
print("目录身份/碰撞/字节预算/资格先过滤再检查可用分数（禁用项缺score或NaN不阻断）/歧义弃答/循环/路径反例通过；未安装或执行Skill")
```

程序读取 entry 以校验，但只把精简目录发布；正文/参考的模型准入应另记三级日志。symlink 示例指向包内文件也拒绝，说明这是本例保守政策，不能据此声称所有 host 都拒绝 symlink。文件读取与本地索引无需安装 Skill；本例没有加载它为本次指令。

## 4. 激活不授予动作权限

五层要分别回答：capability 是否暴露操作；policy 是否许可该 actor/目标；approval 谁接受这项后果；sandbox 进程可到哪里；verification 结果是否满足合同。Skill/reference 影响程序选择，但本轮用户目标与硬政策仍约束它；网页、issue、email、image、tool result 是资料或观察，不能发出当前用户的授权。

动作提案应先成为数据：actor、operation、argv、cwd、read/write targets、HTTPS origins、credential scopes、side effects、reason。脚本合同还应写参数、输入格式、输出路径、独立验收、时间/输出上限、exit codes 与失败后的状态。实际执行证据需要 **已解析 script path、target path、cwd、argv、exit 与产物**；`scripts/check.py` 的相对拼接依赖 cwd，不能拿“已运行 checker”代替这几个观察。许可集合和真实 executor 独立于 Skill 内容，来源 canonical SKILL/AGENTS 在阅读任务中只是数据。

| 控制 | 能约束什么 | 仍不能证明 |
|---|---|---|
| 不注册 shell | 模型不能通过该能力请求 shell | 其它已注册工具安全 |
| 按对象限制读写 | 操作范围 | 业务判断正确 |
| 针对候选/目标的批准记录 | 具体后果授权 | 代码执行隔离 |
| 限文件/网络/环境/资源的执行器 | 可达后果 | 修改是用户所需 |
| 输出/差异/回读验收 | 已观察结果 | 后续新动作授权 |

`allowed-tools` 不建立 OS 隔离；`shell=False` 也不阻止解释器运行任意代码。python、package manager、tests 可能执行仓库受控 hooks；只允一个 bare executable 或 argv prefix 仍不足。应固定真实 executable、被审脚本/参数、cwd、环境 allowlist、凭据、deadline、输出/进程/内存限制和 egress。对未知代码的真实隔离见[安全模式](../01-核心章节/18-安全模式.md)，这里的 reviewer 没有 launch 路径。

HTTPS origin 包含 scheme、规范 host 与 effective port；默认443和显式443等价，8443另需许可。拒 userinfo，redirect 每一跳重新审查目标与可发送资料；文件沙箱不限制 DNS/HTTP 外传。秘密 regex 只能提供信号，不能证明任意文字无敏感内容。hash 证明 bytes 一致，signature/attestation 证明某身份认可一个声明，仍要检查声明含义及认可者职责。

### 完整离线例二：只决定，不启动命令或网络

该例检查精确 argv、cwd/target 作用域、origin、可能秘密及与请求摘要绑定的模拟批准。批准记录由调用方代表 host 提供，不能由 Skill 自写；改 target 后旧批准失效。`allow/ask/deny` 均保持 executed=false，没有任何 subprocess、URL 请求或目标文件写入。根由程序自己创建，校核根之下的组件；未证明宿主任意祖先目录或 TOCTOU 竞态安全。

```python
import hashlib
import ipaddress
import json
import re
import tempfile
from pathlib import Path
from urllib.parse import urlsplit

def origin(url):
    if type(url) is not str:
        raise ValueError("url_type")
    p = urlsplit(url)
    if p.scheme != "https" or not p.hostname or p.username is not None or p.password is not None:
        raise ValueError("https_origin")
    host = p.hostname.rstrip(".").lower()
    try:
        address = ipaddress.ip_address(host)
        host = f"[{address.compressed}]" if address.version == 6 else address.compressed
    except ValueError:
        host = host.encode("idna").decode("ascii")
        if not all(re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", label) for label in host.split(".")):
            raise ValueError("hostname")
    port = 443 if p.port is None else p.port
    if not 1 <= port <= 65535:
        raise ValueError("port")
    return f"https://{host}:{port}"

def contained(root, raw):
    if type(raw) is not str:
        raise ValueError("path_type")
    root = root.resolve()
    candidate = Path(raw) if Path(raw).is_absolute() else root / raw
    resolved = candidate.resolve()
    if resolved != root and root not in resolved.parents:
        raise ValueError("outside_scope")
    # 校核配置根之下每个已存在的组件；本例固定根由自身创建。
    relative = candidate.relative_to(root)
    current = root
    for part in relative.parts:
        if part == "..":
            raise ValueError("parent_segment")
        current /= part
        if current.is_symlink():
            raise ValueError("symlink")
    return str(resolved)

def action_digest(request):
    return hashlib.sha256(json.dumps(request, ensure_ascii=False, sort_keys=True,
                                    separators=(",", ":"), allow_nan=False).encode()).hexdigest()

def review(request, root, allowed_argv, origins, approved_digests=frozenset()):
    fields = {"actor", "kind", "target", "cwd", "argv", "url", "payload"}
    if type(request) is not dict or set(request) != fields:
        return {"verdict": "deny", "reason": "request_shape", "executed": False}
    def result(verdict, reason):
        return {"verdict": verdict, "reason": reason, "executed": False}
    if (request["actor"] != "skill:release-review" or type(request["kind"]) is not str
            or request["kind"] not in {"read", "write", "command", "network"}
            or type(request["argv"]) is not list
            or any(type(v) is not str for v in request["argv"])
            or type(request["payload"]) is not str):
        return result("deny", "closed_request_contract")
    if re.search(r"(?i)(api_key|password|access_token)\s*[:=]", request["payload"]):
        return result("deny", "possible_secret")  # 不回显秘密。
    try:
        contained(root, request["cwd"])
        if request["kind"] in {"read", "write"}:
            contained(root, request["target"])
        elif request["kind"] == "command":
            if tuple(request["argv"]) != allowed_argv:
                return result("deny", "argv_identity")
        elif origin(request["url"]) not in origins:
            return result("deny", "origin_allowlist")
    except (ValueError, UnicodeError):
        return result("deny", "target_boundary")
    if request["kind"] != "read" and action_digest(request) not in approved_digests:
        return result("ask", "exact_action_approval")
    return result("allow", "bounded_policy")

with tempfile.TemporaryDirectory(prefix="study-action-review-") as td:
    base = Path(td).resolve()
    root = base / "workspace"; root.mkdir()
    outside = base / "outside"; outside.mkdir()
    argv = ("/Users/wangshuiqing/codex-tools/bin/python3", "-I", str(root / "inspect.py"))
    req = {"actor": "skill:release-review", "kind": "read", "target": "report.json",
           "cwd": str(root), "argv": [], "url": None, "payload": "public fixture"}
    assert review(req, root, argv, set())["verdict"] == "allow"
    write = dict(req, kind="write")
    assert review(write, root, argv, set())["verdict"] == "ask"
    approvals = frozenset({action_digest(write)})  # 模拟宿主针对精确请求的记录。
    assert review(write, root, argv, set(), approvals)["verdict"] == "allow"
    assert review(dict(write, target="different.json"), root, argv, set(), approvals)["verdict"] == "ask"
    assert review(dict(req, target="../secret"), root, argv, set())["verdict"] == "deny"
    assert review(dict(write, payload="api_key=fixture"), root, argv, set(), approvals)["verdict"] == "deny"
    cmd = dict(req, kind="command", argv=list(argv))
    assert review(cmd, root, argv, set())["verdict"] == "ask"
    assert review(dict(cmd, argv=["python3", "-c", "anything"]), root, argv, set())["verdict"] == "deny"
    assert origin("https://BÜCHER.example") == origin("https://xn--bcher-kva.example:443/path")
    net = dict(req, kind="network", url="https://api.example.test:8443/data")
    assert review(net, root, argv, {"https://api.example.test:443"})["verdict"] == "deny"
    for url in ("https://user:pass@api.example.test", "https://api.example.test:0"):
        try: origin(url)
        except ValueError: pass
        else: raise AssertionError("origin")
    (root / "link").symlink_to(root / "report.json")
    assert review(dict(req, target="link"), root, argv, set())["verdict"] == "deny"
    (root / "escape").symlink_to(outside, target_is_directory=True)
    assert review(dict(req, target="escape/file"), root, argv, set())["verdict"] == "deny"
print("动作摘要绑定目标/argv/cwd/作用域/HTTPS有效端口/秘密与symlink审查通过；executed始终False")
```

approval 的文字应展示候选 hash、操作、目标、stage/prod、影响和回滚条件。已授权的可逆范围可直接执行，局部 hard deny 不能靠“用户点过 allow”变 allow。实际 executor 启动前重新核相同归一目标/命令/批准身份，独立施加 isolation；批准不能关闭 sandbox，也不授权下一个对象。容器会共享 kernel，mount home/socket 或带 production secrets 可破坏限制；微虚拟机也要管 mounts、credentials 和 egress。本次不拉镜像或运行容器 probe。

## 5. 六层评测：目录正确还不是工作有效

先定义产物、验证方法、采证工具和决策图，再写 entry 与 description。评价按层保留，不能让 prose 得分抵消 authority failure：

| 层 | 测量 | 失败时修哪一层 |
|---|---|---|
| 结构 | 入口、核心字段、直接引用、物理树、大小、类型、输出/失败合同 | 包结构与 parser |
| Trigger routing | 正负/近邻/竞争、弃答、raw TP/FP/TN/FN、重复稳定性 | description、eligibility、router |
| Artifact behavior | 同任务 baseline/treatment 的事实、覆盖、证据、范围、恢复、人工修正 | procedure、reference、tool合同 |
| Scripts | 空/坏输入、Unicode/空格路径、重跑、partial output、timeout/exit | 确定性程序 |
| Safety/authority | 注入、路径/网络/凭据、越权、循环、重复副作用 | policy、approval、真实sandbox |
| Install/portability | clean destination、manifest、逐宿主能力/adapter/fallback | installer、版本与host adapter |

precision=TP/(TP+FP)，recall=TP/(TP+FN)，F1为二者调和平均。8TP/2FP 的 precision=.8；不知道 FN 就不知道 recall。报告原始数和每次预测，不只一个平均；十次与一百次全对的证据量不同，重复同一人工答案也不产生一百个独立任务证据。先分 development/validation，再改 description；重要门禁还保留 held-out。真实 trigger 要通过目标 host/model/catalog/policy，精确 harness activation 用于隔离程序行为，不能替代生产路由。

baseline/treatment 用同任务、工具、模型、采样政策、预算与输入；唯一差异是可用 Skill 或包版本。比较 correctness、completeness、tool calls/time/tokens、证据、scope、恢复及人类修正。每任务重复，保留 regressions 和分层失败。assertion 必须指真实产物证据：标题出现不等有实质内容，关键词出现不等结论正确。开发迭代可以修评价器，最终决定前冻结合同和留出集，不能按失败结果改 gold。[Agent Skills Evaluating output quality](https://agentskills.io/skill-creation/evaluating-skills)（本次全文核方法，未启动模型实验）。

### Manifest、独立采集与可信声明

manifest 用规范相对 POSIX path→原始 bytes SHA-256；拒 `./`、absolute、backslash、parent，以及 missing/unexpected/mismatched。`assets/manifest.json` 保留为元数据，排除自身哈希域，真实性由外层可信渠道确认。相同文义的 LF/CRLF 变化也应报 drift，不先规范化再冒称原 bytes。

source、clean installed copy 与真实 host probe 是三个对象。source 程序过了不证明 installer 复制了 references/scripts、保留 mode 或清掉旧文件；给定目录 hash 匹配也不证明它曾安装或被 host 发现。先物理树 preflight，再读配置；根据配置根检查 package 路径组件。来源 evaluator 的包内 symlink 拒绝不等显式验证包路径外每个祖先。

原课六层 evaluator 可接受传入的 `passed:true` 与非空 evidence 字符串；这些是 fixture 数据，未必来自运行。分开三种结论：

1. **fixturePassed**：人工夹具能演示门禁逻辑。
2. **localEvidenceReady**：所称 captured mode、非空 source、完整 raw sequences/两个 artifacts/checks/host matrix 与摘要一致。
3. **productionReady**：分层效果与完整性通过，且独立可信采集/验收渠道认可 evidenceRoot。

包作者能改 mode、source 标签、观测和所有本地摘要，所以第二项不证明真实采集。原课 production 路径还要求包外 attestation JSON 绑定完整 evidenceRoot，并用 out-of-band 的 exact-bytes digest 校验；如果期望 digest 也由同一包作者随手提供，就没有独立信任。attester 需要审核采集环境、运行身份、原 traces 与门禁政策。禁止把“生成一个 attestation”当制造完成证据。

### 完整离线例三：原 bytes、分层失败与移除范围

下面只验证机制：固定 trigger 观测、固定两标题产物、SHA 与本地升级计划。没有独立采集者，因此 productionReady 与 passed 始终 false。改变参考文件换行仍会报 mismatched；重复预测顺序变化会改变证据摘要；移除只提出旧 manifest 所有且当前仍是原 bytes 的路径，modified resource 留待审查，未列入旧所有权的其它文件不在移除集合。没有发布、安装、升级或执行删除。

```python
import hashlib
import json
import tempfile
from pathlib import Path, PurePosixPath

RESERVED = "assets/manifest.json"

def sha(data):
    return "sha256:" + hashlib.sha256(data).hexdigest()

def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")

def preflight(root):
    if root.is_symlink() or not root.is_dir():
        raise ValueError("bundle_root")
    for path in root.rglob("*"):
        if path.is_symlink() or not (path.is_dir() or path.is_file()):
            raise ValueError("symlink_or_special_file")

def manifest(root):
    preflight(root)
    # 摘要覆盖原始bytes；不改变换行/空格/编码，不包含manifest自身。
    return {p.relative_to(root).as_posix(): sha(p.read_bytes())
            for p in sorted(root.rglob("*")) if p.is_file()
            and p.relative_to(root).as_posix() != RESERVED}

def verify_tree(root, expected):
    if type(expected) is not dict or not expected:
        raise ValueError("manifest_shape")
    for key, value in expected.items():
        if type(key) is not str or not key or "\\" in key:
            raise ValueError("manifest_path")
        rel = PurePosixPath(key)
        if (rel.is_absolute() or ".." in rel.parts or rel.as_posix() != key
                or key == RESERVED):
            raise ValueError("manifest_path")
        if (type(value) is not str or not value.startswith("sha256:")
                or len(value) != 71 or any(c not in "0123456789abcdef" for c in value[7:])):
            raise ValueError("manifest_digest")
    actual = manifest(root)
    missing, extra = sorted(expected.keys() - actual.keys()), sorted(actual.keys() - expected.keys())
    changed = sorted(k for k in expected.keys() & actual.keys() if expected[k] != actual[k])
    return {"passed": not (missing or extra or changed),
            "missing": missing, "unexpected": extra, "mismatched": changed}

def trigger_metrics(cases):
    counts = dict(tp=0, fp=0, tn=0, fn=0)
    seen = set()
    for case in cases:
        cid, expected, observed = case["id"], case["expected"], case["observed"]
        if (type(cid) is not str or not cid or cid.strip() != cid or cid in seen
                or type(expected) is not bool or type(observed) is not list or not observed
                or any(type(x) is not bool for x in observed)):
            raise ValueError("trigger_shape")
        seen.add(cid)
        for got in observed:
            key = "tp" if expected and got else "fn" if expected else "fp" if got else "tn"
            counts[key] += 1
    if not cases or not any(c["expected"] for c in cases) or all(c["expected"] for c in cases):
        raise ValueError("needs_positive_and_negative")
    tp, fp, fn = counts["tp"], counts["fp"], counts["fn"]
    return dict(counts, precision=tp / (tp + fp) if tp + fp else 0,
                recall=tp / (tp + fn) if tp + fn else 0)

def artifact_check(text):
    # 只验证两个固定标题；值/逻辑质量由任务专用检查另验。
    return "# Decision\n" in text and "# Evidence\n" in text

def gate(layers, evidence):
    required = {"structure", "routing", "behavior", "scripts", "safety", "portability"}
    if type(layers) is not dict or set(layers) != required or any(type(v) is not bool for v in layers.values()):
        raise ValueError("closed_layer_verdicts")
    if type(evidence) is not dict or set(evidence) != {"mode", "source", "cases", "baseline", "treatment", "hosts"}:
        raise ValueError("evidence_shape")
    if evidence["mode"] not in {"fixture", "claimed_capture"}:
        raise ValueError("evidence_mode")
    if type(evidence["hosts"]) is not list or not evidence["hosts"]:
        raise ValueError("hosts_required")
    root_digest = sha(canonical({"layers": layers, "evidence": evidence}))
    checks = all(layers.values())
    # 此教学程序没有独立采集者的真实性核验，不能生成production verdict。
    return {"checksPassed": checks,
            "fixturePassed": checks and evidence["mode"] == "fixture",
            "evidenceRoot": root_digest, "captureObserved": False,
            "productionReady": False, "passed": False,
            "failedLayers": [k for k, v in layers.items() if not v]}

def upgrade_plan(old_manifest, installed_manifest, new_manifest, old_files):
    # 不删除任何文件。只有旧manifest所有、且仍是原bytes的路径才可提出移除。
    obsolete = sorted(old_manifest.keys() - new_manifest.keys())
    removable, preserve = [], []
    for key in obsolete:
        if (installed_manifest.get(key) == old_manifest[key]
                and old_files.get(key) == old_manifest[key]):
            removable.append(key)
        else:
            preserve.append(key)
    return {"proposedRemove": removable, "preserveForReview": preserve,
            "executed": False}

cases = [{"id": "positive", "expected": True, "observed": [True] * 5},
         {"id": "near-miss", "expected": False, "observed": [False] * 5}]
metrics = trigger_metrics(cases)
assert metrics["tp"] == metrics["tn"] == 5 and metrics["precision"] == 1
reordered = [dict(cases[0], observed=[True, False, True]), cases[1]]
changed_order = [dict(cases[0], observed=[True, True, False]), cases[1]]
assert sha(canonical(reordered)) != sha(canonical(changed_order))
base, treatment = "Looks fine.", "# Decision\nNeeds review.\n# Evidence\nFixture paths."
assert not artifact_check(base) and artifact_check(treatment)
evidence = {"mode": "fixture", "source": "teaching-fixture", "cases": cases,
            "baseline": base, "treatment": treatment, "hosts": [{"name": "simulated-host"}]}
layers = dict.fromkeys(("structure", "routing", "behavior", "scripts", "safety", "portability"), True)
assert gate(layers, evidence)["fixturePassed"]
assert not gate(layers, dict(evidence, mode="claimed_capture"))["productionReady"]
assert gate(dict(layers, safety=False), evidence)["failedLayers"] == ["safety"]
with tempfile.TemporaryDirectory(prefix="study-skill-integrity-") as td:
    root = Path(td).resolve() / "demo-skill"; (root / "references").mkdir(parents=True)
    (root / "SKILL.md").write_bytes(b"demo\n")
    ref = root / "references" / "contract.md"; ref.write_bytes(b"policy\n")
    expected = manifest(root)
    assert verify_tree(root, expected)["passed"]
    ref.write_bytes(b"policy\r\n")  # 文义相同但bytes变化，仍须检测。
    assert verify_tree(root, expected)["mismatched"] == ["references/contract.md"]
    (root / "user-notes.txt").write_bytes(b"unowned user file\n")
    installed = manifest(root)
    new = {"SKILL.md": expected["SKILL.md"]}
    plan = upgrade_plan(expected, installed, new, installed)
    assert plan["preserveForReview"] == ["references/contract.md"] and not plan["executed"]
    assert "user-notes.txt" not in plan["proposedRemove"] + plan["preserveForReview"]
    assert upgrade_plan(expected, expected, new, expected)["proposedRemove"] == ["references/contract.md"]
    (root / "linked.md").symlink_to(ref)
    try: manifest(root)
    except ValueError as error: assert str(error) == "symlink_or_special_file"
    else: raise AssertionError("symlink")
    (root / "linked.md").unlink()
    try: verify_tree(root, {"./SKILL.md": expected["SKILL.md"]})
    except ValueError as error: assert str(error) == "manifest_path"
    else: raise AssertionError("canonical")
print("六层fixture/逐run摘要/原bytes漂移/symlink/升级移除只作计划通过；productionReady始终False")
```

此例的 artifact 标题检查很窄，不能判定内容正确；来源的 `artifactImprovement` 也只是 baseline fail/treatment pass，不能比较两者都过形状但质量或效率不同的情况。例中 evidenceRoot 仅覆盖传入的层判定与fixture；生产证据根还需绑定包manifest、全部配置、阈值、采集环境和版本，并由独立渠道验真。真实业务需要独立值/覆盖/来源 checks 与人工 rubric 校准。脚本测试是普通软件测试，script/safety 结果不能靠输入布尔值自证；安全 required cases 全过是 hard gate，而非平均得分。

## 6. 跨宿主能力、更新与移除怎样验收

不要只问“支持 skills 吗”。对每个 required capability 记录 native、adapter、degraded with acceptable fallback 或 unsupported：核心目录、body activation、companions、process tool、explicit/implicit、human/model policy、argument binding、delegated context、hooks、persistent resume、scope与uninstall。缺 required 行为且 fallback 不满足时不能发布给该宿主；支持字段而未观察行为标 unverified。SDK 可以封装调用和追踪，但这张机制矩阵仍需实际故障测试，不能由品牌或包下载量替代。

后续真实宿主 checkpoint 的操作合同如下。本阶段仅记录，不安装：

1. 固定 source revision、包 SHA、host/version/date、选定 project/user scope和干净 target；查看预期文件列表及冲突，先 review 整包 tree，不覆盖其它包。
2. 安装整目录后记录实际 installed root，rescan/新会话依 host 当前文档；显式调用使用宿主真正语法，再用无名称同任务和一个 near miss 测隐式。没有可见选择记录就 unverified，不从 fluent reply 推断。
3. 要求读取 installed reference，运行被审 helper 时展示绝对 script/target、cwd、精确 argv，记录 exit/stdout/artifact hash。未观察任一字段就标未观察；相对路径按 installed root 或目标 workspace 哪个基准解释要明确。
4. 检验 authority：只评估请求不发布；若用户确已授权外部动作，再核具体对象/后果与当前 policy。记录控制来自 Skill 指令、host policy、approval、缺 capability或sandbox，不能统称“安全保证”。
5. 第二 host 重做同一 probes；不可用则标 unverified/unsupported 与可行 fallback，一台成功不叫 universal portable。
6. 升级先看 old/new tree、metadata、invocation policy、required capabilities与 resource diff；旧 manifest 所有的未修改文件可列计划，修改文件、unknown文件、symlink或模糊所有权先保留。移除只限该 installed bundle，不用宽 glob、不移除兄弟scope包。重建目录，重试显式调用确认不再发现；残留 catalog 是另一个失效状态。

持续状态应记录候选 commit、已完成 check、效果未知动作、idempotency key与下一步；中断不能重复外部写入。发布流程、host配置和新费用仍由当前具体授权范围约束。这里没有执行 source installer、npx、SDK、真实 host、容器或 API。

## 7. 原课程练习与参考判据

下面覆盖原22、24–27的全部32项 Exercises。它们是可选实践题和答案标准，未执行的真实宿主/模型题不会记成个人经历。工具与结构输出课的另外25题分别见[工具使用](../01-核心章节/05-工具使用.md)与[发票核验](../../LLM%20工程实践/13-结构化输出与对话状态.md)。

### 练习组22：Agent Skills: Portable Contract and Runtime Boundary

| 原题 | 问题 | 答案或判据 |
|---|---|---|
| 22.1 | 用TaskShape分类五个实际workflow，可否组合单元？ | 5个团队真实workflow以职责选择，组合逐项有理由；可由模拟任务讲规则，不记用户团队实际经历。 |
| 22.2 | compatibility500/501边界应怎样检查？ | compatibility500通过501拒绝是标准边界；现源tests已有该测试，未来新增自己的实现才能记实跑。 |
| 22.3 | 允许一个宿主扩展后是否仍是portable-only？ | 扩展allowlist使结构加载可用但报告仍标runtime_extensions，未知宿主不可默认赋义。 |
| 22.4 | 如何把400行prompt拆为入口/reference/script/template？ | 400行prompt分离核心workflow、分支reference、确定性script接口和output模板；不能仅为短入口搬走必要动作。 |
| 22.5 | Skill引用不存在的MCP工具怎样失败？ | 缺MCP工具返回missing_dependency与未完成步骤，禁止换更宽权限工具；Skill名称不创造capability。 |
| 22.6 | 逐句标routing/procedure/policy/pointer/output怎样整理？ | 逐句labelrouting/procedure/policy/pointer/output；政策不扩授权，正文保留核心流程及错误出口。 |

### 练习组24：Skill Discovery and Progressive Disclosure

| 原题 | 问题 | 答案或判据 |
|---|---|---|
| 24.1 | 新增plugin scope，优先级依据是什么？ | 新增plugin rank在user与builtin之间，碰撞预期不由文件mtime决定；不能称Codex默认优先级。 |
| 24.2 | 改为qualified identity时如何保留两个同名包？ | qualified identity保留scope/source并显式invocation，不依同名随机选择；diagnostic保留shadowed。 |
| 24.3 | reference字节limit与limit+1怎样测试？ | byte size与chars不同，UTF8边界limit/limit+1测试且先限读取；现main只有chars后检查。 |
| 24.4 | 如何重写两个近似description并验证？ | 近邻description按触发/输出/排除拆分，再用paraphrase+near miss验证，不能只看文字不同。 |
| 24.5 | manifest怎样发现resource漂移？ | manifest覆盖reference/script，加载前核比对；哈希匹配只证明未漂移，不证明安全或来源。 |
| 24.6 | 怎样分别报告L1/L2/L3实际成本？ | 分别记L1 exact serialization/L2 body/L3实际资源成本，注明bytes/chars/tokens单位与计数器。 |

### 练习组25：Skill Invocation and Routing

| 原题 | 问题 | 答案或判据 |
|---|---|---|
| 25.1 | 人类/模型四象限各有什么例子？ | 四象限给各自场景，disabled/app-only是否可用另看app policy；不会自动获得工具权限。 |
| 25.2 | 怎样实现application-only调用？ | app-only许可精确name，human/model均拒；app target allowlist不扩大filesystem/network。 |
| 25.3 | 为deployment写十个near misses。 | 10个deploymentnear misses包括解释、构建失败、发布说明、引用他人请求、反对部署和只问方案，标gold先分development/holdout。 |
| 25.4 | top1/top2歧义margin如何决定？ | margin=top1-top2不足返回ask/abstain而非字母赢家；验证禁用top1后重新排名。 |
| 25.5 | A→B→A与最大调用深度怎样检测？ | visited调用链+maxdepth防A→B→A与selfcycle；原代码只实现self+depth，标新增需写。 |
| 25.6 | 同集core与extension adapter为什么可能不同？ | 同集core/extension比较，记录哪个宿主字段改变eligibility；禁止把词面simulator数字当宿主准确率。 |

### 练习组26：Skill Permissions, Sandboxes, and Trust

| 原题 | 问题 | 答案或判据 |
|---|---|---|
| 26.1 | 同路径read/create/overwrite/delete怎样分权？ | 按read/create/overwrite/delete分别same target检查，并验已有/不存在/父symlink/TOCTOU；真实强边界需fd绑定，不只resolve一次。 |
| 26.2 | 443/8443与redirect怎样做origin policy？ | allow registry443和8443分开，redirect到undeclared deny；本代码没有实际redirect网络执行，不记通过。 |
| 26.3 | package manager lifecycle hooks应如何处理？ | package manager lifecycle hooks需代码信任/隔离执行，review argvprefix不够；审批不替代sandbox。 |
| 26.4 | 外部写入为什么要idempotency key？ | 外部写必须idempotency key与效果状态，retry以回读优先，重复key不能重复扣款/发布。 |
| 26.5 | stage/prod发布批准分别要展示什么？ | 批准文案写候选hash、版本、stage/prod目标、动作、风险、回滚；授权范围新后果不可继承。 |
| 26.6 | 网页读取到PR评论的trust边界在哪里？ | webpage→model→comment边界：网页仅资料，输出评论需人类直接授权，限制secret与egress且回读记录；本任务没有评论发布。 |

### 练习组27：Skill Evals, Packaging, and Portability

| 原题 | 问题 | 答案或判据 |
|---|---|---|
| 27.1 | 三类各十题怎样分development/holdout？ | 10positive/10negative/10near miss在修描述前分dev/validation，手工gold与competitors明确；数量不是质量标准，固定simulator不能替targethost。 |
| 27.2 | 五次baseline/treatment怎样报告退步？ | 五次paired每任务保持同模型/工具/预算，保留raw predictions和每case regressions；未做真实API实验。 |
| 27.3 | human rubric怎样校准？ | 人类rubric需五example校准judge/human一致与failureboundaries，不把任何LLM“感觉好”作机械通过。 |
| 27.4 | 新增hostcapability如何给四种兼容结果？ | 加hostcapability明确native/adapter/degraded/unsupported与fallback是否满足required；没有hostprobe仅fixture。 |
| 27.5 | 安装后reference改变应怎样拒绝？ | manifest后改reference，应mismatched并在activation前挡；manifest本身由外围渠道auth，不能recompute后冒称未改。 |
| 27.6 | body过lint而script坏artifact是谁阻发布？ | bodylint过scriptartifact失败应scripts/behavior阻发布，各层并列不能加权抵消。 |
| 27.7 | 升级怎样比invocation policy与capabilities？ | 升级diff invocationpolicy/required capabilities及新resource，重新验目标host/权限，避免silent degradation。 |
| 27.8 | 兼容报告怎样避免一个portable badge掩盖未知？ | compatibility report含version/date/evidence/未验证；本次未publish、install、upgrade、uninstall，模拟passed不记录用户技能。 |


## 8. 原30道 quiz 的核对答案

保留原题知识判断而用中文提问；选项字母对应源 `quiz.json` 的0=A、1=B、2=C、3=D。题目能核对概念，不能证明答题者实际跑过 host、具有能力或完成课程。关于一层 reference、六层阈值与 attestation 的题目按题设发布政策回答，不能升级成 Agent Skills 全局规范。

### Quiz组22

| 题号 | 核对问题 | 原选项与答案 |
|---|---|---|
| 22.Q1 | 复用审查方法和已存在API怎样分工？ | A：Skill放方法，MCP tool暴露API。 |
| 22.Q2 | 为什么name与目录名必须一致？ | B：发现/打包只有一致身份；不授权限。 |
| 22.Q3 | 只有一宿主认识的字段如何解释？ | B：宿主扩展由明确adapter解释，不升格核心标准。 |
| 22.Q4 | 每次tool call后必须执行检查选什么？ | D：Hook；要求是事件时点，非概率路由。 |
| 22.Q5 | 何时AGENTS.md比Skill合适？ | C：仓库全程惯例/命令/边界放AGENTS；稀有任务方法放Skill。 |
| 22.Q6 | 有效目录包自身授予什么？ | B：可发现的方法说明；是否执行由host控制。 |

### Quiz组24

| 题号 | 核对问题 | 原选项与答案 |
|---|---|---|
| 24.Q1 | 项目/用户有同名包，什么决定胜出？ | A：host声明的scope政策，非mtime/长正文。 |
| 24.Q2 | 初始catalog应该装什么？ | B：compact name/description/identity，不预运行script。 |
| 24.Q3 | 渐进披露的正确顺序？ | D：catalog→选中body→该分支所需reference。 |
| 24.Q4 | 同优先级重复为什么要报歧义？ | A：相同rank按偶然顺序选会不可复现，应明确冲突。 |
| 24.Q5 | 题设只允一层，references/archive/schema.md怎样处理？ | C：拒绝违反题设的深度政策；标准推荐浅链不等普遍禁nested目录。 |
| 24.Q6 | catalog超预算怎样处理最可核对？ | A：确定性截短/遗漏报告，再用窄发现找未列项。 |

### Quiz组25

| 题号 | 核对问题 | 原选项与答案 |
|---|---|---|
| 25.Q1 | 从host看，什么是programmatic activation？ | A：应用或harness按精确身份编排；UI人选与语义路由是其它通道。 |
| 25.Q2 | user-invocable:false怎样写可移植说明？ | C：host extension，经adapter验证；非文件权限或required核心字段。 |
| 25.Q3 | near miss低于threshold怎样处理？ | D：abstain，普通推理或澄清，不私降threshold。 |
| 25.Q4 | human=true/model=false什么意思？ | B：人类可显式选择，model不可隐式；不代表tool authority。 |
| 25.Q5 | harness为什么精确指定名字？ | C：隔离技能本体行为与routing方差，另作trigger eval。 |
| 25.Q6 | 怎样分开activation与action authority？ | C：先按host政策加载说明，再逐动作检查scope/permission。 |

### Quiz组26

| 题号 | 核对问题 | 原选项与答案 |
|---|---|---|
| 26.Q1 | 入口写“可写任意磁盘”得到什么权限？ | A：无新增权限；文字不变host policy。 |
| 26.Q2 | workspace jail为什么resolve symlink？ | D：词面包内路径可能link到包外，需真实目标与operation检查。 |
| 26.Q3 | 网页要求关闭approval怎样处理？ | B：不可信资料不能成为批准或新policy。 |
| 26.Q4 | 教育例如何演示破坏命令审查？ | C：parse argv返回deny且不执行；有execute=false证据。 |
| 26.Q5 | 用户调用过Skill，未许可HTTPSorigin能用吗？ | D：deny越界origin；activation不是网络授权。 |
| 26.Q6 | 疑似秘密写入没有合规权限路径怎么办？ | D：拒绝且不回显秘密；如确有需求另走已授权secret workflow。 |

### Quiz组27

| 题号 | 核对问题 | 原选项与答案 |
|---|---|---|
| 27.Q1 | 什么样trigger集最能看到过度触发？ | A：positives和语义近邻negatives，不能只一个demo或同名prompt。 |
| 27.Q2 | 8TP/2FP的precision是多少？ | B：.8；recall缺FN无法算。 |
| 27.Q3 | baseline/treatment为何用相同断言？ | D：测产物实际改进，不能只测被激活。 |
| 27.Q4 | host只装入口却丢必须companions怎么办？ | B：adapter-required并列companions/process能力缺口；无可行adapter才unsupported。 |
| 27.Q5 | 重复run率比一次成功多证明什么？ | C：每case重复一致性；不是结构、权限或host普适证明。 |
| 27.Q6 | 按本课发布政策完整gate包含什么？ | D：六层效果、localcaptured完整摘要、独立可信包外attestation；这是本课生产门禁，非所有Skill统一标准。 |


## 9. 图意、来源与验证边界

来源静态 skills-stack 把 AGENTS、Skills、MCP分层，但旧生态数量、SDK品牌/UI标签不作为当前事实。19幅动态 Skills 图的有效含义已融入上面的目录树、生命周期、资格/参数、authority链、六层门禁与升级流程：它们强调分层与分支，不是模型或host运行。入口的动画步骤/固定 host profiles、prediction、passed与示例artifact都是教学数据；未验证真宿主、SDK或容器行为。

2026-10-08 吸收[AI Engineering from Scratch Phase13 22、24–27](https://github.com/rohitg00/ai-engineering-from-scratch/tree/3be078b37ffd8f0c04953c0678e48f5c6d0c7775/phases/13-tools-and-protocols)，源 commit `3be078b37ffd8f0c04953c0678e48f5c6d0c7775`。完整读取原文、代码/tests/quiz、5个 bundle及全部 companion bytes；source SHA/GitBlob、标题、图builder/helper和 primary 指定范围记录在正式覆盖报告。GitSkills论文没有阅读全文，生态数量与所有性能百分比不吸收为质量或当前效果结论。本文三个新程序从最终 Markdown 提取在Python3.12.13标准库 CPU运行，只证明明确的本地反例和政策机制，不证明真实 capture、productionReady、跨宿主或用户掌握。
