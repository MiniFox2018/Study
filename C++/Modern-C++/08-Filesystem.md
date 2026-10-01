# 08 · Filesystem

## 1. std::filesystem（C++17）

C++17 将文件系统能力纳入标准库，核心位于：

```cpp
#include <filesystem>
namespace fs = std::filesystem;
```

它负责处理：

- path
- 普通文件
- 目录
- 文件状态
- 遍历
- 创建、复制、移动、删除

早期 GCC/LLVM 工具链有时需要额外链接 filesystem 库，现代主流工具链一般已不需要。

## 2. std::filesystem::path

`fs::path` 是文件系统库的核心类型。  
它表示**路径语法对象**，构造 path 本身不会访问磁盘，也不要求对应文件真实存在。

```cpp
fs::path base = "/usr/local";
fs::path p = base / "bin" / "clang";
```

使用 `operator/` 拼接路径可以避免手工处理平台路径分隔符。

## 3. 路径分解

常用接口：

- `filename()`
- `stem()`
- `extension()`
- `parent_path()`
- `root_path()`
- `relative_path()`

示意：

```cpp
fs::path p = "/tmp/report.txt";

p.filename();     // report.txt
p.stem();         // report
p.extension();    // .txt
p.parent_path();  // /tmp
```

## 4. 查询文件状态

常见非成员函数：

```cpp
fs::exists(p);
fs::is_regular_file(p);
fs::is_directory(p);
fs::file_size(p);
fs::last_write_time(p);
```

这些操作会真实访问文件系统，因此可能因为：

- 路径不存在；
- 权限不足；
- I/O 失败；

而产生错误。

## 5. 异常与 error_code

filesystem 许多 API 有两套形式：

### 抛异常
```cpp
auto size = fs::file_size(p);
```

### error_code
```cpp
std::error_code ec;
auto size = fs::file_size(p, ec);

if (ec) {
    // handle error
}
```

选择哪种取决于项目统一错误处理策略。

## 6. 目录遍历

### directory_iterator
只遍历当前目录一层：

```cpp
for (const auto& entry : fs::directory_iterator(dir)) {
    std::cout << entry.path() << '\n';
}
```

### recursive_directory_iterator
递归遍历整个目录树。

```cpp
for (const auto& entry : fs::recursive_directory_iterator(dir)) {
    if (entry.is_regular_file()) {
        // ...
    }
}
```

`directory_entry` 可缓存部分状态信息，因此直接使用其成员函数有时比对 path 重复查询更高效。

## 7. 创建目录

```cpp
fs::create_directory(path);
fs::create_directories(path);
```

- `create_directory` 创建单层目录；
- `create_directories` 可递归创建缺失的中间目录。

## 8. 复制

```cpp
fs::copy_file(src, dst);
fs::copy(src, dst, fs::copy_options::recursive);
```

复制行为可以通过 `copy_options` 控制，例如：

- overwrite_existing
- skip_existing
- recursive
- copy_symlinks 等

## 9. rename / move

```cpp
fs::rename(old_path, new_path);
```

rename 可用于重命名，也可在文件系统允许时移动路径。

跨文件系统移动不一定能通过单一 rename 完成。

## 10. 删除

```cpp
fs::remove(p);
fs::remove_all(p);
```

- `remove`：删除一个文件或空目录；
- `remove_all`：递归删除目录树，并返回删除条目数。

对 `remove_all` 应保持高度谨慎，尤其当 path 来自外部输入时。

## 11. 临时目录

标准库提供：

```cpp
fs::temp_directory_path();
```

适合测试、临时文件和自包含 demo。

## 12. 文件系统安全

操作用户提供的路径时应防范：

- `..` 路径穿越；
- 符号链接逃逸；
- TOCTOU（检查与使用之间状态变化）；
- 递归删除错误路径；
- 权限问题；
- 不可信文件名。

不能只靠字符串替换保证 path 安全。

## 13. filesystem 与 fstream 的区别

`fstream` 负责**文件内容 I/O**。  
`filesystem` 负责**文件和目录的元数据及结构操作**。

常见组合：

```cpp
fs::path file = dir / "data.txt";
std::ofstream out(file);
```

## 核心结论

现代 C++ 中不应再手工拼路径或为常见文件系统操作写平台分支。  
`std::filesystem` 把“路径语义”和“文件系统操作”标准化，并提供更好的跨平台可移植性。

## 来源
Modern C++ Tutorial — Chapter 08
