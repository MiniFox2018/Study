# 12｜Prompt、PEFT 与量化

> 先修：矩阵乘法、微调与训练显存构成。先能区分“更少可训练参数”和“更少存储位数”，再选择具体方法。

## 1. 三种“改变模型行为”的层级

```text
Context / Prompt
→ Parameter-Efficient Adaptation
→ Full Parameter Training
```

原则：

> 能通过更便宜、更可逆的上层方法解决，就不急于修改全部模型参数。

## 2. Prompt 的本质

Prompt 不只是自然语言问题，它可以包含：

- instruction；
- demonstrations；
- output schema；
- constraints；
- context；
- tools；
- state。

对于 in-context learning，Prompt 本身就是推理阶段临时提供的数据。

## 3. Demonstration Selection

Few-shot 示例的选择非常重要。

理想示例应：

- 与当前 query 相关；
- 覆盖任务边界；
- 输出质量高；
- 格式一致；
- 不引入冲突。

KATE/EPR 等路线本质上研究：

> 怎样检索更适合当前输入的 demonstrations。

这直接连接现代动态 few-shot 和 RAG-style prompt construction。

## 4. Order Sensitivity

Few-shot LLM 可能对示例顺序敏感。

因此：

- 不应只凭单一顺序评估；
- 可做随机排列；
- 稳定任务应降低顺序带来的方差。

## 5. Calibration

模型在 few-shot 下可能存在 label/token prior bias。

早期 Calibration 工作提示：

> Prompt 评测中要区分真实任务能力与由 label order / token frequency 产生的偏差。

## 6. Chain-of-Thought

CoT 提供中间推理结构。

演进：

- Scratchpad；
- CoT；
- Self-Consistency；
- Zero-Shot CoT；
- Auto-CoT；
- Least-to-Most。

长期抽象：

```text
Complex Task
→ Decomposition
→ Intermediate State
→ Verification / Aggregation
→ Answer
```

## 7. Soft Prompt

Hard Prompt 使用离散 Token。

Soft Prompt 学习连续向量：

$$
P\in\mathbb R^{m\times d}
$$

输入层 Prompt Tuning 将其拼到输入 embedding；更广义的连续提示方法也可在中间层引入参数。

代表：

- Prompt Tuning；
- Prefix Tuning；
- P-Tuning。

## 8. Prefix Tuning

不是修改全部模型，而是在 Transformer 各层引入可训练 prefix key/value。

优点：

- 参数少；
- 每个任务维护小规模参数。

## 9. Adapter

在 Transformer 层中加入小型 bottleneck module：

```text
hidden
→ down-project
→ nonlinearity
→ up-project
→ residual
```

Base model 可冻结。

AdapterFusion 进一步组合多个已训练 Adapter。

## 10. LoRA

用低秩参数化近似权重更新。若 $W\in\mathbb R^{d_{out}\times d_{in}}$，则 $B\in\mathbb R^{d_{out}\times r}$、$A\in\mathbb R^{r\times d_{in}}$，通常另乘缩放 $\alpha/r$：

$$
\Delta W=BA
$$

其中 rank：

$$
r\ll d
$$

训练时冻结 W，仅更新 A/B。

价值：

- 参数少；
- 显存低；
- Adapter 可独立管理；
- 易于多任务切换。

## 11. QLoRA

QLoRA：

```text
Quantized Base Model
+ LoRA Adapter
→ Memory-efficient Fine-tuning
```

重要思想：

- 基础权重低比特存储；
- 计算仍使用合适的计算 dtype；
- 只训练 LoRA。

## 12. BitFit

只训练 bias 参数。

它证明：

> 某些下游适配并不一定需要更新大量参数。

但实际效果高度依赖任务和模型。

## 13. 量化目标

量化将高精度表示转换到低比特：

```text
FP32 / BF16 / FP16
→ INT8 / INT4 / FP8 / other low-bit
```

潜在收益（取决于硬件与 kernel 支持，并非低比特就必然更快）：

- 更小权重；
- 更少 memory bandwidth；
- 更高吞吐；
- 更低 serving cost。

## 14. PTQ 与 QAT

### PTQ

Post-Training Quantization：训练完成后做量化，许多方法仍需要代表性校准数据，以选取尺度或补偿误差。

优点：

- 简单；
- 不需要重新大规模训练。

### QAT

Quantization-Aware Training：训练中模拟量化误差。

通常能获得更好的低比特精度，但成本更高。

## 15. Weight-only vs Weight+Activation

### Weight-only

只量化权重，activation 仍较高精度。

部署简单，很多 LLM 推理采用。

### W+A

权重和 activation 都低比特，潜在加速更大，但校准/数值稳定性更困难。

## 16. Outlier

LLM activation 往往存在 outlier channels。

LLM.int8、SmoothQuant 等方法的关键贡献之一就是：

> 处理少量极端值，避免它们迫使整个张量使用过大的量化范围。

SmoothQuant 通过变换把 activation 的量化困难转移到 weight。

## 17. GPTQ

GPTQ 是典型 post-training weight quantization。

核心思想：

- 分块量化；
- 利用二阶/近似 Hessian 信息；
- 逐步补偿量化误差。

## 18. SparseGPT

把 pruning 与近似二阶信息结合，在一次性后训练处理下获得高稀疏度。

长期启示：

> 压缩不仅看单个权重大小，也可以利用参数间误差补偿关系。

## 19. Mixed Precision

不同张量/操作不一定需要同样精度。

现代训练常混合：

- BF16/FP16；
- FP32 accumulations；
- 更低精度 kernel。

其本质是：

> 在数值稳定性和硬件效率之间分配精度预算。

## 20. 选择路线

### 只改变当前任务行为

Prompt / few-shot。

### 需要可训练但轻量

LoRA / Adapter / soft prompt。

### 显存不足的微调

QLoRA 类方案。

### 推理显存/吞吐瓶颈

PTQ / optimized low-bit serving。

### 需要极低精度

先建立高精度 baseline，再评估每层误差、任务指标和硬件 kernel 支持。

## 21. 不保留旧实现的原因

量化框架、kernel、支持的 bit format 和 GPU/NPU 能力变化非常快。

因此本章保留：

- 方法；
- 数值原理；
- 选择条件。

具体 `transformers`、`bitsandbytes`、`AutoGPTQ`、推理引擎命令在执行时重新查当前官方文档。

来源：华校专 Prompt Engineering、PEFT、LLM Quantization 系列章节。

## 估算 LoRA 与量化节省什么

一个 $4096\times4096$ 权重矩阵有 16,777,216 个参数。取 $r=8$ 的 LoRA，两个低秩矩阵合计 $8\times4096+4096\times8=65,536$ 个参数，约为原矩阵的 0.39%。但前向仍需原始权重，激活也不会因为这 0.39% 自动消失。

仅看权重裸数据，16-bit 存储约 32 MiB，4-bit 约 8 MiB；真实内存还包括量化尺度、零点/元数据、临时反量化、激活与缓存。

自查：QLoRA 是否把所有反向计算都变成 4-bit？**答案：**不是。基础权重低比特存储并冻结，通过较高精度计算把梯度传给 LoRA 参数。原论文采用 NF4、双重量化和分页优化器等设计，不能把所有低比特微调都当作同一个配置。

核验（2026-10-02）：[QLoRA 原论文](https://arxiv.org/abs/2305.14314)。
