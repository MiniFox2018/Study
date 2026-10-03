# 15 · NumPy、pandas、可视化与统计

## 1. 数据分析主线

源站的数据科学部分覆盖 NumPy、pandas、分析、可视化、Matplotlib、Seaborn、数据清洗与统计。真正工作流应按问题推进：

~~~text
问题定义
→ 数据读取
→ 质量审查
→ 清洗与类型
→ 探索/统计
→ 分组与建模
→ 可视化
→ 验证结论
→ 可复现输出
~~~

不要从“先画图”开始，也不要把 DataFrame 能运行等同于结论可信。

## 2. NumPy ndarray

~~~python
import numpy as np

arr = np.array([1.0, 2.0, 3.0])
print(arr.shape)
print(arr.dtype)
print(arr.ndim)
print(arr.size)
~~~

ndarray 通常是同质、固定 dtype、多维的数值数组。NumPy 的优势来自连续/规则内存布局和向量化底层实现，而不是 Python for 循环语法更短。

## 3. 创建数组

~~~python
np.zeros((2, 3))
np.ones((2, 3))
np.full((2, 3), 7)
np.arange(0, 10, 2)
np.linspace(0, 1, 5)
~~~

随机分析使用 Generator API 更容易显式控制随机源：

~~~python
rng = np.random.default_rng(42)
sample = rng.normal(loc=0, scale=1, size=1000)
~~~

固定 seed 有助于复现示例，但不代表随机实验只需一个 seed 就足以证明结论稳健。

## 4. 索引、切片与 view

~~~python
matrix = np.array([
    [1, 2, 3],
    [4, 5, 6],
])

print(matrix[1, 2])   # 6
print(matrix[:, 1])   # [2 5]
~~~

NumPy 切片常返回 view，修改切片可能影响原数组。需要独立数据时显式 copy。

~~~python
part = matrix[:, 1].copy()
~~~

## 5. 广播

~~~python
matrix = np.array([[1, 2], [3, 4]])
offset = np.array([10, 20])

print(matrix + offset)
~~~

广播从尾部维度比较：维度相等或其中一个为 1 才兼容。广播很强，但错误 shape 也可能“合法运行却语义错误”，所以分析前明确数组维度和观测单位。

## 6. 向量化与聚合

~~~python
values = np.array([1, 2, 3, 4])

print(values * 2)
print(values.mean())
print(values.std())
print(values.sum())
~~~

axis 决定沿哪个维度聚合。二维表中 axis=0/1 的含义必须结合 shape 解释，不要靠死记“行/列”。

## 7. pandas Series 与 DataFrame

~~~python
import pandas as pd

df = pd.DataFrame({
    "channel": ["web", "store", "web"],
    "amount": [100.0, 80.0, 120.0],
})
~~~

核心对象：

- Series：带索引的一维数据；
- DataFrame：共享行索引的二维列集合。

先查看：

~~~python
df.info()
df.head()
df.describe(include="all")
print(df.shape)
~~~

## 8. 选择数据

~~~python
amounts = df["amount"]
subset = df[["channel", "amount"]]

web = df.loc[df["channel"].eq("web"), ["channel", "amount"]]
first_two = df.iloc[:2]
~~~

loc 是按标签/条件；iloc 按整数位置。

赋值优先 loc，避免链式索引造成语义不确定：

~~~python
df.loc[df["amount"] < 0, "amount"] = pd.NA
~~~

## 9. 缺失值

先问“为什么缺失”，再决定填什么。

~~~python
df.isna().sum()
~~~

常见策略：

- 删除：缺失少且删除不会引入系统性偏差；
- 常数/中位数等填补：必须说明假设；
- 模型填补；
- 保留缺失指示变量；
- 业务规则回补。

不要为了让代码跑通一律 fillna(0)。0 与 unknown 是不同含义。

## 10. 重复值

~~~python
duplicates = df.duplicated(subset=["order_id"])
clean = df.drop_duplicates(subset=["order_id"], keep="first")
~~~

“重复”必须先定义观测单位。同一用户多次下单不是重复；完全相同的抓取记录可能才是。

## 11. 类型与日期

~~~python
df["created_at"] = pd.to_datetime(
    df["created_at"],
    errors="coerce",
    utc=True,
)
~~~

