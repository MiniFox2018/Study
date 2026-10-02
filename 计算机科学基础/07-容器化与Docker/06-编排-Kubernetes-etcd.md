# 06｜容器编排、Kubernetes 与 etcd

## 1. 为什么单机 Docker 不够

当容器规模从“几个进程”增长到“跨多台机器的服务系统”后，会出现：

- 容器应该放到哪台机器；
- 节点挂了怎么恢复；
- 如何水平扩容；
- 服务 IP 变化如何发现；
- 如何滚动更新；
- 配置与 secret 怎么分发；
- 数据卷如何跨节点；
- 如何管理批处理、守护进程和有状态服务。

这就是 orchestration 的问题域。

## 2. Kubernetes 的核心抽象

Kubernetes 不是“远程 docker run”，而是声明式控制系统。

```text
期望状态
  ↓
Kubernetes API
  ↓
Controllers / Scheduler
  ↓
实际集群状态
  ↓
持续 reconciliation
```

核心思想：**描述想要什么，由控制器持续把现实拉回期望状态。**

## 3. Pod

Pod 是 Kubernetes 最小调度单位。

一个 Pod 可以包含多个紧密耦合容器，它们通常共享：

- network namespace；
- localhost；
- 按各容器挂载声明访问 Pod 内声明的 volume；
- 生命周期边界。

不要把 Pod 直接等同于“一个容器”。

## 4. 工作负载对象

### Deployment

适合无状态服务：

- replica；
- rolling update；
- rollback；
- declarative rollout。

### ReplicaSet

保证某个 Pod 模板的副本数，通常由 Deployment 管理。

### StatefulSet

适合：

- 数据库；
- 有稳定网络身份需求；
- 有序启动/停止；
- 持久存储绑定。

### DaemonSet

保证每个或指定节点运行一个 Pod，常用于：

- log agent；
- monitoring agent；
- CNI/CSI 组件；
- node security agent。

### Job / CronJob

用于一次性任务和定时任务。

## 5. Service 与服务发现

Pod 是短生命周期对象，IP 会变。

Service 提供：

- 稳定虚拟地址；
- DNS 名称；
- 流量负载；
- 后端 Pod 选择。

应用应面向 Service，而不是记录 Pod IP。

## 6. Ingress 与 Gateway API

它们解决集群外部流量进入服务的问题。

新系统更应理解 Gateway API 的角色模型与可扩展路由，而不是只记某个 Ingress Controller 的注解。

## 7. 配置与秘密

### ConfigMap

保存非敏感配置。

### Secret

保存敏感数据的 Kubernetes 对象，但“放进 Secret”并不自动等于安全：

- 需要 RBAC；
- etcd 加密；
- 访问审计；
- rotation；
- 外部 secret manager 集成。

## 8. 持久化

Kubernetes 把存储分成：

- PV：存储资源；
- PVC：工作负载对存储的请求；
- StorageClass：动态供应策略；
- CSI：存储插件标准接口。

这可以解耦应用和供应接口，但不保证数据自动跨节点可用。local PV、访问模式、StorageClass、CSI 和实际存储后端仍决定迁移/共享能力；StatefulSet 也不会自动提供数据库复制、备份或高可用。

## 9. HPA

Horizontal Pod Autoscaler 根据指标调整副本数。

扩容设计必须同时考虑：

- CPU / memory 指标是否真的反映瓶颈；
- 冷启动；
- 下游容量；
- DB 连接池；
- queue；
- rate limit。

“自动加 Pod”不是无限容量。

## 10. Helm

Helm 是 Kubernetes 包管理/模板工具，解决：

- 多资源组合；
- 参数化；
- release；
- chart 分发。

要避免把复杂逻辑都堆进模板；业务架构仍应保持清晰。

## 11. Sidecar

Sidecar 是与主容器协作的辅助容器，例如：

- proxy；
- log shipping；
- config reload；
- data sync。

使用前应判断它是否真的需要与主应用共享 Pod 生命周期，否则可能增加资源和故障耦合。

## 12. Pod Security

生产集群应围绕最小权限设计：

- 非 root；
- read-only root filesystem；
- drop capabilities；
- 禁止 privileged；
- seccomp；
- 限制 hostPath / hostNetwork / hostPID；
- namespace / RBAC 分区。

## 13. 控制平面与工作节点

### Control Plane

主要组件包括：

- API Server；
- Scheduler；
- Controller Manager；
- etcd。

### Worker

主要包括：

- kubelet；
- container runtime；
- CNI；
- kube-proxy 或等效数据平面；
- 实际 Pod。

## 14. etcd

etcd 是强一致分布式 KV 存储。

在 Kubernetes 中，它保存控制平面关键状态，因此：

- 数据一致性比单节点吞吐更重要；
- 集群成员数通常采用奇数；
- 需要备份与恢复；
- 需要 TLS；
- 不应把 etcd 当普通业务缓存使用。

理解 Raft 的基本目标：

```text
多个节点
→ 选举 leader
→ 日志复制
→ 多数派提交
→ 一致状态
```

## 15. 集群部署方式的正确认知

### kubeadm

适合理解标准 Kubernetes 集群构成和自建集群流程。

### Kind

在 Docker/容器中运行 Kubernetes 节点，适合：

- 本地开发；
- CI；
- 控制器测试；
- 学习。

### K3s

轻量 Kubernetes 发行版，适合：

- edge；
- homelab；
- 资源受限节点；
- 小型集群。

不要把某个安装脚本本身当作知识重点。

## 16. Docker 与 Kubernetes 的关系

Kubernetes 的运行时接口是 CRI，不依赖 Docker Engine。

```text
Kubernetes
   ↓ CRI
containerd / CRI-O
   ↓ OCI runtime
runc
```

如果必须让 Kubernetes 使用 Docker Engine，需要额外适配层；新集群应优先使用原生 CRI runtime。

## 17. 云上的容器形态

云平台通常提供三类能力：

- 托管 Kubernetes；
- serverless / container instance；
- managed registry。

多云设计不要追求“所有云完全一样”，而应固定真正需要可移植的接口：

- OCI image；
- Kubernetes API；
- IaC；
- observability；
- secret abstraction；
- data portability。

数据库、网络和身份系统往往是多云成本最高的部分。

## 18. 从 Compose 迁移到 Kubernetes 的思路

```text
Compose service
→ Deployment / StatefulSet

Compose network
→ Service + NetworkPolicy

Compose volume
→ PVC / StorageClass

environment
→ ConfigMap / Secret

healthcheck
→ liveness / readiness / startup probe

ports
→ Service / Gateway
```

迁移目标不是“逐字段翻译”，而是把单机应用重新表达为声明式集群系统。

## 19. 用一个失败场景区分三种探针

假设 API 启动需 40 秒，启动后可能暂时连接不到数据库：

- startup probe 给启动预热留出窗口，成功前不执行 liveness/readiness 检查；
- readiness 失败通常使该 Pod 不再作为常规 Service 就绪后端，避免接入新流量，不会因此自动重启；
- liveness 达到失败阈值会导致容器重启，应检查进程自身无法恢复的状态，不宜把所有下游故障都算成本进程死亡。

自测：数据库短暂不可用时，所有 API 的 liveness 都查 DB，可能怎样？答：大量正常 API 被同时重启，叠加冷启动和重连压力。先区分“暂时不能服务”和“本进程必须重启”。

etcd 的 3 个成员需要 2 个形成多数派，可容忍 1 个失效；5 个需要 3 个，可容忍 2 个。增加成员不是免费扩吞吐。NetworkPolicy 还要求网络插件支持和实施策略，创建 YAML 不能独立证明流量被隔离。
