# 18 · 代码风格、性能、安全、设计模式与重构

## 1. 最佳实践不是规则堆

好的 Python 工程追求：

- 意图清楚；
- 边界明确；
- 易测试；
- 可观察；
- 安全；
- 性能与复杂度匹配；
- 可演进。

PEP 8 是共同风格基线，不是把所有代码变成同一模板。

## 2. 命名

惯例：

- variable_name / function_name；
- ClassName；
- CONSTANT_NAME；
- _internal_name；
- __magic__ 只给 Python 数据模型规定的特殊方法。

名称表达业务语义：

~~~python
# 差
x = 86400

# 好
SECONDS_PER_DAY = 86_400
~~~

不要把 list、dict、id、str 等内置名称当普通变量长期覆盖。

## 3. PEP 8

核心习惯：

- 4 空格缩进；
- 导入分标准库、第三方、本地；
- 适当空行；
- 运算符周围合理空格；
- 长表达式用括号自然换行；
- 命名一致。

PEP 8 的默认行长常用于风格工具，但项目可有一致的自动格式化策略。可读性与团队工具链优先，不需要手工每天争论空格。

## 4. 自动格式化与 lint

现代团队通常让工具处理机械风格，再把 code review 留给设计和正确性。可根据项目选择 formatter、linter、type checker。

工具生态会变化，本仓库不把某个第三方工具写成永久唯一标准。建立一套 CI 可重复规则比争论“哪个最潮”重要。

## 5. 文档

文档分层：

- 名称：能自解释的不再写废话注释；
- 注释：解释非显然的原因、约束、算法；
- docstring：公共模块、类、函数契约；
- README：项目入口；
- architecture / ADR：跨模块决策；
- API docs：对外接口。

常见 docstring 风格有 Google、NumPy、reST。项目统一一种即可。

## 6. 类型提示

类型提示可以描述：

- 参数/返回；
- 容器元素；
- Protocol；
- Literal；
- TypedDict；
- generic。

它们默认不做运行时校验。静态检查不替代测试，测试也不替代类型设计。

公共 API 类型应尽量表达真正契约，不要为了“全覆盖”写成 Any。

## 7. 性能：先测量

优化顺序：

1. 明确性能目标；
2. 用真实/代表性负载测量；
3. profiler 找热点；
4. 改算法/数据结构；
5. 再做局部优化；
6. 重新测量并防回归。

不要从“把所有 for 改列表推导式”开始。

## 8. 常见性能方向

### 使用合适数据结构

set/dict 做频繁成员查询通常优于 list。

### 内置函数

sum、min、max、sorted 等在底层高度优化且语义清晰。

### 生成器

大数据单次流式处理可降低峰值内存。

### NumPy

大量同构数值计算可向量化时，NumPy 往往远快于 Python 层循环。

### 批处理

数据库/API 按批量接口处理可减少往返成本。

## 9. profiling

CPU：

~~~python
import cProfile

cProfile.run("main()")
~~~

微基准用 timeit；端到端延迟要用真实计时和分位数。

内存可用 tracemalloc 检查分配趋势。第三方 profiler 需要按项目选型。

微基准结果不能替代真实系统性能。

## 10. 内存管理

CPython 常以引用计数及时回收多数对象，并用循环垃圾回收器处理引用环。实现细节不是 Python 语言保证，其他实现可能不同。

减少内存峰值的常见方法：

- 流式读取；
- generator；
- 删除不再需要的大对象引用；
- 避免无意缓存；
- 使用合适 dtype；
- 及时关闭资源；
- 分块处理。

不要把 gc.collect 当普通业务循环的性能优化手段，先测量。

## 11. 安全：输入与信任边界

不要“先相信、出错再说”。明确外部输入：

- HTTP；
- 文件；
- 数据库内容；
- 环境变量；
- CLI；
- message queue；
- pickle；
- 模板；
- shell；
- 第三方 API。

验证长度、类型、范围和语义；输出到 SQL、HTML、shell 等不同上下文时使用对应安全 API。

## 12. SQL、Shell 与代码执行

- SQL：参数化；
- shell：优先 subprocess 传参数列表，避免 shell=True；
- Python 动态执行：不要对不可信字符串 eval/exec；
- YAML：安全加载；
- pickle：不反序列化不可信数据。

~~~python
import subprocess

subprocess.run(
    ["git", "status", "--short"],
    check=True,
)
~~~

