# 06 · 模块、包、虚拟环境与依赖管理

## 1. 模块与包

一个 .py 文件通常就是模块；包把多个模块组织成一个命名空间。

~~~text
project/
├── pyproject.toml
├── src/
│   └── myapp/
│       ├── __init__.py
│       ├── math_utils.py
│       └── text_utils.py
└── tests/
~~~

现代 Python 支持 namespace package，所以并非所有包都强制需要 __init__.py；普通应用包仍常保留它来明确边界并提供包级初始化或导出。

## 2. import 形式

~~~python
import math
from pathlib import Path
import numpy as np
~~~

不要在普通工程代码中使用 from module import *，因为它让名称来源不清晰，也容易覆盖已有名称。

模块首次导入后会被缓存到 sys.modules。交互实验中 importlib.reload 可以重新加载，但正式应用不应把 reload 当热更新机制。

## 3. __name__ 与脚本入口

~~~python
def main():
    print("run application")

if __name__ == "__main__":
    main()
~~~

模块被直接执行时 __name__ 为 "__main__"；被导入时是模块名。把主要逻辑放进函数，可以让代码更容易测试和复用。

## 4. 模块搜索路径

Python 通过 sys.path 查找模块。它受脚本位置、当前环境、安装包和 PYTHONPATH 等影响。

不要在业务代码中到处修改 sys.path 解决项目结构问题；更好的方法是正确组织包并以可编辑安装等方式让环境认识项目。

## 5. 标准库

源站重点展示 math、random、datetime、os、json、re。还应熟悉：

- pathlib：路径与文件；
- collections：专用容器；
- itertools：迭代工具；
- functools：函数工具；
- statistics：基础统计；
- sqlite3：内置数据库；
- argparse：CLI；
- logging：日志；
- concurrent.futures / asyncio：并发；
- dataclasses：数据类；
- typing：类型提示。

优先考虑标准库是否已解决问题，再决定引入第三方依赖。

## 6. 虚拟环境

每个项目建立独立环境，避免依赖互相污染：

~~~text
python -m venv .venv
~~~

激活：

~~~text
# macOS / Linux
source .venv/bin/activate

# Windows PowerShell
.venvScriptsActivate.ps1
~~~

随后：

~~~text
python -m pip install --upgrade pip
python -m pip install requests
~~~

deactivate 退出激活状态。即使不激活，也可以直接调用 .venv 内的解释器；激活本质上主要是调整当前 shell 的 PATH。

不要把 .venv 提交到 Git。

## 7. pip

常用命令：

~~~text
python -m pip install package-name
python -m pip install "package-name>=1.2,<2"
python -m pip uninstall package-name
python -m pip list
python -m pip show package-name
python -m pip freeze
~~~

从 Git、wheel、本地目录安装是高级能力，应确保来源可信并理解供应链风险。

## 8. requirements.txt 的正确位置

requirements.txt 很适合描述“某个环境要安装哪些分发包”：

~~~text
requests==2.x.y
pytest==x.y.z
~~~

但它不是现代 Python 项目的完整元数据模型。新项目的名称、版本、构建后端、依赖等更适合放在 pyproject.toml。

freeze 会把当前环境大量传递依赖都写出来，不等于人工维护的最小直接依赖列表。是否全部锁定版本取决于应用、库和部署策略。

## 9. pyproject.toml：新项目主入口

一个最小示意：

~~~toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "example-app"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
  "requests>=2",
]
~~~

具体构建后端可以是 Hatchling、Setuptools、Flit、PDM 等。核心思想是：**项目元数据采用标准 pyproject.toml，构建工具可替换。**

源站以 setup.py 演示分发，这在历史和既有项目中仍会遇到，但新项目不应把手写 setup.py 作为默认教学起点。

## 10. 项目本身的可编辑安装

开发一个包时：

~~~text
python -m pip install -e .
~~~

这让解释器通过安装元数据认识项目，而不是靠修改 sys.path。

## 11. 包导出与 __init__.py

可以在包入口重导出少量稳定 API：

~~~python
# myapp/__init__.py
from .models import User
from .service import create_user

__all__ = ["User", "create_user"]
~~~

不要把所有内部实现都提升到包顶层，否则后续重构会形成兼容负担。

## 12. 依赖管理策略

应用项目通常追求可重复部署：

- 声明直接依赖；
- 使用锁文件或经过审查的固定依赖集；
- CI 从干净环境安装；
- 定期更新并测试；
- 安全扫描只是信号之一，不替代更新策略和代码审查。

库项目则通常避免把依赖版本锁得过死，因为它需要与下游环境共存。

## 13. 系统 Python 与 externally managed 环境

现代 Linux 发行版常保护系统 Python，不允许普通 pip 直接覆盖系统管理的软件包。正确做法通常是：

- 项目用 venv；
- CLI 工具考虑 pipx 等隔离安装方式；
- 系统组件交给系统包管理器。

不要用强制选项破坏系统环境来“解决安装报错”。

## 14. 一个最小可复用模块

~~~python
# math_utils.py
def mean(values):
    if not values:
        raise ValueError("values cannot be empty")
    return sum(values) / len(values)


if __name__ == "__main__":
    print(mean([1, 2, 3]))
~~~

另一个模块：

~~~python
from math_utils import mean

print(mean([10, 20, 30]))
~~~

正式项目进一步放入包、增加 pyproject.toml 和 tests。

## 15. 常见错误

- 在全局系统 Python 直接安装所有项目依赖；
- pip 与 python 指向不同解释器；
- 把 .venv 提交 Git；
- 把 requirements.txt 当作所有 Python 打包问题的唯一标准；
- 新项目继续只教 setup.py；
- from x import *；
- 在代码里随意改 sys.path；
- 把密钥或私有仓库 token 写进依赖文件。

## 16. 练习与答案

**练习 1**：为什么推荐 python -m pip？  
**答案**：它明确使用当前这个 python 对应的 pip，减少多版本解释器混淆。

**练习 2**：库和应用的依赖版本策略为什么不同？  
**答案**：应用强调可复现部署，可以更严格锁定；库需要与下游共存，通常声明兼容范围而非锁死全部传递依赖。

**练习 3**：什么时候仍会看见 setup.py？  
**答案**：既有项目、兼容性场景或某些构建工具内部仍可能使用；但现代新项目的标准元数据入口优先 pyproject.toml。
