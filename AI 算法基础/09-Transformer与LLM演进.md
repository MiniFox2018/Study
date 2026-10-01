# 09｜Transformer 与 LLM 演进

> 本章只保留仍具有解释力的架构与训练思想；具体模型版本、榜单和旧 API 不作为长期结论。

## 1. Transformer 的核心改变

RNN 通过递归状态传递历史信息，序列计算天然串行。

Transformer 用 Self-Attention 建立任意位置之间的直接交互：

\[
Attention(Q,K,V)
=
softmax\left(\frac{QK^T}{\sqrt{d_k}}\right)V
\]

这带来两点根本变化：

1. 长距离依赖路径显著缩短；
2. 训练阶段可以高度并行。

## 2. Encoder / Decoder

### Encoder

典型：

```text
Embedding
→ Self-Attention
→ FFN
→ Representation
```

适合理解、分类、检索等表征任务。

### Decoder

增加 causal mask：

```text
过去 Token → 预测下一个 Token
```

现代通用 LLM 多采用 decoder-only 路线。

### Encoder-Decoder

输入由 Encoder 编码，Decoder 基于编码结果自回归生成。

适合翻译、摘要等 seq2seq 任务。

## 3. GPT 路线

### GPT-1

验证“生成式预训练 + 下游微调”。

### GPT-2

强化 zero-shot / task-agnostic language modeling 的可能性。

### GPT-3

规模扩大后，in-context learning 和 few-shot 能力显著出现。

长期结论不是“参数越大越好”，而是：

> 模型能力同时受到参数规模、数据规模、数据质量、训练计算和训练配方影响。

## 4. BERT 路线

BERT 使用双向 masked language modeling 获取上下文表征。

它推动了：

- pretrained encoder；
- fine-tuning paradigm；
- contextual embedding。

随后 RoBERTa、ALBERT、SpanBERT 等分别从训练配方、参数共享、span masking 等方向改进。

今天即使 decoder-only LLM 更受关注，BERT 类 Encoder 在分类、向量化、rerank 等场景仍有实际价值。

## 5. Seq2Seq 预训练

T5/BART 等把 NLP 任务统一为 text-to-text 或 denoising generation。

重要思想：

> 不同任务可以通过统一的输入输出接口共享同一预训练模型。

这直接影响后来 instruction tuning 的统一任务表达方式。

## 6. Position Representation

Transformer 原始实现使用 absolute sinusoidal position。

随后出现：

- learned position；
- relative position；
- RoPE 等。

长期问题不变：

> Attention 本身没有顺序概念，模型必须显式获得位置关系。

## 7. Scaling Laws

Scaling Law 研究说明 loss 与模型规模、数据规模、计算量之间存在可预测趋势。

Chinchilla 一类工作进一步指出：

> 在固定训练计算下，参数量和训练 Token 需要更合理地配比；过大的模型但数据不足并非最优。

工程启示：

- 参数规模不是唯一目标；
- data/token budget 是一等公民；
- 训练效率要看 compute-optimal，而不是只看模型大小。

## 8. Instruction Tuning

从 FLAN、T0、Self-Instruct、InstructGPT 到后续工作，一个长期趋势是：

```text
预训练模型
→ 多任务/指令数据
→ 更稳定的 instruction following
```

Instruction tuning 使用户可以用自然语言描述任务，而不必为每个任务训练独立头部。

## 9. Preference Alignment

从人类反馈学习的核心不是某一个算法，而是引入“偏好信号”。

基本链路：

```text
SFT
→ Preference Data
→ Reward / Direct Preference Optimization
→ Alignment Evaluation
```

今天具体可用 PPO、DPO、GRPO 等不同方案，但目标相同：

> 让模型输出分布更接近目标偏好，而不仅仅拟合训练语料。

## 10. In-Context Learning

模型参数不更新，仅通过上下文示例改变当前任务行为。

重要因素：

- demonstration selection；
- demonstration order；
- label distribution；
- instruction wording；
- context length。

因此 Prompt 不是“随便写一句自然语言”，而是推理时的数据设计。

## 11. Chain-of-Thought

CoT 的长期价值在于：

> 对需要多步中间状态的任务，通过显式或隐式的中间计算提高求解能力。

后续 Self-Consistency、Least-to-Most 等方法都在利用：

- decomposition；
- multiple reasoning paths；
- aggregation。

对于现代推理模型，不应把“展示完整思维过程”当作系统必须输出的接口；更重要的是任务分解、验证和可控推理预算。

## 12. Sentence Representation

从 Sentence-BERT、SimCSE 等工作中形成的关键方法：

- siamese / dual encoder；
- contrastive learning；
- positive/negative pair；
- pooling strategy。

这条路线直接连接今天的 Embedding、semantic search 和 RAG。

## 13. 架构阅读方法

面对新模型，不要背型号，按以下问题拆：

1. Transformer 类型：Encoder / Decoder / Encoder-Decoder？
2. Attention：MHA / GQA / MQA / MLA / local/global？
3. Position：absolute / relative / RoPE family？
4. Norm：LayerNorm / RMSNorm？Pre/Post？
5. FFN：GELU / SwiGLU？Dense / MoE？
6. Context：如何扩展？
7. KV Cache：如何降低推理成本？
8. Training：预训练数据和计算如何配比？
9. Post-training：SFT / preference / RL？
10. Serving：每 Token 激活多少参数、需要多少内存带宽？

## 14. 与现有知识库的关系

更完整的底层实现统一进入：

- [LLM 基础](../LLM%20%E5%9F%BA%E7%A1%80/README.md)

部署、微调、评测进入：

- [LLM 工程实践](../LLM%20%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/README.md)

本章只负责 Transformer/LLM 方法演进脉络。

来源：华校专 Transformer 系列章节及 Prompt/PEFT 相关论文整理。
