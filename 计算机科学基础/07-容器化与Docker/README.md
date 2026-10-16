# 07｜容器化与 Docker

> 定位：把 Docker 当作“可重复交付 + 进程隔离 + 镜像分发”的系统工程来学习，而不是只记 CLI。
>
> 来源基线：yeasy，《Docker 从入门到实践》v1.11.0（2026-07-04，Docker Engine v29.x 基线）。

## 1. 为什么单独成章

Docker 同时连接：

- 操作系统：process、namespace、cgroup、filesystem、network；
- 软件工程：build、artifact、configuration、test、release；
- DevOps：CI/CD、Registry、observability、rollback；
- 分布式系统：service discovery、orchestration、Kubernetes；
- 安全工程：least privilege、SBOM、签名、供应链审计。

因此它不适合只塞进“生产级软件工程”的一个小节，而应作为独立知识骨架。

## 2. 核心心智模型

```text
源码 + 依赖 + 构建规则
        ↓
    Dockerfile
        ↓ build
      Image
  （只读、分层、可寻址）
        ↓ run
    Container
（镜像 + 可写层 + 隔离进程）
        ↓ push/pull
     Registry
        ↓
Compose / Kubernetes / CI-CD
```

必须先掌握三个基本对象：

- **Image**：静态、只读、分层的运行模板；
- **Container**：镜像的运行实例，本质上是被隔离和限制资源的进程；
- **Registry**：镜像存储、版本管理与分发系统。

## 3. 学习结构

1. [核心模型与生命周期](./01-核心模型与生命周期.md)
2. [镜像、Dockerfile 与构建系统](./02-镜像-Dockerfile-构建.md)
3. [数据、网络与镜像仓库](./03-数据-网络-仓库.md)
4. [Compose 与多容器应用](./04-Compose与多容器应用.md)
5. [底层实现与容器生态](./05-底层实现与容器生态.md)
6. [容器编排、Kubernetes 与 etcd](./06-编排-Kubernetes-etcd.md)
7. [安全、可观测性与故障诊断](./07-安全-可观测性-故障诊断.md)
8. [DevOps、生产实践与速查](./08-DevOps-生产实践与速查.md)

## 4. 推荐学习顺序

```text
Image / Container / Registry
→ Dockerfile
→ Volume / Network
→ Compose
→ Namespace / cgroup / OverlayFS
→ BuildKit / buildx
→ Security / Observability
→ Kubernetes / etcd
→ CI/CD / Production
```

### 初学者

先完成 01～04，目标是能独立容器化一个 Web + DB 应用。

### 开发者

重点 02、03、04、08，目标是可重复构建、开发环境一致和可部署。

### DevOps / 平台工程

完整学习 01～08，重点放在 Registry、Kubernetes、安全、监控和发布闭环。

## 5. 版本与时效原则

主知识库只保留长期有效的抽象和当前工程实践。以下内容不固定成“永久结论”：

- 某发行版的具体安装命令；
- Docker Desktop UI 路径；
- 镜像加速站点；
- 云厂商产品价格与套餐；
- Docker Hub 配额数字；
- 某个 Kubernetes / Docker / etcd 小版本号。

遇到这些问题时，先理解本目录中的决策原则，再查官方最新文档。

## 6. 与仓库其他目录的关系

- [计算机体系结构与操作系统](../02-计算机体系结构与操作系统.md)：理解 namespace、cgroup、进程、网络和文件系统；
- [生产级软件工程](../05-生产级软件工程.md)：理解 CI/CD、可观测性、配置与 secret；
- LLM 工程实践：容器是模型服务、推理网关、评测平台和 Agent sandbox 的常见运行边界。

## 7. 完整性说明

历史整理为原资料的 21 章与 8 个附录建立了主题映射；这不等于每个细节已逐项验证或每个实验已迁移。原资料中的平台安装截图、易失效镜像源、短期版本号、历史废弃用法不进入主干；对应章节仍在来源保全层记录，保证可追溯而不污染主知识库。

## 8. 练习基线与本轮核验

先用 `docker version` 确认 Server 可达，用 `docker compose version` 确认 Compose 插件。本文使用 `docker compose`，不依赖旧的独立 `docker-compose`。01～04 提供完整小实验；写有“结构示意/占位”的片段不能直接运行。macOS/Windows 的 Linux 容器由虚拟机承载，与原生 Linux 系统管理要分开理解。

2026-10-02 核验：

- [Compose 启动依赖](https://docs.docker.com/compose/how-tos/startup-order/)：service_healthy 必须配实际健康检查。
- [PostgreSQL 官方镜像](https://hub.docker.com/_/postgres)：18+ 的卷路径变化、空目录初始化条件与密码文件配置。
- [Docker tmpfs](https://docs.docker.com/engine/storage/tmpfs/)：临时内存页可能换出到 swap。
- [Docker host 网络](https://docs.docker.com/engine/network/drivers/host/)：Linux Engine 与 Desktop 的支持/行为边界不同。
- [Kubernetes 三类探针](https://kubernetes.io/docs/concepts/configuration/liveness-readiness-startup-probes/)：就绪、存活和启动检测的作用不同。

本轮只能在当前机器解析 Compose 配置；Docker daemon 未运行，容器启动、镜像构建、数据持久化和 Kubernetes 集群行为尚未实跑验收。上面的运行预期来自配置语义和官方文档，后续实跑需记录实际版本、digest、结果与失败原因。后续更新备注统一使用中文。

### 2026-10-03 配置验证

使用 Docker Compose 5.1.4 对 04 章完整 YAML 执行 `docker compose config --quiet` 和 JSON 规范化解析，均成功；检查了健康依赖、容器内变量转义、secret 文件引用与 PostgreSQL 18 卷路径。当前 Docker daemon 仍不可连接，因此没有拉取/构建镜像、创建容器、验证查询结果或数据卷持久化。配置解析通过与运行验收通过分开记录。
## AI工作负载的深化

已有构建/网络/Compose基础后，进入[AI容器与硬件边界](./09-AI容器与硬件运行边界.md)，用CPU小例子验证持久产物，再按当前平台判断GPU路径。
