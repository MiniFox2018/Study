# 08｜Shell 脚本、自动化与终端效率

## 1. Shell 脚本的定位

Shell 最适合调用已有命令、文件与服务编排、CI/CD glue、系统初始化和小型批处理。出现复杂数据结构、长期状态、大量单元测试需求或复杂错误恢复时，应考虑 Python、Go 等语言。

## 2. Shebang

~~~bash
#!/usr/bin/env bash
~~~

也可以固定为：

~~~bash
#!/bin/bash
~~~

前者按 PATH 查找 bash，便于多环境；后者更确定。生产环境按可控性选择。

## 3. 变量与引用

~~~bash
name="linux"
echo "$name"
cp "$src" "$dst"
~~~

赋值两侧不能随意加空格。变量展开时通常加双引号，否则空格、通配符和空字符串可能改变参数数量。

## 4. 单引号与双引号

- 单引号：内容基本原样；
- 双引号：允许变量和命令替换；
- 不加引号：会发生 word splitting 和 globbing。

脚本可靠性的大量问题都来自错误引用。

## 5. 命令替换与算术

~~~bash
now=$(date +%F)
count=$((count + 1))
~~~

现代命令替换优先使用 $() 而不是反引号。Bash 整数算术适合计数；高精度或浮点计算应使用其他工具。

## 6. 参数

重要变量：

- $0：脚本名；
- $1...：位置参数；
- $#：参数个数；
- $@：全部参数；
- $?：上一条命令退出码；
- $$：当前 shell PID。

遍历参数时：

~~~bash
for arg in "$@"; do
    printf '%s\n' "$arg"
done
~~~

## 7. getopts

处理短选项时使用 shell builtin getopts，而不是手写大量 shift 判断。复杂 CLI 应使用更合适的语言和参数库。

## 8. 退出状态

Unix 工具通常约定 0 为成功，非 0 为失败或特殊状态。脚本应显式传播失败。

~~~bash
if command; then
    ...
else
    ...
fi
~~~

grep、diff 等工具的非 0 状态有具体语义，不能一概视为程序崩溃。

## 9. 条件判断

~~~bash
if [[ -f "$file" ]]; then
    ...
fi
~~~

常见文件测试：

- -e：存在；
- -f：普通文件；
- -d：目录；
- -r/-w/-x：权限；
- -s：非空。

字符串和数值比较要区分语法。

## 10. case 与循环

~~~bash
case "$action" in
  start) ... ;;
  stop) ... ;;
  *) echo "unknown" >&2; exit 2 ;;
esac
~~~

~~~bash
for item in ...; do
    ...
done

while condition; do
    ...
done
~~~

逐行读取文件时：

~~~bash
while IFS= read -r line; do
    ...
done < "$file"
~~~

这样能更好保留空格和反斜杠。

## 11. 数组

Bash 数组适合安全保存参数列表，避免把多个参数拼成一个字符串再 eval。核心原则是：数组元素应作为独立参数传递，展开时保持参数边界。

## 12. 函数

~~~bash
log() {
    printf '%s %s\n' "$(date -Is)" "$*" >&2
}
~~~

函数参数仍使用 $1、$@ 等。需要局部变量时使用 local，避免函数不必要地修改全局状态。

## 13. set -euo pipefail

~~~bash
set -Eeuo pipefail
~~~

大致含义：

- -e：某些命令失败时退出；
- -u：未定义变量视为错误；
- pipefail：管道中任一命令失败可影响整体状态；
- -E：ERR trap 在更多上下文继承。

但 -e 有复杂语义，不是自动正确的错误处理。仍需显式处理预期失败、条件判断、清理和重试。

## 14. trap 与清理

~~~bash
tmp=$(mktemp)
cleanup() {
    rm -f "$tmp"
}
trap cleanup EXIT
~~~

任何创建临时文件、锁、挂载或中间状态的脚本，都应设计退出清理。

## 15. mktemp

~~~bash
tmpdir=$(mktemp -d)
~~~

不要默认使用可预测的固定临时文件名。系统工具能减少竞争条件和临时文件攻击。

## 16. 重定向与文件描述符

~~~bash
exec 3>report.log
printf '%s\n' "message" >&3
exec 3>&-
~~~

自定义 FD 适合把业务输出和日志分离。

## 17. Here document

~~~bash
cat > config.txt <<'EOF'
literal $VALUE
EOF
~~~

给 delimiter 加引号可以避免变量展开。大量结构化模板建议使用真正模板工具。

## 18. 管道

~~~bash
producer | grep pattern | consumer
~~~

如果只检查最后一个命令，可能掩盖前面失败，因此脚本中常配合 pipefail。

## 19. sed、awk、grep 与 shell 的边界

推荐：

