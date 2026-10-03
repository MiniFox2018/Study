# Compile N Run Python 来源记录与覆盖核验

## 来源

- 网站：https://www.compilenrun.com/docs/language/python
- 上游源码：https://github.com/Compile-N-Run/Compile-N-Run
- 本轮固定读取 commit：https://github.com/Compile-N-Run/Compile-N-Run/commit/d065f4f52553824687aa1f8f6ae4b7be43ea6533
- 源码目录：https://github.com/Compile-N-Run/Compile-N-Run/tree/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python
- 吸收日期：2026-10-03
- Study 落点：[Python/README.md](../Python/README.md)

## 完整性结论

本轮按上游源码目录而不是网页搜索结果建立完整性基线。docs/language/python 下共有 18 个一级模块目录；每个模块另有 1 个 index.mdx 和 1 个 _category_.json 用于导航/分类，因此结构文件共 36 个。排除这 36 个结构文件后，**正文共 167 篇**，已全部读取并在下方逐篇映射到 Study 的 18 个中文主章节。

这里的“吸收完整”按 Study 规则指：正文知识、关键边界、代码思路、练习价值与章节关系足以在 Study 内独立学习；不复制原网站的英文页面、营销文案、重复例子和高时效旧操作步骤。

## 许可与保存方式

2026-10-03 核验上游仓库根目录，未发现 LICENSE 文件。基于这一边界，本仓库不镜像、不批量翻译保存其原文，也不复制整套上游代码；采用原创中文知识重构 + 精确来源映射。若上游后续补充许可证，应再按新许可更新记录。

## 时效审查与主动替换

以下内容没有机械照搬，而按 2026-10-03 当前生态修订：

- Python 版本：以 Python 3.14 系列为当前基线；Python 2 仅作为历史差异，不进入学习主线。
- 控制流：补充源站缺少的 match/case，标明 Python 3.10+。
- 类型：补充 type hints 的真实边界——默认不做运行时强制。
- 打包：不再把 setup.py 作为新项目首选；主线改为 pyproject.toml + venv + python -m pip，并保留 requirements.txt 的正确用途。
- 文件：pathlib、with、UTF-8 作为主线；pickle 明确禁止加载不可信数据。
- 并发：不保留“Python 线程永远不能 CPU 并行”的绝对说法；区分默认 CPython GIL、进程池、asyncio 与 Python 3.14 free-threaded 构建；补 TaskGroup。
- 数据库：SQLAlchemy 保留稳定 ORM/事务思想，示例口径更新为现代 Session/select；所有 SQL 强调参数化。
- Web：不把易过时的 Flask/Django/FastAPI/云平台具体版本命令固化成长期操作手册；认证部分不使用普通快速哈希保存密码。
- 抓取：加入站点规则、限速、timeout、解析器与动态页面边界。
- 数据科学：补缺失值语义、合并基数、数据泄漏、相关不等于因果等实际分析边界。
- Docker：删除“Alpine 一定更小所以优先”的绝对建议，改为按 native dependency、musl/glibc 和最终镜像实测选择。
- 安全：强化 SQL/shell 注入、不可信 pickle、secret/log、上传与解压路径边界。

## 逐页映射

## 基础、环境与运行模型（15 篇）

