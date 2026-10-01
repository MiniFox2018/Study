# 11 · Modern C++ Best Practices

## 1. 工具链

### 编译器警告

开发阶段建议至少开启：

```bash
-Wall -Wextra -Wpedantic
```

在合适的 CI / 项目环境中可考虑：

```bash
-Werror
```

目标是避免警告长期累积，而不是机械追求“所有场景必须 Werror”。

## 2. Sanitizers

### AddressSanitizer
发现：

- heap/stack buffer overflow
- use-after-free
- 部分内存错误

```bash
-fsanitize=address
```

### UndefinedBehaviorSanitizer
发现多类 undefined behavior：

```bash
-fsanitize=undefined
```

### ThreadSanitizer
发现 data race：

```bash
-fsanitize=thread
```

不同 sanitizer 未必能同时组合运行，具体依工具链而定。

## 3. 自动格式与静态分析

常用工具：

- `clang-format`
- `clang-tidy`

format 解决风格一致性；tidy 更偏 bug pattern、modernization 与静态检查。

## 4. Build System 与包管理

现代项目应追求可重复构建。

常见组合：

- CMake
- vcpkg
- Conan

项目中应明确：

- 编译器版本；
- C++ standard；
- 依赖版本；
- feature options；
- build type；
- test configuration。

## 5. Compiler Explorer

Compiler Explorer 适合快速验证：

- 不同编译器行为；
- 标准版本差异；
- optimizer 输出；
- assembly；
- 模板实例化和 ABI 现象。

它是实验工具，不替代真实项目 benchmark。

## 6. Coding Style

风格选择本身不如一致性重要。

重点包括：

- 命名一致；
- include 规则一致；
- brace/format 统一；
- ownership 表达一致；
- error handling 一致。

## 7. Const Correctness

能 const 就 const，包括：

- 局部变量；
- 参数；
- 成员函数；
- 引用；
- view。

const 能帮助：

- 表达接口契约；
- 降低修改范围；
- 支持更多调用场景；
- 让编译器参与检查。

## 8. auto 的边界

auto 适合减少冗长重复：

```cpp
auto it = container.begin();
```

但如果 RHS 无法让读者快速推断实际语义，就应显式类型。

auto 是可读性工具，不是“隐藏所有类型”的目标。

## 9. 优先标准库

优先：

- `std::string`
- `std::vector`
- `std::array`
- `std::span`
- algorithms
- filesystem
- thread/chrono

而不是重复手写：

- 动态数组；
- 字符串类；
- 排序；
- 智能指针；
- 平台专用文件系统封装。

## 10. Measure Before Optimize

正确流程：

1. 正确性；
2. benchmark；
3. profiler；
4. 确认热点；
5. 优化；
6. 再测。

不要根据直觉优化冷路径。

## 11. 避免无意义复制

常见方式：

- 大对象只读参数用 `const T&`；
- 需要拥有副本时可考虑 pass-by-value + move；
- 容器提前 `reserve()`；
- 返回对象依赖 copy elision；
- 只读文本参数考虑 string_view。

## 12. std::move 的正确理解

`std::move` 是 cast，不是“移动动作”。

移动真正发生在：

- move constructor；
- move assignment；
- 接收右值引用并窃取资源的操作。

不要为了“看起来更快”在所有 return 中加 std::move。

## 13. RAII 管理所有资源

RAII 应覆盖：

- memory
- file
- lock
- socket
- handle
- transaction

只要存在 acquire/release 对，就应优先考虑封装到对象生命周期。

## 14. Smart Pointer

优先级通常：

1. value object
2. unique_ptr
3. shared_ptr
4. weak_ptr
5. non-owning raw pointer/reference

裸指针不是问题本身，**不明确的 ownership** 才是问题。

## 15. Undefined Behavior

重点避免：

- 越界；
- use-after-free；
- signed overflow；
- dangling reference；
- strict-aliasing violation；
- invalid shift；
- data race；
- 解引用 null/invalid pointer。

优化编译器会利用“UB 不会发生”的假设，因此 UB 不能靠“测试时没崩”判断安全。

## 16. 边界安全

当边界重要时优先：

- `std::array`
- `std::span`
- `.at()`
- range
- 明确 size

而不是只传裸指针却没有长度信息。

## 17. Named Casts

优先：

- `static_cast`
- `dynamic_cast`
- `const_cast`
- `reinterpret_cast`

避免 C-style cast，因为它把多种完全不同的转换语义隐藏在同一个语法里。

## 18. 可维护性

- 函数保持单一职责；
- 优先标准算法表达意图；
- API 应尽量 hard to misuse；
- 用 enum class/strong type 代替神秘 int/bool flag；
- 自动化测试；
- 注释解释“为什么”，而不是逐行翻译代码。

## 19. 可移植性

若位宽重要：

```cpp
std::int32_t
std::uint64_t
```

不要假设：

- int 必然 32 位；
- char 必然 signed；
- endian 固定；
- long 的位宽固定。

## 20. std::endian（C++20）

字节序敏感代码可查询：

```cpp
#include <bit>

if constexpr (std::endian::native == std::endian::little) {
    // ...
}
```

不要根据 CPU 名称或平台宏随意猜测。

## 21. 平台差异隔离

如果必须调用：

- POSIX API；
- Win32 API；
- 特殊 SIMD；
- OS-specific file/socket API；

应将平台依赖隔离在小型 adapter 层，而不是扩散到业务代码。

## 22. 一条总原则

现代 C++ 最重要的工程方向可以压缩为：

> **让类型系统、对象生命周期、标准库和工具链承担更多正确性工作，让人工记忆承担更少。**

## 来源
Modern C++ Tutorial — Appendix 2
