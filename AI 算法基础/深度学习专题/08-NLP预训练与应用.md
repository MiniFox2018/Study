# 08｜NLP 预训练与应用

> 先修：序列概率、Embedding、注意力。先理解正负样本与遮盖标签如何构造，历史模型名作检索入口。

## 1. 从静态词向量到上下文表示

经典文本表示经历：

```text
one-hot
→ Word2Vec / GloVe
→ subword
→ contextual representation
→ pretrained Transformer
```

长期主线是：表示越来越依赖上下文，同时预训练任务越来越充分利用无标注数据。

## 2. Word2Vec

### Skip-Gram

给定中心词预测上下文。

### CBOW

给定上下文预测中心词。

训练目标本质上在学习哪些词出现在相似上下文中。

## 3. Negative Sampling

完整 Softmax 需要遍历整个词表，成本高。

Negative Sampling 改写训练目标为区分真实共现对与噪声对的二分类：

- 正样本：真实共现词对；
- 负样本：按噪声分布采样的错误词对。

它降低了训练成本，但不是归一化 Softmax 概率或其梯度的直接无偏估计；不要把负采样与 sampled softmax 混为一谈。

## 4. Hierarchical Softmax

Hierarchical Softmax 把大词表概率计算组织成树上的路径判定，使单次计算从遍历整个词表转化为沿树路径完成若干二分类。

它与 Negative Sampling 都是在解决大词表 Softmax 的计算瓶颈：前者重构输出空间，后者改写训练目标。

## 5. GloVe

GloVe 利用全局词共现统计，把词向量学习与共现矩阵结构结合。

Word2Vec 更强调局部预测任务；GloVe 更显式使用全局统计，两者都属于静态词表示。

## 6. Subword Embedding

单词级词表面临：

- OOV；
- 稀有词；
- 形态变化。

子词方法通过字符 n-gram 或 BPE/WordPiece 等单元复用结构，使模型能够组合表示新词。

现代 LLM tokenizer 正是这条思想的延续。

## 7. Similarity 与 Analogy

词向量常用：

- cosine similarity；
- nearest neighbor；
- analogy；

来检查语义结构。

这些可用于教学诊断，但不能把简单类比测试当成完整语言理解能力。

## 8. BERT

BERT 使用 Transformer Encoder 产生双向上下文表示。

核心任务：

### Masked Language Modeling

随机遮盖输入 token，让模型恢复被遮盖内容。

它让每个 token 的表示同时利用左右上下文。

### Next Sentence Prediction（历史任务）

原始 BERT 还加入 NSP，判断两个句子是否具有连续关系。后续研究并不都保留 NSP，因此这里把它作为 BERT 原始训练设计与方法演进的一部分，而不是现代预训练的必需组件。

### 预训练 → 微调

预训练阶段学习通用表示，下游任务只需加入较小任务头并联合微调。

这一范式深刻影响后续 foundation model。

## 9. BERT 数据构造

重要工程点：

- tokenizer；
- special token；
- segment / position；
- masking strategy；
- padding mask；
- mini-batch。

具体 mask 比例不是永久知识；更重要的是理解“自监督地从原始文本生成监督信号”。

## 10. 情感分析

D2L 分别展示 RNN 与 CNN 文本分类。

长期意义是：

> 下游任务不只有一种正确架构，关键是输入表示、聚合方式和任务监督如何配合。

TextCNN 通过不同窗口卷积抽取局部 n-gram 特征；RNN 则按顺序聚合状态。

## 11. Natural Language Inference

NLI 输入 premise 与 hypothesis，判断关系，例如 entailment / contradiction / neutral。

它是研究“文本对关系”的典型任务。

经典 attention-based 方法通过跨句对齐，再进行比较和聚合。

## 12. BERT Fine-tuning

BERT 可用统一 backbone 处理：

- 单文本分类；
- 文本对分类；
- token classification；
- QA 等。

典型方式：

```text
pretrained encoder
→ task-specific head
→ end-to-end fine-tuning
```

## 13. 与现代 LLM 的关系

D2L 的 NLP 章节停留在 BERT 时代，但其长期知识直接连接现代模型：

- self-supervised pretraining；
- subword tokenization；
- contextual representation；
- attention/Transformer；
- pretrain → adapt；
- embedding reuse；
- task transfer。

现代 decoder-only LLM、instruction tuning、RAG 等是在这些基础上继续发展。

## 14. 不再固化的旧实现

不保存：

- D2L 当时特定框架的 tokenizer/API；
- 旧版预训练模型下载方式；
- 旧 benchmark；
- 固定库版本。

执行时统一查当前 PyTorch / Hugging Face 等官方文档。

## 从一句话构造两种训练信号

用空格切分的教学句子“猫 坐 在 垫子 上”（此处不用真实子词分词器）：

- Skip-Gram，窗口半径 1，以“在”为中心得到正对 `(在, 坐)`、`(在, 垫子)`；负样本来自指定噪声分布，采样结果可能偶然也是合理上下文，因此不是人工真值“错误词对”。
- MLM，遮盖“垫子”，输入为“猫 坐 在 [MASK] 上”，目标只在选中位置预测原 token；未选位置与 padding 不应同等计入这个教学目标。

自查：将“垫子”也作为输入某个额外字段传入，再评估恢复准确率，能证明学到了语义吗？**答案：**不能，答案泄漏会使目标变成复制。真实预训练还要检查文档重复、分词和 train/test 污染。
