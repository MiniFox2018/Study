# 17 · 自动化、CLI、日志、配置与部署

## 1. 自动化脚本的工程边界

Python 很适合批量文件、数据转换、API 调用、巡检和运维任务。脚本一旦进入长期运行，就应从“一次性代码”升级为：

- 参数化；
- 幂等；
- 可观察；
- 有超时；
- 有明确退出码；
- 有 dry-run 或安全边界；
- 可测试；
- 配置与代码分离。

## 2. 文件自动化

~~~python
from pathlib import Path
import shutil

def archive_logs(source: Path, target: Path) -> int:
    target.mkdir(parents=True, exist_ok=True)
    count = 0

    for path in source.glob("*.log"):
        shutil.copy2(path, target / path.name)
        count += 1

    return count
~~~

删除、覆盖、递归移动前验证路径。批处理尽量先打印计划，再允许执行。

## 3. argparse

标准库适合大多数 CLI：

~~~python
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("input")
parser.add_argument("--limit", type=int, default=100)
parser.add_argument("--dry-run", action="store_true")
args = parser.parse_args()
~~~

CLI 应提供：

- --help；
- 合理默认值；
- 类型/范围检查；
- 清楚错误信息；
- 退出码；
- stdout/stderr 分工。

## 4. Click 与 Typer

Click 提供 decorator 风格命令、子命令和参数系统；Typer 基于类型提示构建 CLI。它们适合命令较多、体验要求较高的工具。

第三方库 API 变化快，本章不固定某个版本写法；项目采用后以官方文档为准。

## 5. 可安装 CLI

在 pyproject.toml 声明 console script，让用户安装后直接运行命令，而不是要求记住 python path/to/script.py。

示意：

~~~toml
[project.scripts]
study-tool = "study_tool.cli:main"
~~~

## 6. 环境变量

读取：

~~~python
import os

database_url = os.environ["DATABASE_URL"]
debug = os.getenv("DEBUG", "false").lower() == "true"
~~~

环境变量是配置传递机制，不是秘密保险箱。它们可能出现在进程、崩溃转储、CI 日志或错误输出中。

密钥应由 secret manager / CI secret / 平台凭据系统管理，并在应用中最小暴露。

## 7. .env

本地开发可用 python-dotenv 加载 .env，但：

- .env 不提交 Git；
- 提供 .env.example 只列名称和假值；
- 生产环境不要依赖开发者本地 .env 文件；
- 泄露过的 secret 必须轮换，而不是只删文件。

## 8. 配置文件

常见格式：

- TOML；
- INI；
- JSON；
- YAML。

Python 配置也可写代码，但会增加执行副作用和安全风险。

使用 YAML 时只加载数据，避免不可信输入触发任意对象构造；选用安全加载 API。

配置优先级要明确，例如：

~~~text
defaults
< config file
< environment
< CLI args
~~~

避免同一配置在五个地方都能覆盖却没人知道最终值来自哪里。

## 9. logging

库代码：

~~~python
import logging
logger = logging.getLogger(__name__)
~~~

应用入口统一配置 handler/formatter/level。

重要字段：

- timestamp；
- level；
- logger/module；
- request/job id；
- operation；
- duration；
- outcome。

生产日志应结构化并可关联，但不要记录密码、token、完整 cookie、私钥和不必要个人数据。

## 10. Rotating logs

本地文件日志可用 RotatingFileHandler 或 TimedRotatingFileHandler。容器环境通常更适合写 stdout/stderr 交给平台收集，不要在容器内部维护无人读取的长期日志文件。

## 11. 异常与堆栈

~~~python
try:
    run_job()
except Exception:
    logger.exception("job failed")
    raise
~~~

记录后是否重抛取决于任务模型。CLI 通常应返回非零退出码；后台 worker 可能由任务框架处理重试。

## 12. Docker

容器化 Python 应用的关键不是“写一个 Dockerfile”，而是构建可重复、最小权限、可缓存的镜像。

示意：

~~~dockerfile
FROM python:3.14-slim

