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

本专题覆盖原资料的 21 章与 8 个附录的长期知识。原资料中的平台安装截图、易失效镜像源、短期版本号、历史废弃用法不进入主干；对应章节仍在来源保全层记录，保证可追溯而不污染主知识库。
