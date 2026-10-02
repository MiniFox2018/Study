# 07｜训练与推理优化、LoRA

## 1. 优化分两类

### 训练优化

目标：

- 更稳定；
- 更快；
- 更省显存；
- 更高吞吐。

### 推理优化

目标：

- 更低延迟；
- 更高 Token/s；
- 更少 KV Cache；
- 更高并发。

两者不能混为一谈。

## 2. Learning Rate Warmup

训练初期逐渐提高学习率。

作用：

- 避免随机初始化阶段出现过大更新；
- 降低训练早期不稳定。

Warmup 不是固定比例，应通过模型规模和训练计划验证。

## 3. Learning Rate Decay

训练后期逐步降低学习率，可以减少在最优区域附近的震荡。

常见形式包括：

- cosine decay；
- linear decay。

具体选择属于训练策略，而不是模型架构本身。

## 4. Gradient Clipping

当梯度范数过大时，将其缩放到阈值范围。

主要用于降低：

- gradient explosion；
- 突然的训练不稳定。

它是安全阀，不是优化所有 loss 问题的万能手段。

## 5. Mixed Precision

较低精度训练可降低显存和提高吞吐。

现代训练常用 BF16 等格式。

实际效果依赖：

- GPU 架构；
- 算子支持；
- 数值稳定性。

因此不要直接照搬某张 GPU 的 benchmark。

## 6. Fused Kernels 与编译优化

训练加速常来自：

- fused optimizer；
- fused attention；
- 编译器优化；
- 更高效 kernel；
- 更好的数据传输。

核心原则：

> 优先减少 kernel 调用、内存搬运和重复计算。

## 7. KV Cache

自回归生成时，历史 Token 的 K/V 不需要每一步重新计算。

KV Cache 保存此前的 Key 和 Value，仅对新增 Token 计算新的 K/V。

收益：

- 显著减少重复计算；
- 提升生成速度。

代价：

- 占用显存；
- 上下文越长占用越大；
- 多并发时缓存压力显著。

## 8. KV Cache 的长期优化方向

主要思路包括：

- GQA：减少 K/V Head 数量；
- MLA：压缩 K/V 表示；
- Sliding Window：只保留局部可见范围；
- Cross-layer KV Sharing：跨层共享部分 KV。

它们本质上都在解决：

> 长上下文推理时 KV Cache 增长过快。

## 9. LoRA

对权重 W ∈ R^(d_out×d_in)，标准 LoRA 用低秩参数化限制可学习的更新：

```text
ΔW = (α/r) B A，A ∈ R^(r×d_in)，B ∈ R^(d_out×r)
```

而不是直接更新完整 W。

于是：

```text
W' = W + (α/r)BA
```

通常冻结原权重，仅训练 A、B；上式是适配器更新的定义，不是先做一次全量训练再拟合得到的近似。不同实现可采用不同缩放规则，必须记录实际配置。

## 10. LoRA 的价值

主要优势：

- 训练参数少；
- 显存需求低；
- 多任务可维护多个 Adapter；
- 不必为每个任务复制完整模型权重。

关键超参数包括：

- rank；
- scaling / alpha；
- 目标层选择。

## 11. LoRA 不等于永远更好

LoRA 适合：

- 小到中等规模任务适配；
- 算力有限；
- 需要多个任务 Adapter；
- 不希望改动基础模型。

但如果任务需要大幅改变模型知识或能力，全量微调或更大规模后训练可能更合适。

## 12. 优化时的正确顺序

不要一开始就堆所有“高性能技巧”。

更可靠的流程：

```text
正确性基线
  ↓
Profiler / 指标
  ↓
定位瓶颈
  ↓
单项优化
  ↓
重新验证效果与数值一致性
  ↓
继续下一项
```

每次只改少量变量，才能判断优化是否真正有效。

来源：<https://github.com/rasbt/LLMs-from-scratch/tree/main/appendix-D>  
来源：<https://github.com/rasbt/LLMs-from-scratch/tree/main/appendix-E>  
补充：<https://github.com/rasbt/LLMs-from-scratch/tree/main/ch04/03_kv-cache>

## 13. 手算 LoRA 与 KV 内存

一个 `1024×1024` 权重有 1,048,576 个参数；rank=8 的 LoRA 两个矩阵共 `8×1024 + 1024×8 = 16,384` 个可训练参数，为原层的 1/64。但原模型权重、激活和部分工作空间仍需存在，因此不能推断总训练显存也减少到 1/64。

普通 MHA/GQA 的 KV 缓存粗算为：`2×层数×批大小×序列长度×KV头数×每头维度×每元素字节数`。例如 2 层、批大小 1、长度 4、2 个 KV 头、头维 8、FP16 的 2 字节，得到 512 字节。这里只算 K/V 有效载荷，排除框架元数据、内存对齐、额外工作区；MLA 或混合注意力需用各自结构另算。

单请求 KV 缓存复用的是同一因果前缀；跨请求 Prefix Cache 还要求模型、Tokenizer、前缀 Token 和相关推理状态兼容。缓存不是模型“记住了事实”，也不是把不同用户数据随意混用。

**自检**：窗口长度翻倍，普通 KV 有效载荷如何变？用了 KV Cache 后，每个新 Query 还要访问历史 K/V 吗？

**核对**：其他条件相同则翻倍；仍要访问可见历史 K/V，因此缓存省去重算旧状态，并没有消除长上下文注意力成本。

核验依据（2026-10-02）：[PEFT LoRA](https://huggingface.co/docs/peft/main/en/conceptual_guides/lora)、[Transformers 缓存说明](https://huggingface.co/docs/transformers/main/en/kv_cache)。所链 main 文档是开发分支；运行时应切换到实际安装版本。
