# 06｜网络、SSH 与防火墙

## 1. Linux 网络排障先建立模型

一台主机的网络至少分为：

~~~text
interface
→ link
→ IP address / prefix
→ route
→ DNS
→ socket / port
→ host firewall
→ upstream network/firewall
→ remote service
~~~

“ping 不通”“curl 不通”“域名打不开”不是同一个问题。

## 2. iproute2 是现代主入口

优先使用：

~~~bash
ip link
ip addr
ip route
ip neigh
ss -lntup
~~~

它们分别回答：

- 网卡是否 up；
- IP 是否正确；
- 路由走哪里；
- 邻居/ARP/NDP 是否正常；
- 哪些进程在监听端口。

旧命令 ifconfig、route、netstat 仍可能存在，但属于 net-tools 时代，不作为新运维主接口。

## 3. 地址、前缀与路由

CIDR 示例：

~~~text
192.168.1.10/24
2001:db8::10/64
~~~

路由表决定目标地址通过哪个接口、下一跳是什么。

~~~bash
ip route
ip route get 8.8.8.8
~~~

排障时不要只看有没有 IP，还要看默认路由、子网路由、policy routing、VPN/tunnel 和多网卡优先级。

## 4. DNS

域名解析和 IP 连通性是两个层次。

~~~bash
getent hosts example.com
dig example.com
host example.com
nslookup example.com
~~~

优先 getent 检查应用实际使用的系统解析路径；dig 更适合直接查询 DNS 记录。

常见问题：

- /etc/resolv.conf 指向错误；
- systemd-resolved/NetworkManager 管理的 stub resolver；
- 搜索域；
- 内外网 split DNS；
- DNS 可达但远端服务不可达。

## 5. ping、traceroute 与 tracepath

ping 测试 ICMP 回显，不等同于应用服务健康。远端可能屏蔽 ICMP，但 TCP/HTTPS 正常。

~~~bash
ping host
traceroute host
tracepath host
~~~

路由跟踪结果受 ACL、负载均衡和 ICMP 策略影响，只能作为证据之一。

## 6. curl 与 wget

### curl

更适合 API、协议调试和请求构造：

~~~bash
curl -v https://example.com
curl -I https://example.com
curl -o file URL
~~~

### wget

更偏向下载和递归抓取场景。

下载生产 artifact 时应校验 HTTPS、checksum、签名和版本来源。

## 7. nc/netcat

nc 是通用 TCP/UDP 测试工具。

~~~bash
nc -vz host 443
~~~

它可以帮助区分 TCP 端口是否能连接，但不能替代真正应用层健康检查。

## 8. ss

~~~bash
ss -lnt
ss -lntp
ss -ant
ss -s
~~~

排查“端口明明启动却访问不到”时先看：

- 是否监听；
- 监听 127.0.0.1 还是 0.0.0.0/::；
- 进程是谁；
- TCP 状态；
- 防火墙是否允许。

## 9. SSH 的信任模型

第一次连接主机会看到 host key fingerprint。

真正意义是：客户端需要确认“这台主机确实是预期服务器”，防止中间人攻击。

主机密钥记录在 known_hosts。

如果已知主机的 key 突然变化，不要机械删除 known_hosts 条目，先确认服务器是否重装、IP 是否复用、DNS 是否指向新主机以及是否存在中间人风险。

## 10. SSH 密钥登录

现代新建密钥通常优先 Ed25519：

~~~bash
ssh-keygen -t ed25519
ssh-copy-id user@host
ssh user@host
~~~

私钥：

- 不上传到服务器；
- 不共享；
- 建议设置 passphrase；
- 权限应严格；
- 可使用 ssh-agent 管理解锁后的 key。

公钥放到远端用户 authorized_keys。

## 11. ~/.ssh/config

可以把复杂连接参数变成别名：

~~~sshconfig
Host prod
    HostName 203.0.113.10
    User deploy
    Port 22
    IdentityFile ~/.ssh/id_ed25519
~~~

之后使用 ssh prod。复杂环境还可以配置 ProxyJump、不同 key、KeepAlive 等。

## 12. SSH 服务安全

优先：

- 使用密钥认证；
- 限制可登录用户；
- root 远程登录按环境谨慎控制；
- 定期更新 OpenSSH；
- 保护私钥；
- 配合 MFA/堡垒机时遵循组织策略；
- 日志监控失败登录；
- 防火墙只开放必要来源。

