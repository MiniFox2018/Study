# 04｜Compose 与多容器应用

## 1. Compose 解决的问题

单个 `docker run` 适合运行一个容器，但真实应用往往包含：

- Web/API；
- DB；
- Cache；
- Queue；
- Worker；
- Object Storage；
- observability 组件。

如果全部依赖手写命令，会产生不可复现的隐式配置。

Compose 的作用是把“一个多容器应用”声明为可版本控制的配置。

## 2. 核心对象

```text
Compose Project
├── services
├── networks
├── volumes
├── configs
└── secrets
```

### services

定义每个可运行组件：

- image 或 build；
- command / entrypoint；
- environment；
- ports；
- volumes；
- healthcheck；
- resource/security 约束。

### networks

定义哪些服务处于同一通信边界。服务间应使用服务名，而不是固定 IP。

### volumes

声明长期数据。

### configs / secrets

把运行配置与镜像解耦。敏感值不应硬编码到 compose 文件或镜像。

## 3. 最小结构

```yaml
services:
  web:
    build: .
    ports:
      - "8080:8080"
    depends_on:
      db:
        condition: service_healthy

  db:
    image: postgres
    volumes:
      - db_data:/var/lib/postgresql/data

volumes:
  db_data:
```

重点不是语法，而是明确了：

- 应用由哪些服务构成；
- 服务如何连接；
- 哪些数据要持久化；
- 哪些端口需要暴露；
- 启动健康依赖是什么。

## 4. `depends_on` 不等于“业务已就绪”

“容器进程已经启动”和“数据库已经接受请求”不是一回事。

可靠启动顺序应结合：

- healthcheck；
- 应用自身重试；
- timeout / backoff；
- migration / initialization 逻辑。

不要把初始化正确性建立在固定 `sleep 10` 上。

## 5. 配置与环境变量

环境变量适合注入运行时配置，但需要管理：

- 默认值；
- 必填校验；
- 类型；
- secret；
- dev/staging/prod 差异。

Compose 可读取 `.env`，但 `.env` 不是 secret manager。

## 6. 端口与 `expose`

- `ports`：发布到宿主机；
- `expose`：表达容器间可用端口，不等价于公网发布。

数据库、Redis 等通常只需要在内部网络可见。

## 7. 健康检查

健康检查用于表达服务真实可用性，例如：

- HTTP readiness endpoint；
- DB ping；
- TCP 连接；
- 应用内部自检。

检查脚本本身应轻量，不要造成额外负载或写操作。

## 8. profiles

Profiles 适合把可选服务纳入同一配置，例如：

- debug；
- admin；
- observability；
- integration-test。

这样可以避免维护多份几乎相同的 compose 文件。

## 9. Compose 中的安全配置

可使用：

- `cap_drop` / `cap_add`；
- `security_opt`；
- read-only filesystem；
- 非 root USER；
- secrets；
- 网络隔离。

默认原则：不给不需要的权限。

## 10. 开发环境与生产环境必须分开理解

Compose 很适合：

- 本地开发；
- 集成测试；
- 单机部署；
- 小规模内部服务。

但生产系统还需要：

- 高可用；
- 自动调度；
- 滚动升级；
- 节点故障恢复；
- 集群级网络；
- 统一 secret；
- 弹性扩缩容。

这些能力属于 Kubernetes 等编排系统。

## 11. 典型应用模式

### Web + DB

```text
web
 ↓
db(volume)
```

核心是 DB 持久化、健康检查、迁移和 secret。

### Web + Cache + DB

```text
web ─→ redis
  └─→ db
```

Cache 可以重建，DB 数据不可依赖容器层。

### WordPress / CMS

典型关注：

- Web 与 DB 分离；
- 上传文件和 DB 都需要持久化；
- secret 不写进镜像；
- 反向代理/TLS 在生产层管理。

### LNMP / 多服务栈

重点不是复刻某个旧版配置，而是理解：

- Nginx 作为入口；
- 应用运行时独立；
- DB 独立；
- 服务名解析；
- 卷与网络边界；
- 统一配置注入。

## 12. 开发容器（Dev Container）

Compose 可以和 VS Code Dev Containers 等工具结合，统一：

- 编译器；
- SDK；
- lint / format；
- DB / Redis；
- 调试依赖。

但代码仍应挂载自宿主机，开发容器不是最终生产镜像。

## 13. 常用生命周期

```bash
docker compose up -d
docker compose ps
docker compose logs -f
docker compose exec web sh
docker compose build
docker compose pull
docker compose down
```

需要谨慎理解 `down -v`：它会同时删除声明的数据卷，可能造成不可逆数据损失。
