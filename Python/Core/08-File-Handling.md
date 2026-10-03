# 08 · 文件、目录、CSV、JSON 与二进制

## 1. 文件操作的三个核心问题

处理文件时始终明确：

1. 路径在哪里；
2. 文本还是二进制；
3. 谁负责关闭资源。

现代 Python 优先 pathlib 和 with。

## 2. 打开模式

常见模式：

- r：读取，文件不存在报错；
- w：写入，会截断已有文件；
- a：追加；
- x：仅新建，存在时报错；
- b：二进制；
- +：同时读写。

~~~python
with open("notes.txt", "r", encoding="utf-8") as file:
    text = file.read()
~~~

with 块退出时，即使抛异常也会关闭文件。

## 3. 读取方式

~~~python
with open("data.txt", encoding="utf-8") as file:
    content = file.read()
~~~

大文件通常逐行：

~~~python
with open("data.txt", encoding="utf-8") as file:
    for line in file:
        process(line.rstrip("
"))
~~~

readline 读取一行；readlines 一次性返回所有行列表。大文件不应无意义地 read/readlines 全部载入内存。

## 4. 写入与追加

~~~python
from pathlib import Path

path = Path("result.txt")
path.write_text("first
", encoding="utf-8")

with path.open("a", encoding="utf-8") as file:
    file.write("second
")
~~~

w 会覆盖原内容。重要文件需要原子写入或备份时，应写临时文件并 replace，而不是直接覆盖后祈祷。

## 5. pathlib

~~~python
from pathlib import Path

root = Path("project")
data_dir = root / "data"
data_dir.mkdir(parents=True, exist_ok=True)

for path in data_dir.glob("*.csv"):
    print(path.name, path.stat().st_size)
~~~

常见能力：

- exists / is_file / is_dir；
- mkdir；
- iterdir / glob / rglob；
- rename / replace / unlink；
- read_text / write_text；
- read_bytes / write_bytes；
- resolve；
- suffix / stem / name / parent。

需要批量移动、复制目录等操作时配合 shutil。

## 6. 当前工作目录与相对路径

相对路径是相对于进程当前工作目录，而不一定是脚本文件所在目录。这是很多“本机能跑、换地方失败”的原因。

需要相对于模块文件定位资源时：

~~~python
from pathlib import Path

HERE = Path(__file__).resolve().parent
config_path = HERE / "config.json"
~~~

更成熟的包内资源应考虑 importlib.resources。

## 7. 文件指针

file.tell 返回当前位置；file.seek 改变位置。文本模式下不要把偏移量理解成字符编号；复杂随机访问更适合二进制文件或明确的格式索引。

## 8. CSV

标准库 csv 会处理分隔符、引用与换行规则：

~~~python
import csv

rows = [
    {"name": "Ada", "score": 95},
    {"name": "Linus", "score": 88},
]

with open("scores.csv", "w", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(file, fieldnames=["name", "score"])
    writer.writeheader()
    writer.writerows(rows)
~~~

读取：

~~~python
with open("scores.csv", newline="", encoding="utf-8") as file:
    for row in csv.DictReader(file):
        print(row["name"], int(row["score"]))
~~~

CSV 所有字段最初都是文本，需要显式类型转换与缺失处理。

## 9. JSON

~~~python
import json

data = {"name": "Ada", "active": True}

with open("user.json", "w", encoding="utf-8") as file:
    json.dump(data, file, ensure_ascii=False, indent=2)

with open("user.json", encoding="utf-8") as file:
    restored = json.load(file)
~~~

dumps/loads 操作字符串；dump/load 操作文件对象。

JSON 原生类型有限：object、array、string、number、boolean、null。datetime、Decimal、自定义对象需明确编码策略，不要假设 json 自动懂任意 Python 对象。

## 10. Pickle

pickle 能序列化很多 Python 对象：

~~~python
import pickle

with open("state.pkl", "wb") as file:
    pickle.dump({"value": 42}, file)
~~~

**绝不能反序列化不可信 pickle 数据。** pickle 加载过程可触发任意代码执行。它适合自己控制的本地缓存/状态，不是跨信任边界的数据交换格式。

跨语言或不可信输入优先使用 JSON、MessagePack、Protobuf 等具有明确数据模型的方案，并做验证。

## 11. bytes、bytearray 与二进制文件

~~~python
payload = bytes([0x50, 0x59])
mutable = bytearray(payload)
mutable[0] = 0x70
~~~

二进制读写：

~~~python
with open("image.bin", "rb") as source:
    chunk = source.read(4096)
~~~

大文件复制用分块或 shutil.copyfileobj，而不是一次性全部加载。

## 12. struct

struct 用于按明确字节布局打包和解析二进制协议：

~~~python
import struct

payload = struct.pack(">If", 7, 3.5)
number, value = struct.unpack(">If", payload)
~~~

必须明确字节序、字段宽度和格式版本。自定义二进制格式还应定义 magic、版本、长度和完整性校验。

## 13. 文件管理

~~~python
from pathlib import Path
import shutil

src = Path("a.txt")
dst = Path("archive/a.txt")

dst.parent.mkdir(parents=True, exist_ok=True)
shutil.copy2(src, dst)
src.unlink()
~~~

删除和递归清理是不可逆操作。自动化脚本应先验证目标目录边界，必要时支持 dry-run。

## 14. 临时文件

~~~python
from tempfile import TemporaryDirectory
from pathlib import Path

with TemporaryDirectory() as tmp:
    path = Path(tmp) / "result.txt"
    path.write_text("ok", encoding="utf-8")
~~~

临时资源由上下文自动清理，测试中特别有用。

## 15. 文件异常

常见异常：FileNotFoundError、PermissionError、IsADirectoryError、NotADirectoryError、UnicodeDecodeError、OSError。

只捕获你能处理的异常；不要用 except Exception 然后静默忽略。

## 16. 练习与答案

**练习 1**：为什么打开 CSV 写文件常传 newline=""？  
**答案**：让 csv 模块统一处理记录换行，避免某些平台出现额外空行。

**练习 2**：JSON 和 pickle 最大的信任边界差异？  
**答案**：JSON 解析数据；pickle 加载可能执行代码，因此不可信 pickle 具有代码执行风险。

**练习 3**：为什么相对路径常导致部署问题？  
**答案**：它相对当前工作目录而不是必然相对脚本；启动方式变化就可能指向不同位置。