修改 SSH 到非 22 端口只能减少扫描噪声，不能替代认证和补丁。

## 13. SCP、SFTP 与 rsync

### scp

适合简单文件复制。

### sftp

基于 SSH 文件传输子系统，语义更明确。

### rsync

适合目录同步和增量传输：

~~~bash
rsync -aH --info=progress2 source/ user@host:/target/
~~~

删除同步前使用 --dry-run。

生产发布不要只依赖“scp 覆盖目录”，应设计原子切换和回滚。

## 14. 防火墙分层

至少可能存在：

~~~text
application bind address
→ Linux host firewall
→ container/network namespace rules
→ VM/security group
→ VPC/network ACL
→ upstream enterprise firewall
~~~

开放 Linux 本机端口并不代表公网可达。

## 15. firewalld

firewalld 提供较高层的动态防火墙管理，常见于 Fedora/RHEL 系。

核心概念：

- zone；
- service；
- port；
- interface/source binding；
- runtime vs permanent configuration。

典型流程：

~~~bash
firewall-cmd --get-active-zones
firewall-cmd --list-all
sudo firewall-cmd --add-service=https --permanent
sudo firewall-cmd --reload
~~~

比“关闭防火墙”更正确的是添加最小必要规则。

## 16. nftables

nftables 是现代 Linux Netfilter 规则管理框架。

它统一承接传统 iptables、ip6tables、arptables、ebtables 和大量 ipset 用途。

核心对象：

~~~text
table
→ chain
→ rule
→ set/map
~~~

复杂、高性能或需要精细策略时可以直接使用 nft。

使用 firewalld 时不要同时随意手工修改同一规则域，避免多个管理层互相覆盖。

## 17. iptables 的位置

iptables 仍存在于很多系统和旧脚本，但新部署不应默认以它为首选。

仍需理解：

- INPUT / OUTPUT / FORWARD；
- filter/nat；
- state/connection tracking；
- DNAT/SNAT/masquerade；

因为大量历史系统仍依赖这些概念。迁移时优先考虑 nftables/firewalld。

## 18. NetworkManager

现代 RHEL/Fedora 和许多桌面 Linux 使用 NetworkManager。

常用 CLI：

~~~bash
nmcli device
nmcli connection show
~~~

旧 CentOS network-scripts、ifcfg-* 和 rc.local 网络修改方式不进入新部署基线。

## 19. NTP 与时间同步

正确时间对 TLS、日志排序、Kerberos、分布式系统、数据库和审计都至关重要。

现代系统常使用：

- chrony；
- systemd-timesyncd；
- 发行版提供的其他受支持 NTP 客户端。

~~~bash
timedatectl
~~~

旧 ntpd/ntpdate 教程可用于理解 NTP 原理，但不应默认照抄。

## 20. Samba/SMB

Samba 用于 Linux 与 Windows/SMB 客户端共享文件和打印资源。

真正需要同时处理三层权限：

~~~text
Samba share/auth 配置
+
Linux 文件系统 owner/group/ACL
+
SELinux/firewall
~~~

旧教程常建议关闭 SELinux 和防火墙，这是错误的长期习惯。正确方式是配置对应端口、服务和安全上下文。

## 21. 网络故障最小排查流程

### 域名访问失败

~~~text
getent/dig 是否能解析
→ IP 是否正确
→ ip route get
→ nc/curl 目标端口
→ 本机防火墙
→ 上游网络
→ 远端服务
~~~

### 本机服务外部访问失败

~~~text
systemctl status
→ ss -lntp
→ 是否只监听 localhost
→ firewalld/nftables
→ VM/云安全组
→ 路由/NAT
→ 客户端 DNS
~~~

### SSH 失败

~~~text
DNS/IP
→ route
→ TCP 22/自定义端口
→ ssh -vvv
→ host key
→ 用户/密钥权限
→ sshd 日志
→ AllowUsers/认证策略
~~~

## 22. 抓包

当应用层证据不足时，tcpdump 是关键工具：

~~~bash
sudo tcpdump -ni any host 203.0.113.10
sudo tcpdump -ni eth0 port 443
~~~

抓包会包含敏感流量元数据甚至明文内容，应按最小范围采集并妥善处理。
