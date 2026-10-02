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
- dynamic batching：请求到达后等待短窗口组成批次；
- continuous batching：通常在解码迭代间移除已完成请求、加入新请求。二者有关联，但不是完全相同的调度机制。

目标是在不显著增加尾延迟的情况下提高 GPU 利用率。

## 6. Prefill 与 Decode

LLM 推理通常分：

- prefill：处理整个 prompt，在常见长输入场景偏计算密集；
- decode：每请求每步生成少量 token，小批量时常偏内存带宽密集。

这是典型现象，实际瓶颈会随批大小、上下文、架构、量化和硬件变化，应以测量为准。

两阶段的性能模型不同，不能用同一个优化策略概括。

## 7. Speculative Decoding

核心思路：

```text
小/快模型先提出多个候选 token
→ 大模型并行验证
→ 一次接受多个
```

采用正确的接受/拒绝和修正采样算法时，可以保持目标分布；随意“接受看起来合理的候选”不满足这一保证。加速还取决于接受率、草稿成本、批大小与硬件，可能反而变慢。

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

## 17. 用一个请求预算做系统设计

教学目标：单用户本地查询，端到端延迟希望不超过 5 秒；输入 1000 Token，预期输出 100 Token。若测得排队/网络 0.2 秒、prefill 0.8 秒、decode 20 Token/s，则总时延粗算 `0.2+0.8+100/20=6 秒`，已超预算。压缩输出至 60 Token 可降至约 4 秒，但必须确认答案仍完整；单纯优化 prefill 0.1 秒无法解决主要瓶颈。

当输入输出长度分布变化时，必须重新测量。服务中的成功吞吐应只计满足质量与延迟约束的请求；否则通过无限排队得到的高吞吐没有交互价值。

**自检**：一个算法理论 FLOPs 减半，为什么实测可能不快？

**核对**：可能受带宽、通信、碎片化小算子、硬件不支持或调度开销限制；用剖析工具定位主要耗时后再优化。投机解码的正确性和速度也应分别验证。

核验依据（2026-10-02）：[投机解码原论文](https://arxiv.org/abs/2211.17192)。论文算法保证附带精确采样条件，论文中的加速倍数不外推到任意部署。
