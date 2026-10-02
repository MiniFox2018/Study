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

## 3. 可运行结构：数据库与查询服务

前提：Docker daemon 可连接，使用 `docker compose` 插件。在新的空目录中保存为 `compose.yaml`；使用两个容器观察服务名连接，数据库不发布主机端口。这里固定 **PostgreSQL 18 主版本**以明确数据目录，不把标签当作不可变 digest。

```yaml
name: study-compose-lab
services:
  db:
    image: postgres:18
    environment:
      POSTGRES_USER: study
      POSTGRES_DB: study
      POSTGRES_PASSWORD_FILE: /run/secrets/db_password
    secrets:
      - db_password
    volumes:
      - db_data:/var/lib/postgresql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U \"$$POSTGRES_USER\" -d \"$$POSTGRES_DB\""]
      interval: 2s
      timeout: 3s
      retries: 15
      start_period: 10s

  query:
    image: postgres:18
    depends_on:
      db:
        condition: service_healthy
    secrets:
      - db_password
    entrypoint: ["/bin/sh", "-c"]
    command:
      - |
        export PGPASSWORD="$$(cat /run/secrets/db_password)"
        exec psql -h db -U study -d study -v ON_ERROR_STOP=1 -c 'SELECT 1 AS ok;'

volumes:
  db_data:
secrets:
  db_password:
    file: ./db-password.txt
```

先生成本地练习密码文件（不打印密码），再检查/运行：

```bash
(umask 077; openssl rand -hex 24 > db-password.txt)
printf 'db-password.txt\n' > .gitignore
docker compose config --quiet
docker compose up -d db
docker compose run --rm query
docker compose down
```

查询预期返回一行 `ok = 1`。`$$` 让变量留到容器 shell 展开；单个 `$` 可能被 Compose 在宿主解析。query 是一次性任务，成功退出才是预期。

密码文件仅用于本地练习，Compose secrets 不等于外部密钥管理系统。初始化变量仅对空数据目录生效；已有卷后重新生成密码文件，不会自动修改数据库里已创建的密码。PostgreSQL 18+ 官方镜像的数据卷挂载点改为 `/var/lib/postgresql`，17 及以下默认路径不同，升级必须按官方迁移步骤，不能只换 tag。

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
- `expose`：表达/记录容器端口，不发布主机端口，也不是防火墙白名单；同一网络内能否连接主要取决于监听地址和网络规则。

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

代码可以来自宿主机 bind mount，也可在受控开发卷/远程工作区中；选择取决于工具链和 I/O 性能。开发容器通常包含调试工具，目标与最终生产镜像不同。

## 13. 常用生命周期

```bash
docker compose up -d
docker compose ps
docker compose logs -f
docker compose exec db sh
docker compose build
docker compose pull
docker compose down
```

`down` 默认保留命名卷；`down -v` 会删除由项目管理的声明命名卷和附带匿名卷（external 卷不由它删除），可能造成数据损失。练习默认不加 `-v`，完成备份/确认测试卷后才单独清理。

## 14. 自测：就绪与持续可用不同

把 db 的 healthcheck 删除而保留 `condition: service_healthy`，依赖条件就失去依据；不能用 `sleep 10` 替代真正就绪检测。即使启动时健康，后续数据库也可能断开，业务仍需连接超时、有限重试和失败处理。

`docker compose config` 只做配置解析/规范化，不能证明镜像存在、密码有效、网络连通或数据库可用。真正验收还需看到查询输出，并通过实际数据读写验证持久化。
