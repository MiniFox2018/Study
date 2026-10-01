# Modern C++ 学习笔记

本目录根据 **Modern C++ Tutorial: C++11/14/17/20 On the Fly** 整理，用于补充主目录中的基础 C++ 笔记。

> 原书作者：Changkun Ou  
> PDF 版本：Last update: June 7, 2026  
> 原书许可：CC BY-NC-ND 4.0  
> 原书提示 PDF 可能不是最新版本，应以其网站或 GitHub 上的最新内容为准。  
> 本目录为重新归纳的学习笔记，不复制原书正文。

## 目录

1. [Towards Modern C++](./01-Towards-Modern-Cpp.md)
2. [Language Usability Enhancements](./02-Language-Usability.md)
3. [Language Runtime Enhancements](./03-Runtime-Enhancements.md)
4. [Modern Containers](./04-Containers.md)
5. [Smart Pointers and Memory Management](./05-Smart-Pointers-and-Memory.md)
6. [Regular Expressions](./06-Regular-Expressions.md)
7. [Parallelism, Concurrency and Memory Model](./07-Concurrency-and-Memory-Model.md)
8. [Filesystem](./08-Filesystem.md)
9. [Minor and Low-Level Features](./09-Minor-Low-Level-Features.md)
10. [C++20](./10-Cpp20.md)
11. [Modern C++ Best Practices](./11-Best-Practices.md)

## 与主目录的关系

这一组笔记重点放在 **C++98 → C++11/14/17/20 的演进**。与主目录中 Templates、STL、Memory Management、Multithreading、Modern Features 等章节有交叉，但这里按照“现代 C++ 特性演进”重新组织，保留更完整的上下文。

## 主题速查

### C++11
- `nullptr`
- `constexpr`
- initializer_list
- `auto` / `decltype`
- range-based for
- alias templates / variadic templates / SFINAE
- delegating/inheriting constructors
- `override` / `final` / `=default` / `=delete`
- enum class
- lambda
- `std::function` / `std::bind`
- rvalue references / move semantics / perfect forwarding
- `std::array` / `forward_list` / unordered containers / tuple
- smart pointers
- regex
- thread / mutex / future / condition_variable / atomic
- `noexcept`
- raw/custom literals
- `alignof` / `alignas`

### C++14
- relaxed `constexpr`
- generic lambda
- function return type deduction
- `decltype(auto)`
- `std::make_unique`
- index_sequence 等模板工具

### C++17
- if/switch initializer
- structured bindings
- `if constexpr`
- fold expressions
- non-type template parameter deduction
- inline variables
- nested namespaces
- constexpr lambda
- single-argument static_assert
- aggregate rule improvements
- boolean type-trait metafunctions
- `__has_include`
- guaranteed copy elision
- `string_view` / `byte`
- associative container improvements
- `std::pmr`
- `filesystem`
- over-aligned allocation
- mathematical special functions

### C++20
- concepts
- modules
- ranges
- coroutines
- `std::bit_cast`
- `std::endian`

## 来源
Modern C++ Tutorial: C++11/14/17/20 On the Fly — Changkun Ou