金额、分类、布尔、时间都应使用适合类型。字符串列“看起来像数字”会导致排序、聚合和缺失处理错误。

## 12. 分组与聚合

~~~python
summary = (
    df.groupby("channel", dropna=False)
      .agg(
          orders=("amount", "size"),
          revenue=("amount", "sum"),
          avg_order=("amount", "mean"),
      )
      .reset_index()
)
~~~

每个指标都应明确分母。平均客单价按订单还是按用户？先定义再 groupby。

## 13. Merge / Join

~~~python
result = orders.merge(
    customers,
    on="customer_id",
    how="left",
    validate="many_to_one",
)
~~~

validate 能帮助发现意外多对多导致的行数膨胀。合并前后检查行数、唯一键和未匹配率。

## 14. Matplotlib

推荐对象式 API：

~~~python
import matplotlib.pyplot as plt

fig, ax = plt.subplots()
ax.plot([1, 2, 3], [2, 4, 3])
ax.set(
    title="Trend",
    xlabel="Day",
    ylabel="Value",
)
fig.tight_layout()
~~~

常见图：

- line：时间/连续变化；
- bar：类别比较；
- scatter：两个数值关系；
- histogram：分布；
- boxplot：分布与离群；
- heatmap：矩阵/相关性。

图表先表达问题，不要为了“高级”堆 3D、双轴、过多颜色。

## 15. Seaborn

Seaborn 建在 Matplotlib 上，擅长统计语义映射：

~~~python
import seaborn as sns

sns.scatterplot(
    data=df,
    x="amount",
    y="margin",
    hue="channel",
)
~~~

pairplot、boxplot、violinplot、heatmap、regplot 等方便探索，但最终结论仍要回到统计假设和数据生成过程。

## 16. 相关性不等于因果

Pearson correlation 衡量线性关系，Spearman 更关注排序单调关系。高相关可能来自共同原因、选择偏差、时间趋势或数据泄漏。

不要从相关热图直接写“X 导致 Y”。

## 17. 描述统计

中心：

- mean；
- median；
- mode。

离散：

- range；
- variance；
- standard deviation；
- IQR。

分布偏斜或有极端值时，median/IQR 往往比 mean/std 更稳健，但选指标仍取决于问题。

## 18. Z-score 与分布

标准化：

~~~text
z = (x - mean) / standard_deviation
~~~

Z-score 的解释依赖分布和总体/样本定义。不能仅凭 |z| > 某固定阈值就自动判数据“错误”。

## 19. 离群值

IQR 方法：

~~~text
IQR = Q3 - Q1
lower = Q1 - 1.5 × IQR
upper = Q3 + 1.5 × IQR
~~~

这是探索规则，不是普遍真理。离群可能是错误，也可能是最有价值事件。先回到业务和数据来源核验。

## 20. 数据泄漏

分析/建模时常见：

- 用未来信息预测过去；
- 先全量计算统计量再拆训练测试；
- 同一实体跨训练/测试重复；
- 标签生成逻辑泄露到特征。

清洗步骤如果会从数据中“学习”参数，也应只在训练部分拟合。

## 21. 一个完整小例子

~~~python
import pandas as pd

sales = pd.DataFrame({
    "order_id": [1, 2, 2, 3],
    "channel": ["web", "store", "store", "web"],
    "amount": [100.0, None, None, 200.0],
})

sales = sales.drop_duplicates("order_id")
valid = sales.dropna(subset=["amount"])

summary = (
    valid.groupby("channel")
         .agg(
             orders=("order_id", "nunique"),
             revenue=("amount", "sum"),
             avg_amount=("amount", "mean"),
         )
)

print(summary)
~~~

解释结论时必须说明：订单 2 因 amount 缺失未进入金额平均，不应把它默默当 0。

## 22. 练习与答案

**练习 1**：为什么 fillna(0) 可能严重错误？  
**答案**：缺失通常表示未知/未采集，而 0 是一个真实观测值，会改变均值、分布和业务含义。

**练习 2**：merge 后行数突然翻倍先查什么？  
**答案**：连接键是否真的唯一；用 validate、duplicated 和匹配率检查是否发生意外多对多。

**练习 3**：相关系数很高能否推出因果？  
**答案**：不能。还需识别混杂、选择机制、时间顺序并采用合适因果设计。