1. [0-python-introduction.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/0-python-fundamentals/0-python-introduction.mdx) → [Python/Core/01-Fundamentals.md](../Python/Core/01-Fundamentals.md)
2. [1-python-environment-setup.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/0-python-fundamentals/1-python-environment-setup.mdx) → [Python/Core/01-Fundamentals.md](../Python/Core/01-Fundamentals.md)
3. [2-python-first-program.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/0-python-fundamentals/2-python-first-program.mdx) → [Python/Core/01-Fundamentals.md](../Python/Core/01-Fundamentals.md)
4. [3-python-syntax.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/0-python-fundamentals/3-python-syntax.mdx) → [Python/Core/01-Fundamentals.md](../Python/Core/01-Fundamentals.md)
5. [4-python-comments.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/0-python-fundamentals/4-python-comments.mdx) → [Python/Core/01-Fundamentals.md](../Python/Core/01-Fundamentals.md)
6. [5-python-variables.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/0-python-fundamentals/5-python-variables.mdx) → [Python/Core/01-Fundamentals.md](../Python/Core/01-Fundamentals.md)
7. [6-python-data-types.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/0-python-fundamentals/6-python-data-types.mdx) → [Python/Core/01-Fundamentals.md](../Python/Core/01-Fundamentals.md)
8. [7-python-numbers.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/0-python-fundamentals/7-python-numbers.mdx) → [Python/Core/01-Fundamentals.md](../Python/Core/01-Fundamentals.md)
9. [8-python-strings.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/0-python-fundamentals/8-python-strings.mdx) → [Python/Core/01-Fundamentals.md](../Python/Core/01-Fundamentals.md)
10. [9-python-booleans.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/0-python-fundamentals/9-python-booleans.mdx) → [Python/Core/01-Fundamentals.md](../Python/Core/01-Fundamentals.md)
11. [10-python-operators.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/0-python-fundamentals/10-python-operators.mdx) → [Python/Core/01-Fundamentals.md](../Python/Core/01-Fundamentals.md)
12. [11-python-input-output.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/0-python-fundamentals/11-python-input-output.mdx) → [Python/Core/01-Fundamentals.md](../Python/Core/01-Fundamentals.md)
13. [12-python-type-conversion.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/0-python-fundamentals/12-python-type-conversion.mdx) → [Python/Core/01-Fundamentals.md](../Python/Core/01-Fundamentals.md)
14. [13-python-scope.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/0-python-fundamentals/13-python-scope.mdx) → [Python/Core/01-Fundamentals.md](../Python/Core/01-Fundamentals.md)
15. [14-python-interpreter-and-repl.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/0-python-fundamentals/14-python-interpreter-and-repl.mdx) → [Python/Core/01-Fundamentals.md](../Python/Core/01-Fundamentals.md)

## 条件、循环与推导式（10 篇）

1. [0-python-conditional-statements.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/1-python-control-flow/0-python-conditional-statements.mdx) → [Python/Core/02-Control-Flow.md](../Python/Core/02-Control-Flow.md)
2. [1-python-if-else.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/1-python-control-flow/1-python-if-else.mdx) → [Python/Core/02-Control-Flow.md](../Python/Core/02-Control-Flow.md)
3. [2-python-elif-statement.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/1-python-control-flow/2-python-elif-statement.mdx) → [Python/Core/02-Control-Flow.md](../Python/Core/02-Control-Flow.md)
4. [3-python-nested-if.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/1-python-control-flow/3-python-nested-if.mdx) → [Python/Core/02-Control-Flow.md](../Python/Core/02-Control-Flow.md)
5. [4-python-loops.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/1-python-control-flow/4-python-loops.mdx) → [Python/Core/02-Control-Flow.md](../Python/Core/02-Control-Flow.md)
6. [5-python-for-loop.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/1-python-control-flow/5-python-for-loop.mdx) → [Python/Core/02-Control-Flow.md](../Python/Core/02-Control-Flow.md)
7. [6-python-while-loop.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/1-python-control-flow/6-python-while-loop.mdx) → [Python/Core/02-Control-Flow.md](../Python/Core/02-Control-Flow.md)
8. [7-python-break-continue.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/1-python-control-flow/7-python-break-continue.mdx) → [Python/Core/02-Control-Flow.md](../Python/Core/02-Control-Flow.md)
9. [8-python-pass-statement.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/1-python-control-flow/8-python-pass-statement.mdx) → [Python/Core/02-Control-Flow.md](../Python/Core/02-Control-Flow.md)
10. [9-python-comprehensions.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/1-python-control-flow/9-python-comprehensions.mdx) → [Python/Core/02-Control-Flow.md](../Python/Core/02-Control-Flow.md)

## 函数、参数、装饰器与生成器（9 篇）

1. [0-python-functions-basics.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/2-python-functions/0-python-functions-basics.mdx) → [Python/Core/03-Functions.md](../Python/Core/03-Functions.md)
2. [1-python-function-parameters.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/2-python-functions/1-python-function-parameters.mdx) → [Python/Core/03-Functions.md](../Python/Core/03-Functions.md)
3. [2-python-function-arguments.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/2-python-functions/2-python-function-arguments.mdx) → [Python/Core/03-Functions.md](../Python/Core/03-Functions.md)
4. [3-python-return-values.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/2-python-functions/3-python-return-values.mdx) → [Python/Core/03-Functions.md](../Python/Core/03-Functions.md)
5. [4-python-lambda-functions.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/2-python-functions/4-python-lambda-functions.mdx) → [Python/Core/03-Functions.md](../Python/Core/03-Functions.md)
6. [5-python-recursion.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/2-python-functions/5-python-recursion.mdx) → [Python/Core/03-Functions.md](../Python/Core/03-Functions.md)
7. [6-python-decorators.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/2-python-functions/6-python-decorators.mdx) → [Python/Core/03-Functions.md](../Python/Core/03-Functions.md)
8. [7-python-generators.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/2-python-functions/7-python-generators.mdx) → [Python/Core/03-Functions.md](../Python/Core/03-Functions.md)
9. [8-python-yield-statement.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/2-python-functions/8-python-yield-statement.mdx) → [Python/Core/03-Functions.md](../Python/Core/03-Functions.md)

