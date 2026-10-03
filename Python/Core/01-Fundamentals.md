# 01 · Python 基础、环境与运行模型

## 1. Python 解决什么问题

Python 是动态类型、自动内存管理、强调可读性的通用编程语言。它同时适合脚本自动化、Web、数据处理、机器学习、测试、运维工具和教学。学习 Python 的关键不是记语法，而是建立三层认识：

1. **值与对象**：整数、字符串、列表等都是对象，变量名绑定到对象。
2. **语句与表达式**：表达式产生值，语句组织程序流程。
3. **模块与运行环境**：代码通常放在 .py 文件或包中，由解释器加载执行。

Python 2 已经结束维护。新学习与新项目只讨论受支持的 Python 3。本仓库以 Python 3.14 系列作为 2026-10-03 的当前核验基线。

## 2. 安装、解释器与 REPL

安装后先验证：

~~~text
python --version
python -m pip --version
~~~

某些系统命令可能是 python3。重要的是确认“你运行代码的解释器”和“你安装依赖的解释器”是同一个，因此推荐用 **python -m pip** 而不是孤立地调用 pip。

直接执行 python 会进入 REPL。REPL 适合验证表达式、探索对象和阅读帮助：

~~~python
>>> 2 ** 8
256
>>> help(str.split)
~~~

脚本则适合保存、测试和复用：

~~~python
# hello.py
name = "Python"
print(f"Hello, {name}!")
~~~

运行：

~~~text
python hello.py
~~~

Jupyter/IPython 是增强交互环境，适合探索和数据分析；正式应用仍应把可复用逻辑放入模块并接受测试。

## 3. 第一个程序与缩进

Python 用缩进定义代码块。推荐统一 4 个空格，不混用 Tab：

~~~python
temperature = 28

if temperature >= 30:
    print("炎热")
else:
    print("适中")
~~~

常见初学错误：

- 缩进层级不一致；
- 冒号缺失；
- 字符串引号未闭合；
- 把赋值 = 与相等比较 == 混淆；
- 使用尚未绑定的名称。

## 4. 变量、常量约定与动态类型

赋值是“名称绑定”：

~~~python
count = 3
count = count + 1
label = "done"
~~~

Python 允许同一名称之后绑定到不同类型，但工程代码中应避免毫无必要地改变语义。变量和函数用 snake_case，类用 PascalCase，常量通常写成 UPPER_CASE；“常量”是约定，不是语言强制。

多重赋值和解包：

~~~python
x, y = 10, 20
x, y = y, x
~~~

## 5. 核心数据类型

| 类别 | 常用类型 | 关键性质 |
|---|---|---|
| 数值 | int、float、complex | int 可表示任意精度整数；float 是二进制浮点 |
| 文本 | str | Unicode、不可变 |
| 布尔 | bool | True / False；是 int 的子类但语义应当独立 |
| 序列 | list、tuple、range | list 可变，tuple 不可变 |
| 映射 | dict | 键到值；现代 Python 保持插入顺序 |
| 集合 | set、frozenset | 去重和集合运算 |
| 二进制 | bytes、bytearray | bytes 不可变，bytearray 可变 |
| 空值 | NoneType | 唯一常用值是 None |

用 type 或 isinstance 检查类型。公共 API 更常用 isinstance，因为它考虑继承关系。

## 6. 数字与精度

~~~python
a = 10
b = 3

