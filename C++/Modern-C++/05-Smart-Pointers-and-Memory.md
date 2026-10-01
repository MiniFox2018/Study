# 05 · Smart Pointers and Memory Management

## 1. RAII

RAII 的关键不是“只管理内存”，而是把任意资源的生命周期绑定到对象生命周期。

对象构造时获得资源，析构时释放资源，因此：

- 正常 return 会释放；
- 异常栈展开也会释放；
- 不需要在每条退出路径手动 cleanup。

资源可以是：

- 内存
- 文件
- mutex
- socket
- 数据库句柄
- GPU 资源
- OS handle

## 2. 引用计数不是垃圾回收

`shared_ptr` 使用引用计数管理共享所有权，但这不等于 tracing GC。

主要差异：

- 析构时机通常确定；
- 不能自动解决强引用环；
- 所有权语义由代码显式表达。

## 3. std::shared_ptr

`shared_ptr<T>` 允许多个对象共同拥有同一资源。

```cpp
auto p = std::make_shared<Widget>();
auto p2 = p;
```

控制块通常记录：

- strong count
- weak count
- deleter
- allocator 等元数据

当最后一个 strong owner 消失时，目标对象被销毁。

## 4. make_shared

通常优先：

```cpp
auto p = std::make_shared<Foo>(args...);
```

相较直接：

```cpp
std::shared_ptr<Foo> p(new Foo(...));
```

make_shared 往往：

- 语法更安全；
- 一次分配同时容纳对象和控制块；
- 异常安全更容易正确。

## 5. get / reset / use_count

- `get()`：取裸指针，不增加所有权；
- `reset()`：释放当前 shared ownership；
- `use_count()`：查看 strong owner 数量。

不要把 `use_count()` 当作线程同步机制或业务状态判断条件。

## 6. std::unique_ptr

`unique_ptr<T>` 表达唯一所有权。

特点：

- 不可复制；
- 可移动；
- 析构自动 delete；
- 几乎没有额外引用计数成本。

```cpp
auto p = std::make_unique<Foo>();
auto p2 = std::move(p);
```

移动后 p 不再拥有对象。

## 7. make_unique

`std::make_unique` 在 C++14 标准化。

通常优先使用它，而不是直接 new：

```cpp
auto p = std::make_unique<Node>(42);
```

## 8. std::weak_ptr

weak_ptr 是 shared_ptr 控制块的非拥有观察者，不增加 strong count。

主要用途：

- 打破 shared_ptr 强引用环；
- 缓存；
- observer；
- 需要“对象可能已不存在”的弱关联。

weak_ptr 不能直接解引用，需要 `lock()`：

```cpp
if (auto p = weak.lock()) {
    p->work();
}
```

也可以通过 `expired()` 判断对象是否已经销毁。

## 9. 循环引用

若 A 和 B 互相持有 shared_ptr：

```text
A -> B
^    |
|____|
```

即使外部所有 owner 都释放，A/B strong count 仍可能大于零，资源无法销毁。

解决方案是让至少一个方向变成 weak_ptr。

## 10. 所有权设计优先级

通常可按以下思路：

1. 能直接作为值对象，就不要动态分配；
2. 必须动态分配且单一所有者 → unique_ptr；
3. 真正需要共享生命周期 → shared_ptr；
4. 只观察 shared 对象 → weak_ptr；
5. 裸指针/引用尽量表达“non-owning”。

## 11. Rule of Zero

如果成员已经使用 string、vector、unique_ptr 等 RAII 类型，则优先让编译器生成特殊成员函数，不自己写析构/拷贝/移动。

这通常比手工实现 Rule of Five 更安全。

## 核心结论

现代 C++ 的内存管理重点不在“如何 delete”，而在**所有权设计**。  
正确的类型选择应让“谁负责释放资源”从接口本身就能看出来。

## 来源
Modern C++ Tutorial — Chapter 05
