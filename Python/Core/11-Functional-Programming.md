# 11 · 函数式编程

## 1. Python 的函数式能力

Python 不是纯函数式语言，但函数是一等对象，并提供高阶函数、闭包、不可变数据、迭代器和 functools / itertools。函数式思想的重点不是把所有代码写成 lambda，而是减少隐式状态和副作用，让数据变换可组合、可测试。

## 2. 一等函数

函数可以赋值、传参、返回、放入容器：

~~~python
def double(x):
    return x * 2

operation = double
print(operation(5))
~~~

作为参数：

~~~python
def apply(values, transform):
    return [transform(v) for v in values]

print(apply([1, 2, 3], double))
~~~

## 3. 高阶函数

高阶函数接收函数或返回函数。常见内置和标准库工具：

- sorted 的 key；
- map；
- filter；
- functools.reduce；
- functools.partial；
- decorators。

许多 Python 代码用推导式会比 map/filter + lambda 更清晰。

## 4. 纯函数

纯函数：

1. 相同输入得到相同输出；
2. 不修改外部可观察状态。

~~~python
def add_tax(price, rate):
    return price * (1 + rate)
~~~

非纯函数示例：

~~~python
total = 0

def add_to_total(value):
    global total
    total += value
~~~

副作用并非错误；文件、数据库、网络都需要副作用。更好的设计是把纯计算放中间，把 I/O 集中在边界。

## 5. 避免修改输入

~~~python
def with_discount(order, rate):
    return {
        **order,
        "price": order["price"] * (1 - rate),
    }
~~~

这种写法更容易推理，但复制大结构也有成本。工程上追求“明确所有权与副作用”，不应教条式禁止一切 mutation。

## 6. 不可变数据

常见不可变类型：

- int / float / bool；
- str；
- tuple；
- frozenset；
- bytes。

tuple 中可以引用可变对象，所以“tuple 不可变”指它的元素引用位置不能被重新赋值。

不可变数据适合哈希键、并发共享和状态快照。

## 7. map 与 filter

~~~python
numbers = [1, 2, 3, 4]

doubled = map(lambda x: x * 2, numbers)
even = filter(lambda x: x % 2 == 0, numbers)
~~~

Python 3 的 map/filter 返回惰性迭代器。若只是简单表达式：

~~~python
doubled = [x * 2 for x in numbers]
even = [x for x in numbers if x % 2 == 0]
~~~

通常更直观。

## 8. reduce

~~~python
from functools import reduce

product = reduce(lambda a, b: a * b, [2, 3, 4], 1)
~~~

常见聚合优先内置 sum、min、max、any、all、math.prod，因为语义更直接。reduce 更适合真正的二元累积规则。

空序列若没有 initializer 会报错。

## 9. partial

partial 固定部分参数，生成更专门的函数：

~~~python
from functools import partial

def power(base, exponent):
    return base ** exponent

square = partial(power, exponent=2)
print(square(5))  # 25
~~~

适合回调、配置化函数和依赖注入，不必为了固定参数再写一层无意义 wrapper。

## 10. 函数组合

~~~python
def compose(f, g):
    return lambda x: f(g(x))

strip_and_lower = compose(str.lower, str.strip)
print(strip_and_lower("  HELLO "))
~~~

大型业务流水线更适合具名步骤、显式错误处理和可观察性，而不是构造难以调试的深层 lambda 链。

## 11. 管道思想

把处理分成小步骤：

~~~python
def parse(raw):
    return [float(x) for x in raw]

def positive(values):
    return [x for x in values if x > 0]

def average(values):
    if not values:
        raise ValueError("no values")
    return sum(values) / len(values)

result = average(positive(parse(["2", "-1", "4"])))
~~~

输入/输出契约清楚时，各步都容易独立测试。

## 12. 闭包

闭包可生成带配置的函数：

~~~python
def above(threshold):
    def predicate(value):
        return value > threshold
    return predicate

is_high = above(80)
~~~

当状态增多、方法变多或生命周期复杂时，用类更清晰。

## 13. 函数式工具

functools 常用：

- cache / lru_cache；
- partial；
- reduce；
- wraps；
- singledispatch；
- cmp_to_key。

itertools 常用：

- chain；
- islice；
- repeat；
- product；
- combinations / permutations；
- accumulate；
- groupby。

operator 模块提供 itemgetter、attrgetter 等，可在排序和分组中替代简单 lambda。

## 14. 缓存不是纯函数替代品

cache 最适合确定性、输入可哈希且结果可安全复用的函数。若函数依赖时间、网络、外部数据库或隐藏全局状态，缓存必须设计过期和失效策略。

## 15. 回调与事件

一等函数让事件系统可注册回调：

~~~python
handlers = []

def subscribe(handler):
    handlers.append(handler)

def publish(event):
    for handler in handlers:
        handler(event)
~~~

生产事件系统还要处理异常隔离、顺序、并发、重试与取消订阅。

## 16. 常见误区

- 为了“函数式”把可读循环全部改成 lambda；
- reduce 做 sum 已经能表达的事；
- 纯函数与“函数里不能调用任何函数”混淆；
- 不考虑复制成本就到处重建大对象；
- 缓存带副作用或外部状态函数；
- 函数组合后完全没有可观察中间步骤。

## 17. 练习与答案

**练习 1**：为什么 sum(values) 通常优于 reduce(lambda a,b: a+b, values)？  
**答案**：语义更直接、边界清楚、实现优化更成熟。

**练习 2**：什么时候 partial 比 lambda 更适合？  
**答案**：只是固定已有函数部分参数时，partial 能更直接表达意图并保留可调用对象结构。

**练习 3**：纯函数对测试的优势？  
**答案**：没有隐藏外部状态，相同输入可重复得到同一输出，测试前置条件更少。
