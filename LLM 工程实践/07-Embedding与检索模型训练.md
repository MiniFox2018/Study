# 07｜Embedding 与检索模型训练

## 1. Embedding 模型的训练目标与生成模型不同

生成模型预测 Token。

Embedding 模型希望：

- 相关 Query / Document 更近；
- 不相关样本更远。

## 2. 对比学习

一个常见目标：

```text
query → q
positive document → p+
negative document → p-
```

优化后：

```text
sim(q,p+) ↑
sim(q,p-) ↓
```

## 3. In-batch Negatives

在一个 Batch 中：

- 第 i 个 Query 与第 i 个 Document 是正样本；
- 其他 Document 自动作为负样本。

若 Batch 大小为 N，每个 Query 最多得到 N-1 个批内负样本。

这可以提高负样本利用效率。

## 4. 相似度矩阵

对 Query 矩阵 Q 和文档矩阵 P：

```text
S = QPᵀ / τ
```

若向量已做 L2 normalize，点积对应 cosine similarity。

目标通常让矩阵对角线更高。

## 5. Temperature

`τ` 控制 softmax 分布尖锐程度。

较低温度：

- 放大相似度差异；
- 提高 hard negative 的训练压力。

但太低会影响稳定性，应通过验证集调节。

## 6. Batch Size

In-batch negative 使 Batch Size 与负样本数直接相关。

更大 Batch 往往能提供更丰富负样本，但代价包括：

- 显存；
- 通信；
- 训练成本。

不能简单认为“越大越好”。

## 7. Hard Negative

随机负样本往往太容易。

高质量检索训练需要加入：

- 语义接近但答案错误；
- 同领域易混淆文档；
- BM25 / dense retrieval 找到的高分错误样本。

Hard Negative 往往比简单扩大数据量更重要。

## 8. 训练后如何评估

不要只看 loss。

至少看：

- Recall@k；
- MRR；
- nDCG；
- 不同领域 slice；
- 不同 Query 长度；
- 不同文档长度；
- latency；
- index size。

## 9. 与 RAG 的关系

Embedding 的最终价值必须回到 RAG：

```text
Embedding Improvement
        ↓
Retrieval Improvement
        ↓
Context Improvement
        ↓
Answer Improvement
```

如果 embedding benchmark 上升但业务检索不变，价值有限。

来源：<https://github.com/datawhalechina/self-llm/tree/master/models/BGE-M3-finetune-embedding-with-valid>