不要把用户字符串拼成一整条 shell 命令。

## 13. 文件安全

处理上传/解压：

- 不信任文件名；
- 防路径穿越；
- 限制大小；
- 限制扩展名不等于验证内容；
- 解压时防 zip/tar traversal；
- 存储名与原文件名分离；
- 上传目录不可直接当可执行代码目录。

## 14. Secret

不要在代码、日志、测试 fixture、Docker image、Git history 中保存真实 secret。

若 secret 已提交 Git，删除当前文件并不够，需要轮换凭据，并按需要清理历史。

## 15. 依赖供应链

- 使用可信来源；
- 限制维护权限；
- 审查 lock/依赖变更；
- 定期更新；
- 关注安全公告；
- CI 构建不运行不必要脚本；
- 对关键发布验证签名/来源能力。

安全扫描工具的数据库和规则会变，只能作为持续流程的一部分。

## 16. 设计模式

源站介绍 Singleton、Factory、Adapter、Decorator、Observer、Strategy。Python 中应理解意图而非机械类图。

### Factory

当创建逻辑依赖配置或类型：

~~~python
def create_storage(kind):
    if kind == "memory":
        return MemoryStorage()
    if kind == "file":
        return FileStorage()
    raise ValueError(kind)
~~~

简单字典映射可能比完整 Factory class 更 Pythonic。

### Adapter

把旧接口包装成新接口，不修改调用方。

### Decorator pattern

对象包装器动态叠加职责；不要和 Python @function_decorator 概念混淆，虽然思想相近。

### Observer

发布订阅，注意异常隔离、订阅生命周期和并发。

### Strategy

把可替换算法作为对象或函数传入。在 Python 中策略常可以直接是 callable，不需要为每个策略创建类。

### Singleton

通常不是优先模式。模块本身就是自然单例式命名空间，依赖注入通常比全局 Singleton 更易测试。

## 17. 重构

典型 code smell：

- 超长函数；
- 重复代码；
- 深层条件；
- 大类承担多个职责；
- 模糊命名；
- 隐式全局状态；
- 参数列表失控；
- 同一逻辑散落多个入口。

常用手法：

- extract function；
- rename；
- introduce data object；
- move function；
- split responsibility；
- replace conditional with dispatch/strategy；
- 封装外部依赖。

## 18. 重构的安全流程

1. 先用测试或可复现输入固定行为；
2. 一次做小改动；
3. 运行测试；
4. 比较可观察行为；
5. 性能敏感时重新基准；
6. 提交小变更。

“顺便重写一遍”不是安全重构。

## 19. 代码组织

小脚本：

~~~text
imports
constants
functions/classes
main
if __name__ == "__main__"
~~~

应用：

~~~text
project/
├── pyproject.toml
├── src/
│   └── app/
│       ├── domain/
│       ├── services/
│       ├── adapters/
│       └── cli.py
└── tests/
~~~

目录应该反映职责，不是为了看起来“专业”制造十层空文件夹。

## 20. dataclass

纯数据对象可用 dataclass 减少样板：

~~~python
from dataclasses import dataclass

@dataclass(frozen=True)
class Money:
    amount: int
    currency: str
~~~

frozen 提供浅层不可变语义，不等于所有成员递归不可变。

## 21. 一个实用检查表

提交前至少问：

- 输入边界验证了吗？
- 异常会被正确传播/记录吗？
- secret 会不会进入日志？
- 文件/连接一定关闭吗？
- SQL/shell 是否参数化？
- 有测试覆盖关键失败路径吗？
- 算法复杂度适合数据规模吗？
- 依赖是否真的需要？
- 代码结构能否让下一次修改只改一个地方？
- 对时效敏感的第三方 API 是否查了当前官方文档？

## 22. 练习与答案

**练习 1**：为什么“100% PEP 8”不等于高质量代码？  
**答案**：格式一致只解决可读性的机械部分，不能保证设计、正确性、安全、测试和性能。

**练习 2**：什么时候先换算法而不是微优化语法？  
**答案**：profile 显示瓶颈且复杂度是主要问题时，O(n²) → O(n log n) 的收益通常远大于局部语法优化。

**练习 3**：为什么 Python 里 Strategy 不一定需要 class？  
**答案**：函数是一等对象，只要策略无复杂状态，一个 callable 就能表达可替换算法。
