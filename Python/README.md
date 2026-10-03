# Python 学习笔记

本目录是 Compile N Run Python Tutorial 的中文吸收版。目标不是镜像原站，而是把源站 18 个模块、167 篇正文中仍有长期价值的知识重构成可独立学习、可维护、可继续扩展的 Study 主线。

## 学习基线

- 当前核验基线：Python 3.14 系列；2026-10-03 核验时最新 Python 3 为 3.14.8。
- 示例优先使用现代 Python 3 写法；涉及版本差异时注明最低版本或兼容边界。
- 包管理以 venv、python -m pip、pyproject.toml 为当前主线；requirements.txt 仍可用于环境依赖清单，但不再把 setup.py 作为新项目的首选入口。
- Web、数据库、云部署、第三方库的版本变化快，本目录保留稳定原理与常用接口；实际部署前仍需核对对应官方文档。
- 默认 CPython 与 free-threaded CPython 的并发语义分开说明，避免沿用“Python 线程永远不能并行执行 CPU 任务”的过时绝对表述。

## Core · 18 个主章节

1. [Python 基础、环境与运行模型](./Core/01-Fundamentals.md)
2. [条件、循环与推导式](./Core/02-Control-Flow.md)
3. [函数、参数、装饰器与生成器](./Core/03-Functions.md)
4. [内置数据结构与常用容器](./Core/04-Data-Structures.md)
5. [字符串、正则、文本与 Unicode](./Core/05-Strings.md)
6. [模块、包、虚拟环境与依赖管理](./Core/06-Modules-and-Packages.md)
7. [面向对象编程](./Core/07-OOP.md)
8. [文件、目录、CSV、JSON 与二进制](./Core/08-File-Handling.md)
9. [异常、断言与调试](./Core/09-Exceptions-and-Debugging.md)
10. [迭代器、上下文管理器、描述符与元类](./Core/10-Advanced-Features.md)
11. [函数式编程](./Core/11-Functional-Programming.md)
12. [线程、进程与异步并发](./Core/12-Concurrency.md)
13. [数据库访问与 ORM](./Core/13-Database-Access.md)
14. [Web 开发、HTTP、API 与认证](./Core/14-Web-Development.md)
15. [NumPy、pandas、可视化与统计](./Core/15-Data-Science.md)
16. [测试、TDD、Mock 与覆盖率](./Core/16-Testing.md)
17. [自动化、CLI、日志、配置与部署](./Core/17-DevOps.md)
18. [代码风格、性能、安全、设计模式与重构](./Core/18-Best-Practices.md)

## 推荐学习顺序

第一次学习先完成 01～06，能够独立写脚本、函数和模块；随后学 07～10，建立对象、资源和 Python 数据模型的理解。之后根据目标分支：

- 日常脚本、工具与工程：16 → 17 → 18。
- 数据分析：15，并回看 04、05、06。
- 后端开发：13 → 14 → 16 → 17。
- 高并发 I/O：12 → 14。
- 深入 Python 语言机制：09 → 10 → 11 → 12。

每章建议按“先预测 → 运行示例 → 修改一个条件 → 解释边界”的方式学习。只看完文字不等于掌握。

## 来源与完整性

- 原站：https://www.compilenrun.com/docs/language/python
- 上游源码：https://github.com/Compile-N-Run/Compile-N-Run
- 本轮读取基线 commit：d065f4f52553824687aa1f8f6ae4b7be43ea6533
- 吸收日期：2026-10-03
- 完整性：已核对 docs/language/python 下 18 个模块目录，共 167 篇正文；逐页来源映射见 [Compile N Run Python 来源记录](../来源保全/Compile-N-Run-Python.md)。

上游仓库根目录在本轮核验时未发现 LICENSE 文件，因此 Study 不保存其原文镜像；这里只保留原创中文知识重构、必要短语义对应与来源映射。
## 开发与实验实践

- [开发环境、编辑器与依赖复现](./实践/01-开发环境编辑器与依赖复现.md)：运行位置、内核、锁和兼容性。
- [调试、日志与性能定位](./实践/02-调试日志与性能定位.md)：静默shape错误、日志、profiler与资源边界。

这两篇补充已有Core，不是另一套来源课程；新增来源吸收状态见[五站进度](../维护/五站吸收/进度与续接.md)。
