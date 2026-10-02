# 12 · 预处理与头文件

## 预处理阶段
预处理发生在正式编译前，主要负责文件包含、宏展开和条件编译。

## include
`#include <...>` 常用于标准/系统头文件，`#include "..."` 常优先查找项目本地文件。头文件应尽量自包含。

## Include Guard
传统方式使用 `#ifndef/#define/#endif` 防止重复包含。主流编译器也广泛支持 `#pragma once`。

## 宏
对象宏和函数式宏本质是文本替换，没有类型保护。普通常量优先 constexpr，简单函数优先 inline/constexpr 函数或模板。

## 宏风险
函数式宏需注意括号、参数重复求值和作用域污染，不应用宏模拟本可由类型安全语言特性完成的逻辑。

## 条件编译
常用：`#if`、`#ifdef`、`#ifndef`、`#elif`、`#else`、`#endif`。适合平台差异、可选功能和构建特性。

## 预定义宏
常见包括 `__FILE__`、`__LINE__`、`__DATE__`、`__TIME__`、`__cplusplus`。编译器还会提供平台相关宏。

## 原则
缩小宏范围；平台判断集中管理；避免公共头文件污染全局宏命名空间；优先使用 C++ 类型系统能表达的方案。

## 小实验：函数比重复求值的宏可靠

```cpp
#include <iostream>
constexpr int square(int x) { return x * x; }
int main() {
    int i = 3;
    std::cout << square(i++) << ' ' << i << '\n';
}
```

输出 `9 4`，实参只求值一次。如果改成 `#define SQUARE(x) ((x)*(x))` 再传入 `i++`，会把副作用复制到两个未排序操作数，产生未定义行为。加括号不能修复重复求值。

头文件保护只防止**同一翻译单元**重复包含；不能让普通非 inline 全局变量在多个源文件中重复定义。`#pragma once` 广泛支持但不是 ISO C++ 标准指令。

自测：`#ifdef FEATURE` 在 `#define FEATURE 0` 时成立吗？答：成立，它检查是否定义；要检查数值使用 `#if FEATURE`。

## 参考
https://www.compilenrun.com/docs/language/cpp/cpp-preprocessing/
