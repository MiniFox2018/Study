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

## 15. AI模型依赖与外部provider

普通service通常描述容器。AI模型则可以作为顶层`models`声明，再由service显式引用，平台负责把模型的连接信息注入应用。**声明模型、应用知道地址、推理后端可用、业务生成正确**仍是四个检查。

2026-10-18核对[Compose Models官方参考](https://docs.docker.com/reference/compose-file/models/)：此能力要求Compose 2.38.0及以上，并需要实施该模型机制的平台。`model`指定模型OCI资产，`context_size`指定上下文配置，`runtime_flags`传给实际推理引擎；不同平台/引擎不保证接受同一组参数。

下面是**结构示例**，`your-app:VERSION`和`ai/your-model:VERSION`是待替换资产，未拉取、未运行，不属于前面已验过的数据库实验：

```yaml
services:
  app:
    image: your-app:VERSION
    models:
      assistant:
        endpoint_var: AI_BASE_URL
        model_var: AI_MODEL_ID
models:
  assistant:
    model: ai/your-model:VERSION
    context_size: 2048
```

应用读取`AI_BASE_URL`与`AI_MODEL_ID`，再按后端实际API构造请求。模型声明键`assistant`是配置内逻辑名，OCI引用是资产名，API请求model字段由平台注入的标识决定，三者不能猜成同一个字符串。

短语法以模型逻辑名生成变量：例如`embedding-model`对应`EMBEDDING_MODEL_URL`、`EMBEDDING_MODEL_MODEL`。长语法显式命名更适合复用已有应用；不要在代码里假定容器的localhost就是宿主模型服务。API base URL是否已包含`/v1`或引擎路径也须核对，避免重复拼接。

**资源与结果条件**：上下文越大通常需要更多KV缓存，不能只看权重能否放入内存；线程数也不等于支持的并发请求数。来源“concurrent”示例只调threads/mlock，没有展示排队或并发服务合同。temperature=0与top-k=1可减少采样随机性，不能保证跨硬件/后端/版本逐字节一致；embeddings还需模型与端点、引擎模式真正匹配。原理参见[AI容器与硬件边界](09-AI容器与硬件运行边界.md)。

### 外部provider为何多了一条宿主执行路径

Compose的`provider` service代表由第三方组件管理的能力，不必对应一个普通容器。其type可指Docker CLI插件、PATH二进制或脚本路径；`compose up`可能因此调用宿主程序来配置资源。配置文件来源与插件实现都需要审阅，不能因为YAML里没有shell service就认定只有容器内执行。

依赖它的service通常通过`<PROVIDER_SERVICE>_<VARIABLE>`收到连接信息。例如名为database的provider返回URL/token，应用可能收到`DATABASE_URL`与`DATABASE_TOKEN`。这些变量提供连接能力，未证明资源只读、可用或无费用；`depends_on`也不能替代请求超时、鉴权和实际就绪检查。

[Provider官方说明](https://docs.docker.com/compose/how-tos/provider-services/)目前标注Compose 2.36.0及以上，并建议AI模型优先使用顶层models。它与models支持版本不同，不能拿一台支持普通Compose的机器就假定两者都支持。跨平台可移植指声明机制，供应商生命周期、收费、清理和权限仍由具体实现决定。

迁移到云guest里的嵌套Docker时还需核运行器限制：2026-10-18官方仍列出exec/healthcheck可能访问错误文件系统的情况，详见[沙箱工作台19.3](10-Docker沙箱与Agent工作台.md)。这不改变前面本地数据库实验的历史配置结果，但不能把该结果推广为云环境已实跑。

本节来源为第一来源固定`1a8c4fd…`中三页Compose资料，整理2026-10-18；两页上述官方参考同日现核。只做正文审阅与静态配置说明，未启动provider/模型/Compose，不改变原数据库实验的历史验证日期。
