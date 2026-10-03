# Notebook 实验与可复现分析

先修：能够运行 Python、读取一张小表。这里补足[数据准备](./05-Python数据处理与数据准备.md)中的实验工作台：既看得见结果，也能从零重做。Notebook 是一种选择，不是所有 AI 项目的必需工具。

## 1. 文档、界面和内核是不同对象

`.ipynb` 是含单元、元数据和可选输出的 JSON 文档；JupyterLab、Notebook 或编辑器提供操作界面；kernel 是执行代码、保存变量与导入状态的进程。

保存文件保留文档内容，不会把进程的全部内存保存进去。显示的旧输出可能来自另一时间、环境或输入。删除一个代码单元不会自动删除它已经在内核里创建的变量。

不同内核可以执行不同语言，当前教程例子选 Python；Python 解释器、Jupyter 服务进程和所选内核也可能不在同一虚拟环境。

## 2. 乱序执行怎样制造“看上去正确”的结果

建立三格：

```python
# 单元 A
scale = 10
```

```python
# 单元 B
values = [1, 2, 3]
```

```python
# 单元 C
result = [x * scale for x in values]
print(result)
```

A→B→C 输出 `[10,20,30]`。随后只把 A 的文字改成 `scale=100`，但不运行 A，再运行 C，仍得到旧结果。保存 Notebook 时，代码写着 100、输出却是 10 倍。

另一个陷阱：先运行 A，再删除 A，C 仍可能成功，因为 `scale` 在内核中。全新内核运行 B→C 才会暴露 `NameError`。因此交付前执行“重启内核，从第一格顺序运行全部”，并确认输出来自这次执行。

这就是源图中“单元文档”与“共享状态内核”的关系；它不要求额外返回网站看图才能理解。

## 3. 创建环境和选内核

本地已选好项目环境后，可安装 JupyterLab；只需一个界面，不必同时安装所有编辑器。安装动作由你按需要执行：

```bash
python -m pip install jupyterlab ipykernel
python -m ipykernel install --user --name study-lab --display-name 'Study 练习环境'
python -m jupyterlab
```

`--name` 是内部标识，显示名供界面选择；多个项目同名会造成混淆。内核注册与包安装不同，删除项目环境后旧注册项也可能存在。先在第一格输出：

```python
import sys
from pathlib import Path
print(sys.executable)
print(Path.cwd())
```

确认内核解释器与数据路径。编辑器选择解释器、Notebook 选择内核、终端激活环境三处应核对一致，不由 UI 名称推断。

## 4. 单元类型与常用操作

代码单元执行程序；Markdown 单元解释目的、输入、假设、结论，支持标题、表格和数学 `$x^2$`。代码单元最后一个表达式一般通过丰富显示协议呈现；`print(df)` 则输出文本形式。

常见 Jupyter 快捷操作包括：`Shift+Enter` 执行并移动，命令模式下 A/B 插入单元、M/Y 转换类型、D 两次删除、Z 撤销。编辑模式下 Tab 补全、Shift+Tab 查看帮助。这些是界面的默认习惯，具体快捷键和是否可用以所选界面为准；无法识别时用菜单搜索，而不是假设快捷键没反应就是内核坏了。

## 5. Magic 不是普通 Python 语法

| 命令 | 用途 | 容易误解的地方 |
|---|---|---|
| `%timeit 表达式` | 多轮小规模计时 | 会重复执行，有写文件/扣费副作用时不适用 |
| `%%time` | 单次单元计时 | 包括该单元所做的全部工作，不能拿不同工作量比较 |
| `%pip install 包名` | 向当前 Python 内核环境安装 | 装完某些库需重启内核；不要无说明改变共享环境 |
| `%matplotlib inline` | 选择内嵌绘图后端 | 许多现代界面已默认内嵌，不必机械反复调用 |
| `!命令` | 启动 shell 子进程 | 子进程里的 `cd` 不会永久改变内核工作目录 |
| `%env 变量名` | 查看环境配置 | 不使用它显示密钥等秘密值 |

源教程的 `!pip` 可能调用 PATH 上另一个 pip；用 `%pip` 或明确当前 `sys.executable -m pip` 更能保证环境一致。把 `%timeit` 原样放进 `.py` 文件通常会发生语法错误。

## 6. 从小数据到图表的完整例子

