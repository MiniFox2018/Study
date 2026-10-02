# 13 · 内存管理与对象生命周期

## 栈与堆
### 自动存储期
局部自动对象通常由作用域控制生命周期，常实现于栈上。创建与销毁开销较低，生命周期清晰。

### 动态存储期
动态对象的生命周期由程序控制，传统方式使用 `new/delete`；现代 C++ 更推荐智能指针、容器和 RAII。

## 内存泄漏
常见原因包括：
- `new` 后未对应 `delete`
- 异常或提前返回绕过释放逻辑
- 覆盖仍需释放的唯一地址
- `shared_ptr` 循环引用

优先使用 RAII、智能指针、标准容器以及 AddressSanitizer、Valgrind 等工具发现问题。

## C++ 与垃圾回收
标准 C++ 不依赖类似 Java/C# 的强制追踪式垃圾回收。资源通常通过确定性析构、RAII 和所有权类型管理，因此资源释放时机更加可控。

## RAII
Resource Acquisition Is Initialization：把资源生命周期绑定到对象生命周期。

RAII 不仅用于内存，还适用于：
- 文件句柄
- socket
- mutex
- 数据库事务
- GPU/系统资源

`std::vector`、`std::string`、`std::unique_ptr`、`std::lock_guard` 都体现了 RAII 思想。

## 移动语义
C++11 通过右值引用与移动语义减少不必要的资源复制。

关键概念：
- lvalue / rvalue
- `T&&`
- move constructor
- move assignment
- `std::move`

`std::move` 本身不会执行资源移动，它只是把表达式转换成可供移动操作处理的值类别。

## 拷贝与移动规则
资源管理类型应理解：
- Rule of Three
- Rule of Five
- Rule of Zero

现代设计通常优先 Rule of Zero：让标准库成员自动完成资源管理。

## Copy Elision
编译器可以省略临时对象的复制或移动。C++17 对部分场景提供保证的复制消除。返回局部对象时通常直接 `return obj;`，不应为了“优化”而随意写 `std::move(obj)`，否则可能妨碍 NRVO。

## 所有权设计
- 单一所有权：`std::unique_ptr`
- 共享所有权：`std::shared_ptr`
- 非拥有观察：引用、裸指针或 `std::weak_ptr`

接口应尽量让所有权关系清晰可见。

## 小实验：资源随作用域释放

```cpp
#include <iostream>
#include <memory>
struct Item {
    ~Item() { std::cout << "释放\n"; }
};
int main() {
    auto first = std::make_unique<Item>();
    auto second = std::move(first);
    std::cout << std::boolalpha << (first == nullptr) << '\n';
}
```

输出 `true` 后输出一次 `释放`。移动使 `second` 获得独占所有权；`first` 为空，不能再解引用。作用域结束时 `second` 自动销毁对象。

自测：`std::move` 总能避免复制吗？答：不能。若类型没有适用的移动操作，或对象为 `const` 而移动构造需要非 const 右值引用，仍可能复制。标准库对象通常移动后有效但值未指定，具体类型可能有更强保证（如 unique_ptr 变空）。

## 参考
https://www.compilenrun.com/docs/language/cpp/cpp-memory-management/
