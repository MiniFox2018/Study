# 06 · 正则表达式

## 1. 正则表达式解决什么问题

正则表达式用于描述字符串模式，典型任务包括：

1. 判断文本是否匹配规则；
2. 查找符合规则的子串；
3. 提取捕获组；
4. 替换匹配内容。

C++11 将正则支持正式纳入标准库 `<regex>`。

## 2. 基本模式元素

### 普通字符
普通字母、数字和大部分标点直接匹配自身。

### 常见元字符

- `^`：开头
- `$`：结尾
- `.`：通常匹配单字符，但换行等例外依引擎/模式而定
- `[]`：字符集合
- `()`：分组/捕获组
- `|`：分支
- `\`：转义

## 3. Quantifiers

- `*`：0 次或更多
- `+`：1 次或更多
- `?`：0 或 1 次
- `{n}`：恰好 n 次
- `{n,}`：至少 n 次
- `{n,m}`：n 到 m 次

## 4. C++ 字符串中的双重转义

正则表达式本身使用反斜杠转义，而 C++ 字符串也使用反斜杠。

例如正则中的：

```text
\.
```

传统字符串字面量中需要：

```cpp
"\\."
```

此时 raw string literal 往往更清楚：

```cpp
R"(\.)"
```

## 5. std::regex

构造模式：

```cpp
std::regex pattern(R"([a-z]+\.txt)");
```

## 6. regex_match

`std::regex_match` 要求**整个字符串**匹配模式：

```cpp
if (std::regex_match(filename, pattern)) {
    // full match
}
```

这与只寻找局部匹配的 search 语义不同。

## 7. std::smatch

`std::smatch` 保存 string 匹配结果，包括：

- 整体匹配；
- 捕获组；
- 每个子匹配对应的字符串范围。

```cpp
std::regex p(R"(([a-z]+)\.txt)");
std::smatch m;

if (std::regex_match(name, m, p)) {
    auto whole = m[0].str();
    auto stem  = m[1].str();
}
```

## 8. regex_search 与 regex_replace

虽然原书重点演示 regex_match，但完整标准库还包括：

- `std::regex_search`：寻找是否存在匹配子串；
- `std::regex_replace`：替换匹配内容；
- regex iterator/token iterator：遍历多个匹配。

## 9. 路由匹配场景

Web server/router 中，正则可用于：

- URL path pattern；
- 参数捕获；
- 方法 + path 分发；
- 资源文件过滤。

但对于复杂路由系统，还要同时处理：

- URL 解码；
- path traversal；
- 输入长度限制；
- ReDoS 风险；
- 正则引擎性能。

## 10. 使用边界

正则适合结构明确的文本模式，但不是所有解析问题的最佳工具。  
层级语法、编程语言、复杂协议更适合专门 parser。

## 来源
Modern C++ Tutorial — Chapter 06

## 小实验：字面点与通配点

```cpp
#include <iostream>
#include <regex>
#include <string>
int main() {
    const std::regex pattern(R"(([a-z]+)\.txt)");
    for (const std::string name : {"note.txt", "noteXtxt"}) {
        std::smatch match;
        const bool ok = std::regex_match(name, match, pattern);
        std::cout << name << ':' << std::boolalpha << ok;
        if (ok) std::cout << ':' << match[1].str();
        std::cout << '\n';
    }
}
```

输出 `note.txt:true:note` 和 `noteXtxt:false`。删去正则中的反斜杠后，两者都会匹配，因为 `.` 成为通配符。默认语法是修改后的 ECMAScript，不应假设支持任意 PCRE 功能。

模式非法时构造 regex 可抛 `std::regex_error`；匹配结果保存输入迭代器，使用 smatch 前应保证原字符串仍有效且未发生使迭代器失效的修改。不要在循环内反复编译相同模式。
