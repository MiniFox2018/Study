# 01 · C++ Fundamentals

## C++ 概览
C++ 是编译型、静态类型、多范式语言，既能进行接近硬件的资源控制，也支持面向对象、泛型和现代函数式风格。典型应用包括系统软件、游戏引擎、嵌入式、图形、数据库和高性能计算。

## 开发环境
完整开发链通常包含编译器、编辑器/IDE、构建工具和调试器。Windows 常见 Visual Studio/MSVC 或 MinGW/Clang；macOS 常用 Xcode Command Line Tools/Clang；Linux 常用 GCC/G++ 或 Clang。常见编译命令：`g++ main.cpp -std=c++17 -Wall -Wextra -o app`。

## 第一个程序与语法
程序入口是 `main()`，源文件通常先包含头文件，再定义函数和类型。语句通常以分号结束；代码块使用花括号；C++ 区分大小写；标准库实体位于 `std` 命名空间。

```cpp
#include <iostream>
int main() {
    std::cout << "Hello, C++!\n";
    return 0;
}
```

## 注释
单行使用 `//`，多行使用 `/* ... */`。注释应解释意图、原因和边界条件，而不是复述代码。

## 变量与初始化
变量需要类型、名字和可选初始值。现代 C++ 推荐尽量初始化变量，常用列表初始化：`int n{10};`，可减少窄化转换。

## 数据类型
基础类型包括整数、无符号整数、浮点、字符、布尔和 void。常见复合/库类型包括数组、指针、引用、`std::string`、结构体、类、枚举和 STL 容器。实际大小受平台和 ABI 影响，可用 `sizeof` 查看。

## 常量
`const` 表示初始化后不可通过该名字修改；`constexpr` 用于可在编译期求值的常量和函数。普通常量优先使用 constexpr，而不是宏。

## 运算符
包括算术、比较、逻辑、赋值、自增自减、位运算、条件运算和成员/指针相关运算。重点注意整数除法、运算符优先级、短路求值和溢出。

## 输入输出
`std::cout` 输出，`std::cerr` 输出错误，`std::cin` 格式化输入，`std::getline` 读取整行。混用 `>>` 与 `getline` 时要处理残留换行符。

## 类型转换
优先使用 C++ 命名转换：
- `static_cast`：常规显式转换
- `dynamic_cast`：多态层次运行时转换
- `const_cast`：调整 const/volatile
- `reinterpret_cast`：低层重新解释，风险最高

## 作用域
包括块、函数、类、命名空间和全局作用域。应避免无意义的同名遮蔽，使用命名空间减少符号冲突。

## 参考
https://www.compilenrun.com/docs/language/cpp/cpp-fundamentals/
