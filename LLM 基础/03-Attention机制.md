# 03｜Attention 机制

## 1. Attention 解决什么问题

序列中一个 Token 的含义通常依赖其他 Token。

Self-Attention 让每个位置根据当前输入，动态选择序列中哪些位置更重要。

最终得到的不是孤立 Token 表示，而是带上下文的表示。

## 2. Query、Key、Value

输入向量经过三个可训练投影得到：

```text
Q = XWq
K = XWk
V = XWv
```

可直观理解为：

- **Query**：当前 Token 在“寻找什么”；
- **Key**：每个 Token 提供“可以被匹配的特征”；
- **Value**：匹配后真正被聚合的信息。

## 3. Scaled Dot-Product Attention

核心计算：

```text
Attention(Q,K,V)
= softmax(QK^T / sqrt(d_k)) V
```

步骤：

1. Query 与 Key 做点积；
2. 得到 attention score；
3. 按维度缩放；
4. softmax 归一化；
5. 用 attention weight 加权 Value；
6. 得到 context vector。

缩放项用于缓解高维点积过大带来的 softmax 饱和问题。

## 4. Causal Mask

自回归语言模型训练时，当前位置不能看到未来 Token。

因此需要 causal mask：

```text
位置 i 只能关注 ≤ i 的位置
```

否则训练时模型会直接读取答案，造成信息泄漏。

## 5. Dropout

Attention 权重和其他网络层可以使用 dropout 作为正则化手段。

其作用不是改变模型结构，而是降低过拟合风险。

## 6. Multi-Head Attention

单个 Attention Head 只提供一个投影视角。

Multi-Head Attention 并行学习多组 Q/K/V：

```text
Head_1
Head_2
...
Head_n
  ↓
Concat
  ↓
Linear Projection
```

不同 Head 可以学习不同类型的依赖关系。

## 7. Attention 的计算瓶颈

固定隐藏维度时，标准全局 Self-Attention 在序列长度上的计算复杂度为：

```text
O(n²)
```

更完整地说，打分与加权聚合约需 O(n²d) 计算；朴素实现存储 O(n²) 分数矩阵。FlashAttention 一类实现可避免完整保存该矩阵、减少访存，但不会把精确全局注意力的理论计算量自动降为线性。

因此现代 LLM 会探索多种效率优化。

## 8. GQA

Grouped-Query Attention 的核心是：

> 多个 Query Head 共享较少数量的 Key/Value Head。

主要收益：

- 减少 KV Cache；
- 降低内存带宽压力；
- 通常比完整 MHA 更节省推理资源。

## 9. MLA

Multi-Head Latent Attention 的核心思路是：

> 用共享的低维潜在表示表达 K/V，并结合相应投影与位置编码设计减少需要缓存的状态。

目的同样是降低长上下文推理中的 KV Cache 内存占用；具体缓存还可能包含独立的位置相关 Key，不能把 MLA 当作在任何现有模型上随意压缩 K/V 的无损插件。

## 10. Sliding Window Attention

只让 Token 关注有限的局部窗口，可把部分长序列计算限制在固定范围。

它牺牲一部分全局可见性，以换取更低的计算和缓存成本。

## 11. 长期理解重点

不要只记某一种 Attention 变体。

更重要的是理解现代 Attention 优化都围绕三个目标：

1. 减少计算；
2. 减少 KV Cache；
3. 尽量保持建模能力。

来源：<https://github.com/rasbt/LLMs-from-scratch/tree/main/ch03>  
补充：<https://github.com/rasbt/LLMs-from-scratch/tree/main/ch04>

## 12. 用两个位置算一次注意力

设某个 Query 与两个 Key 的**缩放后分数**为 `[0, ln(3)]`，softmax 后权重为 `[1/4, 3/4]`。若两个 Value 分别为 `[2, 0]`、`[0, 4]`，输出就是 `[0.5, 3]`。这显示权重决定“取多少”，Value 决定“取什么”。如果第二个位置是未来位置，在 softmax **之前**把它的分数设为负无穷，权重变为 `[1, 0]`，输出为 `[2, 0]`。

**形状检查**：单头 `Q,K` 为 `n×d_k`，`V` 为 `n×d_v`；`QKᵀ` 为 `n×n`，最终结果为 `n×d_v`。softmax 对每个 Query 对应的 Key 维度归一化。

**自检**：把未来位置的分数直接设为 0，能否保证掩码生效？注意力权重大能否证明该词是答案的因果原因？

**核对**：不能，`exp(0)=1` 仍有正权重；需要在归一化前屏蔽。权重是中间计算量，不能单独代替干预实验或完整的模型解释。

原理依据：[Transformer 原论文](https://arxiv.org/abs/1706.03762)、[FlashAttention](https://arxiv.org/abs/2205.14135)。它们用于解释机制，不提供当前硬件性能保证。
