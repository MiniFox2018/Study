# Linux 学习资源来源保全

> 本目录用于保存本次 Linux 知识吸收的来源版本、许可、覆盖范围与恢复标识。主学习入口位于：  
> [计算机科学基础 / 08-Linux系统与运维](../../计算机科学基础/08-Linux系统与运维/README.md)

## 1. USTC LUG Linux 101 Docs

- 仓库：<https://github.com/ustclug/Linux101-docs>
- 默认分支：master
- 基准提交：222487639e197366d217248f072b7d2c8d9a5e46
- 基准提交日期：2026-08-27
- 许可证：Creative Commons Attribution-ShareAlike 4.0 International（CC BY-SA 4.0）
- 基准规模：148 个 blob
- Markdown：36 个
- 图片：PNG 88、JPG 3、GIF 5
- 其余：少量 shell、CSS/SCSS、MkDocs/Node/Python 构建配置

### Markdown 原始清单

~~~text
README.md
docs/Appendix/distribution.md
docs/Appendix/man.md
docs/Appendix/markdown.md
docs/Appendix/wsl.md
docs/Ch01/index.md
docs/Ch01/solution.md
docs/Ch01/supplement.md
docs/Ch02/index.md
docs/Ch02/solution.md
docs/Ch02/supplement.md
docs/Ch03/index.md
docs/Ch03/solution.md
docs/Ch03/supplement.md
docs/Ch04/index.md
docs/Ch04/solution.md
docs/Ch04/supplement.md
docs/Ch05/index.md
docs/Ch05/solution.md
docs/Ch05/supplement.md
docs/Ch06/index.md
docs/Ch06/solution.md
docs/Ch06/supplement.md
docs/Ch07/index.md
docs/Ch07/supplement.md
docs/Ch08/index.md
docs/Ch08/supplement.md
docs/Ch09/index.md
docs/Ch09/supplement.md
docs/Spec/slide.md
docs/Spec/writing.md
docs/credits.md
docs/index.md
docs/notations.md
docs/postface.md
docs/preface.md
~~~

### 恢复方式

需要核对历史正文、图片、思考题、截图或课程站点文件时，以基准提交作为唯一恢复锚点：

~~~text
repository: ustclug/Linux101-docs
commit: 222487639e197366d217248f072b7d2c8d9a5e46
~~~

主知识库未机械复制 97 个图片文件，因为多数承担截图、桌面/虚拟机界面、Logo 和课程展示作用，且具有版本时效性；对应原始字节可由 commit 精确恢复。

## 2. dunwu/linux-tutorial

- 仓库：<https://github.com/dunwu/linux-tutorial>
- 默认分支：master
- 基准提交：b672dd04296093c4a525bb6682f3f41b8afcbbd7
- 基准提交日期：2025-08-27
- 许可证：Creative Commons Attribution-ShareAlike 4.0 International（CC BY-SA 4.0）
- 基准规模：356 个 blob
- Markdown：68 个
- Shell：219 个
- conf：26 个
- 另含 systemd service、repo、XML、XMind、JS 等

### 内容分布

