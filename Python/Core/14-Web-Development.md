# 14 · Web 开发、HTTP、API 与认证

## 1. 客户端—服务器模型

浏览器、移动端或其他服务作为 client，通过网络请求 server。Web 后端的核心循环是：

~~~text
HTTP request
  → routing
  → authentication / validation
  → domain logic
  → database / external services
  → HTTP response
~~~

框架只是组织这条链路，不会替你解决数据设计、安全和错误语义。

## 2. HTTP 基础

请求包含：

- method；
- URL；
- headers；
- body。

常见方法：

- GET：读取；
- POST：创建/触发；
- PUT：整体替换语义常见；
- PATCH：部分修改；
- DELETE：删除。

常见状态码：

- 2xx 成功；
- 3xx 重定向；
- 4xx 客户端请求问题；
- 5xx 服务端失败。

状态码应表达协议语义，不应所有错误都返回 200 再塞一个 success=false。

## 3. URL 与路由

URL 由 scheme、host、port、path、query 等组成。路由把 path + method 映射到处理逻辑。

动态 path 参数与 query 参数语义不同：

~~~text
GET /users/42
GET /users?active=true&page=2
~~~

前者定位一个资源；后者通常过滤/分页集合。

## 4. Flask、Django、FastAPI 如何选

### Flask

轻量、可组合，适合小服务、教学和需要自行选组件的应用。

### Django

完整框架，带 ORM、admin、template、auth、migration 等，适合需要统一工程约定的业务应用。

### FastAPI

以类型提示和 ASGI 为核心，擅长 API、数据校验、异步集成与自动 OpenAPI 文档。

没有“一律最快/最好”的框架。根据团队、生态、同步/异步依赖、管理后台、ORM、部署和长期维护选择。

第三方框架变化快，本章只保留稳定结构；具体创建项目、启动命令、配置项使用时核对当前官方版本。

## 5. 请求验证

所有外部输入都不可信：

- path/query；
- JSON/form；
- headers/cookies；
- 上传文件；
- 第三方 webhook。

验证包括类型、长度、范围、枚举、跨字段关系和权限，不是只“strip 一下”。

FastAPI/Pydantic、Django Form/Serializer、Flask 周边库都能提供结构验证，但业务不变量仍需领域逻辑负责。

## 6. Template 与静态资源

服务端模板把数据渲染为 HTML。Jinja2、Django templates 等默认通常提供 HTML escaping，但不能因此忽略上下文安全。

关键原则：

- 不关闭自动转义除非非常明确；
- 富文本使用可信 sanitizer；
- URL、JavaScript、CSS 等上下文需要各自正确转义；
- CSP 等浏览器安全机制用于纵深防御。

模板继承适合 base layout + page blocks，减少重复 HTML。

本节参考实现为TypeScript，吸收的是与语言无关的文本、HTML和发布合同；偏移单位不能直接换成Python字符索引。

### 6.1 先管理词条身份，再向正文添加解释

给术语添加上下文释义，需要同时解决四个问题：词表无歧义、文本定位准确、HTML结构与代码不破坏、发布时释义与词表同版。它是确定性的文档加工，不自动判断定义是否专业，更不是模型对读者理解程度的测量。

词条结构为`{id,term,aliases,definition}`：ID用小写字母开头，仅字母/数字/连字符，且唯一；term和definition非空；aliases缺省为空数组，指定时必须是非空字符串数组。把所有规范名称与别名转小写检查重复，任何两处相同短语都拒绝，包括同一词条自己重复的别名。这样`map scale`和`MAP SCALE`不能静默指向两套定义；但`map`与`map scale`是不同短语，可合法重叠。

示例词表可以有map与scale两条：map的别名chart，scale的规范名称map scale、别名scale ratio。定义由编辑者用自己的准确表述填写；别名是指向同一概念的入口，不等于新建一条同义概念。

来源检查“去空白后不为空”，但保留原字符串，因此Map与“ Map ”并未自动规范成同一个短语；也没有Unicode规范化或完整语言相关大小写折叠。应先声明术语空白、规范化和语言政策，避免在发布中途改变规则，使旧覆盖数字失去可比性。

“reviewed glossary”是编辑输入前提，不是已有审批工作流。参考CLI读取可选reviewFile后没有使用该对象，没有审稿人、批准状态、版本指纹或批准回写。不能因页面写reviewed就称定义已经过专业审查；长期笔记应另外记录定义出处、适用领域、编辑核验与版本。

