# 10 · 迭代器、上下文管理器、描述符与元类

## 1. 可迭代对象与迭代器

可迭代对象能产生迭代器；迭代器实现逐项取值状态。

~~~python
values = [10, 20, 30]
iterator = iter(values)

print(next(iterator))
print(next(iterator))
~~~

迭代器耗尽后 next 抛 StopIteration。for 会自动完成 iter、next 和 StopIteration 处理。

### Iterable 与 Iterator

- Iterable：实现 __iter__，或满足旧式序列协议。
- Iterator：实现 __iter__ 并返回自身，同时实现 __next__。

自定义倒计时：

~~~python
class Countdown:
    def __init__(self, start):
        self.current = start

    def __iter__(self):
        return self

    def __next__(self):
        if self.current <= 0:
            raise StopIteration
        value = self.current
        self.current -= 1
        return value
~~~

很多时候生成器比手写迭代器类更简洁。

## 2. itertools

标准库 itertools 提供惰性迭代工具：

- count：无限计数；
- cycle：循环重复序列；
- repeat：重复值；
- chain：串联多个可迭代对象；
- islice：对迭代器做切片式读取；
- combinations / permutations：组合排列；
- groupby：按相邻键分组。

无限迭代器必须有明确停止条件。

## 3. 推导式、map 与 filter 的选择

这三者都能表达转换与过滤：

~~~python
numbers = range(10)

a = [x * 2 for x in numbers if x % 2 == 0]
b = list(map(lambda x: x * 2, filter(lambda x: x % 2 == 0, numbers)))
~~~

Python 代码通常优先推导式；已有具名函数、函数组合或真正想保留惰性时，map/filter 可能更自然。

## 4. 上下文管理器

with 解决“进入资源 → 使用 → 无论成功失败都退出清理”。

协议由 __enter__ / __exit__ 实现：

~~~python
class Timer:
    def __enter__(self):
        from time import perf_counter
        self.start = perf_counter()
        return self

    def __exit__(self, exc_type, exc, tb):
        from time import perf_counter
        self.elapsed = perf_counter() - self.start
        return False
~~~

__exit__ 返回真值会抑制异常，除非确实要把异常视为已处理，否则返回 False。

## 5. contextlib.contextmanager

简单上下文可用生成器式写法：

~~~python
from contextlib import contextmanager

@contextmanager
def managed_resource(resource):
    resource.open()
    try:
        yield resource
    finally:
        resource.close()
~~~

yield 前是进入逻辑，yield 后是退出逻辑。

contextlib 还包括 closing、suppress、nullcontext、ExitStack 等。ExitStack 适合运行时动态决定要打开多少个资源。

## 6. 描述符

只要对象定义 __get__、__set__ 或 __delete__ 中至少一个，并作为类属性存在，它就参与属性访问协议。

一个验证描述符：

~~~python
class Positive:
    def __set_name__(self, owner, name):
        self.storage_name = "_" + name

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return getattr(instance, self.storage_name)

    def __set__(self, instance, value):
        if value <= 0:
            raise ValueError("value must be positive")
        setattr(instance, self.storage_name, value)


class Product:
    price = Positive()

    def __init__(self, price):
        self.price = price
~~~

property 本身就是建立在描述符机制上的常见高级抽象。

## 7. 数据描述符与非数据描述符

实现 __set__ 或 __delete__ 的描述符通常称数据描述符，其优先级高于实例字典中的同名属性。只有 __get__ 的非数据描述符优先级更低。

理解这个优先级能解释 method、property、cached_property 等行为，但日常业务代码不应滥用描述符。

## 8. 惰性属性

描述符或 functools.cached_property 可在第一次访问时计算并缓存昂贵结果。缓存前要确认对象状态是否会改变，否则可能得到陈旧值。

## 9. 元类

类本身也是对象。默认大多数类由 type 创建：

~~~python
class User:
    pass

assert isinstance(User, type)
~~~

元类控制“类如何创建”。定义：

~~~python
class RegistryMeta(type):
    registry = {}

    def __new__(mcls, name, bases, namespace):
        cls = super().__new__(mcls, name, bases, namespace)
        if name != "Plugin":
            mcls.registry[name] = cls
        return cls
~~~

常见用途：

- 框架自动注册类；
- 类创建时校验约束；
- ORM 字段收集；
- 声明式 API。

## 10. 元类创建流程

核心钩子包括：

1. 解析基类与合适元类；
2. 元类 __prepare__ 可提供类命名空间；
3. 执行 class body；
4. 元类 __new__ 创建类；
5. 元类 __init__ 初始化类对象；
6. 描述符 __set_name__ 获得所属名称。

实际项目中，class decorator、__init_subclass__、descriptor 往往能以更低复杂度解决问题，应在写元类前先考虑它们。

## 11. __init_subclass__

~~~python
class Plugin:
    registry = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        Plugin.registry[cls.__name__] = cls
~~~

对于“子类定义时自动注册”，这通常比自定义元类更简单。

## 12. 高级装饰器回顾

装饰器可以：

- 带参数；
- 用类实现 __call__；
- 多层叠加；
- 用 wraps 保留元数据；
- 做缓存、限流、计时、校验。

限流、重试等装饰器要考虑并发安全、异常、时钟与分布式场景，教学示例不能直接等同生产实现。

## 13. 常见误区

- 把 iterator 当可重复遍历容器；
- next 耗尽后还期待“自动重置”；
- 上下文管理器的 __exit__ 意外吞异常；
- 描述符写在实例属性上而不是类属性；
- 为普通字段校验就上元类；
- Singleton 元类被当作通用全局状态方案；
- 不理解缓存失效就做惰性缓存。

## 14. 练习与答案

**练习 1**：为什么 list 可多次 for，而 generator 常只能消费一次？  
**答案**：list 每次可创建新迭代器；generator 本身通常就是有状态迭代器，耗尽后不会自动重建。

**练习 2**：property、descriptor、metaclass 的抽象层级？  
**答案**：property 管一个属性；descriptor 可复用属性访问协议；metaclass 控制整个类的创建。能用低层级方案解决就不要上更高复杂度。

**练习 3**：上下文管理器最重要的价值？  
**答案**：把资源生命周期与异常安全绑定在一个明确语法范围中。
