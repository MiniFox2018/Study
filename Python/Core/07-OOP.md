# 07 · 面向对象编程

## 1. 类与对象

类定义一组状态与行为，对象是类的实例。

~~~python
class BankAccount:
    bank_name = "Example Bank"

    def __init__(self, owner: str, balance: float = 0.0):
        if balance < 0:
            raise ValueError("balance cannot be negative")
        self.owner = owner
        self.balance = balance

    def deposit(self, amount: float) -> None:
        if amount <= 0:
            raise ValueError("amount must be positive")
        self.balance += amount
~~~

bank_name 是类属性；owner 和 balance 是实例属性。

## 2. __init__ 与 __new__

__new__ 负责创建实例，__init__ 在实例创建后初始化它。绝大多数业务类只需要 __init__。只有不可变类型子类化、元类/缓存等特殊场景才常直接处理 __new__。

构造函数应保持清晰：完成必要验证和状态建立，不要偷偷执行昂贵网络请求、长时间 I/O 或难以回滚的副作用。

## 3. self

self 只是实例方法第一个参数的惯例名称。调用 account.deposit(10) 时，实例会自动作为第一个参数传入。

## 4. 实例方法、类方法与静态方法

### 实例方法

需要访问具体实例状态。

### classmethod

第一个参数通常是 cls，适合替代构造器和管理类级状态：

~~~python
from datetime import date

class Person:
    def __init__(self, name, birth_year):
        self.name = name
        self.birth_year = birth_year

    @classmethod
    def from_age(cls, name, age):
        return cls(name, date.today().year - age)
~~~

### staticmethod

不依赖实例或类状态，但在概念上属于这个类：

~~~python
class Temperature:
    @staticmethod
    def c_to_f(c):
        return c * 9 / 5 + 32
~~~

如果函数与类没有强概念关系，放在模块级通常更简单。

## 5. 封装：Python 更依赖约定与属性

Python 没有 Java/C++ 式强制 private。常见约定：

- _name：内部实现，不建议外部依赖；
- __name：触发名称改写，主要用于减少继承冲突，不是安全边界。

不要通过名称改写假装“数据不可访问”。封装的真正价值是建立稳定 API。

## 6. property

property 允许在保持属性式访问的同时添加验证或计算：

~~~python
class Product:
    def __init__(self, price):
        self.price = price

    @property
    def price(self):
        return self._price

    @price.setter
    def price(self, value):
        if value < 0:
            raise ValueError("price cannot be negative")
        self._price = float(value)
~~~

不需要逻辑时直接公开普通属性即可，不要机械写 getter/setter。

## 7. 继承与 super

~~~python
class Animal:
    def __init__(self, name):
        self.name = name

    def speak(self):
        return "..."

class Dog(Animal):
    def __init__(self, name, breed):
        super().__init__(name)
        self.breed = breed

    def speak(self):
        return "woof"
~~~

继承表达“is-a”关系。若只是复用功能或组合多个部件，组合通常比深继承更灵活。

## 8. 多态与鸭子类型

Python 常以行为而不是继承层级判断对象能否使用：

~~~python
def save(document):
    document.write()
~~~

只要传入对象提供合适的 write 方法即可。这就是 duck typing。

方法重载在 Python 中不是按签名自动选择多个同名定义；后定义会覆盖前定义。需要不同调用形式时，用默认参数、*args、singledispatch 或不同方法名。

## 9. 抽象基类

~~~python
from abc import ABC, abstractmethod

class Storage(ABC):
    @abstractmethod
    def save(self, data):
        ...

class FileStorage(Storage):
    def save(self, data):
        print("saved")
~~~

ABC 适合需要运行时保证“子类必须实现某接口”的体系。

## 10. Protocol：结构化接口

静态类型检查中，typing.Protocol 能描述“只要具有这些成员就满足接口”，无需继承：

~~~python
from typing import Protocol

class Writable(Protocol):
    def write(self, data: str) -> int:
        ...

def emit(target: Writable, text: str) -> None:
    target.write(text)
~~~

这比为每个鸭子类型场景强制建立共同父类更符合 Python 风格。

## 11. 多重继承与 MRO

Python 支持多重继承，并使用 Method Resolution Order 决定方法查找顺序：

~~~python
print(MyClass.mro())
~~~

super 不是简单表示“父类”，而是沿 MRO 的下一项继续协作调用。因此设计 mixin 或多继承体系时，各类初始化签名要可协作。

钻石继承能由 C3 MRO 处理，但复杂多继承仍会增加推理成本。工程代码更常把多重继承限制在小型 mixin。

## 12. 魔术方法

常见数据模型钩子：

- __repr__：调试表示；
- __str__：用户可读表示；
- __len__：len(obj)；
- __iter__：迭代；
- __getitem__ / __setitem__：索引访问；
- __contains__：in；
- __eq__ / __lt__：比较；
- __add__ 等：运算符；
- __call__：让实例可调用；
- __enter__ / __exit__：上下文管理。

只在语义真正匹配时实现，不要为了炫技改变用户对运算符的自然预期。

## 13. 一个小型领域模型

~~~python
class Inventory:
    def __init__(self):
        self._stock = {}

    def add(self, sku: str, quantity: int) -> None:
        if quantity <= 0:
            raise ValueError("quantity must be positive")
        self._stock[sku] = self._stock.get(sku, 0) + quantity

    def sell(self, sku: str, quantity: int) -> None:
        available = self._stock.get(sku, 0)
        if quantity <= 0:
            raise ValueError("quantity must be positive")
        if quantity > available:
            raise ValueError("insufficient stock")
        self._stock[sku] = available - quantity

    def stock(self, sku: str) -> int:
        return self._stock.get(sku, 0)
~~~

这个例子展示封装、验证、方法职责和内部状态，而不需要复杂继承。

## 14. 常见错误

- 继承层级太深；
- 把 classmethod 与 staticmethod 混用；
- 把 __private 当安全机制；
- 每个字段都机械加 getter/setter；
- 构造函数执行外部网络请求；
- 多重继承中直接调用某个父类而破坏协作 super；
- 运算符重载语义反直觉；
- 本可用 dataclass/组合解决的问题强行设计大量样板类。

## 15. 练习与答案

**练习 1**：替代构造器为什么适合 classmethod 而不是 staticmethod？  
**答案**：classmethod 接收 cls，子类调用时可自然构造子类实例。

**练习 2**：Protocol 与 ABC 的主要区别？  
**答案**：Protocol 强调结构化类型，满足成员即可；ABC 通常要求显式继承并可提供运行时抽象约束。

**练习 3**：什么时候优先组合而不是继承？  
**答案**：关系是“has-a”、只为复用行为、或多个部件可以独立替换时。