## 内置数据结构与常用容器（10 篇）

1. [0-python-lists.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/3-python-data-structures/0-python-lists.mdx) → [Python/Core/04-Data-Structures.md](../Python/Core/04-Data-Structures.md)
2. [1-python-list-methods.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/3-python-data-structures/1-python-list-methods.mdx) → [Python/Core/04-Data-Structures.md](../Python/Core/04-Data-Structures.md)
3. [2-python-tuples.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/3-python-data-structures/2-python-tuples.mdx) → [Python/Core/04-Data-Structures.md](../Python/Core/04-Data-Structures.md)
4. [3-python-sets.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/3-python-data-structures/3-python-sets.mdx) → [Python/Core/04-Data-Structures.md](../Python/Core/04-Data-Structures.md)
5. [4-python-dictionaries.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/3-python-data-structures/4-python-dictionaries.mdx) → [Python/Core/04-Data-Structures.md](../Python/Core/04-Data-Structures.md)
6. [5-python-dictionary-methods.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/3-python-data-structures/5-python-dictionary-methods.mdx) → [Python/Core/04-Data-Structures.md](../Python/Core/04-Data-Structures.md)
7. [6-python-arrays.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/3-python-data-structures/6-python-arrays.mdx) → [Python/Core/04-Data-Structures.md](../Python/Core/04-Data-Structures.md)
8. [7-python-collections-module.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/3-python-data-structures/7-python-collections-module.mdx) → [Python/Core/04-Data-Structures.md](../Python/Core/04-Data-Structures.md)
9. [8-python-stacks-queues.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/3-python-data-structures/8-python-stacks-queues.mdx) → [Python/Core/04-Data-Structures.md](../Python/Core/04-Data-Structures.md)
10. [9-python-linked-lists.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/3-python-data-structures/9-python-linked-lists.mdx) → [Python/Core/04-Data-Structures.md](../Python/Core/04-Data-Structures.md)

## 字符串、正则、文本与 Unicode（7 篇）

1. [0-python-string-operations.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/4-python-strings/0-python-string-operations.mdx) → [Python/Core/05-Strings.md](../Python/Core/05-Strings.md)
2. [1-python-string-methods.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/4-python-strings/1-python-string-methods.mdx) → [Python/Core/05-Strings.md](../Python/Core/05-Strings.md)
3. [2-python-string-formatting.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/4-python-strings/2-python-string-formatting.mdx) → [Python/Core/05-Strings.md](../Python/Core/05-Strings.md)
4. [3-python-string-templates.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/4-python-strings/3-python-string-templates.mdx) → [Python/Core/05-Strings.md](../Python/Core/05-Strings.md)
5. [4-python-regular-expressions.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/4-python-strings/4-python-regular-expressions.mdx) → [Python/Core/05-Strings.md](../Python/Core/05-Strings.md)
6. [5-python-text-processing.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/4-python-strings/5-python-text-processing.mdx) → [Python/Core/05-Strings.md](../Python/Core/05-Strings.md)
7. [6-python-unicode-handling.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/4-python-strings/6-python-unicode-handling.mdx) → [Python/Core/05-Strings.md](../Python/Core/05-Strings.md)

## 模块、包、虚拟环境与依赖管理（8 篇）

1. [0-python-modules-basics.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/5-python-modules-and-packages/0-python-modules-basics.mdx) → [Python/Core/06-Modules-and-Packages.md](../Python/Core/06-Modules-and-Packages.md)
2. [1-python-creating-modules.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/5-python-modules-and-packages/1-python-creating-modules.mdx) → [Python/Core/06-Modules-and-Packages.md](../Python/Core/06-Modules-and-Packages.md)
3. [2-python-importing-modules.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/5-python-modules-and-packages/2-python-importing-modules.mdx) → [Python/Core/06-Modules-and-Packages.md](../Python/Core/06-Modules-and-Packages.md)
4. [3-python-packages.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/5-python-modules-and-packages/3-python-packages.mdx) → [Python/Core/06-Modules-and-Packages.md](../Python/Core/06-Modules-and-Packages.md)
5. [4-python-standard-libraries.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/5-python-modules-and-packages/4-python-standard-libraries.mdx) → [Python/Core/06-Modules-and-Packages.md](../Python/Core/06-Modules-and-Packages.md)
6. [5-python-virtual-environments.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/5-python-modules-and-packages/5-python-virtual-environments.mdx) → [Python/Core/06-Modules-and-Packages.md](../Python/Core/06-Modules-and-Packages.md)
7. [6-python-pip-package-manager.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/5-python-modules-and-packages/6-python-pip-package-manager.mdx) → [Python/Core/06-Modules-and-Packages.md](../Python/Core/06-Modules-and-Packages.md)
8. [7-python-requirements-file.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/5-python-modules-and-packages/7-python-requirements-file.mdx) → [Python/Core/06-Modules-and-Packages.md](../Python/Core/06-Modules-and-Packages.md)

