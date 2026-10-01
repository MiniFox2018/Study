# 04｜注意力机制与 Transformer

## 1. 注意力的基本问题

固定长度向量很难无损压缩长序列。注意力允许查询根据当前需求，从一组键值对中动态聚合信息。

基本抽象：

[
Attention(q,K,V)=sum_i alpha(q,k_i)v_i
]

其中 (alpha) 是归一化的相关性权重。

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

[
score(q,k)=rac{q^	op k}{sqrt{d}}
]

除以 (sqrt d) 是为了避免维度增大后点积方差过大，导致 Softmax 饱和。

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

[
head_i=Attention(QW_i^Q,KW_i^K,VW_i^V)
]

它允许模型同时学习不同关系模式。

现代模型可能改为 MQA/GQA 等以降低 KV Cache 成本，但多头分解思想仍是理解基础。

## 7. 位置编码

Self-Attention 本身对顺序没有天然感知，因此必须注入位置信息。

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