### 6.2 匹配合同：左到右、当前位置最长、不重叠

把term与aliases展开为候选，按短语长度降序排序。从文本起点逐个位置扫描；找到满足左右边界的第一个候选就记录`{termId,start,end,text}`并前进到end，否则前进一个位置。保留原大小写，匹配时转小写比较；start从0起，end不包含在区间内，单位是JavaScript UTF-16码元，不是UTF-8字节或显示字符。

对`Map scale, then map`，期望区间为scale:[0,9)、map:[16,19)。在同一起点先匹配map scale，不能让短map先消耗它。但这不是全局最长片段优化：词表有a b与b c d时，文本a b c d会先选[0,3)的a b，之后不会回头选择从位置2开始、更长的b c d。

边界谓词把Unicode字母、数字和下划线视为词字符。所以mapping、_map、map2不应命中map，单独的“a RATIO.”可通过别名命中scale。它不做词形还原、中文分词、同义推理或跨空白归一化：连续中文“这张地图很好”里的地图两边也是字母，可能不命中，而空格隔开的地图可以命中。

还有实现层面的Unicode缺口：虽然谓词用Unicode属性转义，代码却把text[i-1]/text[end]的**单个UTF-16码元**传进去。非基本多文种平面字母𐐀由两个码元组成，紧接的map会被错误看成从边界开始；自写模型得到`𐐀map`中的map区间[2,5)。组合重音也不在当前word集合里，所以map后接组合重音仍可能被命中。来源的é边界测试只涉及BMP，不能证明全部Unicode边界正确。

修进应保持偏移合同：可用按码点识别的边界并映射回UTF-16偏移，或采用明确locale的分词器，再用中文、组合字符、非基本多文种平面字母、数字和技术符号反例核行为。不要改成Python字符索引后仍沿用“UTF-16位置”的标签。

### 6.3 只注释允许的文本，不用正则替换整页

参考输入是有平衡标签栈的小型HTML片段。允许p、h1–h4、列表、em/strong/span、div/section/article、blockquote、code/pre、a、br/hr；属性限class/id/title/lang，a额外允许href。属性必须加引号，事件属性和script等元素拒绝，href限HTTP(S)或规定格式的片段链接，属性实体也在此子集之外。

处理结构与匹配分开：

```text
逐个读取标签/文本token
标签：检查白名单、属性与嵌套栈，输出规范标签
文本若有a/pre/code祖先：不做术语注释
其余文本：先按实体分段，每段调用最长匹配
将命中替换成button和隐藏释义span，同时累计对应termId计数
```

因此`<p>Map</p><code>map</code><a href="https://example.invalid">map</a>`只注释段落中的一次。`map <em>scale</em>`不跨元素形成map scale；`map&nbsp;scale`也不跨实体边界匹配长短语。若词表另有map，它可能只注释实体之前的map段。来源不把HTML实体解码后重新映射偏移，也不进行浏览器完整DOM解析。

命中的最小输出结构如下，定义在HTML文本上下文转义：

```html
<span class="term">
  <button type="button" class="term-trigger" aria-expanded="false">Map</button>
  <span class="term-definition" role="note" hidden>一份经过编辑核验的定义</span>
</span>
```

