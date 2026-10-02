# 05 · 指针、引用与所有权

## 指针基础
指针保存对象地址。常用操作：`&obj` 取地址、`*ptr` 解引用、`nullptr` 表示空指针。解引用空指针、悬空指针或非法地址属于未定义行为。

```cpp
int value = 42;
int* p = &value;
*p = 100;
```

## 指针算术
指向数组元素的指针可以进行加减、自增自减，移动单位自动按元素大小缩放。只有同一数组对象及尾后一位置范围内的运算才有规范意义。

## 指针与数组
数组名在很多表达式中会退化为首元素指针，因此 `arr[i]` 与 `*(arr+i)` 语义相关，但数组本身并不等于指针，`sizeof` 等场景会体现差异。

## 指针参数
指针参数可用于修改调用者对象、表达“可能为空”或处理连续内存。接口应明确是否可空、是否拥有对象、有效长度和生命周期。

## 引用
引用是已有对象的别名。普通引用必须初始化，不能重新绑定；`const T&` 常用于高效只读传参。

## 动态内存
传统方式使用 `new/delete` 和 `new[]/delete[]`，必须严格配对。现代 C++ 更推荐容器和 RAII，减少手工管理。

## 智能指针
- `std::unique_ptr`：独占所有权，优先默认选择
- `std::shared_ptr`：共享所有权，引用计数
- `std::weak_ptr`：非拥有观察，常用于打破 shared_ptr 环
优先使用 `make_unique` 和 `make_shared` 创建对象。

## 安全重点
避免野指针、悬空指针、double delete、数组越界、所有权不明确和 shared_ptr 循环引用。

## 小实验：观察者不拥有资源

```cpp
#include <iostream>
#include <memory>
int main() {
    auto owner = std::make_unique<int>(42);
    int* observer = owner.get();
    *observer += 1;
    std::cout << *owner << '\n';
    owner.reset();
    observer = nullptr; // 已无有效对象，后续不再解引用
}
```

输出 `43`。`get()` 返回观察指针，没有转移所有权；不能对 `observer` 调用 `delete`。`reset()` 后旧地址成为悬空指针，即使地址数值没有变化，也不能使用。

自测：数组尾后指针能做什么？答：可作迭代终点、在合法范围内参与运算，不能解引用。检查非空也不能证明指针未悬空。

## 参考
https://www.compilenrun.com/docs/language/cpp/cpp-pointers/
