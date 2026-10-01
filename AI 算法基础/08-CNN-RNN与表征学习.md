# 08｜CNN、RNN 与表征学习

## 1. CNN 的两个归纳偏置

- local connectivity；
- weight sharing。

卷积核在空间复用，因此参数少于完全连接。

## 2. Stride / Padding / Dilation

- Stride：采样步长；
- Padding：控制边界与尺寸；
- Dilation：扩大 receptive field。

## 3. Pooling

Max/Average Pooling 用于下采样、提高局部不变性、增大有效感受野。现代网络也常用 stride convolution 替代部分 pooling。

## 4. CNN 架构演进

### LeNet

早期端到端 CNN。

### AlexNet

GPU + ReLU + 大规模数据推动深 CNN。

### VGG

重复简单 block，强调 depth。

### Inception

并行多尺度分支。

### ResNet

\[
y=F(x)+x
\]

Residual connection 显著改善深网络优化。

### DenseNet

密集跨层连接，促进 feature reuse。

### SENet

通过 channel attention 重标定通道。

这些模型不一定是当前 SOTA，但核心设计思想仍有效。

## 5. RNN

\[
h_t=f(W_xx_t+W_hh_{t-1}+b)
\]

隐藏状态显式携带历史信息。

## 6. BPTT

时间展开后反向传播，容易出现 vanishing/exploding gradient 和长距离依赖困难。

## 7. LSTM / GRU

LSTM 通过 forget/input/output gate 和 cell state 提供更稳定长期信息路径；GRU 用更简化门结构达到类似目标。

## 8. Transformer 为什么替代很多 RNN

RNN 时间维串行，长距离路径长；Transformer 通过 self-attention 直接连接任意位置，并更适合训练并行。

RNN 仍是理解 state、sequence dynamics 与 streaming system 的重要基础。

## 9. Word Embedding

Word2Vec：

- CBOW；
- Skip-Gram；
- negative sampling。

GloVe：利用全局共现。

FastText：加入 subword，提高 rare/OOV 表示能力。

## 10. Contextual Embedding

ELMo/BERT 之后，同一个词在不同上下文中拥有不同表示，static embedding 走向 contextual representation。

## 11. Sentence Embedding

方法演进包括：

- pooling；
- supervised pair；
- NLI；
- contrastive learning；
- SimCSE 等。

最终连接现代 Embedding 与 RAG。

## 12. 统一视角

CNN、RNN、Transformer 都在解决：

```text
raw input → useful representation → task
```

真正长期的能力是判断任务需要什么 inductive bias。

来源：华校专 CNN、RNN、词向量、句子向量相关章节。
