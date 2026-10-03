# 04 · 内置数据结构与常用容器

## 1. 先按语义选择容器

Python 容器不是“都能装多个值”的不同写法，而是不同的数据模型。

| 结构 | 是否有序 | 是否可变 | 典型用途 |
|---|---|---|---|
| list | 是 | 是 | 顺序数据、动态数组 |
| tuple | 是 | 否 | 固定记录、不可变序列、解包 |
| dict | 保持插入顺序 | 是 | 键值映射、索引 |
| set | 不承诺业务顺序 | 是 | 去重、成员测试、集合运算 |
| frozenset | 不承诺业务顺序 | 否 | 可哈希集合 |
| deque | 是 | 是 | 两端高效入队出队 |
| Counter | 映射语义 | 是 | 计数 |
| defaultdict | 映射语义 | 是 | 带默认工厂的分组与累计 |

## 2. list：Python 的动态数组

创建和访问：

~~~python
values = [10, 20, 30, 40]
print(values[0])      # 10
print(values[-1])     # 40
print(values[1:3])    # [20, 30]
print(values[::-1])   # [40, 30, 20, 10]
~~~

常用修改：

~~~python
values.append(50)
values.extend([60, 70])
values.insert(1, 15)
values.remove(30)     # 按值删除第一个匹配项
last = values.pop()   # 删除并返回末项
~~~

查找和组织：

- index：返回第一个匹配位置，不存在会抛 ValueError。
- count：统计次数。
- sort：原地排序并返回 None。
- sorted：返回新列表，可接受任意可迭代对象。
- reverse：原地反转。
- copy：浅拷贝。

### 浅拷贝不是递归复制

~~~python
a = [[1], [2]]
b = a.copy()
b[0].append(99)

print(a)  # [[1, 99], [2]]
~~~

外层列表不同，但内部列表仍是共享对象。真正需要深拷贝时再考虑 copy.deepcopy，并先确认共享语义是否本来就是需要的。

### 常见复杂度

- 按索引读取：O(1)
- 末尾 append / pop：摊销 O(1)
- 中间插入/删除：O(n)
- 成员查找 x in list：O(n)

如果频繁从左端 pop(0)，优先 deque。

## 3. tuple：固定结构与解包

~~~python
point = (3, 5)
x, y = point

single = (42,)  # 单元素 tuple 必须有逗号
~~~

tuple 本身不可修改，但它可以引用可变对象：

~~~python
record = ("items", [1, 2])
record[1].append(3)   # 合法：列表变了，tuple 的引用位置没变
~~~

适合用 tuple 表达固定、轻量、按位置有明确含义的数据；字段多时 dataclass 或 NamedTuple 通常更清晰。

## 4. set：唯一值与集合代数

空集合必须写 set()，因为 {} 是空字典。

~~~python
a = {1, 2, 3}
b = {3, 4, 5}

print(a | b)   # 并集
print(a & b)   # 交集
print(a - b)   # 差集
print(a ^ b)   # 对称差
~~~

常用方法：

- add：加入单项。
- update：加入多个元素。
- remove：不存在时抛 KeyError。
- discard：不存在也不报错。
- pop：删除某个任意元素，不应依赖它删除哪个。
- issubset / issuperset / isdisjoint：关系判断。

set 的元素必须可哈希，因此 list、dict 等可变对象不能直接作为元素。

成员测试通常为平均 O(1)，适合去重和频繁查询。

## 5. dict：键值索引

~~~python
user = {"id": 7, "name": "Ada"}

print(user["name"])
print(user.get("email", "unknown"))

user["active"] = True
user.update({"name": "Ada L."})
~~~

读取差异：

- mapping[key]：键缺失时抛 KeyError，适合“缺少就是程序错误”。
- mapping.get(key, default)：缺失返回默认值，适合可选字段。

keys、values、items 返回动态视图。字典更新后，已有视图也反映变化。

~~~python
for key, value in user.items():
    print(key, value)
~~~

