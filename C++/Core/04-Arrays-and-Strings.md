# 04 · 数组与字符串

## 原生数组
原生数组长度固定、内存连续、索引从 0 开始。C++ 不自动做越界检查。数组在很多表达式中会退化为首元素指针，因此传入函数时通常需要另行传递长度。

## 多维数组
多维数组本质是“数组的数组”，默认按行连续布局。大型矩阵常使用 vector、array 或专门数值库。

## 数组参数
现代接口更适合使用 `std::array`、`std::vector`，C++20 可用 `std::span` 表达非拥有连续范围。

## std::string
现代 C++ 首选文本类型。常用操作包括：
- `size()/length()`
- `find()`
- `substr()`
- `insert()`
- `erase()`
- `replace()`
- `append()`
- 比较与拼接

## 字符串处理
可按索引、迭代器或 range-for 遍历，并结合 `<algorithm>`、`<cctype>`、字符串流处理文本。

## C 风格字符串
C 字符串以空字符 `'\0'` 结束，常见于 `char[]` 或 `const char*`。传统函数如 `strlen`、`strcmp`、`strcpy` 更容易产生缓冲区和生命周期问题。现代代码应优先 `std::string`。

## 常见问题
数组越界、忘记终止符、混淆字节数与元素数、混用 getline 与格式化输入、保存 `c_str()` 指针后修改原字符串造成失效。

## 小实验：范围、字节与边界

```cpp
#include <array>
#include <iostream>
#include <stdexcept>
#include <string>
int main() {
    const std::array<int, 3> a{10, 20, 30};
    std::cout << a.size() << ' ' << a.at(1) << '\n';
    try { std::cout << a.at(3); }
    catch (const std::out_of_range&) { std::cout << "越界已捕获\n"; }
    const std::string text = "a,b,c";
    std::cout << text.substr(0, text.find(',')) << '\n';
}
```

输出依次为 `3 20`、`越界已捕获`、`a`。`operator[]` 不保证检查边界；换成 `a[3]` 就不是“更快的异常”，而是未定义行为。

`std::string::size()` 统计 `char` 单元；UTF-8 的一个汉字通常占多个字节，不等于屏幕字符数。向 `std::toupper` 等 `<cctype>` 函数传入 `char` 时，先转成 `unsigned char`，避免负值（非 EOF）造成未定义行为。

自测：`find` 找不到时返回什么？答：`std::string::npos`；不能直接把它当有效下标。

## 参考
https://www.compilenrun.com/docs/language/cpp/cpp-arrays-and-strings/