## 面向对象编程（13 篇）

1. [0-python-classes-objects.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/6-python-object-oriented-programming/0-python-classes-objects.mdx) → [Python/Core/07-OOP.md](../Python/Core/07-OOP.md)
2. [1-python-constructors.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/6-python-object-oriented-programming/1-python-constructors.mdx) → [Python/Core/07-OOP.md](../Python/Core/07-OOP.md)
3. [2-python-inheritance.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/6-python-object-oriented-programming/2-python-inheritance.mdx) → [Python/Core/07-OOP.md](../Python/Core/07-OOP.md)
4. [3-python-encapsulation.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/6-python-object-oriented-programming/3-python-encapsulation.mdx) → [Python/Core/07-OOP.md](../Python/Core/07-OOP.md)
5. [4-python-polymorphism.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/6-python-object-oriented-programming/4-python-polymorphism.mdx) → [Python/Core/07-OOP.md](../Python/Core/07-OOP.md)
6. [5-python-method-overriding.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/6-python-object-oriented-programming/5-python-method-overriding.mdx) → [Python/Core/07-OOP.md](../Python/Core/07-OOP.md)
7. [6-python-abstract-classes.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/6-python-object-oriented-programming/6-python-abstract-classes.mdx) → [Python/Core/07-OOP.md](../Python/Core/07-OOP.md)
8. [7-python-interfaces.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/6-python-object-oriented-programming/7-python-interfaces.mdx) → [Python/Core/07-OOP.md](../Python/Core/07-OOP.md)
9. [8-python-multiple-inheritance.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/6-python-object-oriented-programming/8-python-multiple-inheritance.mdx) → [Python/Core/07-OOP.md](../Python/Core/07-OOP.md)
10. [9-python-property-decorators.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/6-python-object-oriented-programming/9-python-property-decorators.mdx) → [Python/Core/07-OOP.md](../Python/Core/07-OOP.md)
11. [10-python-magic-methods.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/6-python-object-oriented-programming/10-python-magic-methods.mdx) → [Python/Core/07-OOP.md](../Python/Core/07-OOP.md)
12. [11-python-static-methods.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/6-python-object-oriented-programming/11-python-static-methods.mdx) → [Python/Core/07-OOP.md](../Python/Core/07-OOP.md)
13. [12-python-class-methods.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/6-python-object-oriented-programming/12-python-class-methods.mdx) → [Python/Core/07-OOP.md](../Python/Core/07-OOP.md)

## 文件、目录、CSV、JSON 与二进制（10 篇）

1. [0-python-file-operations.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/7-python-file-handling/0-python-file-operations.mdx) → [Python/Core/08-File-Handling.md](../Python/Core/08-File-Handling.md)
2. [1-python-reading-files.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/7-python-file-handling/1-python-reading-files.mdx) → [Python/Core/08-File-Handling.md](../Python/Core/08-File-Handling.md)
3. [2-python-writing-files.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/7-python-file-handling/2-python-writing-files.mdx) → [Python/Core/08-File-Handling.md](../Python/Core/08-File-Handling.md)
4. [3-python-appending-files.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/7-python-file-handling/3-python-appending-files.mdx) → [Python/Core/08-File-Handling.md](../Python/Core/08-File-Handling.md)
5. [4-python-working-directories.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/7-python-file-handling/4-python-working-directories.mdx) → [Python/Core/08-File-Handling.md](../Python/Core/08-File-Handling.md)
6. [5-python-file-management.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/7-python-file-handling/5-python-file-management.mdx) → [Python/Core/08-File-Handling.md](../Python/Core/08-File-Handling.md)
7. [6-python-csv-files.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/7-python-file-handling/6-python-csv-files.mdx) → [Python/Core/08-File-Handling.md](../Python/Core/08-File-Handling.md)
8. [7-python-json-files.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/7-python-file-handling/7-python-json-files.mdx) → [Python/Core/08-File-Handling.md](../Python/Core/08-File-Handling.md)
9. [8-python-pickle-serialization.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/7-python-file-handling/8-python-pickle-serialization.mdx) → [Python/Core/08-File-Handling.md](../Python/Core/08-File-Handling.md)
10. [9-python-binary-files.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/7-python-file-handling/9-python-binary-files.mdx) → [Python/Core/08-File-Handling.md](../Python/Core/08-File-Handling.md)

