# 10 · File Handling

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

## 参考
https://www.compilenrun.com/docs/language/cpp/cpp-file-handling/