span属于可用于段落/强调内部的行内结构，CSS把展开释义显示为块不等于改成不合法嵌套。原生button提供键盘激活，点击时同步aria-expanded与相邻释义hidden状态。Enter/Space是按钮交互规则；实际键盘路径、焦点可见性、读屏关系与长定义布局仍需浏览器验收。[WAI按钮交互](https://www.w3.org/WAI/ARIA/apg/patterns/button/)

标题中的hovercard不能理解为“只有鼠标悬停才可看”：当前实现主要是按钮点击/键盘展开，也不是复杂弹出层。没有测试过读屏，就不能把存在ARIA属性写成完整无障碍认证。

### 6.4 安全输出与可靠发布是独立合同

释义里的`A <drawing>`应显示为字面文本，不能变成元素；用HTML上下文转义处理&、<、>与引号。词表嵌入script下载逻辑时还必须用JSON序列化并把<转成Unicode转义，以免`</script>`提前关闭脚本。文本、属性URL和脚本数据各有边界，一个escapeHTML函数不自动涵盖所有上下文。

这个受限解析器不适合任意网页：按`<[^>]*>`分token不能完整处理引号内>、HTML5容错与内容模型；它也会丢评论、统一标签大小写/属性写法。因此“代码/链接不注释”不等于输入HTML逐字保真。若扩展到任意网页，应换成熟解析器与明确sanitization策略，并保留原文/派生位置关系。

即使没有引入脚本，保留输入class/id也可能干扰工具本身：`<p id="export">Other</p>`合法通过子集校验，却出现在生成的同ID下载按钮之前；document.querySelector('#export')可能绑定到该段落，使真正按钮失效。输入class=term-trigger也会被工具的全局选择器选中。需使用隔离命名空间、生成器专用容器/元素引用，并校验ID冲突；不能把“标签全在白名单”称作完整功能隔离。

publish返回完整HTML、深复制的词表和coverage，每个词条都有count，包括0。样本五词表的准确覆盖为：

| termId | 规范词 | count |
|---|---|---:|
| map-scale | map scale | 1 |
| legend | legend（含map key别名） | 2 |
| latitude | latitude | 1 |
| longitude | longitude | 1 |
| coordinates | coordinates（含coordinate pair别名） | 2 |

合计7个注释；代码里的coordinates和链接文本里的legend不计。覆盖数回答“在当前规则允许的正文区域命中了几次”，不回答读者是否读懂、定义是否正确或该概念在全文是否重要。0可能是未使用，也可能因为只出现在code/link、跨元素、实体或语言边界不同，不能直接删词。

CLI依次写report.html、glossary.json、coverage.json；glossary是原样Term数组，可重新送入validateGlossary。重做同一课时应从原lesson和固定词表重建，不能把已含生成button的输出当原片段再次注释，因为输入白名单不接受生成的button结构。长期复现还需保存课文版本、词表/规则版本、偏移单位、生成器及编辑记录；当前没有完整版本绑定或产物原子发布。

### 6.5 自检与图示边界

- map与map scale是否应因部分重叠拒绝？**不应。** 完整短语重复才歧义；当前位置最长解决竞争。
- 起点0终点9意味着9字节吗？**不是。** 这里是UTF-16码元半开区间。
- map&nbsp;scale为什么没有命中长词？**实体被分成边界。** 不能声称实现了浏览器可见文本匹配。
- 页面支持点击释义是否意味着已有编辑批准？**不意味。** 展开状态与词条审稿是不同对象。
- 定义含</script>能否直接塞进内联JS字符串？**不能。** JSON嵌入与HTML文本必须分别处理。
- coverage有0是否说明定义无价值？**不能。** 需核可注释范围和匹配规则，再作编辑判断。

四图分别演示重复别名、固定map/map scale匹配、正文与code计数、覆盖汇总。第二图使用ASCII风格\b正则，不等于核心Unicode边界/全词表；第四图把非法数字过滤掉，空字符串经Number可变0，也不是严格coverage输入校验。没有一幅图实现真实HTML解析或编辑审批。

来源：[Glossary Hovercard Publisher](https://github.com/rohitg00/ai-engineering-from-scratch/tree/1a8c4fd5f5b3012e50e111f694b4d84df8a4eb1e/projects/glossary-hovercard-publisher)，源截止2026-10-15，本次2026-10-23，作者日志2026-10-09分记。25原项及1交互JS逐项核Blob，公共helper/教程和测试相同行机械精确复用，所有不同语义实际读完；25原测试仅静读。2PNG已看，2GIF共24帧仅数据解码；样本7注释和UTF-16边界用自写纯字符串模型核对。来源TS/JS/CLI/HTML均未执行，未作浏览器键盘/读屏实测。整文件渲染及结构核验见本节融合记录。


## 7. REST API 设计

常见资源风格：

~~~text
GET    /books
POST   /books
GET    /books/{id}
PATCH  /books/{id}
DELETE /books/{id}
~~~

API 还必须定义：

- 请求/响应 schema；
- 错误格式；
- 分页；
- 排序过滤；
- 认证授权；
- 幂等性；
- 版本兼容；
- rate limit；
- trace/request id。

“有 CRUD endpoint”还不等于生产 API。

## 8. 调用 HTTP API

requests 是同步 HTTP 客户端的常见选择：

~~~python
import requests

response = requests.get(
    "https://api.example.com/items",
    params={"page": 1},
    timeout=10,
)
response.raise_for_status()
data = response.json()
~~~

生产代码至少考虑：

- timeout；
- raise_for_status 或显式状态处理；
- Session 连接复用；
- retry 只用于适合重试的失败；
- 限制响应体大小；
- 认证信息不要打日志。

不要发没有 timeout 的网络请求并假设它“总会回来”。

异步应用选用异步客户端，避免在 event loop 里调用阻塞 requests。

## 9. POST 与认证头

~~~python
headers = {"Authorization": f"Bearer {token}"}
response = requests.post(
    url,
    json={"name": "Ada"},
    headers=headers,
    timeout=10,
)
~~~

token 不应放在 URL query 中，因为 URL 更容易进入日志、历史和代理记录。

## 10. Web 抓取

静态 HTML 可用 HTTP client + BeautifulSoup 等解析器。基本流程：

1. 检查站点条款、robots 与法律/许可边界；
2. 设置合理 User-Agent；
3. timeout；
4. 限速；
5. 解析结构而不是正则整个 HTML；
6. 处理分页；
7. 缓存和去重；
8. 监控结构变化。

动态页面可能需要浏览器自动化，但 Selenium/Playwright 代价更高。优先查页面是否存在稳定公开 API。

不要用“随机 sleep 1~3 秒”替代真正的限速、重试、并发控制和站点规则。

## 11. 密码认证

密码不能明文保存，也不应用普通快速哈希（如单独 SHA-256）直接存储。

应使用专门的密码哈希/KDF，例如由成熟认证框架或库提供的 Argon2、scrypt、bcrypt、PBKDF2 等，并带随机 salt 和合理成本参数。

认证流程还需：

- 登录限速；
- MFA 视风险使用；
- session rotation；
- 安全 cookie；
- CSRF 防护；
- 密码重置 token 过期与单次使用；
- 审计但不记录密码。

## 12. Session / Cookie

Cookie 是浏览器保存并随请求发送的数据。服务端 session 常用 cookie 保存一个不可猜测的 session id。

敏感会话 cookie 通常配置：

- Secure；
- HttpOnly；
- 合适 SameSite；
- 明确过期；
- HTTPS only。

不要把完整敏感账户状态直接放在客户端可修改 cookie。

## 13. JWT

JWT 是 token 格式，不是完整认证架构。使用时明确：

- 签名算法；
- issuer / audience；
- exp；
- key rotation；
- revocation 或短生命周期；
- refresh token 策略。

不要接受客户端自报算法，也不要把敏感明文放 JWT 后误以为“签名就是加密”。

许多传统 Web 应用用服务器 session 比 JWT 更简单。

## 14. OAuth / OIDC

OAuth 2.x 解决授权委托，OpenID Connect 在其上增加身份层。第三方登录优先使用成熟客户端库和标准流程，不手写协议细节。

重点包括：

- state；
- PKCE；
- redirect URI 精确匹配；
- nonce（OIDC）；
- token 验证；
- provider metadata；
- secret 安全存储。

## 15. 授权

Authentication 是“你是谁”；Authorization 是“你能做什么”。

仅登录成功不代表能访问任意资源。每个敏感操作都要检查对象级/角色级/策略级权限，防止 IDOR / Broken Access Control。

## 16. CSRF、XSS、SQL 注入

- CSRF：利用浏览器自动携带凭证诱导状态变更；使用 CSRF token、SameSite 等。
- XSS：不可信内容进入可执行页面上下文；用自动转义、sanitize、CSP。
- SQL injection：使用参数化 SQL/ORM，不拼 SQL。
- Command injection：不要把用户输入拼 shell 命令。

安全不是某一行 sanitize()。

## 17. 一个 API 分层示意

~~~python
def create_user(payload, repository):
    email = normalize_email(payload["email"])

    if repository.exists_by_email(email):
        raise ConflictError("email already exists")

    user = User(email=email, name=payload["name"])
    repository.save(user)
    return user
~~~

HTTP 层负责把 JSON 解析/验证并映射异常到状态码；领域函数不必知道 Flask/FastAPI。

## 18. 练习与答案

**练习 1**：为什么 requests 一定要考虑 timeout？  
**答案**：默认无限等待会占住线程/连接并放大故障，生产系统必须给等待建立上界。

**练习 2**：JWT 为什么不能简单理解为“更安全的 session”？  
**答案**：它只是带签名声明的 token 格式，引入撤销、密钥轮换、泄漏窗口等新问题；是否适合取决于架构。

**练习 3**：认证通过后为什么仍可能越权？  
**答案**：认证只确认身份；每个资源/动作还必须执行授权检查。


本次读取范围、主代理复核与实际验收见[融合记录](../../维护/来源更新/2026-10-16/104-术语释义发布项目读取与融合.json)。