## 异常、断言与调试（7 篇）

1. [0-python-try-except.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/8-python-exception-handling/0-python-try-except.mdx) → [Python/Core/09-Exceptions-and-Debugging.md](../Python/Core/09-Exceptions-and-Debugging.md)
2. [1-python-multiple-exceptions.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/8-python-exception-handling/1-python-multiple-exceptions.mdx) → [Python/Core/09-Exceptions-and-Debugging.md](../Python/Core/09-Exceptions-and-Debugging.md)
3. [2-python-else-finally.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/8-python-exception-handling/2-python-else-finally.mdx) → [Python/Core/09-Exceptions-and-Debugging.md](../Python/Core/09-Exceptions-and-Debugging.md)
4. [3-python-raise-exception.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/8-python-exception-handling/3-python-raise-exception.mdx) → [Python/Core/09-Exceptions-and-Debugging.md](../Python/Core/09-Exceptions-and-Debugging.md)
5. [4-python-custom-exceptions.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/8-python-exception-handling/4-python-custom-exceptions.mdx) → [Python/Core/09-Exceptions-and-Debugging.md](../Python/Core/09-Exceptions-and-Debugging.md)
6. [5-python-assertion.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/8-python-exception-handling/5-python-assertion.mdx) → [Python/Core/09-Exceptions-and-Debugging.md](../Python/Core/09-Exceptions-and-Debugging.md)
7. [6-python-debugging-techniques.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/8-python-exception-handling/6-python-debugging-techniques.mdx) → [Python/Core/09-Exceptions-and-Debugging.md](../Python/Core/09-Exceptions-and-Debugging.md)

## 迭代器、上下文管理器、描述符与元类（12 篇）

1. [0-python-iterators.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/9-python-advanced-features/0-python-iterators.mdx) → [Python/Core/10-Advanced-Features.md](../Python/Core/10-Advanced-Features.md)
2. [1-python-list-comprehension.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/9-python-advanced-features/1-python-list-comprehension.mdx) → [Python/Core/10-Advanced-Features.md](../Python/Core/10-Advanced-Features.md)
3. [2-python-dictionary-comprehension.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/9-python-advanced-features/2-python-dictionary-comprehension.mdx) → [Python/Core/10-Advanced-Features.md](../Python/Core/10-Advanced-Features.md)
4. [3-python-set-comprehension.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/9-python-advanced-features/3-python-set-comprehension.mdx) → [Python/Core/10-Advanced-Features.md](../Python/Core/10-Advanced-Features.md)
5. [4-python-map-function.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/9-python-advanced-features/4-python-map-function.mdx) → [Python/Core/10-Advanced-Features.md](../Python/Core/10-Advanced-Features.md)
6. [5-python-filter-function.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/9-python-advanced-features/5-python-filter-function.mdx) → [Python/Core/10-Advanced-Features.md](../Python/Core/10-Advanced-Features.md)
7. [6-python-reduce-function.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/9-python-advanced-features/6-python-reduce-function.mdx) → [Python/Core/10-Advanced-Features.md](../Python/Core/10-Advanced-Features.md)
8. [7-python-closures.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/9-python-advanced-features/7-python-closures.mdx) → [Python/Core/10-Advanced-Features.md](../Python/Core/10-Advanced-Features.md)
9. [8-python-decorators-advanced.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/9-python-advanced-features/8-python-decorators-advanced.mdx) → [Python/Core/10-Advanced-Features.md](../Python/Core/10-Advanced-Features.md)
10. [9-python-context-managers.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/9-python-advanced-features/9-python-context-managers.mdx) → [Python/Core/10-Advanced-Features.md](../Python/Core/10-Advanced-Features.md)
11. [10-python-descriptors.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/9-python-advanced-features/10-python-descriptors.mdx) → [Python/Core/10-Advanced-Features.md](../Python/Core/10-Advanced-Features.md)
12. [11-python-metaclasses.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/9-python-advanced-features/11-python-metaclasses.mdx) → [Python/Core/10-Advanced-Features.md](../Python/Core/10-Advanced-Features.md)

