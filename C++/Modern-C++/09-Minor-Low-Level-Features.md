# 09 · 低层特性与对象表示

## 1. long long

C++11 正式把 `long long int` 纳入标准，保证它至少具有 64 位宽度。

如果代码依赖**精确位宽**，更推荐：

```cpp
#include <cstdint>

std::int64_t x;
std::uint64_t y;
```

而不是假设某个平台的 long 或 long long 具体大小。精确位宽类型只在实现支持相应类型时提供；例如 `int64_t` 不是对所有可能平台的无条件保证。

## 2. noexcept

C++11 用 `noexcept` 取代旧式异常规范的主要用途。

```cpp
void may_throw();
void never_throw() noexcept;
```

如果异常逃出 noexcept 函数，程序调用 `std::terminate`。

## 3. noexcept operator

`noexcept(expr)` 是编译期查询表达式：

```cpp
static_assert(noexcept(foo()));
```

它常用于：

- 泛型代码；
- 条件 noexcept；
- 移动构造/交换操作；
- 类型 traits 风格判断。

例如：

```cpp
template<class T>
void wrapper(T&& value)
    noexcept(noexcept(process(std::forward<T>(value))))
{
    process(std::forward<T>(value));
}
```

## 4. noexcept 与移动语义

标准容器在重新分配元素时，通常更愿意使用保证不抛异常的移动构造。

因此资源类型常写：

```cpp
Widget(Widget&&) noexcept = default;
```

前提是该移动操作确实不会抛异常。

## 5. Raw String Literal

普通字符串中大量 `\`、引号或正则表达式会产生很多转义。

C++11 raw string：

```cpp
auto path = R"(C:\Path\To\File)";
auto regex = R"([a-z]+\.txt)";
```

实际上 raw string 中的字符按原始文本处理，尤其适合：

- 正则表达式；
- JSON/XML/HTML 片段；
- SQL；
- Windows 路径；
- 多行文本。

## 6. User-Defined Literals

C++11 支持用户自定义字面量后缀。

```cpp
constexpr long double operator"" _km(long double x) {
    return x * 1000.0L;
}

auto distance = 2.5_km;
```

可以作为单位接口入口，但本例仍返回 `long double`，本身不会阻止米和秒混用；真正的单位类型安全需要返回不同的包装类型。常见用途：

- 单位系统；
- 时间；
- 大小；
- 领域值类型。

自定义后缀通常应以下划线开头，避免与标准库保留命名冲突。

## 7. alignof

`alignof(T)` 查询类型对齐要求：

```cpp
std::cout << alignof(double);
```

结果类型为 `std::size_t`。

## 8. alignas

`alignas` 指定更严格的对齐：

```cpp
struct alignas(64) CacheLineData {
    int value;
};
```

常见用途：

- SIMD；
- cache line 隔离；
- 硬件接口；
- lock-free 数据结构；
- 特殊 allocator。

## 9. Over-Aligned Allocation（C++17）

C++17 对 over-aligned type 的动态分配提供标准支持。  
对于：

```cpp
struct alignas(64) Block {
    double data[8];
};
```

普通 new 能选择相应 aligned allocation 机制。

## 10. Strict Aliasing

通过不兼容类型指针直接重新解释对象：

```cpp
float f = 3.14f;
auto bits = *reinterpret_cast<std::uint32_t*>(&f);
```

可能违反 strict-aliasing 规则，产生未定义行为。

`reinterpret_cast` 能通过编译不代表访问语义合法。

## 11. std::memcpy

传统标准中，如果需要读取对象 representation，可使用 memcpy：

```cpp
static_assert(sizeof(float) == sizeof(std::uint32_t));
std::uint32_t bits{};
std::memcpy(&bits, &f, sizeof(bits));
```

编译器通常能优化掉实际复制。

## 12. std::bit_cast（C++20）

C++20 提供更直接的类型安全 representation cast：

```cpp
#include <bit>

auto bits = std::bit_cast<std::uint32_t>(f);
```

基本约束：

- 源类型和目标类型大小相同；
- 满足 trivially copyable 等要求。

它表达的是**对象表示重解释**，不是普通数值转换。

## 13. 数学特殊函数（C++17）

`<cmath>` 增加多种特殊函数，例如：

- `std::riemann_zeta`
- `std::beta`
- `std::assoc_legendre`
- `std::cyl_bessel_j`

它们面向科学计算和工程计算。

使用时要检查具体标准库实现的支持程度，语言标准包含某功能不代表所有旧工具链均已完整实现。

## 14. 低层代码原则

- 不依赖未定义行为“碰巧工作”；
- 区分数值转换和 representation 转换；
- 对齐要求必须来自真实数据结构/硬件需求；
- 精确位宽使用 `<cstdint>`；
- 优先标准语言设施，而不是平台专用 hack；
- 用 sanitizer 验证边界、对齐、生命周期问题。

## 来源
Modern C++ Tutorial — Chapter 09

## 小实验：数值转换与表示转换

```cpp
#include <bit>
#include <cstdint>
#include <iostream>
#include <limits>
int main() {
    static_assert(sizeof(float) == sizeof(std::uint32_t));
    static_assert(std::numeric_limits<float>::is_iec559);
    const float value = 1.0f;
    std::cout << static_cast<std::uint32_t>(value) << '\n';
    std::cout << std::hex << std::bit_cast<std::uint32_t>(value) << '\n';
}
```

在这里约束的常见 IEEE 754 binary32 平台上，C++20 输出 `1` 与 `3f800000`。`static_cast` 转数值，`bit_cast` 复制表示。一般情况下还必须确保目标位模式表示合法值；bit_cast 不等于“任意位都能变成可用对象”。

自测：`alignas(64)` 是否证明避免了所有 false sharing？答：不能，它只要求对齐；缓存行尺寸、对象布局和相邻对象分配仍须实测。