WORKDIR /app
COPY pyproject.toml .
COPY src/ src/

RUN python -m pip install --no-cache-dir .

USER 10001
CMD ["python", "-m", "myapp"]
~~~

真实镜像要按项目构建后端、依赖和系统库调整。

### 关于 Alpine

源站把 Alpine 作为“更小镜像”的普遍最佳实践，这不应作为默认结论。许多 Python 包依赖 native wheel / glibc 生态，Alpine 的 musl 可能导致额外编译、兼容和镜像构建成本。**slim 与 Alpine 应按依赖实测选择。**

## 13. Multi-stage build

需要编译 C 扩展或前端资源时，可以在 builder stage 安装编译工具，再把最终运行产物复制到更小运行镜像，减少攻击面和体积。

## 14. Docker Compose

适合本地组合应用 + database + cache 等服务。生产部署是否使用 Compose 取决于平台，不要把本地编排文件直接等同生产架构。

## 15. CI

典型流水线：

~~~text
checkout
→ install
→ lint / type check
→ unit tests
→ integration tests
→ build artifact/image
→ security checks
→ deploy
→ smoke check
~~~

每一步失败都应阻断后续不安全发布。

## 16. CI 的依赖与缓存

缓存能加速，但必须以 lock/依赖文件 hash 为 key，避免复用错误环境。CI 应从干净环境安装，不能依赖开发者机器残留包。

矩阵测试适合库项目验证多个受支持 Python 版本；应用项目至少测试生产实际版本。

## 17. Secrets in CI/CD

使用平台 Secrets，不把密钥写进 workflow YAML、Dockerfile、日志或仓库。

云平台优先短期身份（OIDC / workload identity）而不是长期 access key。

## 18. 部署模型

常见：

- PaaS；
- VM/IaaS；
- containers；
- serverless。

选择看：

- 启动时间；
- 长连接；
- CPU/内存；
- 扩缩容；
- 网络；
- 数据库；
- 状态；
- 成本；
- 运维能力。

源站列举 Heroku、AWS、GCP、Azure 的具体命令，这类 UI/CLI/平台步骤高时效，本仓库不固化 2026 可能继续变化的操作手册。真正部署时查对应平台官方文档。

## 19. 云部署前的应用要求

至少做到：

- 配置来自环境/secret；
- 日志到 stdout 或平台规范；
- 健康检查；
- 优雅关闭；
- 请求/任务 timeout；
- 数据库连接池；
- migration 有独立流程；
- 无本地持久磁盘假设；
- 静态/用户上传对象明确存储策略；
- 可重复 build；
- rollback 方案。

## 20. 调度

重要定时任务要设计：

- 时区；
- 重复执行幂等；
- missed run；
- 并发锁；
- 重试；
- 运行超时；
- 告警；
- 历史记录。

应用内 schedule 库适合简单情况；关键生产任务优先交给具备持久化与监控的系统调度/任务平台。

## 21. 常见错误

- 自动化脚本无 dry-run 就递归删除；
- 配置和 secret 混在源码；
- logger 到处重复添加 handler；
- Docker 镜像使用 root 且带编译工具；
- 盲目认为 Alpine 一定更好；
- CI 只跑 lint 不跑测试；
- migration 与应用发布无兼容策略；
- 云平台教程命令复制多年不核验；
- 定时任务没有幂等设计。

## 22. 练习与答案

**练习 1**：环境变量是否等于安全 secret storage？  
**答案**：不是。它只是注入方式；secret 的生成、保存、授权、轮换仍应由专门系统负责。

**练习 2**：为什么 Dockerfile 不建议默认 Alpine？  
**答案**：体积可能更小，但 Python native 依赖常在 manylinux/glibc 生态更顺畅，应比较构建复杂度、运行兼容和最终体积。

**练习 3**：为什么定时任务必须幂等？  
**答案**：实际调度可能重试、重复触发或故障恢复；同一任务重复执行不应造成重复扣款、重复通知等破坏。
