# 07 · 常用数据结构

## struct
C++ 中 struct 与 class 能力接近，主要差异是成员和继承的默认访问级别：struct 默认 public，class 默认 private。struct 常用于轻量数据对象。

## union
多个成员共享同一块存储，同一时刻通常只有一个活动成员。现代代码需要安全“多选一”类型时可优先考虑 `std::variant`。

## enum
传统 enum 与强类型 `enum class`。现代 C++ 更推荐 enum class，因为作用域明确且不会轻易隐式转整数。

## 链表
节点通过指针连接。单链表只有 next，双链表同时有 prev 和 next。优点是局部插入删除方便；缺点是随机访问慢、缓存局部性差且有额外指针开销。

## 栈
LIFO，核心操作 push、pop、top。典型应用：表达式求值、括号匹配、DFS、撤销。

## 队列
FIFO，核心操作 push、pop、front。常见应用：任务调度、BFS、生产者消费者。

## 树
理解根、父子、叶节点、深度、高度和遍历。二叉树常见前序、中序、后序；二叉搜索树性能与平衡程度相关。

## 图
由顶点和边组成，可分有向/无向、加权/无权。常见表示为邻接矩阵和邻接表；常见遍历为 BFS 和 DFS，并可扩展到最短路、拓扑排序、连通性分析。

## 哈希表
通过哈希函数把键映射到桶。平均查找/插入/删除接近 O(1)，需关注哈希质量、冲突、装载因子和 rehash。STL 对应 unordered_map/unordered_set。

## 结构选择
选择数据结构时不仅看复杂度，还要看访问模式、缓存局部性、内存开销和数据规模。

## 小实验：括号匹配为什么用栈

```cpp
#include <iostream>
#include <stack>
#include <string_view>
bool balanced(std::string_view text) {
    std::stack<char> pending;
    for (char c : text) {
        if (c == '(') pending.push(c);
        else if (c == ')') {
            if (pending.empty()) return false;
            pending.pop();
        }
    }
    return pending.empty();
}
int main() {
    std::cout << std::boolalpha << balanced("(())") << ' '
              << balanced(")(") << '\n';
}
```

输出 `true false`。最后出现的左括号应最先被匹配，所以用后进先出的栈。每个字符最多进出栈一次，时间 O(n)、最坏额外空间 O(n)。这里只处理圆括号，其他字符忽略。

自测：左右括号总数相同就足够吗？答：不够，`)(` 在前缀阶段已不合法；结构选择来自操作约束，而非只看总计数。

## 参考
https://www.compilenrun.com/docs/language/cpp/cpp-advanced-data-structures/
