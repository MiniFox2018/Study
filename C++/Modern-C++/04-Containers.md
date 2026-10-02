# 04 · 现代容器与非拥有视图

## 1. std::array

`std::array<T, N>` 是固定长度容器，大小属于类型的一部分。

```cpp
std::array<int, 4> a{1, 2, 3, 4};
```

它与原生数组相比提供：

- `size()`
- `empty()`
- 迭代器
- `data()`
- 与 STL 算法一致的接口

与 vector 的区别在于：array 大小编译期固定，不负责动态扩容。

需要把 array 传给 C 风格接口时，可显式使用：

```cpp
foo(a.data(), a.size());
```

## 2. vector 的 size 与 capacity

动态数组要区分：

- `size()`：实际元素数量
- `capacity()`：当前已分配、无需重新分配即可容纳的元素数量

`clear()` 删除全部元素，保留 capacity；原有元素的引用、指针和迭代器不能再用。\
`shrink_to_fit()` 可请求释放多余容量，但它是 non-binding request，不能假设一定回收。

若最终规模大致已知，优先提前 `reserve()`，减少扩容和元素迁移。

## 3. std::forward_list

C++11 的 `std::forward_list` 是单链表：

- 节点只保存 next；
- 已知位置后的插入/删除可 O(1)；
- 不支持随机访问；
- 不提供普通 `size()` 成员；
- 相比 `std::list` 节省一个反向指针。

它适用于真正需要单向链式结构且节点操作占主导的场景。

## 4. Unordered Containers

C++11 标准化：

- `unordered_map`
- `unordered_multimap`
- `unordered_set`
- `unordered_multiset`

它们通常基于哈希表。

与 `map/set` 的主要差异：

| 特征 | map/set | unordered_* |
|---|---|---|
| 顺序 | 有序 | 不保证顺序 |
| 典型实现 | 平衡树 | 哈希表 |
| 平均查找 | O(log n) | O(1) |
| 最坏查找 | O(log n) | 可能 O(n) |
| 范围查询 | 适合 | 不适合 |

选择时应看是否需要排序、范围查询、稳定遍历顺序以及哈希成本。

## 5. std::tuple

tuple 是固定长度、异构类型的值集合。

核心接口：

- `std::make_tuple`
- `std::get<N>`
- `std::tie`
- `std::tuple_size`
- `std::tuple_cat`

```cpp
auto t = std::make_tuple(7, 3.14, std::string{"cpp"});
auto value = std::get<0>(t);
```

C++17 后，很多解包需求更适合 structured bindings：

```cpp
auto [id, score, name] = t;
```

## 6. Tuple 的索引特点

`std::get<N>` 中的 N 必须是编译期常量，因此 tuple 并不是运行时动态索引容器。

如果需求本质上是“运行时索引 + 多类型值”，可能更适合：

- `std::variant`
- 动态多态
- 自定义数据模型

对 tuple 做编译期遍历时，可使用：

- `std::index_sequence`
- parameter pack
- fold expression
- C++20 template lambda

## 7. std::string_view（C++17）

`string_view` 是字符串数据的 **非拥有只读视图**，通常只保存指针和长度。

```cpp
void print(std::string_view text);
```

优点：

- 可同时接收 string 和字符串字面量；
- 不需要复制字符；
- `substr()` 通常只产生新的 view。

最大风险是生命周期：

```cpp
std::string_view bad() {
    std::string s = "temp";
    return s; // dangling
}
```

string_view 不能延长底层字符序列的生命期，也不保证视图末尾有 `'\0'`。把 `view.data()` 当 C 字符串传入需要终止符的 API 可能越界或读取视图之外的数据；可先构造拥有自身内容的 `std::string`。

## 8. std::byte（C++17）

`std::byte` 表达“原始字节”而不是字符或整数。

它支持位运算，但不会像 char/unsigned char 一样自然参与算术，从类型层面减少误用。

```cpp
std::byte b{0b00001100};
b <<= 2;
int value = std::to_integer<int>(b);
```

适用于：

- 二进制协议
- 内存缓冲区
- 序列化
- 低层数据表示

## 9. Associative Container Improvements（C++17）

### try_emplace
仅当 key 不存在时构造 value：

```cpp
m.try_emplace(key, args...);
```

若 key 已存在，不会在容器节点中构造 mapped value，也不会消费传入的可移动对象；但函数实参仍先求值，`m.try_emplace(key, expensive())` 仍会调用 `expensive()`。

### insert_or_assign
不存在则插入，存在则更新：

```cpp
m.insert_or_assign(key, value);
```

### Node Handle
`extract()` 可把节点从容器中分离，而不复制其元素。  
`merge()` 可把兼容容器的节点直接迁移过来。

适合需要低成本改变 key、迁移元素或合并容器的场景。

## 10. std::pmr（C++17）

`std::pmr` 提供 polymorphic memory resource，把“容器类型”和“内存分配策略”解耦。

常见资源：

- `monotonic_buffer_resource`
- `unsynchronized_pool_resource`
- `synchronized_pool_resource`

示意：

```cpp
std::array<std::byte, 4096> storage;
std::pmr::monotonic_buffer_resource pool{
    storage.data(), storage.size()
};

std::pmr::vector<int> v{&pool};
```

适合：

- 生命周期一致的一批对象；
- 高频分配；
- 游戏/实时系统；
- 减少通用 heap allocator 压力。

## 核心结论

现代容器并不是“越新越好”，而是提供更准确的语义：

- 固定大小 → array
- 动态连续 → vector
- 哈希查找 → unordered
- 异构固定集合 → tuple
- 非拥有字符串 → string_view
- 原始内存 → byte
- 定制分配策略 → pmr

## 来源
Modern C++ Tutorial — Chapter 04

## 小实验：容量不是元素数量

```cpp
#include <iostream>
#include <vector>
int main() {
    std::vector<int> values;
    values.reserve(8);
    std::cout << values.size() << ' ' << (values.capacity() >= 8) << '\n';
    values.push_back(42);
    std::cout << values.at(0) << '\n';
}
```

输出 `0 1`、`42`，不要求 capacity 恰好等于 8。`reserve` 后的未构造位置不是合法元素。

`pmr` 的内存资源必须活得比使用它的容器长；`monotonic_buffer_resource` 默认缓冲用尽后会向上游申请内存，不能把示例的 4096 字节理解成硬上限。访问或销毁容器前调用资源 `release()` 会让仍依赖资源的对象失效。
