# 12 · Preprocessing

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

## 参考
https://www.compilenrun.com/docs/language/cpp/cpp-preprocessing/