- shell：流程；
- grep：筛选；
- sed：简单替换；
- awk：字段和聚合；
- jq/yq：JSON/YAML；
- Python：复杂逻辑。

不要用一条超长 sed/awk 证明所有事都能用 shell。

## 20. 输入与 Secret

~~~bash
read -r value
read -r -p "Name: " name
read -r -s -p "Password: " password
~~~

隐藏输入不等于 secret 安全。

避免：

- password 写死在脚本；
- token 提交 Git；
- secret 放在命令行参数；
- set -x 时打印 secret；
- 临时文件权限过宽。

优先使用 secret manager、stdin/文件描述符、短期凭证和最小权限文件。

## 21. 日志

脚本日志至少应包含时间、level、操作对象、错误原因和退出码。不要只输出 failed。

系统服务脚本让 stdout/stderr 进入 journald 往往更简单。

## 22. 幂等性

自动化脚本理想状态：

~~~text
运行一次 → 得到目标状态
运行第二次 → 仍是同一目标状态，不破坏系统
~~~

例如：

- mkdir -p；
- 检查配置是否已经存在；
- 比较后再修改；
- 重启前判断是否需要；
- 不重复追加同一行。

## 23. 并发与锁

Cron 任务可能上一轮还没结束下一轮又启动。

~~~bash
flock -n /run/myjob.lock command
~~~

更复杂的分布式任务需要外部锁或调度器。

## 24. 重试

网络任务可以重试，但必须限定次数、设置 timeout、使用 backoff、只重试安全操作，并记录最终失败。无限重试会把局部故障变成系统压力。

## 25. 远程自动化与 expect

旧脚本常使用 expect 自动输入密码。

优先顺序：

~~~text
SSH key / agent
→ API/token
→ 非交互 CLI
→ 配置管理工具
→ expect（只有没有机器接口时）
~~~

expect 仍值得理解，但不应把模拟人工输入作为自动化首选。

## 26. 数据库批处理

Shell 可以调用数据库 CLI，但注意：

- 不在参数中暴露密码；
- SQL 与 shell quoting 分层；
- 检查事务和退出码；
- 大任务使用数据库迁移工具；
- 不用 grep 解析数据库复杂输出。

## 27. 发布脚本的通用结构

dunwu 仓库中的 Java/JS 发布脚本可以抽象为：

~~~text
preflight
→ 检查依赖/用户/目录
→ 获取 artifact
→ 校验版本
→ 解压到新 release 目录
→ 配置
→ 停旧/启动新
→ health check
→ 原子切换 current symlink
→ 保留上一个版本
→ 失败回滚
~~~

比直接覆盖当前目录并重启更可靠。

## 28. ShellCheck 与格式化

长期维护脚本建议使用 ShellCheck 发现 quoting、未使用变量、错误 test 等问题，用 shfmt 统一格式；同时保持小函数、明确退出码、最小副作用并测试危险路径。

## 29. 调试

~~~bash
bash -n script.sh
bash -x script.sh
~~~

也可以局部启用 set -x / set +x。启用 trace 前确认不会泄露 secret。

## 30. Vim 最小生存集

远程服务器编辑配置时至少会：

- i：插入；
- Esc：回普通模式；
- :w：保存；
- :q：退出；
- :wq：保存退出；
- :q!：放弃退出；
- /pattern：搜索；
- n/N：下一个/上一个；
- dd：删除行；
- yy/p：复制/粘贴；
- u：撤销。

进一步可以掌握 0/^/$、w/b/e、ciw、visual mode、宏、split/vsplit。

## 31. Zsh、Fish 与 oh-my-zsh

交互 shell 可以提升体验，但脚本运行环境与交互 shell 要分开：

- 脚本明确 shebang；
- 不依赖个人 alias；
- 不依赖主题插件；
- 自动化不要假设 oh-my-zsh 存在。

## 32. 命令行效率

值得形成肌肉记忆：

- Ctrl+R：历史搜索；
- Tab：补全；
- Ctrl+A/E：行首/行尾；
- Ctrl+U/K：删除；
- history；
- alias 只用于交互；
- function 适合稍复杂交互快捷命令；
- tmux 用于会话持续。

## 33. “命令行艺术”的正确吸收方式

真正可复用的是组合思想：

~~~text
先用最简单命令取得数据
→ 用管道逐层过滤
→ 每一步都能单独检查
→ 最后才加入写入/删除副作用
~~~

这比保存上百条不可理解的 one-liner 更可靠。

## 34. 完成标准

能独立写出一个脚本，做到：

- 参数清晰；
- 变量正确引用；
- 检查依赖；
- 有退出码；
- 有日志；
- 临时文件可清理；
- 失败不留下半成品；
- 可以重复运行；
- secret 不泄漏；
- cron/systemd 环境下仍能运行；
- 通过 ShellCheck；
- 危险操作有 dry-run 或显式确认。
