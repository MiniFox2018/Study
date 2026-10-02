# 04｜进程、systemd 与任务调度

## 1. 进程是 Linux 运行时的基本对象

程序是磁盘上的代码，进程是正在执行的实例。

每个进程至少要理解：

- PID：进程 ID；
- PPID：父进程 ID；
- UID/GID：运行身份；
- cwd：当前工作目录；
- open files：打开的文件和 socket；
- environment：环境变量；
- memory mappings：地址空间；
- scheduling state：调度状态。

常用观察：

~~~bash
ps aux
ps -ef
top
htop
pstree -p
~~~

## 2. 进程状态

常见状态：

- R：running/runnable；
- S：可中断睡眠；
- D：不可中断睡眠，常见于等待 I/O；
- T：停止/跟踪；
- Z：zombie。

Zombie 不是“还在运行”，而是子进程已经退出，但父进程尚未回收退出状态。

大量 D 状态通常值得关注存储、NFS、设备或内核 I/O 路径，而不是直接 kill。

## 3. 父子进程、进程组与会话

Linux 进程有层级关系。Shell 启动外部命令时，通常经历创建子进程并执行目标程序。

进程组和 session 用于组织作业控制、终端信号和前后台任务。

理解这些概念有助于解释：

- Ctrl+C 为什么能终止前台作业；
- 为什么后台进程可能仍收到 SIGHUP；
- tmux/nohup/disown 为什么能让任务脱离终端。

## 4. 信号

信号是进程间和内核向进程发送事件的一种机制。

| 信号 | 含义 |
|---|---|
| SIGINT | 交互中断，常由 Ctrl+C 产生 |
| SIGTERM | 请求进程正常退出 |
| SIGKILL | 请求不可捕获/忽略的强制终止；处于某些不可中断等待时不保证立即消失 |
| SIGHUP | 终端断开；也常被服务用作重新加载 |
| SIGSTOP | 强制暂停 |
| SIGCONT | 继续运行 |

常规停止服务优先 SIGTERM，让程序有机会 flush 数据、关闭连接、完成事务和清理状态。

~~~bash
kill PID
kill -TERM PID
kill -KILL PID
~~~

kill -9 应作为最后手段，而不是常规停止方式。

## 5. nice 与调度优先级

nice 值影响普通调度类中 CPU 调度倾向：

~~~bash
nice -n 10 command
renice 10 -p PID
~~~

它不是绝对 CPU 配额，也不能解决内存、I/O 或锁竞争问题。容器和现代服务中，资源边界通常还通过 cgroup 实现。

## 6. Shell 作业控制

~~~bash
command &
jobs
fg %1
bg %1
~~~

Ctrl+Z 通常发送 SIGTSTP，把前台作业暂停；bg 继续后台执行；fg 拉回前台。

## 7. nohup、disown 与 tmux

### nohup

让程序忽略 SIGHUP，适合简单、一次性的长任务。

### disown

由 shell 移除作业跟踪，可减少 shell 退出对任务的影响。

### tmux

更适合交互式长任务：

- 会话持续存在；
- 可以 detach/attach；
- 支持多个窗口和 pane；
- SSH 断线后可恢复。

生产服务不应靠 nohup 或 tmux 永久托管，应使用 systemd、容器编排或其他服务管理器。

## 8. 守护进程与服务

Daemon 是长期后台运行的服务进程。现代 Linux 主流由 systemd 管理服务，其职责包括：

- 启动顺序；
- 依赖关系；
- 自动重启；
- 资源与权限约束；
- 日志关联；
- socket/timer/path 激活；
- 开机启停。

## 9. systemd 的 Unit

systemd 管理对象称为 unit。

常见类型：

- .service：服务；
- .socket：socket 激活；
- .timer：定时任务；
- .mount：挂载；
- .path：路径监控；
- .target：多个 unit 的逻辑集合。

~~~bash
systemctl list-units
systemctl list-unit-files
systemctl --failed
~~~

## 10. systemctl：状态、启动与开机启用

~~~bash
systemctl status nginx
sudo systemctl start nginx
sudo systemctl stop nginx
sudo systemctl restart nginx
sudo systemctl reload nginx
sudo systemctl enable nginx
sudo systemctl disable nginx
~~~

关键区别：

- start：现在启动；
- enable：配置为随对应 target 启动；
- enable --now：同时启用并立即启动。

## 11. 一个 service unit 结构示意

以下是模板，运行前须已创建 example 用户/组、工作目录和可执行程序；不要直接复制后重启真实服务。

~~~ini
[Unit]
Description=示例服务
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=example
Group=example
WorkingDirectory=/srv/example
ExecStart=/srv/example/bin/server
Restart=on-failure

[Install]
WantedBy=multi-user.target
~~~

修改 unit 后：

~~~bash
sudo systemctl daemon-reload
sudo systemctl restart example.service
~~~

长期原则：

- 使用绝对路径；
- 以非 root 用户运行；
- 明确 WorkingDirectory；
- 让日志进入 stdout/stderr 或系统日志；
- 使用 Restart 策略但避免无限快速重启；
- 再逐步加入 sandbox 与资源限制。

