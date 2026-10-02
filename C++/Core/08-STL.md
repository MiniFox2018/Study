# 08 · 标准模板库与算法

## STL 架构
STL 通过迭代器把容器和算法解耦，核心包括 Containers、Algorithms、Iterators 和 Function Objects。

## 容器
### 顺序容器
`vector`、`list`、`deque`、`array`、`forward_list`。

### 有序关联容器
`set`、`multiset`、`map`、`multimap`。

### 无序关联容器
`unordered_set`、`unordered_map` 及 multi 版本。

### 容器适配器
`stack`、`queue`、`priority_queue`。

## vector
连续内存、O(1) 随机访问、尾部追加摊销 O(1)。需要理解 size、capacity、reserve 和扩容导致的迭代器失效。

## list
双向链表，已知位置插删成本低，无随机访问，缓存局部性较差。

## deque
支持头尾高效插删，也支持随机访问，但通常不是单块连续内存。

## set
唯一有序元素，典型操作 O(log n)。

## map
有序键值对。使用 `find` 可避免无意插入；`operator[]` 在键不存在时会创建元素。

## stack 与 queue
分别表达 LIFO 和 FIFO，只暴露符合数据结构语义的有限接口。

## Algorithms
常见：`find`、`find_if`、`count`、`sort`、`stable_sort`、`transform`、`copy`、`move`、`binary_search`、`accumulate`。算法通常操作半开区间 `[first,last)`。

## Iterators
读取迭代器逐步增强为 input、forward、bidirectional、random access（C++20 还定义 contiguous）；output 是输出能力类别，不是这条读取继承链中的一层。不同算法对迭代器能力有不同要求。

## Functors
重载 `operator()` 的对象，可保存状态并作为算法策略。Lambda 在很多场景可替代手写 functor。

## 使用习惯
优先标准算法；只读大型元素常用 `const auto&`；了解迭代器失效规则；按访问和修改模式选容器；避免不必要复制。

## 小实验：排序、去重与查找

```cpp
#include <algorithm>
#include <iostream>
#include <vector>
int main() {
    std::vector<int> values{3, 1, 3, 2};
    std::sort(values.begin(), values.end());
    values.erase(std::unique(values.begin(), values.end()), values.end());
    for (int x : values) std::cout << x << ' ';
    std::cout << '\n' << std::boolalpha
              << std::binary_search(values.begin(), values.end(), 2) << '\n';
}
```

输出第一行 `1 2 3`（末尾有空格），第二行 `true`。`unique` 只把相邻重复值移到逻辑末尾，随后 `erase` 才改变容器大小。二分查找必须满足相应比较器的分区要求；先排序是最直观的充分条件。

自测：`reserve(100)` 后可以直接访问 `v[99]` 吗？答：不能，`reserve` 改容量而不创建元素；需 `resize(100)` 或逐个添加。扩容后旧指针、引用和迭代器可能全部失效。

## 参考
https://www.compilenrun.com/docs/language/cpp/cpp-stl/