现代 Python 字典保持插入顺序，但如果业务需要“排序顺序”，应明确 sorted，而不是把插入顺序当排序规则。

### setdefault 与 defaultdict

简单分组可写：

~~~python
groups = {}
for name in ["alice", "amy", "bob"]:
    groups.setdefault(name[0], []).append(name)
~~~

更适合持续分组时：

~~~python
from collections import defaultdict

groups = defaultdict(list)
for name in ["alice", "amy", "bob"]:
    groups[name[0]].append(name)
~~~

## 6. array.array 与 NumPy array

标准库 array.array 存储同一基础类型的紧凑数值序列：

~~~python
from array import array

temperatures = array("f", [20.5, 21.2, 19.8])
~~~

它适合需要紧凑 C 风格数值数组但又不想引入 NumPy 的场景。科学计算中通常用 NumPy ndarray，因为它提供维度、广播、向量化和大量数值算法。

普通 list 则可以容纳不同对象，通用性最高。

## 7. collections：标准库的专用容器

### Counter

~~~python
from collections import Counter

counts = Counter("banana")
print(counts.most_common(2))
~~~

Counter 适合词频、类别频率和多重集运算。

### defaultdict

见前文，它通过 default_factory 自动创建缺失值。

### namedtuple 与 NamedTuple

namedtuple 为 tuple 增加字段名；现代代码若还需要类型提示，可用 typing.NamedTuple：

~~~python
from typing import NamedTuple

class Point(NamedTuple):
    x: float
    y: float
~~~

### deque

~~~python
from collections import deque

queue = deque(["a", "b"])
queue.append("c")
first = queue.popleft()
~~~

两端 append/pop 都是高效操作，是栈、队列、滑动窗口的常用选择。

## 8. 栈、队列与优先队列

栈是 LIFO：

~~~python
stack = []
stack.append("A")
stack.append("B")
print(stack.pop())  # B
~~~

普通单线程队列可用 deque。线程间生产者消费者应优先 queue.Queue，因为它提供同步和阻塞语义。

优先队列可用 heapq：

~~~python
import heapq

tasks = []
heapq.heappush(tasks, (2, "normal"))
heapq.heappush(tasks, (1, "urgent"))

print(heapq.heappop(tasks))  # (1, 'urgent')
~~~

## 9. 链表：理解价值大于默认工程价值

单链表节点：

~~~python
class Node:
    def __init__(self, value, next_node=None):
        self.value = value
        self.next = next_node
~~~

链表适合理解节点、指针式链接、插入删除和经典算法。但在普通 Python 应用中，内置 list 或 deque 通常更快、更省工程复杂度，因为它们在 C 层高度优化。

链表的理论优势是已知节点位置时局部插入删除可 O(1)；如果先要线性查找节点，总成本仍可 O(n)。

## 10. 推导式与容器构造

~~~python
squares = [n * n for n in range(6)]
lookup = {n: n * n for n in range(6)}
even_squares = {n * n for n in range(10) if n % 2 == 0}
~~~

复杂转换仍以可读性为准，不追求“一行完成”。

## 11. 选择决策

- 需要索引和顺序：list。
- 固定不可变记录：tuple / NamedTuple。
- 通过键找值：dict。
- 去重或高频成员判断：set。
- 两端队列：deque。
- 计数：Counter。
- 分组累计：defaultdict。
- 线程安全队列：queue.Queue。
- 小顶堆/优先级：heapq。
- 大规模向量数值：NumPy。

## 12. 练习与答案

**练习 1**：为什么 queue = [] 然后频繁 pop(0) 不理想？  
**答案**：列表删除首项后需要移动后续元素，O(n)；deque.popleft 更适合。

**练习 2**：去重但不在乎顺序用什么？  
**答案**：set；若还需稳定保留第一次出现顺序，可用 dict.fromkeys 或显式循环。

**练习 3**：dict.get 和 [] 读取如何选？  
**答案**：字段必须存在时用 [] 暴露错误；字段可选时用 get 并给出清晰默认值。
