# 05 · 字符串、正则、文本与 Unicode

## 1. str 与 bytes 先分清

Python 3 的 str 表示 Unicode 文本；bytes 表示原始字节。文本与外部世界交互时才发生编码或解码：

~~~python
text = "你好，Python"
payload = text.encode("utf-8")
restored = payload.decode("utf-8")

assert restored == text
~~~

乱码问题本质上通常是“编码和解码所用规则不一致”。

## 2. 字符串索引、切片与不可变性

~~~python
text = "abcdef"

print(text[0])      # a
print(text[-1])     # f
print(text[1:4])    # bcd
print(text[::2])    # ace
~~~

str 不可变：

~~~python
# text[0] = "A"  # TypeError
text = "A" + text[1:]
~~~

大量拼接片段时优先收集到列表后用 join，避免反复创建中间字符串。

## 3. 常用方法

清理和大小写：

~~~python
raw = "  Python Data  "
clean = raw.strip().lower()
~~~

搜索与替换：

~~~python
text = "python is useful"
print(text.find("is"))       # 找不到返回 -1
print(text.startswith("py"))
print(text.replace("useful", "powerful"))
~~~

拆分和连接：

~~~python
parts = "a,b,c".split(",")
line = " | ".join(parts)
~~~

字符串检查包括 isalpha、isdigit、isalnum、isspace 等，但真实姓名、邮箱、国际化文本往往不能只靠这些简单规则完成业务验证。

## 4. 格式化

### f-string

新代码首选：

~~~python
name = "Ada"
price = 1234.5
print(f"{name}: {price:,.2f}")
~~~

### str.format

在模板来自固定程序结构、又需要兼容旧代码时仍常见。

### 百分号格式

日志库采用延迟格式化时经常看到：

~~~python
logger.info("user_id=%s status=%s", user_id, status)
~~~

不要为了“现代”把所有日志都预先变成 f-string；日志参数化可以避免未启用级别时不必要的字符串构造，并方便日志系统处理。

## 5. string.Template

Template 使用美元占位符，语法比 format/f-string 有意限制：

~~~python
from string import Template

template = Template("Hello, $name")
print(template.substitute(name="Ada"))
~~~

safe_substitute 对缺失占位符不抛 KeyError，而是保留原文本。

安全边界要说清：把普通用户值放进 f-string 并不会自动执行用户文本；真正危险的是 eval 用户输入、把不可信字符串当代码/模板语言执行，或在 HTML、SQL、shell 等目标上下文中缺少正确转义。Template 的价值主要是“模板能力受限、语法简单”，不是万能安全沙箱。

## 6. 正则表达式

使用 re，模式通常写 raw string：

~~~python
import re

text = "order=AB-1234"
match = re.search(r"\b([A-Z]{2})-(\d{4})\b", text)

if match:
    prefix, number = match.groups()
~~~

核心函数：

- re.search：任意位置查第一个匹配。
- re.match：只从开头匹配。
- re.fullmatch：要求整串匹配。
- re.findall：取全部匹配。
- re.finditer：惰性返回 Match 对象。
- re.sub：替换。
- re.split：按模式切分。
- re.compile：复用预编译模式并集中表达意图。

常用语法：

- . 任意字符；
- ^ / $ 起止；
- d 数字、w 单词字符、s 空白；
- [] 字符集合；
- * + ? 重复量词；
- {m,n} 次数范围；
- () 捕获组；
- (?:...) 非捕获组；
- (?P<name>...) 命名组。

### 正则的边界

简单日期、日志字段、固定格式编号很适合正则。完整 HTML/XML 解析应使用解析器；严格邮箱、URL、国际化地址通常由成熟库或业务规则处理，而不是追求一个“完美正则”。

## 7. 文本处理流水线

典型过程：

1. 明确输入编码；
2. Unicode 规范化；
3. 清理空白与不需要字符；
4. 切分或解析；
5. 统计/转换；
6. 明确输出编码。

~~~python
import unicodedata
from collections import Counter

def word_counts(text: str) -> Counter:
    normalized = unicodedata.normalize("NFC", text).casefold()
    words = re.findall(r"w+", normalized, flags=re.UNICODE)
    return Counter(words)
~~~

casefold 比 lower 更适合跨语言的大小写无关比较，但仍不能替代所有本地化规则。

## 8. Unicode：码点、编码与规范化

ord 返回单字符码点；chr 做逆转换：

~~~python
print(ord("A"))   # 65
print(chr(65))    # A
~~~

Unicode 转义：

~~~python
heart = "❤"
emoji = "U0001F680"
~~~

常见编码：

- UTF-8：互联网和跨平台文本的默认优先选择。
- UTF-16/UTF-32：某些协议或系统内部使用。
- legacy 编码：只在已知来源要求时使用。

文件读写明确 encoding：

~~~python
from pathlib import Path

Path("note.txt").write_text("中文", encoding="utf-8")
text = Path("note.txt").read_text(encoding="utf-8")
~~~

## 9. 编码错误处理

decode/encode 可配置 errors：

- strict：默认，遇到错误抛异常；
- replace：替换不可处理字符；
- ignore：直接丢弃，可能造成数据损失。

生产数据管道不要无声使用 ignore。应先记录来源、字节内容和失败位置，确认容错策略。

## 10. Unicode 规范化

视觉上相同的字符序列可能有不同码点组合。需要稳定比较、去重或签名前，应了解 NFC/NFD/NFKC/NFKD。

NFKC 会进行兼容等价折叠，可能改变语义，不能盲目用于密码或需要保真展示的文本。

## 11. 一个日志解析例子

~~~python
import re

pattern = re.compile(
    r"^(?P<level>INFO|WARNING|ERROR)s+"
    r"user=(?P<user>w+)s+"
    r"action=(?P<action>w+)$"
)

line = "INFO user=alice action=login"
match = pattern.fullmatch(line)

if match:
    print(match.groupdict())
~~~

预期：

~~~text
{'level': 'INFO', 'user': 'alice', 'action': 'login'}
~~~

## 12. 常见错误

- 混淆 str 和 bytes；
- 不指定文本文件编码；
- 把 find 返回 -1 当作 False 直接判断；
- 在循环里用 += 拼接大量片段；
- 正则贪婪度与边界写错；
- 用正则解析完整 HTML；
- 把“用户值放进 f-string”误当作代码执行；
- 为解决乱码直接 errors="ignore" 丢数据。

## 13. 练习与答案

**练习 1**：为什么 len("🚀") 在常见 Python 中是 1，但 UTF-8 字节长度大于 1？  
**答案**：str 按 Unicode 码点序列工作；encode 后是具体编码的字节序列。

**练习 2**：find 与 index 找不到子串时有什么区别？  
**答案**：find 返回 -1；index 抛 ValueError。

**练习 3**：为什么正则模式常写 r"d+"？  
**答案**：raw string 减少 Python 字符串转义与正则转义叠加造成的可读性问题。
