# 03 · Lambda、移动语义与完美转发

## 1. Lambda Expression

Lambda 本质上创建一个匿名闭包对象，用于在局部位置定义行为。

基本结构：

```cpp
[capture](parameters) mutable noexcept -> return_type {
    // body
}
```

### 捕获

- `[]`：不捕获
- `[x]`：按值捕获 x
- `[&x]`：按引用捕获 x
- `[=]`：使用到的外部变量默认按值
- `[&]`：默认按引用

按值捕获在 lambda 创建时保存值；按引用捕获观察外部对象的后续变化，但必须保证对象生命周期足够长。

### Init Capture（C++14）

可以用表达式初始化捕获成员，特别适合移动只可移动对象：

```cpp
auto ptr = std::make_unique<int>(42);

auto f = [p = std::move(ptr)] {
    return *p;
};
```

### Generic Lambda（C++14）

Lambda 参数可以使用 auto：

```cpp
auto add = [](auto a, auto b) {
    return a + b;
};
```

## 2. std::function

不同 callable 类型的具体类型各不相同：普通函数、函数指针、lambda、仿函数。  
`std::function<Signature>` 提供统一的类型擦除包装：

```cpp
std::function<int(int)> op =
    [](int x) { return x * 2; };
```

优点：便于存储和传递不同 callable。  
代价：可能引入额外间接调用、动态分配与类型擦除开销。C++17/20 的 `std::function` 要求存储的目标可复制，不能直接保存捕获 unique_ptr 的只可移动 lambda；空包装被调用会抛出 `std::bad_function_call`。

## 3. std::bind 与 placeholders

`std::bind` 可预绑定部分参数：

```cpp
int calc(int a, int b, int c);

auto f = std::bind(calc,
                   std::placeholders::_1,
                   10,
                   20);
```

现代 C++ 很多场景下 lambda 更直观，但理解 bind 有助于阅读旧式现代 C++ 代码。

## 4. 表达式值类别

现代 C++ 讨论的是“表达式的值类别”，而不是简单把对象分成左值和右值。

三种基础类别：

- **lvalue**：标识对象或函数，且不是 xvalue；不能由该分类推断对象一定长寿，例如已经悬空的引用表达式仍可能是 lvalue；
- **prvalue**：纯右值，通常用于初始化或计算临时值；
- **xvalue**：即将被复用资源的“将亡值”。

更高层分类：
- glvalue = lvalue + xvalue
- rvalue = prvalue + xvalue

## 5. 右值引用

语法：

```cpp
T&& ref = temporary();
```

右值引用允许绑定到右值，并支持资源转移。  
注意：**有名字的右值引用变量表达式本身是 lvalue**。

## 6. std::move

`std::move` 不执行移动，它只是进行值类别转换，使对象能够匹配移动构造/移动赋值。

```cpp
std::string s = "large data";
std::vector<std::string> v;
v.push_back(std::move(s));
```

标准库类型通常保证移动后的对象有效但值未指定，除非该类型另有更强约定；自定义类型则由其接口契约决定。有效不代表可以无条件调用有前置条件的操作，例如不能假设移动后的 vector 非空并调用 `front()`。

## 7. Move Semantics

资源类可通过移动构造把资源所有权转交给新对象，而无需深拷贝：

```cpp
Resource(Resource&& other) noexcept
    : handle(other.handle) {
    other.handle = nullptr;
}
```

移动语义尤其适用于 string、vector、unique_ptr 以及大型资源对象。

## 8. Reference Collapsing

模板和类型别名中的引用组合遵循：

- `T&  + &  -> T&`
- `T&  + && -> T&`
- `T&& + &  -> T&`
- `T&& + && -> T&&`

这是 forwarding reference 工作的基础。

## 9. Perfect Forwarding

模板参数 `T&&` 在满足推导条件时可成为 forwarding reference。使用 `std::forward<T>` 保留调用者传入的原始值类别：

```cpp
template<class F, class... Args>
decltype(auto) invoke(F&& f, Args&&... args) {
    return std::forward<F>(f)(
        std::forward<Args>(args)...);
}
```

`std::move` 无条件转成右值；`std::forward` 按模板推导结果有条件地恢复原值类别。

## 10. Guaranteed Copy Elision（C++17）

C++17 在部分 prvalue 初始化场景中保证直接构造目标对象，不再先创建临时对象再移动/复制。

因此下面这种工厂式返回甚至可以用于不可复制、不可移动类型：

```cpp
struct Token {
    Token() = default;
    Token(const Token&) = delete;
    Token(Token&&) = delete;
};

Token make_token() {
    return Token{};
}
```

## 核心结论

运行时增强的核心链路是：

**lambda → callable 抽象 → 值类别 → 右值引用 → 移动语义 → 完美转发 → 更高效的对象生命周期。**

## 来源
Modern C++ Tutorial — Chapter 03

## 小实验：有名字的右值引用仍是左值

```cpp
#include <iostream>
#include <utility>
void show(int&) { std::cout << "左值\n"; }
void show(int&&) { std::cout << "右值\n"; }
int main() {
    int&& reference = 7;
    show(reference);
    show(std::move(reference));
}
```

输出 `左值`、`右值`。`std::move` 改变传参表达式的类别，没有在这里搬运任何资源。

自测：lambda `[=]` 访问成员时是否复制整个对象？答：在 C++17/20 中隐式捕获 `this` 时保存的是指针（C++20 已弃用 `[=]` 隐式捕获 this 的写法），不延长对象生命；需要对象副本可明确用 C++17 `[*this]`，同时考虑复制成本。