print(a + b)   # 13
print(a / b)   # 3.333...
print(a // b)  # 3
print(a % b)   # 1
print(a ** b)  # 1000
~~~

整数可以使用 0b、0o、0x 表示二进制、八进制和十六进制。

浮点数不是十进制精确值：

~~~python
print(0.1 + 0.2 == 0.3)  # False
~~~

金融或必须精确表示十进制的计算考虑 decimal.Decimal；科学计算通常保留 float 并使用容差比较。

## 7. 字符串基础

字符串不可变，索引从 0 开始，负数从末尾倒数：

~~~python
text = "Python"
print(text[0])      # P
print(text[-1])     # n
print(text[1:4])    # yth
print(text[::-1])   # nohtyP
~~~

常用操作包括 lower、upper、strip、replace、split、join、find、startswith、endswith。修改操作会返回新字符串。

首选 f-string：

~~~python
name = "Ada"
score = 93.456
print(f"{name}: {score:.1f}")
~~~

百分号格式化和 str.format 仍可读懂，但新代码通常用 f-string。

## 8. 布尔值、真值与短路

以下值在布尔上下文中为假：False、None、数值 0、空字符串、空容器。其他大多数对象为真。

~~~python
items = []
if not items:
    print("没有数据")
~~~

and 和 or 会短路，并返回操作数而不一定返回 bool：

~~~python
name = user_input or "匿名"
~~~

比较值通常用 ==；判断是否就是 None 要用 is None。不要把 is 当作一般的值相等运算。

## 9. 运算符

需要掌握：

- 算术：+ - * / // % **
- 比较：== != < <= > >=
- 逻辑：and or not
- 身份：is / is not
- 成员：in / not in
- 位运算：& | ^ ~ << >>
- 赋值：= 以及 += 等增强赋值

当表达式开始依赖复杂优先级时，使用括号表达意图比背表更可靠。

## 10. 输入、输出与类型转换

input 总是返回字符串：

~~~python
raw = input("请输入年龄：")
age = int(raw)
print(f"明年 {age + 1} 岁")
~~~

显式转换包括 int、float、str、bool、list、tuple、set、dict。转换可能失败，应在边界处处理 ValueError。

## 11. 作用域与 LEGB

名称查找遵循 LEGB：

1. Local：当前函数局部；
2. Enclosing：外层函数；
3. Global：模块；
4. Built-in：内置命名空间。

~~~python
def make_counter():
    count = 0

    def next_value():
        nonlocal count
        count += 1
        return count

    return next_value
~~~

global 修改模块级名称，nonlocal 修改外层函数名称。两者都应谨慎使用；优先通过参数和返回值传递状态。

## 12. 注释与文档字符串

注释解释“为什么”，不要机械重复代码。连续 # 可以形成多行注释。三引号放在模块、类或函数开头时是 docstring，不应把任意三引号字符串当“注释”。

~~~python
def area(width: float, height: float) -> float:
    """计算矩形面积。"""
    return width * height
~~~

类型提示提升编辑器、静态检查器和读者的理解，但 Python 默认不会在运行时自动强制类型。

## 13. 最小综合例子

~~~python
def normalize_score(raw: str) -> float:
    score = float(raw)
    if not 0 <= score <= 100:
        raise ValueError("score must be between 0 and 100")
    return round(score, 1)


for sample in ["88.26", "100"]:
    print(normalize_score(sample))
~~~

预期输出：

~~~text
88.3
100.0
~~~

这里同时用到类型转换、函数、条件、异常和循环，是后续章节的最小连接点。

## 14. 常见误区

- Python 是解释型语言，不等于“没有编译过程”；CPython 会把源码编译为字节码再由虚拟机执行。
- 动态类型不等于“没有类型”，类型属于对象。
- float 不适合所有精确小数场景。
- is 不是 == 的更快写法。
- REPL 中能运行不代表适合作为可维护程序。
- 不要在系统 Python 环境中无边界安装第三方包，项目应使用虚拟环境。

## 15. 练习与答案

**练习 1**：为什么 int("3.5") 会失败？  
**答案**：字符串不是合法的整数文本；可先 float("3.5")，但是否再转 int 取决于业务是否允许丢失小数。

**练习 2**：解释 a = b = [] 的风险。  
**答案**：a 和 b 绑定到同一个列表；通过任一名称修改都会影响同一对象。

**练习 3**：什么时候用 is？  
**答案**：主要用于身份判断，例如 value is None；一般值比较用 ==。
