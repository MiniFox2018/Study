# 08｜语言学与经典 NLP

## 1. 为什么 LLM 仍需要 NLP 基础

Transformer 改变了建模方法，但语言本身的结构没有消失。理解语言学和经典 NLP，可以解释 tokenizer、任务定义、评测和模型错误。

## 2. Morphology

形态学研究词如何由更小单位组成：

- root/stem；
- prefix/suffix；
- inflection；
- derivation。

这直接影响 subword tokenization 和多语言建模。

## 3. Syntax

句法描述词如何组成短语和句子。

常见抽象：

- constituency；
- dependency；
- grammatical relation。

LLM 不一定显式构造 parse tree，但其注意力和表示仍要学到大量句法依赖。

## 4. Semantics 与 Pragmatics

- semantics：字面和组合意义；
- pragmatics：上下文、意图、会话含义。

同一句话在不同场景中含义不同，是语言模型无法只靠局部词共现解决的问题。

## 5. Phonology

语音语言还要处理音位、发音变化和韵律。它是语音模型和 text-speech 对齐的重要背景。

## 6. Tokenisation

经典单位：

- word；
- character；
- subword。

现代 LLM 使用 subword 的原因：

- 控制词表规模；
- 减少 OOV；
- 能组合稀有词；
- 跨语言更灵活。

## 7. N-gram

N-gram 假设：

```text
P(x_t | x_<t) ≈ P(x_t | 最近 n-1 个 token)
```

它的重要价值是提供“有限上下文语言模型”的基线，帮助理解长上下文模型到底改进了什么。

## 8. TF-IDF

TF-IDF 用词在文档中频繁、在全局中稀有来衡量重要性。

虽然不再是生成模型核心，但仍适用于：

- sparse retrieval；
- lexical baseline；
- explainable text features。

## 9. POS 与 NER

- POS tagging：词性；
- NER：人名、地名、组织、时间等实体。

现代模型通常端到端处理这些任务，但它们仍是语言结构和信息抽取的基本任务定义。

## 10. Word Embedding

Word2Vec / GloVe 把离散词映射到连续向量。

核心思想：

> 词义可从分布上下文中学习。

这为后来的 contextual embedding 奠定基础。

## 11. RNN / LSTM

RNN 按时间递归更新 hidden state；LSTM/GRU 通过门结构缓解长依赖训练困难。

它们今天不是主流大模型骨干，但仍适合理解：

- sequence state；
- recurrence；
- teacher forcing；
- vanishing gradient。

## 12. Seq2Seq

Encoder-decoder 将输入序列编码后生成输出序列，是机器翻译、ASR、summarization 的经典范式。

Attention 最初的重要意义之一就是打破“整个输入必须压进一个固定向量”的瓶颈。

来源：Compendium Chapter 07 前三节；与现有 tokenizer/embedding/attention 章节去重后补充语言学与经典 NLP 背景。