## 12. Unit 依赖与顺序

常见：

- Requires：强依赖；
- Wants：弱依赖；
- After/Before：启动顺序；
- WantedBy：enable 时链接到目标 target。

“依赖关系”和“启动顺序”不是同一件事。

After=network.target 并不保证外网已经可访问。真正需要可用网络的服务常使用 network-online.target，但具体含义仍取决于发行版网络管理器。

## 13. Target

target 类似“系统状态集合”，但不要简单等同于旧 SysV runlevel。

常见：

- multi-user.target；
- graphical.target；
- rescue.target；
- emergency.target。

~~~bash
systemctl get-default
# 修改默认启动目标会影响下次开机；确认目标后才执行管理命令
~~~

## 14. journalctl

systemd-journald 收集结构化日志。

~~~bash
journalctl
journalctl -b
journalctl -b -1
journalctl -u nginx.service
journalctl -u nginx.service -f
journalctl --since '1 hour ago'
journalctl -p warning
journalctl -k
~~~

排查服务失败时的标准路径：

~~~text
systemctl status service
→ journalctl -u service
→ 配置/权限/端口/依赖
~~~

## 15. 日志持久化和容量

Journal 可以存内存或磁盘，行为取决于配置。

~~~bash
journalctl --disk-usage
~~~

生产环境还应设计 retention、rotation/vacuum、中央日志采集、磁盘上限和时间同步。

## 16. Cron

crontab 典型五个时间字段：

~~~text
minute hour day-of-month month day-of-week command
~~~

示例：

~~~cron
5 3 * * * /usr/local/bin/backup
*/15 * * * * /usr/local/bin/check
~~~

常见陷阱：

- PATH 比交互式 shell 少；
- HOME/工作目录不同；
- stdout/stderr 没有被正确保存；
- 同一任务可能重叠执行；
- 命令依赖用户 shell 配置；
- 时区/DST 影响执行时间。

因此 cron 中应使用绝对路径、明确环境、记录日志，并为不可重入任务加锁。

## 17. systemd timer

现代 systemd 主机上，服务型定时任务常适合 timer。

优势：

- 与 service unit 分离；
- 日志天然进入 journal；
- 可以表达 OnCalendar；
- `Persistent=true` 可让 OnCalendar 定时器在恢复激活时补触发一次错过的事件，不代表逐次重放所有漏跑任务；
- 支持随机延迟；
- 依赖/权限/资源策略可复用。

不要因为熟悉 cron 就忽略 timer；也不必把所有简单 cron 强行改成 timer。

## 18. at

at 适合一次性的未来任务，而不是周期性任务。

## 19. 长任务的正确托管

~~~text
临时交互长任务 → tmux
一次性后台任务 → systemd-run / nohup（简单场景）
周期任务 → systemd timer / cron
长期服务 → systemd service
容器化服务 → 容器运行时/编排
~~~

## 20. SysV init 与 rc.local

旧资料中的：

- service 命令；
- chkconfig；
- /etc/init.d；
- rc.local；
- runlevel；

今天仍可能在兼容环境见到，但不作为新部署主方案。理解即可，不应把旧 CentOS 启动脚本复制到现代主机。

## 21. SysRq

Magic SysRq 是内核级紧急控制机制，可在用户空间严重失灵时执行部分诊断或恢复动作。

它属于高级故障处置工具，误用可能导致数据丢失。应在了解具体键位效果、文件系统状态和运行环境后使用。

## 22. 故障排查顺序

服务无法启动时：

~~~text
systemctl status
→ journalctl -u
→ unit ExecStart 是否存在
→ 运行用户/权限
→ 配置语法
→ 端口占用
→ 依赖服务
→ 文件系统/磁盘
→ SELinux/AppArmor
→ 资源限制
~~~

不要一开始就重装软件或 kill -9。

## 23. 可运行练习：用户级一次性服务

前提是 Linux 的 systemd 用户管理器可用（先运行 `systemctl --user status`）。先运行 `mkdir -p ~/.config/systemd/user` 建立目录，再把以下内容保存到 `~/.config/systemd/user/study-hello.service`，若同名文件已存在先检查，勿覆盖自己的服务：

~~~ini
[Unit]
Description=学习用一次性问候

[Service]
Type=oneshot
ExecStart=/usr/bin/printf "学习服务运行成功\n"
~~~

~~~bash
systemctl --user daemon-reload
systemctl --user start study-hello.service
journalctl --user -u study-hello.service --no-pager -n 10
~~~

日志应包含 `学习服务运行成功`。oneshot 成功退出后显示 inactive 是正常状态；状态是否符合任务语义比“永远 running”重要。检查退出状态可用 `systemctl --user show study-hello.service -p Result -p ExecMainStatus`，成功时常见 `Result=success`、`ExecMainStatus=0`。本例没有启用开机任务，不需要 sudo。

自测：改了 unit 文件但只执行 start 就一定用新定义吗？答：不一定，应先 daemon-reload；它重读 unit 定义，不等于重启已运行的服务。
