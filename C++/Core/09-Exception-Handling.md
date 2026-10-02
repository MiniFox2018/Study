# 09 · 异常与错误处理

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
旧式动态异常规范已退出主流。现代 C++ 使用 `noexcept` 声明函数不抛异常。若异常逃出 `noexcept` 函数，会触发 `std::terminate`；函数内部抛出后自行捕获不违背该约定。移动构造/移动赋值的 noexcept 属性还会影响标准容器的优化选择。

## 嵌套异常
`std::throw_with_nested` 与 `std::nested_exception` 可在上层追加语义，同时保留底层异常上下文。

## 栈展开
异常传播时，作用域内已构造的自动对象会逆序析构，这也是 RAII 能保证资源安全的重要基础。

## 异常安全
常见保证层级：
- 不抛异常保证：操作不让异常逃出。
- 强保证：失败后可观察状态保持原样，类似事务回滚。
- 基本保证：失败后不泄漏资源、对象不变量仍成立，但值可能改变。
- 无保证：状态或资源可能已损坏。
资源管理对象和事务式更新有助于获得更强保证。

## 使用边界
异常适合处理当前层无法正常恢复的失败，不应承担日常条件分支。部分高性能、实时或禁用异常的系统会选择 error code 或结果类型。

## 小实验：检查前置条件并传播失败

```cpp
#include <iostream>
#include <stdexcept>
double divide(double a, double b) {
    if (b == 0.0) throw std::invalid_argument("除数不能为零");
    return a / b;
}
int main() {
    try { std::cout << divide(1.0, 0.0) << '\n'; }
    catch (const std::invalid_argument& e) { std::cout << e.what() << '\n'; }
}
```

输出 `除数不能为零`。这里有意在浮点除法之前执行领域校验；不要推断所有算术错误都会自动抛 C++ 异常。

自测：析构函数在异常栈展开时再次让异常逃出，会怎样？答：会终止程序。因此析构负责不抛出的清理；可能失败的提交/关闭操作应提供显式接口，让调用者有机会处理错误。

## 参考
https://www.compilenrun.com/docs/language/cpp/cpp-exception-handling/
