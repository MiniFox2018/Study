# 04｜注意力机制与 Transformer

> 先修：点积、矩阵乘法、Softmax。先做一个 query 对两个 key 的计算，再扩大到多头；明确每个矩阵的轴比背结构名称更重要。

## 1. 注意力的基本问题

固定长度向量很难无损压缩长序列。注意力允许查询根据当前需求，从一组键值对中动态聚合信息。

基本抽象：

$$
\operatorname{Attention}(q,K,V)=\sum_i\alpha(q,k_i)v_i
$$

其中 $\alpha_i\ge0$ 且 $\sum_i\alpha_i=1$，通常由合法位置上的 Softmax 得到。

## 2. 从核回归理解注意力

Nadaraya-Watson 核回归可视为早期的“查询—键—值”加权平均：

- query：要预测的位置；
- key：训练样本位置；
- value：训练样本标签；
- kernel：相似度函数。

这说明注意力本质不是“Transformer 专属组件”，而是一种数据依赖的加权聚合机制。

## 3. Attention Scoring Function

常见评分：

### Additive Attention

通过可学习网络计算 query 与 key 的兼容度，适合维度不一致的情况。

### Scaled Dot-Product

$$
\operatorname{score}(q,k)=\frac{q^\top k}{\sqrt{d_k}}
$$

若 query/key 分量近似独立、均值为 0、方差为 1，点积方差约为 $d_k$；除以 $\sqrt{d_k}$ 将其尺度控制在常数量级。这是初始化附近的动机，不是任意训练后分布的严格保证。

## 4. Bahdanau Attention

经典 Seq2Seq 用一个固定 context 表示整个输入，长序列形成瓶颈。

Bahdanau Attention 让 decoder 每个时间步都重新对 encoder 的所有隐藏状态分配权重，从而产生动态 context。

它把“对齐”直接变成可学习、可微的模型组件。

## 5. Self-Attention

当 Q、K、V 都来自同一序列时，就是 Self-Attention。

优点：

- 任意位置之间路径短；
- 训练阶段可并行；
- 可以显式建模全局交互。

代价：

- 标准实现的注意力矩阵随序列长度呈 (O(n^2)) 增长。

## 6. Multi-Head Attention

多个 head 在不同投影子空间中独立计算注意力，再拼接：

$$
\operatorname{head}_i=\operatorname{Attention}(QW_i^Q,KW_i^K,VW_i^V)
$$

它允许模型同时学习不同关系模式。

现代模型可能改为 MQA/GQA 等以降低 KV Cache 成本，但多头分解思想仍是理解基础。

## 7. 位置编码

没有位置特征和位置相关 mask 的 Self-Attention 对输入排列等变。位置编码、相对位置偏置或结构性 mask 可以引入顺序信息；不能将带 causal mask 的系统与完全无位置结构的系统混为一谈。

D2L 重点介绍正弦位置编码。长期需要掌握的是：

- absolute position；
- relative position；
- rotary position（RoPE）；
- 位置外推与上下文长度是独立工程问题。

## 8. Transformer Encoder

典型 block：

```text
Self-Attention
→ Residual + Norm
→ FFN
→ Residual + Norm
```

Encoder 适合生成上下文表征。

## 9. Transformer Decoder

Decoder 在 Self-Attention 中使用 causal mask，确保位置 (t) 看不到未来 token；同时在 encoder-decoder 架构中再加入 cross-attention。

自回归生成必须保持训练与推理的因果约束一致。

## 10. Mask 的两类含义

需要区分：

- **padding mask**：忽略补齐位置；
- **causal mask**：阻止访问未来位置。

错误 mask 会造成隐蔽的数据泄漏或训练异常。

## 11. 为什么 Transformer 成为通用架构

关键不是“Attention 比 RNN 神奇”，而是组合优势：

- 全局交互；
- 高度并行；
- 残差网络；
- 归一化；
- FFN；
- 可扩展的数据和计算规模。

## 12. 与现代 LLM 的连接

从 D2L 的 Transformer 继续向现代 LLM 推导：

```text
MHA → MQA / GQA / MLA
absolute/sinusoidal → relative / RoPE
FFN → gated FFN / SwiGLU
LayerNorm → RMSNorm
dense → MoE
full attention → local / sparse / efficient attention
```

因此学习重点应是结构功能，而不是固定在 2017 年实现。

## 手算一次注意力

令 query $q=(1,0)$，两个 key 分别为 $(1,0)$ 和 $(0,1)$，$d_k=2$。打分为 $(1/\sqrt2,0)$，Softmax 权重约为 $(0.6698,0.3302)$。若两个 value 是标量 10 和 20，输出约为 13.3024。

自查：若第二个位置是未来 token，正确遮罩后输出是多少？**答案：**其 logit 设为负无穷再 Softmax，权重变成 $(1,0)$，输出为 10。只把其 logit 乘以 0 无法保证屏蔽，因为 Softmax(0) 仍分到正概率。

若某个 query 的全部位置都被遮罩，Softmax 可能出现未定义/NaN；构造 batch 和 mask 时要先防止这种情况。公式正确仍需要数据形状和合法位置共同正确。
