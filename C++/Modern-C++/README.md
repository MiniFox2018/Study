# Modern C++ 学习笔记

本目录根据 **Modern C++ Tutorial: C++11/14/17/20 On the Fly** 整理，用于补充主目录中的基础 C++ 笔记。

> 原书作者：Changkun Ou  
> PDF 版本：Last update: June 7, 2026  
> 原书许可：CC BY-NC-ND 4.0  
> 原书提示 PDF 可能不是最新版本，应以其网站或 GitHub 上的最新内容为准。  
> 本目录为重新归纳的学习笔记，不复制原书正文。

## 目录

1. [现代 C++ 的目标与迁移](./01-Towards-Modern-Cpp.md)
2. [类型推导与编译期表达](./02-Language-Usability.md)
3. [Lambda、移动语义与完美转发](./03-Runtime-Enhancements.md)
4. [现代容器与非拥有视图](./04-Containers.md)
5. [智能指针与内存管理](./05-Smart-Pointers-and-Memory.md)
6. [正则表达式](./06-Regular-Expressions.md)
7. [并发、同步与内存模型](./07-Concurrency-and-Memory-Model.md)
8. [文件系统](./08-Filesystem.md)
9. [低层特性与对象表示](./09-Minor-Low-Level-Features.md)
10. [C++20 特性与适用边界](./10-Cpp20.md)
11. [现代 C++ 工程实践](./11-Best-Practices.md)

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

## 先后顺序与版本边界

先完成 Core 的函数、容器、指针和 RAII，再依次阅读本目录 02～05；06 与 08 可以按文本/文件任务选读；07 的内存序属于进阶，先掌握锁与线程生命周期。09、10 中的表示转换、模块和协程按项目需要深入。不能将章节覆盖等同于已经具备系统编程能力。

2026-10-02 复核：修正正则转义、`if constexpr` 适用范围、移动后状态、数据竞争定义、弱引用和文件系统边界；完整示例标明 C++17/20。权威核对：[if constexpr](https://eel.is/c++draft/stmt.if)、[数据竞争](https://eel.is/c++draft/intro.races)、[thread 析构](https://eel.is/c++draft/thread.thread.destr)、[正则语法](https://eel.is/c++draft/re.grammar)、[文件系统操作](https://eel.is/c++draft/fs.op.funcs)。工作草案会继续演进，不能把其中较新标准的条款直接套用到旧标准。
