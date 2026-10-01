# 09 · Exception Handling

## try / catch
异常用于把错误检测与错误处理分离。多个 catch 应从具体类型排到一般类型。

```cpp
try {
    // 可能失败的操作
} catch (const std::exception& e) {
    // 处理
}
```

## throw
通常按值抛出、按 const 引用捕获，避免对象切片和不必要复制。

## 自定义异常
可继承 `std::exception` 或标准异常类型，如 `std::runtime_error`、`std::logic_error`，用于表达领域错误。

## noexcept
旧式动态异常规范已退出主流。现代 C++ 使用 `noexcept` 声明函数不抛异常。若 noexcept 函数实际抛出，会触发 `std::terminate`。移动构造/移动赋值的 noexcept 属性还会影响标准容器的优化选择。

## 嵌套异常
`std::throw_with_nested` 与 `std::nested_exception` 可在上层追加语义，同时保留底层异常上下文。

## 栈展开
异常传播时，作用域内已构造的自动对象会逆序析构，这也是 RAII 能保证资源安全的重要基础。

## 异常安全
常见保证层级：
- no-throw guarantee
- strong guarantee
- basic guarantee
- 无保证
资源管理对象和事务式更新有助于获得更强保证。

## 使用边界
异常适合处理当前层无法正常恢复的失败，不应承担日常条件分支。部分高性能、实时或禁用异常的系统会选择 error code 或结果类型。

## 参考
https://www.compilenrun.com/docs/language/cpp/cpp-exception-handling/