~~~text
docs/linux/cli/       Linux 命令与命令行
docs/linux/ops/       systemd、网络、时间、防火墙、Samba、Vim、Zsh
docs/linux/soft/      各类中间件和开发工具安装/运维
docs/docker/          Docker / Dockerfile / Compose / Kubernetes
codes/shell/          146 个 Shell 学习/实战文件
codes/linux/          123 个系统、发布、中间件安装与配置文件
assets/*.xmind        Linux / Docker 思维导图等
~~~

### 主要 Markdown 内容清单

~~~text
README.md
codes/linux/README.md
codes/linux/build/README.md
codes/linux/libtest/README.md
codes/linux/soft/README.md
codes/linux/soft/config/redis/cluster/README.md
codes/linux/sys/README.md
codes/shell/README.md
docs/README.md
docs/docker/README.md
docs/docker/docker-cheat-sheet.md
docs/docker/docker-compose.md
docs/docker/docker-dockerfile.md
docs/docker/docker-quickstart.md
docs/docker/kubernetes.md
docs/docker/service/docker-install-mysql.md
docs/docker/service/docker-install-nginx.md
docs/linux/cli/README.md
docs/linux/cli/free.md
docs/linux/cli/grep.md
docs/linux/cli/iostat.md
docs/linux/cli/iotop.md
docs/linux/cli/linux-cli-dir.md
docs/linux/cli/linux-cli-file-compress.md
docs/linux/cli/linux-cli-file.md
docs/linux/cli/linux-cli-hardware.md
docs/linux/cli/linux-cli-help.md
docs/linux/cli/linux-cli-net.md
docs/linux/cli/linux-cli-software.md
docs/linux/cli/linux-cli-system.md
docs/linux/cli/linux-cli-user.md
docs/linux/cli/scp.md
docs/linux/cli/top.md
docs/linux/cli/vmstat.md
docs/linux/cli/命令行的艺术.md
docs/linux/expect.md
docs/linux/ops/README.md
docs/linux/ops/crontab.md
docs/linux/ops/firewalld.md
docs/linux/ops/iptables.md
docs/linux/ops/network-ops.md
docs/linux/ops/ntp.md
docs/linux/ops/samba.md
docs/linux/ops/systemd.md
docs/linux/ops/vim.md
docs/linux/ops/zsh.md
docs/linux/soft/README.md
docs/linux/soft/apollo/README.md
docs/linux/soft/elastic/README.md
docs/linux/soft/elastic/elastic-beats.md
docs/linux/soft/elastic/elastic-kibana.md
docs/linux/soft/elastic/elastic-logstash.md
docs/linux/soft/elastic/elastic-quickstart.md
docs/linux/soft/fastdfs.md
docs/linux/soft/gitlab-ops.md
docs/linux/soft/jdk-install.md
docs/linux/soft/jenkins-ops.md
docs/linux/soft/kafka-install.md
docs/linux/soft/maven-install.md
docs/linux/soft/mongodb-ops.md
docs/linux/soft/nacos-install.md
docs/linux/soft/nexus-ops.md
docs/linux/soft/nodejs-install.md
docs/linux/soft/rocketmq-install.md
docs/linux/soft/svn-ops.md
docs/linux/soft/tomcat-install.md
docs/linux/soft/yapi-ops.md
docs/mac/soft/ruby-install.md
~~~

### Shell 与运维脚本的保全策略

原仓库包含 219 个 Shell 文件，其中大量属于：

- Shell 语法示例；
- sed/awk/grep；
- 参数/选项/getopts；
- 重定向/文件描述符；
- trap/信号；
- 函数和数组；
- 远程执行；
- 数据库批处理；
- Java/JS 应用发布；
- CentOS 系统初始化；
- JDK、Tomcat、Kafka、Redis、Elastic、Nacos、Docker 等历史安装脚本。

主知识库没有原样复制这些脚本，原因是其中相当一部分绑定旧 CentOS、固定软件版本、失效仓库地址或旧安全实践。

处理方式：

1. 所有脚本类别先纳入来源覆盖审计；
2. 仍有效的 Shell 语法与自动化模式进入主知识库；
3. 发布脚本提炼为 artifact → release → health check → rollback 模型；
4. 固定版本中间件安装脚本转化为通用部署生命周期；
5. 旧 CentOS、关闭防火墙/SELinux、旧网络脚本、旧 NTP 等实现不保留为推荐实践；
6. 如需历史脚本字节，可通过 commit 精确恢复。

### 恢复方式

~~~text
repository: dunwu/linux-tutorial
commit: b672dd04296093c4a525bb6682f3f41b8afcbbd7
~~~

## 3. 为什么不是原仓库镜像

Study 的目标是“学习后不必依赖原网页”，不是保留所有历史工程噪声。

因此采用两层结构：

~~~text
主知识库
= 去重 + 现代化 + 可直接学习

来源保全
= 来源版本 + 完整目录证据 + 可恢复标识
~~~

以下内容没有机械镜像：

- GitHub Actions / Travis / VuePress / MkDocs 构建文件；
- Logo、版本化 UI 截图；
- 重复 Docker 内容；
- 固定中间件旧版本安装脚本；
- CentOS 5/6/7 repo；
- 失效或不再推荐的系统配置方式。

这些内容在需要历史核验时仍可依据上方 commit 恢复。

## 4. 主知识库覆盖入口

完整吸收关系见：

- [Linux 系统与运维](../../计算机科学基础/08-Linux系统与运维/README.md)
- [来源映射与审计](../../计算机科学基础/08-Linux系统与运维/来源映射与审计.md)
- [容器化与 Docker](../../计算机科学基础/07-容器化与Docker/README.md)

本记录与基准 commit 一起构成此次吸收的可追溯证据。
