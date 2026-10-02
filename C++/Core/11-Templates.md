# 11 · 模板与泛型

## 函数模板
模板让算法脱离具体类型，编译器在实际使用时实例化。

```cpp
template <typename T>
T maxValue(const T& a, const T& b) {
    return a < b ? b : a;
}
```

## 类型推导
函数模板通常可根据实参推导模板参数，也可以显式指定。混合类型可能产生推导失败或额外转换。

## 多模板参数与默认参数
模板可同时声明多个类型参数，也能设置默认模板参数。

## 类模板
用于建立泛型容器和组件，标准库中的 `vector<T>`、`optional<T>` 都属于此类思想。

## 特化
- 全特化：为具体参数组合提供独立实现
- 偏特化：类模板可针对一类参数模式定制
函数模板的类似需求通常更适合通过重载实现。

## 非类型模板参数
模板参数也可以是编译期值，例如 `std::array<int, 16>` 中的 16。

## 模板元编程
可在编译期进行计算和类型转换。传统技术包括递归模板和 SFINAE，现代 C++ 更常结合 constexpr、type traits、if constexpr 和 C++20 concepts。

## 约束与诊断
模板错误往往在实例化时出现。设计时要明确类型必须支持哪些操作，避免“过度泛型”。

## 定义位置
模板定义通常必须在实例化点可见，因此常放在头文件中；显式实例化可作为另一种组织方式。

## 小实验：模板实例化与类型边界

```cpp
#include <iostream>
#include <string>
template<class T>
T max_value(const T& a, const T& b) {
    return a < b ? b : a;
}
int main() {
    std::cout << max_value(2, 5) << '\n';
    std::cout << max_value(std::string("apple"), std::string("pear")) << '\n';
}
```

输出 `5` 与 `pear`。这要求 `T` 可比较、可构造返回值；`std::string` 使用字典序，而不是字符串长度。

自测：`max_value(2, 3.5)` 为什么不能直接调用？答：同一个 `T` 同时被推导成 `int` 和 `double`，推导冲突。可明确选择共同类型，例如 `max_value<double>(2, 3.5)`，同时接受转换的语义。

## 参考
https://www.compilenrun.com/docs/language/cpp/cpp-templates/
