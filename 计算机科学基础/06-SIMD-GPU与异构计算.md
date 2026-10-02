# 06｜SIMD、GPU 与异构计算

## 1. 为什么 AI 工程需要理解硬件

高层框架最终都要落到：

```text
Tensor expression
→ operator graph
→ kernel
→ ISA / accelerator
→ memory hierarchy
```

性能优化的本质通常是：让更多时间花在有效计算，而不是等待数据、同步或启动小任务。

## 2. SIMD

SIMD = Single Instruction, Multiple Data。

一条指令同时处理多个元素，适合：

- vector arithmetic；
- dot product；
- convolution；
- quantized arithmetic。

关键是：

- 数据连续；
- 对齐；
- 足够大的批量；
- 减少分支。

## 3. ARM Vector Extensions

ARM 平台常见向量/矩阵扩展包括 NEON，以及面向低精度矩阵运算的后续扩展。

理解重点不是记某代指令名字，而是：

- vector width；
- register blocking；
- integer dot product；
- matrix tile；
- load/store bandwidth。

这些决定移动端和边缘 AI 的上限。

## 4. x86 AVX

AVX 系列提供更宽向量寄存器和 SIMD 指令。

优化时要考虑：

- instruction availability；
- alignment；
- vectorization；
- cache；
- frequency / thermal tradeoff。

跨 CPU 发布时不能假设所有机器支持同一 ISA 子集。

## 5. GPU 的 SIMT

GPU 更接近 SIMT：

- 大量轻量线程；
- warp/wavefront 成组执行；
- 高吞吐而非单线程低延迟。

关键对象：

- grid / block / thread；
- warp divergence；
- shared memory；
- registers；
- global memory；
- synchronization。

## 6. Memory Coalescing

GPU 经常不是“算力不够”，而是内存访问模式差。

优化重点：

- 连续访问；
- coalesced load/store；
- reuse；
- shared memory tiling；
- 减少 host-device copy。

## 7. CUDA Kernel 思维

高性能 kernel 通常需要同时设计：

- work partition；
- tile size；
- memory layout；
- occupancy；
- register pressure；
- synchronization。

因此“理论 FLOPs 很高”不代表实际 kernel 快。

## 8. Triton

Triton 的价值是用更高层的 block/tile 抽象表达 GPU kernel，同时让编译器完成大量底层映射。

长期要掌握的是：

> 用数据块、并行映射和内存层次设计 kernel。

具体 API 版本不写死。

## 9. TPU 与矩阵加速器

TPU/矩阵引擎把 dense matrix multiply 作为核心工作负载，常通过 systolic / tiled execution 提高数据复用。

因此模型结构、shape 和 dtype 是否适合矩阵单元，直接影响吞吐。

## 10. RISC-V 与嵌入式

RISC-V 提供开放 ISA 和可扩展指令体系。

边缘部署的核心约束：

- memory；
- power；
- real-time；
- quantization；
- compiler support；
- accelerator integration。

## 11. Vulkan / WebGPU 等跨平台 Compute

跨平台 GPU API 的价值在于覆盖非 CUDA 设备。

需要理解：

- shader/compute kernel；
- buffer；
- dispatch；
- synchronization；
- device portability。

具体生态仍快速变化，主库只保留抽象。

## 12. 与 C++ / AI 的关系

- [C++](../C++/)：语言与系统编程能力；
- [深度学习计算性能](../AI%20%E7%AE%97%E6%B3%95%E5%9F%BA%E7%A1%80/%E6%B7%B1%E5%BA%A6%E5%AD%A6%E4%B9%A0%E4%B8%93%E9%A2%98/06-%E8%AE%A1%E7%AE%97%E6%80%A7%E8%83%BD%E4%B8%8E%E5%B9%B6%E8%A1%8C%E8%AE%AD%E7%BB%83.md)：分布式训练；
- [LLM 工程实践](../LLM%20%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/README.md)：模型推理与部署。

来源：Compendium Chapter 16 全八节。

## 13. 算一次带宽上界，再决定优化方向

考虑 FP32 向量加法 `c[i]=a[i]+b[i]`，理想情况下每个元素读两个 4 字节数、写一个 4 字节数，约传输 12 字节，只做 1 次加法。忽略缓存、写分配等细节时，算术强度约为 `1/12 FLOP/byte`。

若**假设**可持续内存带宽 120 GB/s，则带宽给出的上界约 `120/12=10 GFLOP/s`；这是假设演算，不是某款设备实测。即使峰值计算能力远高于 10 GFLOP/s，这个任务仍可能受内存带宽限制。Roofline 的基本约束为 `可达计算吞吐 ≤ min(计算峰值, 带宽 × 算术强度)`。

自测：提高 occupancy 一定变快吗？答：不一定。它可能增加寄存器压力、溢出或同步成本；更高驻留比例只是隐藏延迟的手段，不是最终性能指标。GPU 计时要确认异步任务已完成，并区分内核耗时与主机传输/启动的端到端耗时。

平台边界：CUDA 需要受支持的 NVIDIA GPU/驱动；本机 Apple Silicon 的 GPU 学习通常走 Metal 或兼容框架。不能把 CUDA 命令直接当 macOS 原生可运行练习。
