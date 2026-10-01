# 11｜AI 推理与 ML Systems Design

> 来源增补：Compendium Chapters 17～18  
> 基准提交：`9850ee574a370bc1cde59de98b394e953775b67d`

## 1. 推理系统真正优化什么

模型部署通常要在多个指标之间权衡：

- latency；
- throughput；
- memory；
- cost；
- quality；
- reliability。

“每秒 token 数最高”不等于适合所有业务。

## 2. Quantization

量化将高精度参数/激活映射到更低位宽。

需要区分：

- weight-only；
- weight + activation；
- per-tensor / per-channel / group-wise；
- post-training quantization；
- quantization-aware training。

关键问题：

> 压缩后误差是否落在模型敏感方向上？

大模型还要关注 outlier、KV cache 和校准数据。

## 3. Efficient Architecture

模型效率可从架构层改进：

- parameter sharing；
- sparsity；
- MoE；
- low-rank；
- efficient attention；
- recurrent/state-space；
- KV compression。

不要把“更少 FLOPs”自动等同于“更低延迟”，硬件利用率决定最终效果。

## 4. KV Cache

Autoregressive decoding 会复用历史 K/V，避免每一步重算过去 token。

KV cache 带来：

- 显存占用随 batch、context、layers、heads 增长；
- 长上下文和高并发时成为主要容量瓶颈。

因此服务系统需要管理 block/page、复用和淘汰。

## 5. Batching

- static batching：请求整批处理；
- dynamic/continuous batching：动态把新 token step 插入批次。

目标是在不显著增加尾延迟的情况下提高 GPU 利用率。

## 6. Prefill 与 Decode

LLM 推理通常分：

- prefill：处理整个 prompt，偏计算密集；
- decode：每步生成少量 token，偏内存/带宽密集。

两阶段的性能模型不同，不能用同一个优化策略概括。

## 7. Speculative Decoding

核心思路：

```text
小/快模型先提出多个候选 token
→ 大模型并行验证
→ 一次接受多个
```

目标是减少大模型串行解码步数，同时保持目标模型分布正确。

## 8. Edge Inference

边缘设备额外受限于：

- memory；
- power；
- thermal；
- unsupported ops；
- startup time。

常用手段：

- quantization；
- distillation；
- pruning；
- operator fusion；
- hardware-specific backend。

## 9. Scaling 与 Deployment

服务扩展要考虑：

- replica；
- load balancing；
- queue；
- autoscaling；
- model sharding；
- cache；
- fault isolation。

多 GPU 不只是“把模型切开”，还要处理通信、拓扑和容错。

## 10. System Design Fundamentals

设计系统先确定：

1. functional requirements；
2. scale；
3. SLO；
4. data model；
5. interfaces；
6. bottleneck；
7. failure mode。

然后才选择数据库、队列、缓存或云产品。

## 11. Cloud / Distributed Systems

长期抽象：

- compute；
- object/block storage；
- network；
- queue/stream；
- database；
- orchestration。

分布式系统必须面对：

- partial failure；
- replication；
- consistency；
- idempotency；
- retry；
- partition。

## 12. ML Lifecycle

```text
data
→ feature / representation
→ train
→ evaluate
→ registry
→ deploy
→ monitor
→ feedback
```

每一步都要可追溯，否则无法解释线上变化来自哪里。

## 13. Feature Store 与 Online/Offline 一致性

Feature Store 的核心价值不是一个产品，而是解决：

- feature definition reuse；
- point-in-time correctness；
- training-serving skew；
- online low-latency lookup。

LLM/RAG 场景中的 embedding、retrieval feature 也可以用同样思想理解。

## 14. Experiment / A-B

线上实验必须明确：

- unit of randomization；
- treatment/control；
- primary metric；
- guardrail metric；
- exposure；
- novelty / interference。

离线指标提升不等于线上业务提升。

## 15. 设计案例的共性

推荐、搜索、广告、风控等系统虽然业务不同，但都可以拆成：

```text
candidate generation
→ ranking/scoring
→ constraints/policy
→ serving
→ feedback
```

需要同时处理数据偏差、延迟、冷启动和反馈环。

## 16. 决策原则

优化顺序：

```text
正确性
→ 可观测性
→ 基线性能
→ 定位瓶颈
→ 再做量化/并行/缓存/架构优化
```

不要先堆复杂优化再寻找问题。

具体框架 API、硬件型号和云产品能力变化快，执行前重新核验。