前提：当前内核安装 pandas 和 Matplotlib。以下教学数据并非实测模型成绩：

```python
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

work = Path("notebook-lab")
work.mkdir(exist_ok=True)
pd.DataFrame({"方案": ["基线", "候选"], "正确数": [7, 9], "总数": [10, 10]}).to_csv(
    work / "results.csv", index=False, encoding="utf-8"
)
df = pd.read_csv(work / "results.csv")
if (df["总数"] <= 0).any():
    raise ValueError("分母必须大于零")
df["比例"] = df["正确数"] / df["总数"]
assert df["比例"].tolist() == [0.7, 0.9]
fig, ax = plt.subplots()
ax.bar(["baseline", "candidate"], df["比例"])
ax.set_ylim(0, 1)
ax.set_ylabel("Correct / total")
fig.savefig(work / "comparison.png", bbox_inches="tight")
plt.show()
plt.close(fig)
print(df[["方案", "比例"]].to_string(index=False))
```

在 Notebook 把 `df` 放到单元末尾可看丰富表格；`.show()` 显示图，`.savefig()` 把结果交付为文件，两者目的不同。若需要显示已有图片可使用 `IPython.display.Image` 与 `display`，先确认路径存在。

运行两次时会覆盖练习目录里的同名文件，适合本教学例子；实际实验用不同运行标识避免覆盖证据。小样本 7/10 与 9/10 不能自动证明候选更优，要结合样本和不确定性。

## 7. 微基准要比较相同工作

```python
import timeit

py_time = timeit.timeit("[x*x for x in range(10000)]", number=20)
print("20轮总耗时：", py_time)
```

若比较 NumPy，先确认整数 dtype、溢出范围、结果正确，且双方都包括或都排除数组创建。每次运行机器负载会变；时间数字不是教材固定答案。warm-up、重复测量与中位数可降低偶然波动，GPU 还需同步。

## 8. 内存和崩溃怎样诊断

- 普通异常：看单元堆栈，定位最小失败输入。
- 内核重启/消失：看启动 Jupyter 的终端或服务日志，区别内存不足、原生库崩溃、会话断开。
- 内存增长：检查列表、输出历史、图对象、计算图是否还引用数据。`del` 只删一个名称，不保证全部引用消失；`gc.collect()` 也不保证所有内存立即归还操作系统。
- NumPy 的 `nbytes` 表示数组元素载荷；`sys.getsizeof` 不是整个 Python 进程 RSS。进程、原生库与 GPU 要用各自指标。
- 一个单元不结束：可能是等待输入、网络超时、无限循环或大运算；先中断，再看状态，避免重复启动更多任务。

## 9. 云 Notebook 的边界

云界面可能提供计算资源，但可用 GPU、会话时长、配额和价格会变，不能保证免费账户总能得到某型号 GPU或固定分钟数。工作盘可能随会话终止丢失；代码、输入、输出分别导出或放入明确持久存储。

换到云端前核对数据是否允许上传、依赖是否可安装、网络是否可访问输入；本地样例不需要云账号。重新连接到界面不代表原内核和文件仍存在。

## 10. 从探索迁移到可复现程序

Notebook 保留问题、图表与解释，把稳定处理提取为函数/模块，再由 Notebook 调用它。脚本/模块更适合定期任务、自动测试和部署；Notebook 也能自动运行，但须显式控制输入、内核、执行顺序和结果保存，不能只以格式判定是否“生产化”。

交付检查：重启顺序运行 → 从项目根或明确工作目录复现 → 记录依赖/输入版本 → 比较表与图 → 隐藏秘密和不必要敏感输出 → 标注未执行单元。

自查：代码刚改，旧输出还在，可以交付吗？答案：需重新执行验证输出对应；若无法重跑，明确标记历史输出。

自查：只把 `.ipynb` 发给别人能重现吗？答案：还需数据、依赖、解释器、工作目录和任何外部资源。

来源：AI Engineering from Scratch，Phase 00/05（含程序、图示与诊断 prompt），来源提交见[来源记录](../来源保全/AI-Engineering-From-Scratch.md)。2026-10-03 定点核对：[IPython Magic](https://ipython.readthedocs.io/en/stable/interactive/magics.html)、[Colab FAQ](https://research.google.com/colaboratory/faq.html)。
