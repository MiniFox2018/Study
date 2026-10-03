# 03 · 函数、参数、装饰器与生成器

## 1. 函数的角色

函数把输入映射为输出，并隔离一段可复用逻辑。好的函数有清楚的职责、参数契约、返回值和失败方式。

~~~python
def area(width: float, height: float) -> float:
    if width < 0 or height < 0:
        raise ValueError("size cannot be negative")
    return width * height
~~~

## 2. 定义、调用与返回值

没有显式 return 的函数返回 None。一次返回多个值实际是返回 tuple：

~~~python
def min_max(values):
    return min(values), max(values)

low, high = min_max([3, 8, 1])
~~~

提前 return 可以减少嵌套。

## 3. 参数与实参

常见形式：

~~~python
def connect(host, port=5432):
    ...

connect("db.local")
connect(host="db.local", port=5433)
~~~

- positional argument：按位置绑定。
- keyword argument：按名称绑定。
- default parameter：调用时可省略。
- *args：收集额外位置实参。
- **kwargs：收集额外关键字实参。

~~~python
def report(title, *values, unit="", **meta):
    return title, values, unit, meta
~~~

### 位置仅限与关键字仅限

~~~python
def clamp(value, /, minimum=0, maximum=100, *, strict=False):
    ...
~~~

斜杠左侧只能按位置传；星号右侧只能按关键字传。公共 API 可用它们明确调用约束。

## 4. 可变默认参数陷阱

默认值在函数定义时创建一次：

~~~python
# 不推荐
def append_item(item, bucket=[]):
    bucket.append(item)
    return bucket
~~~

多次调用会共享同一个列表。正确做法：

~~~python
def append_item(item, bucket=None):
    if bucket is None:
        bucket = []
    bucket.append(item)
    return bucket
~~~

## 5. 解包调用

~~~python
point = (3, 4)
options = {"minimum": 0, "maximum": 10}

def normalize(x, y, minimum=0, maximum=100):
    ...

normalize(*point, **options)
~~~

## 6. Lambda

lambda 只支持单个表达式，适合短小的临时函数：

~~~python
users = [
    {"name": "Ada", "score": 90},
    {"name": "Linus", "score": 85},
]

users.sort(key=lambda user: user["score"], reverse=True)
~~~

复杂逻辑用具名函数更可读。

## 7. 递归

递归必须有基线条件：

~~~python
def factorial(n: int) -> int:
    if n < 0:
        raise ValueError("n must be non-negative")
    if n <= 1:
        return 1
    return n * factorial(n - 1)
~~~

Python 没有通用尾递归优化，递归深度也有限。树遍历、分治、递归结构很自然；线性循环通常更适合迭代写法。

缓存可避免重复子问题：

~~~python
from functools import cache

@cache
def fib(n):
    if n < 2:
        return n
    return fib(n - 1) + fib(n - 2)
~~~

## 8. 函数是一等对象

函数可以赋值、放入容器、作为参数传递、从函数返回：

~~~python
def add(x, y):
    return x + y

operations = {"add": add}
print(operations["add"](2, 3))
~~~

这是一切高阶函数、装饰器和回调的基础。

## 9. 闭包

闭包让内层函数记住外层作用域：

~~~python
def make_multiplier(factor):
    def multiply(value):
        return value * factor
    return multiply

double = make_multiplier(2)
print(double(5))  # 10
~~~

需要修改外层变量时用 nonlocal。闭包适合少量状态；状态复杂时类可能更清晰。

## 10. 装饰器

装饰器接收可调用对象并返回新的可调用对象：

~~~python
from functools import wraps
from time import perf_counter

def timed(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = perf_counter()
        try:
            return func(*args, **kwargs)
        finally:
            print(f"{func.__name__}: {perf_counter() - start:.6f}s")
    return wrapper
~~~

wraps 会保留函数名、文档等元数据。常见用途：日志、权限、缓存、重试、指标、参数验证。

带参数装饰器通常有三层函数：配置层 → 接收目标函数 → wrapper。多个装饰器的包装顺序是从下到上，调用时则从外到内。

不要在装饰器中隐藏大量难以观察的副作用。

## 11. 生成器与 yield

含 yield 的函数调用时返回生成器对象，不会立刻把所有结果构造出来：

~~~python
def read_batches(values, size):
    for start in range(0, len(values), size):
        yield values[start:start + size]

for batch in read_batches(list(range(7)), 3):
    print(batch)
~~~

输出：

~~~text
[0, 1, 2]
[3, 4, 5]
[6]
~~~

生成器适合大文件、数据流水线、无限序列和惰性计算。

生成器表达式：

~~~python
total = sum(x * x for x in range(1_000_000))
~~~

它不会先创建一百万项的平方列表。

## 12. yield 与 return 的区别

- return 结束普通函数并返回一个最终值。
- yield 暂停生成器、产出一个值，下一次迭代从暂停处继续。
- 生成器结束时产生 StopIteration，正常 for 循环会自动处理它。

生成器还支持 send、throw、close 等协议，但业务代码通常先掌握迭代和 yield 即可。

## 13. 类型提示与函数契约

~~~python
def average(values: list[float]) -> float:
    if not values:
        raise ValueError("values cannot be empty")
    return sum(values) / len(values)
~~~

类型提示主要服务于读者、IDE 和静态类型检查。运行时参数仍需在可信边界之外按业务要求验证。

## 14. 常见错误

- 可变默认参数；
- 返回值有时是数据、有时是含义完全不同的布尔值；
- 用 lambda 写复杂逻辑；
- 忘记 functools.wraps；
- 装饰器吞掉异常；
- 递归没有基线条件；
- 为了“节省内存”把需要多次遍历的数据错误改成一次性生成器；
- 生成器创建后忘记真正迭代。

## 15. 练习与答案

**练习 1**：*args 和 **kwargs 的值分别是什么类型？  
**答案**：函数内部 *args 是 tuple，**kwargs 是 dict。

**练习 2**：为什么默认参数 None 常用于可变容器？  
**答案**：None 是不可变单例，可在每次调用时新建容器，避免跨调用共享状态。

**练习 3**：何时生成器优于列表？  
**答案**：数据大、只需单次顺序消费、结果可逐项产生时；若需随机访问或多次遍历，列表可能更合适。