## 函数式编程（7 篇）

1. [0-python-first-class-functions.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/10-python-functional-programming/0-python-first-class-functions.mdx) → [Python/Core/11-Functional-Programming.md](../Python/Core/11-Functional-Programming.md)
2. [1-python-higher-order-functions.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/10-python-functional-programming/1-python-higher-order-functions.mdx) → [Python/Core/11-Functional-Programming.md](../Python/Core/11-Functional-Programming.md)
3. [2-python-pure-functions.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/10-python-functional-programming/2-python-pure-functions.mdx) → [Python/Core/11-Functional-Programming.md](../Python/Core/11-Functional-Programming.md)
4. [3-python-function-composition.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/10-python-functional-programming/3-python-function-composition.mdx) → [Python/Core/11-Functional-Programming.md](../Python/Core/11-Functional-Programming.md)
5. [4-python-partial-functions.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/10-python-functional-programming/4-python-partial-functions.mdx) → [Python/Core/11-Functional-Programming.md](../Python/Core/11-Functional-Programming.md)
6. [5-python-immutable-data.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/10-python-functional-programming/5-python-immutable-data.mdx) → [Python/Core/11-Functional-Programming.md](../Python/Core/11-Functional-Programming.md)
7. [6-python-functional-tools.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/10-python-functional-programming/6-python-functional-tools.mdx) → [Python/Core/11-Functional-Programming.md](../Python/Core/11-Functional-Programming.md)

## 线程、进程与异步并发（8 篇）

1. [0-python-threading-basics.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/11-python-concurrency/0-python-threading-basics.mdx) → [Python/Core/12-Concurrency.md](../Python/Core/12-Concurrency.md)
2. [1-python-thread-synchronization.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/11-python-concurrency/1-python-thread-synchronization.mdx) → [Python/Core/12-Concurrency.md](../Python/Core/12-Concurrency.md)
3. [2-python-multiprocessing.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/11-python-concurrency/2-python-multiprocessing.mdx) → [Python/Core/12-Concurrency.md](../Python/Core/12-Concurrency.md)
4. [3-python-locks-semaphores.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/11-python-concurrency/3-python-locks-semaphores.mdx) → [Python/Core/12-Concurrency.md](../Python/Core/12-Concurrency.md)
5. [4-python-async-io-basics.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/11-python-concurrency/4-python-async-io-basics.mdx) → [Python/Core/12-Concurrency.md](../Python/Core/12-Concurrency.md)
6. [5-python-coroutines.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/11-python-concurrency/5-python-coroutines.mdx) → [Python/Core/12-Concurrency.md](../Python/Core/12-Concurrency.md)
7. [6-python-task-scheduling.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/11-python-concurrency/6-python-task-scheduling.mdx) → [Python/Core/12-Concurrency.md](../Python/Core/12-Concurrency.md)
8. [7-python-concurrent-futures.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/11-python-concurrency/7-python-concurrent-futures.mdx) → [Python/Core/12-Concurrency.md](../Python/Core/12-Concurrency.md)

## 数据库访问与 ORM（8 篇）

1. [0-python-database-basics.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/12-python-database-access/0-python-database-basics.mdx) → [Python/Core/13-Database-Access.md](../Python/Core/13-Database-Access.md)
2. [1-python-sqlite.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/12-python-database-access/1-python-sqlite.mdx) → [Python/Core/13-Database-Access.md](../Python/Core/13-Database-Access.md)
3. [2-python-mysql-connection.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/12-python-database-access/2-python-mysql-connection.mdx) → [Python/Core/13-Database-Access.md](../Python/Core/13-Database-Access.md)
4. [3-python-postgresql.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/12-python-database-access/3-python-postgresql.mdx) → [Python/Core/13-Database-Access.md](../Python/Core/13-Database-Access.md)
5. [4-python-mongodb.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/12-python-database-access/4-python-mongodb.mdx) → [Python/Core/13-Database-Access.md](../Python/Core/13-Database-Access.md)
6. [5-python-orm-basics.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/12-python-database-access/5-python-orm-basics.mdx) → [Python/Core/13-Database-Access.md](../Python/Core/13-Database-Access.md)
7. [6-python-sqlalchemy.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/12-python-database-access/6-python-sqlalchemy.mdx) → [Python/Core/13-Database-Access.md](../Python/Core/13-Database-Access.md)
8. [7-python-database-migrations.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/12-python-database-access/7-python-database-migrations.mdx) → [Python/Core/13-Database-Access.md](../Python/Core/13-Database-Access.md)

## Web 开发、HTTP、API 与认证（9 篇）

