# 15 · 现代 C++ 常用特性

## auto
`auto` 根据初始化表达式推导类型，适合复杂迭代器、泛型代码和类型显而易见的局部变量。

普通 `auto` 会忽略部分顶层 const 和引用属性；需要保持引用或只读语义时使用 `auto&`、`const auto&`。

## nullptr
`nullptr` 是专门的空指针字面量，优于 `NULL` 和整数 0，可减少重载解析歧义。

## Range-based for
```cpp
for (const auto& item : items) {
    // ...
}
```

大型对象只读遍历通常使用 `const auto&`；需要修改元素时使用 `auto&`。

## Lambda
Lambda 支持局部闭包、捕获、泛型参数，并能与 STL 算法自然组合。引用捕获时必须特别注意对象生命周期。

## Variadic Templates
可变参数模板允许模板接受任意数量的参数，是 tuple、转发、格式化等泛型设施的重要基础。C++17 可结合 fold expressions 简化参数包处理。

## Rvalue References
`T&&` 支持移动语义和完美转发。模板中的 forwarding reference 通常配合 `std::forward` 保留参数原始值类别。

## constexpr
`constexpr` 允许表达式和函数在条件满足时于编译期求值，可用于常量计算、查表和编译期逻辑。

## Uniform Initialization
花括号初始化统一了多种初始化形式，并能阻止部分窄化转换。

```cpp
int x{42};
std::vector<int> v{1, 2, 3};
```

## Delegating Constructors
一个构造函数可以委托给同类的另一个构造函数，从而减少重复的初始化代码。

## override / final
- `override`：要求编译器确认函数确实覆写基类虚函数
- `final`：禁止继续覆写虚函数或继承某个类

它们既能表达设计意图，也能提前发现签名错误。

## Type Traits
`<type_traits>` 提供编译期类型查询与转换，例如：
- `std::is_same`
- `std::is_integral`
- `std::remove_reference`
- `std::decay`

它们是泛型编程和模板约束的重要基础。

## optional
`std::optional<T>`（C++17）表示“可能存在一个 T”，适合替代部分哨兵值或可空返回约定。

## variant
`std::variant<A, B, ...>` 是类型安全的 tagged union，可通过 `std::get`、`std::get_if` 和 `std::visit` 访问。

## any
`std::any` 可以保存任意可复制类型，并通过 `std::any_cast` 取回。它很灵活，但会弱化编译期类型信息，应在确有需要时使用。

## 现代 C++ 总体方向
- 自动资源管理
- 更强类型安全
- 减少裸 `new/delete`
- 减少 C 风格转换
- 更多编译期检查
- 标准库优先
- 值语义与移动语义
- 用类型明确表达状态和所有权

## 小实验：用 optional 表达未找到

```cpp
#include <iostream>
#include <optional>
#include <vector>
std::optional<int> first_even(const std::vector<int>& values) {
    for (int x : values) if (x % 2 == 0) return x;
    return std::nullopt;
}
int main() {
    if (auto result = first_even({1, 3, 4, 6}); result) {
        std::cout << *result << '\n';
    }
    std::cout << first_even({1, 3}).value_or(-1) << '\n';
}
```

C++17 输出 `4` 与 `-1`。接口自身用“有值/无值”区分状态，`-1` 只是这里的显示兜底；访问前必须检查是否有值。

自测：`std::vector<int> a(3, 7)` 与 `b{3, 7}` 相同吗？答：不同，前者三个 7，后者两个元素 3、7。花括号不是所有构造函数的等价替代。

## 参考
https://www.compilenrun.com/docs/language/cpp/cpp-modern-features/
