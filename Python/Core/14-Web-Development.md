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
