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
- 其他 Document 在单正样本训练假设下作为候选负样本；需过滤同义、重复或同样相关的“假负例”。

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

如果随机负例太容易，可以加入：

- 语义接近但答案错误；
- 同领域易混淆文档；
- BM25 / dense retrieval 找到的高分错误样本。

Hard Negative 的价值取决于标签是否可靠；挖到的高分文档可能其实相关，误标会破坏表示。

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

## 10. 看懂一行对比损失

有两个查询与两个文档，匹配对在对角线；温度缩放后的分数矩阵为 `[[2, 0], [1, 3]]`。第一行正确文档的概率为 `exp(2)/(exp(2)+exp(0))≈0.881`，损失约 `0.127`；第二行也有相同的分差，损失相同。损失迫使正确项相对候选项更高，并不让所有相关度成为绝对概率。

如果第二个文档其实也回答第一个问题，就不能无条件将它当负例；可去重、屏蔽相关负例或采用多正样本目标。训练与检索时还要保持 Query/Document 前缀、池化和归一化一致。更换 Embedding 模型后一般需要重建文档向量，不能把新查询向量直接与旧空间混用。

**自检**：向量维度相同能保证两个模型的向量可混合吗？

**核对**：不能。坐标空间和训练目标不同；必须使用匹配的编码链路，并以业务检索集复验。
