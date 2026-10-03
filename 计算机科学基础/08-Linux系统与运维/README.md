# 08｜Linux 系统与运维

> 定位：把 Linux 作为一套可解释、可操作、可排障的系统来学习，而不是背命令清单。

本专题综合吸收：

- USTC LUG 的 Linux 101 Docs：作为系统化入门主骨架；
- dunwu/linux-tutorial：作为命令、运维与 Shell 实战补强；
- Study 现有操作系统与 Docker 内容：负责原理和容器专题，避免重复。

## 学习目标

完成本专题后，应能够独立完成以下工作：

1. 解释 Linux kernel、用户空间、发行版、shell、进程、文件系统与服务之间的关系；
2. 在陌生 Linux 主机上快速识别系统、用户、网络、磁盘、进程和服务状态；
3. 熟练使用文件、文本、正则、管道、重定向与帮助系统；
4. 正确管理用户、权限、软件包、systemd、日志、定时任务；
5. 使用 SSH、iproute2、DNS 与现代防火墙工具完成常见网络配置和排障；
6. 用 top、free、vmstat、iostat、iotop、journalctl 等定位 CPU、内存、I/O、服务问题；
7. 编写可维护的 Bash 自动化脚本，而不是只会拼接命令；
8. 能识别旧教程中的 CentOS/Yum、SysV、ifconfig、iptables、ntpdate 等历史写法，并转换为当前实践。

## 现代基线

本知识库以 2026 年仍通用的 Linux 实践为基线：

- 服务管理：优先 systemd / systemctl / journalctl；
- 网络：优先 iproute2，即 ip、ss 等；ifconfig、route、netstat 仅作为兼容旧环境的知识；
- 防火墙：优先 firewalld 或 nftables；iptables 作为遗留兼容层理解；
- 软件源：使用发行版当前受支持的软件仓库与签名机制，不沿用 apt-key 等废弃流程；
- RHEL/Fedora 系：以 dnf 体系理解，旧 yum 教程只保留概念价值；
- 时间同步：优先 chrony 或系统自带时间同步服务，不把 ntpdate 作为常驻方案；
- 网络配置：优先 NetworkManager/nmcli 或发行版当前网络栈，不依赖旧 network-scripts；
- 容器：Linux 基础只保留衔接知识，完整 Docker/Kubernetes 内容进入 ../07-容器化与Docker/；
- 具体版本、安装 UI、镜像地址和云厂商操作属于高时效信息，需要使用时重新核验。

## 学习路径

1. [系统基础、发行版与运行环境](./01-系统基础-发行版与运行环境.md)
2. [命令行、文件、文本与正则](./02-命令行-文件-文本-正则.md)
3. [用户、权限与文件系统](./03-用户-权限-文件系统.md)
4. [进程、systemd 与任务调度](./04-进程-systemd-任务调度.md)
5. [软件包、构建与开发环境](./05-软件包-构建-开发环境.md)
6. [网络、SSH 与防火墙](./06-网络-SSH-防火墙.md)
7. [性能、存储、日志与故障排查](./07-性能-存储-日志-故障排查.md)
8. [Shell 脚本、自动化与终端效率](./08-Shell脚本-自动化-终端效率.md)

完整来源覆盖、版本、许可证和筛除项见：

- [来源映射与审计](./来源映射与审计.md)
- [来源保全记录](../../来源保全/linux-resources/README.md)

## 与现有目录的边界

- ../02-计算机体系结构与操作系统.md：解释操作系统抽象、虚拟内存、调度、I/O 等原理；
- 本专题：回答“Linux 上如何观察、操作、配置、自动化和排障”；
- ../07-容器化与Docker/README.md：负责容器、镜像、Compose、Kubernetes、OCI、cgroup/namespace 的完整实践；
- ../../C++/：负责 C/C++ 语言与工程细节；本专题只讲 Linux 构建和运行环境。

## 使用方式

遇到问题时不要从“记住哪个命令”开始，而应先判断问题属于哪一层：

~~~text
用户/权限
→ 进程/服务
→ CPU/内存
→ 文件系统/磁盘
→ 网络/DNS/防火墙
→ 应用配置
→ 外部依赖
~~~

先定位层级，再选择命令。命令只是观测和操作接口。

## 练习前提与验证边界

本专题的系统管理默认 Linux + Bash，服务章节还要求 systemd。macOS 原生可以练通用文件/文本与部分 Bash 示例，但 `systemctl`、`ip`、`ss`、`/proc` 等不能直接照搬；GNU/BSD 的参数也可能不同。先完成 01 的系统识别，再选择适用命令。

建议按“02 临时目录文本练习 → 03 权限练习 → 08 只读脚本 → 04 用户级服务 → 06 本机网络 → 07 指标推理”推进。每次只观察自己的练习对象，修改一个输入，记录实际结果和解释；先不碰磁盘分区、系统账户和生产防火墙。

核验日期：2026-10-02。参考 [GNU Bash set 手册](https://www.gnu.org/software/bash/manual/html_node/The-Set-Builtin.html)、[Linux mount 手册](https://man7.org/linux/man-pages/man8/mount.8.html)、[Linux ldd 手册](https://man7.org/linux/man-pages/man1/ldd.1.html)。本轮修订明确 GNU/Linux 与 macOS 边界、SIGKILL 延迟、错误分类、fstab 检查和脚本末行处理；这不等于已在每个发行版/权限环境实跑全部管理命令。后续验证与更新说明用中文记录环境、命令、结果和未验证项。

### 2026-10-03 本机验证

在 macOS arm64 上使用 Bash 3.2.57、CMake 4.3.3、Python 3.12.13，验证了文本统计、umask 示例、CMake 构建、Bash 行计数的正常/空文件/无末尾换行/空格路径/缺参数分支，以及只监听 localhost 的 HTTP 请求（使用临时空闲端口，响应 200，随后停止）。这仅证明这些跨平台部分在本机成立；Linux systemd、iproute2、防火墙、挂载和内核指标未在 Linux 主机上运行。ldd 安全说明已核对上游 [ldd(1)](https://man7.org/linux/man-pages/man1/ldd.1.html)，systemd 的一次性服务与 timer 语义核对了 [官方 service 源文档](https://github.com/systemd/systemd/blob/main/man/systemd.service.xml)和 [timer 源文档](https://github.com/systemd/systemd/blob/main/man/systemd.timer.xml)。
## 远程实验闭环

[远程实验、进程与日志管理](./09-远程实验进程与日志管理.md)将已有命令、权限、服务、SSH与磁盘知识融合到一个实际工作流：确认运行位置 → 保留日志 → 管理会话/PID → 核对结果和资源。
