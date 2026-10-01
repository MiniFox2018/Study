# Docker 从入门到实践 v1.11.0｜来源保全与吸收映射

## 来源信息

- 名称：Docker 从入门到实践
- 作者：yeasy
- 版本：1.11.0
- 日期：2026-07-04
- 原文件：`docker_practice-v1.11.0.pdf`
- PDF 页数：775
- 基线：Docker Engine v29.x
- 许可证：CC BY-NC-SA 4.0
- 吸收时间：2026-10-01
- 主知识库入口：[容器化与 Docker](../../计算机科学基础/07-容器化与Docker/README.md)

## 处理策略

本次不是把 775 页 PDF 原样复制进仓库，而是：

1. 完整读取目录、正文、实践章节与附录；
2. 把长期有效知识重构为 8 个主知识模块；
3. 删除/降级易失效的平台安装细节、UI、镜像加速地址、短期版本号与云价格；
4. 保留每章到主知识库的映射，确保没有“看过但没落仓”的章节；
5. 对被淘汰的旧用法，仅保留其替代原则，不把历史命令继续作为推荐实践。

## 21 章覆盖映射

| 原章节 | 吸收位置 | 处理 |
|---|---|---|
| 1 Docker 简介 | 01 核心模型 | 完整吸收价值、容器 vs VM、适用边界 |
| 2 基本概念 | 01、02、03 | 镜像/容器/Registry 全部吸收 |
| 3 安装 Docker | 01 | 只保留安装决策原则与权限风险；具体版本命令不固化 |
| 4 使用镜像 | 02 | pull/list/remove、分层、digest、save/load、commit 边界 |
| 5 操作容器 | 01、08 | 生命周期、PID 1、exec/attach、清理与排障 |
| 6 访问仓库 | 03 | 公私有 Registry、认证、Harbor/Nexus、供应链 |
| 7 Dockerfile | 02 | 全部核心指令、多阶段、最佳实践 |
| 8 数据管理 | 03 | Volume/Bind/tmpfs、备份、权限、持久化 |
| 9 网络配置 | 03 | bridge/host/none/macvlan/overlay、DNS、端口与隔离 |
| 10 Buildx | 02 | BuildKit、buildx、多架构、manifest |
| 11 Compose | 04 | service/network/volume/config/secret/health/profile 与案例模式 |
| 12 底层实现 | 05 | Docker 架构、namespace、cgroup、OverlayFS、OCI |
| 13 容器编排基础 | 06 | Kubernetes 对象模型、控制器、Service、存储、高级特性 |
| 14 部署 Kubernetes | 06 | kubeadm/Kind/K3s 角色与选择；短期安装命令不固化 |
| 15 Etcd | 06 | etcd、Raft、集群、备份与 Kubernetes 角色 |
| 16 容器与云计算 | 06 | 托管 K8s、容器实例、Registry、多云原则；价格不固化 |
| 17 容器其它生态 | 05 | CoreOS 思路、Podman/Buildah/Skopeo/containerd/Kata/gVisor/Wasm |
| 18 安全 | 07 | daemon、namespace、cgroup、capability、seccomp、MAC、供应链 |
| 19 监控与日志 | 07 | Prometheus/Grafana/ELK、指标、OOM、性能、上线清单 |
| 20 操作系统案例 | 05 | BusyBox/Alpine/Debian/Ubuntu/RHEL 系选型原则 |
| 21 DevOps | 08 | CI/CD、GitHub Actions/Drone 抽象、Dev Container、实战模式 |

## 8 个附录覆盖映射

| 附录 | 吸收方式 |
|---|---|
| 常见问题与错误速查 | 合并进 08 的排障与误区 |
| 热门镜像介绍 | 合并进 05 的基础镜像选型 |
| Docker 命令查询 | 合并进 08 的问题导向速查 |
| Dockerfile 最佳实践 | 合并进 02 |
| 如何调试 Docker | 合并进 07、08 |
| 资源链接 | 不复制易失效链接清单，保留“优先官方文档”原则 |
| 术语表 | 术语已在 01～08 首次出现处定义 |
| 学习路线图与知识体系 | 重构进专题 README 与 08 的完成标准 |

## 明确不进入主知识库的内容

以下内容并非遗漏，而是按 Study 规则主动淘汰或降级：

- 已废弃的 `--link` 等旧用法；
- Docker Compose V1 历史写法；
- 已停止的镜像加速地址；
- 某日有效的 Docker Hub 配额数字；
- 某个云厂商当期价格；
- Docker Desktop 菜单截图；
- 具体发行版当前支持小版本列表；
- 特定软件当前版本号；
- 纯历史项目沿革；
- 可由官方文档实时获取的安装 UI。

这些信息一旦需要，应以官方最新文档为准。

## 完整性结论

原资料的知识主线已经覆盖：

```text
容器基本模型
→ 镜像与构建
→ 生命周期
→ Registry
→ Dockerfile
→ 数据与网络
→ BuildKit/buildx
→ Compose
→ 底层机制
→ Kubernetes/etcd
→ 容器生态
→ 安全
→ 监控与日志
→ OS 镜像选择
→ DevOps
→ 命令、调试与学习路线
```

后续无需重新阅读原 PDF 才能建立 Docker 的完整知识框架；只有查询某个版本、平台或命令的最新细节时，再回到官方实时文档核验。
