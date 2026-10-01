# 02 · Control Flow

## 条件判断
C++ 使用 `if`、`else if`、`else` 和条件运算符 `?:` 进行分支。复杂条件宜拆成具名布尔表达式，避免把赋值 `=` 误写成比较 `==`。

## switch
`switch` 适合对整数、字符、枚举等离散值分支。每个 case 通常用 `break` 终止；未匹配情况由 `default` 处理。有意贯穿分支时可用 `[[fallthrough]]` 明确意图。

## 循环
- `for`：适合明确计数或迭代器更新
- `while`：先判断条件，适合次数未知
- `do-while`：至少执行一次

写循环时要核对初值、条件、状态更新、终止性和边界，避免死循环、off-by-one 和越界。

## break 与 continue
`break` 立即退出当前循环或 switch；`continue` 跳过本轮剩余语句。过度使用会使控制流难以理解。

## goto
`goto` 可无条件跳转到标签，但现代 C++ 通常用函数拆分、结构化循环、RAII 和异常处理替代。除极少数底层场景外不建议常规使用。

## 控制流组织原则
保持嵌套层级浅；错误分支可提前返回；重复逻辑提取为函数；优先表达业务意图而不是堆叠语法。

## 参考
https://www.compilenrun.com/docs/language/cpp/cpp-control-flow/
