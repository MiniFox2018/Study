# 02 · 类型推导与编译期表达

本章聚焦编译期和编码阶段的语言易用性增强。

## 1. nullptr

C++11 引入 `nullptr`，解决 `NULL` 被实现成整数 0 时的重载歧义。

```cpp
void f(int);
void f(char*);

f(0);        // int
f(nullptr);  // char*
```

`nullptr` 的类型为 `std::nullptr_t`，可转换为任意指针或成员指针类型。

## 2. constexpr

`constexpr` 用于声明可以参与常量表达式求值的对象或函数。

```cpp
constexpr int square(int x) {
    return x * x;
}

constexpr int n = square(8);
```

C++14 放宽了 constexpr 函数限制，可在函数体中使用更多局部变量、循环和分支。

## 3. if / switch 初始化语句（C++17）

C++17 允许在条件前创建局部对象，把临时变量的作用域限制在分支内部：

```cpp
if (auto it = m.find(key); it != m.end()) {
    // it 只在 if / else 范围中存在
}
```

这对于迭代器、锁、解析结果等临时对象很有价值。

## 4. initializer_list 与统一初始化

C++11 使用花括号形成统一初始化语法，并提供 `std::initializer_list` 让自定义类型接收列表参数。

```cpp
std::vector<int> v{1, 2, 3};

class Numbers {
public:
    Numbers(std::initializer_list<int> xs);
};
```

列表初始化还能帮助阻止部分窄化转换。

## 5. Structured Bindings（C++17）

结构化绑定可直接解包 tuple、pair、数组和满足条件的聚合类型：

```cpp
auto [name, score] = record;

for (const auto& [key, value] : table) {
    // ...
}
```

它替代了大量 `first/second`、`std::get<N>` 或 `std::tie` 样板代码。

## 6. auto

C++11 重新定义 `auto` 为类型推导工具：

```cpp
auto it = container.begin();
auto value = compute();
```

使用原则：当类型从右侧已经明显、或完整类型非常冗长时使用；若隐藏类型会降低可读性，则显式写出类型。

## 7. decltype

`decltype(expr)` 根据表达式推导类型，常用于泛型代码、返回类型和 traits。

```cpp
int x = 1;
double y = 2.0;
decltype(x + y) result = 0.0;
```

它与 `auto` 的区别是：auto 根据初始化规则推导，而 decltype 精确查询表达式类型。

## 8. Trailing Return Type

C++11 支持把返回类型写在参数之后：

```cpp
template<class T, class U>
auto add(T a, U b) -> decltype(a + b) {
    return a + b;
}
```

C++14 后普通函数和函数模板很多场景可直接用 `auto` 推导返回类型。

## 9. decltype(auto)

C++14 的 `decltype(auto)` 使用 decltype 规则推导，可保留引用属性：

```cpp
decltype(auto) lookup() {
    return get_reference();
}
```

这在包装函数、转发函数中特别重要。

## 10. if constexpr（C++17）

`if constexpr` 在编译期选择分支。在模板实例化时，条件已不再依赖模板参数的未选分支不被实例化；它仍须能被解析，非模板上下文也不能用它屏蔽任意语义错误：

```cpp
template<class T>
auto normalize(T v) {
    if constexpr (std::is_integral_v<T>)
        return v + 1;
    else
        return v + 0.5;
}
```

它显著简化了过去依赖 SFINAE 的部分模板逻辑。

## 11. Range-based for

C++11 范围循环把“迭代器三件套”压缩为直接遍历：

```cpp
for (const auto& x : values) {
    // read
}

for (auto& x : values) {
    // modify
}
```

自定义类型只要能提供合适的 begin/end 机制，也可以参与范围循环。

## 12. 模板语言增强

### Extern Template
可控制模板实例化，减少多个翻译单元重复实例化带来的编译成本。

### 嵌套模板的 `>>`
C++11 起可以直接写：

```cpp
std::vector<std::vector<int>> matrix;
```

### Alias Templates
`using` 可为模板建立别名：

```cpp
template<class T>
using StringMap = std::map<std::string, T>;
```

### Variadic Templates
支持任意数量模板参数：

```cpp
template<class... Ts>
void log(Ts&&... xs);
```

`sizeof...(Ts)` 可获取参数包元素数量。

### Fold Expressions（C++17）
对参数包直接折叠：

```cpp
template<class... Ts>
auto sum(Ts... xs) {
    return (xs + ...);
}
```

### 非类型模板参数推导（C++17）
可用 `auto` 让编译器推导非类型参数：

```cpp
template<auto V>
struct Constant {};
```

### SFINAE 与 enable_if
“Substitution Failure Is Not An Error”：模板参数替换在规定的直接上下文中失败时，可将候选移出重载集合。函数体里的任意错误不都受此保护，不能把 SFINAE 当通用错误吞掉机制。

```cpp
template<class T,
         class = std::enable_if_t<std::is_integral_v<T>>>
void process(T);
```

C++20 concepts 是更直接、可读性更好的替代方式。

## 13. 面向对象增强

### Delegating Constructor
同一类中的构造函数可委托给另一个构造函数。

### Inheriting Constructor
派生类可通过 `using Base::Base;` 继承基类构造函数。

### override / final
`override` 让编译器检查是否真的覆盖虚函数；`final` 阻止继续覆盖或继承。

### = default / = delete
明确控制特殊成员函数：

```cpp
Widget() = default;
Widget(const Widget&) = delete;
```

### enum class
强类型枚举避免枚举值污染外层作用域，也不再隐式转换成整数。

## 14. C++17 其他语言增强

- inline variables：头文件中定义变量而不违反 ODR；
- nested namespace：`namespace a::b::c {}`；
- constexpr lambda；
- 单参数 `static_assert(condition)`；
- 聚合初始化规则放宽；
- `std::conjunction` / `disjunction` / `negation`；
- 预处理器 `__has_include`。

## 核心结论

语言易用性的主线是：**减少样板代码，同时增加编译期检查和作用域控制。**

## 来源
Modern C++ Tutorial — Chapter 02

## 小实验：auto 的复制和 decltype 的引用

```cpp
#include <iostream>
#include <type_traits>
int main() {
    int value = 3;
    auto copy = value;
    decltype((value)) alias = value;
    static_assert(std::is_same_v<decltype(alias), int&>);
    alias = 8;
    std::cout << copy << ' ' << value << '\n';
}
```

C++17 输出 `3 8`。`decltype(value)` 特殊地取得声明类型 `int`，`decltype((value))` 按左值表达式规则得到 `int&`。因此用 `decltype(auto)` 返回 `(local)` 可能意外返回悬空引用，不能只凭“保留类型更精确”就选择它。

自测：`sum()` 用空参数包调用本章一元 `+` 折叠能成功吗？答：不能，一元加法折叠没有空包恒等值；若语义允许，可用 `(0 + ... + xs)` 指定初值。
