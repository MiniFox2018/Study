# 02 · 条件、循环与推导式

## 1. 控制流的核心问题

控制流决定“哪些语句执行、执行几次、何时退出”。Python 的主干是条件分支、for、while、break、continue、循环 else，以及用于简洁数据变换的推导式。

## 2. if / elif / else

~~~python
score = 86

if score >= 90:
    grade = "A"
elif score >= 80:
    grade = "B"
elif score >= 60:
    grade = "C"
else:
    grade = "D"
~~~

条件按顺序判断，命中后后续分支不再执行。多个条件可用 and、or、not 组合，但当表达式太长时应拆成有名字的布尔变量。

~~~python
is_eligible = age >= 18 and has_id and not is_suspended
if is_eligible:
    approve()
~~~

## 3. 嵌套条件与提前返回

深层嵌套通常降低可读性。函数中可用守卫式提前返回：

~~~python
def shipping_fee(weight: float, is_member: bool) -> float:
    if weight <= 0:
        raise ValueError("weight must be positive")
    if is_member:
        return 0.0
    if weight <= 5:
        return 8.0
    return 15.0
~~~

## 4. 条件表达式

简单二选一可写成：

~~~python
label = "adult" if age >= 18 else "minor"
~~~

它适合短表达式，不适合复杂业务分支。

## 5. 结构化模式匹配

源站控制流章节没有单独介绍 match/case，但当前 Python 已把它作为稳定语法。它从 Python 3.10 起可用，适合按结构而不是只按布尔条件分支：

~~~python
def handle(command):
    match command:
        case {"action": "move", "x": x, "y": y}:
            return f"move to {x},{y}"
        case {"action": "stop"}:
            return "stopped"
        case _:
            return "unknown"
~~~

不要为了替代所有 if 而使用 match；它最有价值的场景是结构解构和多种数据形状。

## 6. for 与可迭代对象

for 会从可迭代对象逐项取值：

~~~python
names = ["Ada", "Grace", "Linus"]

for name in names:
    print(name)
~~~

range 常用于整数序列：

~~~python
for i in range(2, 10, 2):
    print(i)  # 2 4 6 8
~~~

需要索引时用 enumerate，不要手动维护计数器：

~~~python
for index, name in enumerate(names, start=1):
    print(index, name)
~~~

并行遍历多个序列用 zip：

~~~python
for name, score in zip(names, [90, 85, 88]):
    print(name, score)
~~~

zip 默认以最短输入为止；长度不应不一致时要显式检查或使用支持严格模式的写法。

## 7. while

while 适合“重复直到状态满足”，尤其是次数事先未知：

~~~python
attempts = 0
while attempts < 3:
    attempts += 1
    if check_password():
        break
~~~

每次循环都必须有能改变退出条件的路径，否则可能形成无限循环。

## 8. break、continue、pass

- break：立即离开当前循环。
- continue：跳过本次剩余语句，开始下一轮。
- pass：什么都不做，只用于语法占位。

~~~python
for value in values:
    if value is None:
        continue
    if value < 0:
        break
    process(value)
~~~

pass 不等于 continue，也不等于 break。

## 9. 循环 else

for/while 可以带 else。当循环“自然结束”而没有被 break 打断时执行：

~~~python
target = 17

for n in [3, 8, 17, 21]:
    if n == target:
        print("found")
        break
else:
    print("not found")
~~~

这适合搜索逻辑，但若团队不熟悉该语法，用显式函数返回也可能更清晰。

## 10. 嵌套循环

嵌套循环的时间成本通常相乘。二维数据可以合理使用，但一旦用于大规模查找，应考虑 set、dict、索引、排序或向量化方法。

## 11. 推导式

列表推导式：

~~~python
squares = [x * x for x in range(10) if x % 2 == 0]
~~~

字典推导式：

~~~python
lengths = {word: len(word) for word in ["python", "data"]}
~~~

集合推导式：

~~~python
initials = {name[0].upper() for name in names}
~~~

推导式适合“一次变换 + 简单过滤”。出现多层条件、副作用、异常处理或难读嵌套时，普通循环更好。

## 12. 真值和成员条件

Python 风格通常直接判断容器是否为空：

~~~python
if items:
    process(items)
~~~

成员判断用 in：

~~~python
if role in {"admin", "editor"}:
    allow_edit()
~~~

集合成员查询通常比列表在大数据上更适合频繁查找。

## 13. 常见错误

- 用 is 比较字符串或数字值；
- while 忘记更新状态；
- range 的 stop 不包含在结果中；
- 在遍历列表时同时随意删除元素；
- 推导式过度嵌套；
- 误以为 continue 会退出循环；
- 把循环 else 理解为“最后一轮执行”。

## 14. 综合例子：筛选并分级

~~~python
records = [
    {"name": "A", "score": 91},
    {"name": "B", "score": None},
    {"name": "C", "score": 76},
]

result = []
for record in records:
    score = record["score"]
    if score is None:
        continue

    if score >= 90:
        level = "excellent"
    elif score >= 60:
        level = "pass"
    else:
        level = "fail"

    result.append((record["name"], level))

print(result)
~~~

预期：

~~~text
[('A', 'excellent'), ('C', 'pass')]
~~~

## 15. 练习与答案

**练习 1**：如何判断一个数是否同时大于 0 且小于等于 100？  
**答案**：0 < x <= 100。

**练习 2**：搜索列表时只在“未找到”才打印提示，最 Python 的两个方案是什么？  
**答案**：for...else；或封装成函数，找到时直接 return，循环后处理未找到。

**练习 3**：为什么不建议三层以上复杂推导式？  
**答案**：虽然语法合法，但可读性、调试和异常处理成本明显上升，应拆成普通循环或函数。