1. [0-python-web-concepts.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/13-python-web-development/0-python-web-concepts.mdx) → [Python/Core/14-Web-Development.md](../Python/Core/14-Web-Development.md)
2. [1-python-flask-basics.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/13-python-web-development/1-python-flask-basics.mdx) → [Python/Core/14-Web-Development.md](../Python/Core/14-Web-Development.md)
3. [2-python-django-basics.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/13-python-web-development/2-python-django-basics.mdx) → [Python/Core/14-Web-Development.md](../Python/Core/14-Web-Development.md)
4. [3-python-fastapi-basics.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/13-python-web-development/3-python-fastapi-basics.mdx) → [Python/Core/14-Web-Development.md](../Python/Core/14-Web-Development.md)
5. [4-python-restful-apis.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/13-python-web-development/4-python-restful-apis.mdx) → [Python/Core/14-Web-Development.md](../Python/Core/14-Web-Development.md)
6. [5-python-web-scraping.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/13-python-web-development/5-python-web-scraping.mdx) → [Python/Core/14-Web-Development.md](../Python/Core/14-Web-Development.md)
7. [6-python-http-requests.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/13-python-web-development/6-python-http-requests.mdx) → [Python/Core/14-Web-Development.md](../Python/Core/14-Web-Development.md)
8. [7-python-web-authentication.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/13-python-web-development/7-python-web-authentication.mdx) → [Python/Core/14-Web-Development.md](../Python/Core/14-Web-Development.md)
9. [8-python-templating.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/13-python-web-development/8-python-templating.mdx) → [Python/Core/14-Web-Development.md](../Python/Core/14-Web-Development.md)

## NumPy、pandas、可视化与统计（8 篇）

1. [0-python-numpy-basics.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/14-python-data-science/0-python-numpy-basics.mdx) → [Python/Core/15-Data-Science.md](../Python/Core/15-Data-Science.md)
2. [1-python-pandas-basics.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/14-python-data-science/1-python-pandas-basics.mdx) → [Python/Core/15-Data-Science.md](../Python/Core/15-Data-Science.md)
3. [2-python-data-analysis.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/14-python-data-science/2-python-data-analysis.mdx) → [Python/Core/15-Data-Science.md](../Python/Core/15-Data-Science.md)
4. [3-python-data-visualization.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/14-python-data-science/3-python-data-visualization.mdx) → [Python/Core/15-Data-Science.md](../Python/Core/15-Data-Science.md)
5. [4-python-matplotlib.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/14-python-data-science/4-python-matplotlib.mdx) → [Python/Core/15-Data-Science.md](../Python/Core/15-Data-Science.md)
6. [5-python-seaborn.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/14-python-data-science/5-python-seaborn.mdx) → [Python/Core/15-Data-Science.md](../Python/Core/15-Data-Science.md)
7. [6-python-data-cleaning.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/14-python-data-science/6-python-data-cleaning.mdx) → [Python/Core/15-Data-Science.md](../Python/Core/15-Data-Science.md)
8. [7-python-statistics-basics.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/14-python-data-science/7-python-statistics-basics.mdx) → [Python/Core/15-Data-Science.md](../Python/Core/15-Data-Science.md)

## 测试、TDD、Mock 与覆盖率（8 篇）

1. [0-python-testing-basics.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/15-python-testing/0-python-testing-basics.mdx) → [Python/Core/16-Testing.md](../Python/Core/16-Testing.md)
2. [1-python-unit-testing.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/15-python-testing/1-python-unit-testing.mdx) → [Python/Core/16-Testing.md](../Python/Core/16-Testing.md)
3. [2-python-pytest-framework.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/15-python-testing/2-python-pytest-framework.mdx) → [Python/Core/16-Testing.md](../Python/Core/16-Testing.md)
4. [3-python-test-driven-development.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/15-python-testing/3-python-test-driven-development.mdx) → [Python/Core/16-Testing.md](../Python/Core/16-Testing.md)
5. [4-python-mocking.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/15-python-testing/4-python-mocking.mdx) → [Python/Core/16-Testing.md](../Python/Core/16-Testing.md)
6. [5-python-test-coverage.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/15-python-testing/5-python-test-coverage.mdx) → [Python/Core/16-Testing.md](../Python/Core/16-Testing.md)
7. [6-python-integration-testing.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/15-python-testing/6-python-integration-testing.mdx) → [Python/Core/16-Testing.md](../Python/Core/16-Testing.md)
8. [7-python-debugging.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/15-python-testing/7-python-debugging.mdx) → [Python/Core/16-Testing.md](../Python/Core/16-Testing.md)

