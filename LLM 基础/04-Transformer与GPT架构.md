# 04｜Transformer 与 GPT 架构

## 1. GPT 的核心组件

一个典型 Decoder-only Transformer 可以抽象为：

```text
Token Embedding
+ Position Information
      ↓
Transformer Block × N
      ↓
Final Normalization
      ↓
Linear Output Head
      ↓
Vocabulary Logits
```

## 2. Transformer Block

一个基础 Block 通常包含：

```text
Input
  ↓
LayerNorm
  ↓
Causal Multi-Head Attention
  ↓
Residual Add
  ↓
LayerNorm
  ↓
Feed-Forward Network
  ↓
Residual Add
```

现代模型具体使用 Pre-Norm、RMSNorm、SwiGLU 等变体，但这个骨架仍然成立。

## 3. Layer Normalization

LayerNorm 用于控制激活值尺度，帮助训练稳定。

核心作用：

- 让层间数值分布更稳定；
- 改善梯度传播；
- 支持更深网络训练。

现代架构可能改用 RMSNorm，但“需要稳定中间激活尺度”的目标不变。

## 4. Feed-Forward Network

Attention 负责 Token 间信息交互，FFN 负责对每个 Token 的内部特征做非线性变换。

经典结构：

```text
d_model → d_hidden → d_model
```

通常中间维度明显大于输入维度。

## 5. 激活函数

教学 GPT 常用 GELU。

现代模型也常使用：

- SiLU；
- SwiGLU 等。

不必把某种激活函数当成 Transformer 的定义本身。

## 6. Residual Connection

残差连接：

```text
output = x + F(x)
```

使深层网络更容易训练，帮助梯度跨层传播。

## 7. 输出层

最后的隐藏状态通过线性层映射到词表大小：

```text
hidden_state → vocabulary logits
```

logits 再转为 Token 概率。

## 8. Dense 与 MoE

传统 Transformer 的 FFN 每个 Token 都经过同一组参数。

Mixture-of-Experts（MoE）则维护多个 Expert，由 Router 为每个 Token 选择少量 Expert。

核心区别：

```text
Dense：所有参数都参与
MoE：总参数多，但每个 Token 只激活一部分
```

主要目标是在提高模型容量的同时控制单 Token 计算量。

## 9. 架构理解方法

看到新模型时，不要先背模型名，而应拆成几个问题：

- Attention 用什么形式？
- 位置编码怎么做？
- Norm 在哪里？
- FFN 是什么结构？
- Dense 还是 MoE？
- KV Cache 如何设计？
- 上下文长度如何扩展？
- 每 Token 激活多少参数？

用这组问题更容易比较不同 LLM 架构。

来源：<https://github.com/rasbt/LLMs-from-scratch/tree/main/ch04>
