# 10 · 文件读写

## 文件流
`<fstream>` 提供 `std::ifstream`、`std::ofstream` 和 `std::fstream`。文件流对象遵循 RAII，离开作用域时会自动关闭。

## 打开模式
常见模式：`ios::in`、`ios::out`、`ios::app`、`ios::trunc`、`ios::binary`，可按位组合。

## 读取文件
- `operator>>`：格式化读取
- `getline`：逐行读取
- `read`：原始字节读取
循环应以读取操作成功与否作为条件，不要只依赖 `eof()`。

## 写文件
文本可用 `<<`，二进制可用 `write`。关键写入应检查流状态，必要时显式 flush。

## 二进制文件
需要关注对象布局、padding、字节序、平台 ABI 和格式版本。不要直接把包含指针、虚函数或复杂 STL 成员的对象内存原样持久化。

## 文件指针
输入位置：`tellg/seekg`；输出位置：`tellp/seekp`。相对位置可基于 beg、cur、end。

## 状态
常见检查：`good()`、`fail()`、`bad()`、`eof()`、`is_open()`。

## 实践
明确编码和格式；验证输入；把解析逻辑与 I/O 分层；关键写入可采用临时文件再替换；大文件避免一次性全部加载。

## 小实验：可靠地逐行读取

下面程序在当前目录创建或覆盖 `study-lines.txt`，请在空练习目录运行。

```cpp
#include <fstream>
#include <iostream>
#include <string>
int main() {
    {
        std::ofstream out("study-lines.txt");
        if (!out) return 1;
        out << "alpha\nbeta\n";
        out.close();
        if (!out) return 2;
    }
    std::ifstream in("study-lines.txt");
    if (!in) return 3;
    std::string line;
    int count = 0;
    while (std::getline(in, line)) ++count;
    if (in.bad() || !in.eof()) return 4;
    std::cout << count << '\n';
}
```

输出 `2`。以读取结果控制循环，避免 `while (!in.eof())` 在末尾重复处理旧数据。错误退出码是示例的最小错误通道，正式程序应同时报告文件名和失败原因。

`flush()` 和 `close()` 只保证库层面提交缓冲数据，不能独立保证断电后持久性；原子替换和持久落盘还涉及文件系统、目录同步及平台 API。

## 参考
https://www.compilenrun.com/docs/language/cpp/cpp-file-handling/
