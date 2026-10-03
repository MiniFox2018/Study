# C++ 学习笔记

当前目录按学习用途整理为两部分：

```text
C++/
├── README.md
├── Core/
│   ├── 01-Fundamentals.md
│   ├── 02-Control-Flow.md
│   ├── 03-Functions.md
│   ├── 04-Arrays-and-Strings.md
│   ├── 05-Pointers.md
│   ├── 06-OOP.md
│   ├── 07-Advanced-Data-Structures.md
│   ├── 08-STL.md
│   ├── 09-Exception-Handling.md
│   ├── 10-File-Handling.md
│   ├── 11-Templates.md
│   ├── 12-Preprocessing.md
│   ├── 13-Memory-Management.md
│   ├── 14-Multithreading.md
│   ├── 15-Modern-Features.md
│   └── 16-Best-Practices.md
└── Modern-C++/
    └── C++11/14/17/20 专题笔记
```

## Core · C++ 基础主线

1. [基础语法与运行环境](./Core/01-Fundamentals.md)
2. [条件与循环](./Core/02-Control-Flow.md)
3. [函数与参数传递](./Core/03-Functions.md)
4. [数组与字符串](./Core/04-Arrays-and-Strings.md)
5. [指针、引用与所有权](./Core/05-Pointers.md)
6. [类、继承与多态](./Core/06-OOP.md)
7. [常用数据结构](./Core/07-Advanced-Data-Structures.md)
8. [标准模板库与算法](./Core/08-STL.md)
9. [异常与错误处理](./Core/09-Exception-Handling.md)
10. [文件读写](./Core/10-File-Handling.md)
11. [模板与泛型](./Core/11-Templates.md)
12. [预处理与头文件](./Core/12-Preprocessing.md)
13. [内存管理与对象生命周期](./Core/13-Memory-Management.md)
14. [多线程与同步](./Core/14-Multithreading.md)
15. [现代 C++ 常用特性](./Core/15-Modern-Features.md)
16. [工程习惯与调试](./Core/16-Best-Practices.md)

## Modern C++ · 进阶专题

进入：[Modern-C++](./Modern-C++/README.md)

重点覆盖 C++11/14/17/20 的语言与标准库演进，包括：

- 类型推导、constexpr、structured bindings、if constexpr
- 模板增强、SFINAE、fold expressions
- lambda、右值引用、move、perfect forwarding
- modern containers、smart pointers、RAII
- regex、filesystem
- thread、atomic、memory model、memory order
- noexcept、alignment、bit_cast
- concepts、modules、ranges、coroutines
- Modern C++ 工程最佳实践

## 来源记录

原始资料完成吸收后不在 Study 中长期保留文件本体；需要时从官方入口重新获取。

- Compile N Run C++ Tutorial：https://www.compilenrun.com/docs/language/cpp/
- Modern C++ Tutorial — Changkun Ou
  - 官方网站：https://changkun.de/modern-cpp/
  - 官方 GitHub：https://github.com/changkun/modern-cpp-tutorial
  - 本轮曾使用的英文 PDF 下载页：https://changkun.de/modern-cpp/pdf/modern-cpp-tutorial-en-us.pdf
  - 处理方式：知识已吸收到 `Core/` 与 `Modern-C++/`，原始 PDF 不再保存在仓库中。

## 从零开始的学习方式

默认练习基线是 **C++17**；章节标注 C++20 的功能才切换到 `-std=c++20`。先读 Core 01～08 并运行例子，再读 09～13；多线程 14 和 Modern 的内存模型放到能独立解释对象生命周期之后。Modern 是查缺补漏的进阶入口，不必把两套章节逐篇重复背诵。

每章按“预测输出 → 编译运行 → 修改一个条件 → 解释失败边界”学习。能复述术语只是第一步；至少能独立改出一个相近例子、说明为什么正确，才算本章练习完成。文中没有完整头文件/`main` 的代码块是局部语法示意，需要放进对应上下文，不能把每个片段都当作独立程序。

### 核验与后续更新

- 核验日期：2026-10-02。本轮对本目录全部 Markdown 实读，重点纠正正则、生命周期、异常、并发和文件系统边界。
- 后续改动说明使用中文：写明“改了什么、为什么改、适用标准、验证了哪些例子、仍有哪些限制”，保留英文 API 与固定文件名。
- 编译器支持以实际工具链为准；`C++20` 标准特性不等于本机标准库已全部实现。
- 权威核对入口：[C++ 公开工作草案](https://eel.is/c++draft/)、[C++ Core Guidelines](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines)。草案会更新，学习基线仍以上述 C++17/20 标注为准。

### 2026-10-03 实际验证

在 macOS arm64、Apple Clang 21.0.0 上提取本目录 25 个完整程序，并连同 Linux 构建章的 1 个 C++ 程序逐个编译/运行，输出全部与文档一致；除低层表示与 ranges 两例使用 C++20，其余使用 C++17。编译启用 `-Wall -Wextra -Wpedantic -pthread`，修正按值传参例子的无用赋值警告后无编译警告。指针所有权与排序去重两例另用 ASan/UBSan 运行通过。

这次验证覆盖完整程序，不包括省略头文件/上下文的语法片段、故意错误示例、其他编译器/操作系统、TSan、模块构建和协程运行时。运行通过是当前案例的证据，不能证明所有边界和线程调度都正确。