## 自动化、CLI、日志、配置与部署（8 篇）

1. [0-python-automation-basics.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/16-python-devops-tools/0-python-automation-basics.mdx) → [Python/Core/17-DevOps.md](../Python/Core/17-DevOps.md)
2. [1-python-cli-applications.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/16-python-devops-tools/1-python-cli-applications.mdx) → [Python/Core/17-DevOps.md](../Python/Core/17-DevOps.md)
3. [2-python-environment-variables.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/16-python-devops-tools/2-python-environment-variables.mdx) → [Python/Core/17-DevOps.md](../Python/Core/17-DevOps.md)
4. [3-python-logging.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/16-python-devops-tools/3-python-logging.mdx) → [Python/Core/17-DevOps.md](../Python/Core/17-DevOps.md)
5. [4-python-configuration.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/16-python-devops-tools/4-python-configuration.mdx) → [Python/Core/17-DevOps.md](../Python/Core/17-DevOps.md)
6. [5-python-docker-integration.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/16-python-devops-tools/5-python-docker-integration.mdx) → [Python/Core/17-DevOps.md](../Python/Core/17-DevOps.md)
7. [6-python-cicd-integration.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/16-python-devops-tools/6-python-cicd-integration.mdx) → [Python/Core/17-DevOps.md](../Python/Core/17-DevOps.md)
8. [7-python-cloud-deployment.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/16-python-devops-tools/7-python-cloud-deployment.mdx) → [Python/Core/17-DevOps.md](../Python/Core/17-DevOps.md)

## 代码风格、性能、安全、设计模式与重构（10 篇）

1. [0-python-naming-conventions.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/17-python-best-practices/0-python-naming-conventions.mdx) → [Python/Core/18-Best-Practices.md](../Python/Core/18-Best-Practices.md)
2. [1-python-code-style.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/17-python-best-practices/1-python-code-style.mdx) → [Python/Core/18-Best-Practices.md](../Python/Core/18-Best-Practices.md)
3. [2-python-pep8-guidelines.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/17-python-best-practices/2-python-pep8-guidelines.mdx) → [Python/Core/18-Best-Practices.md](../Python/Core/18-Best-Practices.md)
4. [3-python-documentation.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/17-python-best-practices/3-python-documentation.mdx) → [Python/Core/18-Best-Practices.md](../Python/Core/18-Best-Practices.md)
5. [4-python-performance-tips.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/17-python-best-practices/4-python-performance-tips.mdx) → [Python/Core/18-Best-Practices.md](../Python/Core/18-Best-Practices.md)
6. [5-python-memory-management.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/17-python-best-practices/5-python-memory-management.mdx) → [Python/Core/18-Best-Practices.md](../Python/Core/18-Best-Practices.md)
7. [6-python-security-practices.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/17-python-best-practices/6-python-security-practices.mdx) → [Python/Core/18-Best-Practices.md](../Python/Core/18-Best-Practices.md)
8. [7-python-design-patterns.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/17-python-best-practices/7-python-design-patterns.mdx) → [Python/Core/18-Best-Practices.md](../Python/Core/18-Best-Practices.md)
9. [8-python-refactoring.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/17-python-best-practices/8-python-refactoring.mdx) → [Python/Core/18-Best-Practices.md](../Python/Core/18-Best-Practices.md)
10. [9-python-code-organization.mdx](https://github.com/Compile-N-Run/Compile-N-Run/blob/d065f4f52553824687aa1f8f6ae4b7be43ea6533/docs/language/python/17-python-best-practices/9-python-code-organization.mdx) → [Python/Core/18-Best-Practices.md](../Python/Core/18-Best-Practices.md)

## 未吸收为主知识的内容

- index.mdx 与 _category_.json：仅为网站导航和元数据，不是独立知识正文。
- 重复的 Hello World、重复 CRUD、重复 list/string 基础例子：知识点已保留，重复演示合并。
- 具体 IDE 安装截图、云厂商 UI/CLI 步骤、第三方框架固定版本安装细节：高时效，保留稳定原理与官方入口，不固化旧步骤。
- 宣传性应用场景枚举：仅保留能帮助理解语言用途的部分。
- 许可不明情况下的英文原文镜像：不保存。

## 后续更新规则

若需要重新核对 Compile N Run，先比较上游 docs/language/python 在本记录 commit 之后的变更；只吸收新增且仍有效的知识，不重新复制一套平行教材。第三方框架、云平台、数据库驱动、打包工具的具体命令在实际使用前按官方文档重新核验。
