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

## 路由与推理算法的可计算例子

MoE的top-k、容量与丢弃/负载目标，KV与Flash的计算/访存区别，以及推测采样的接受/残差/bonus步骤见[Transformer推理与规模设计](14-Transformer推理与规模设计.md)。本章保留设备、调度与端到端系统判断；接受率、FLOPs或理论载荷不能单独证明硬件延迟改善。

## 18. 托管调用、专用端点与自管集群的边界

托管平台解决的是模型访问、容量与运维责任，不是一条恒定的性能排名。可把选择拆成三层：**模型与功能**（目标修订、上下文、结构化输出、工具、微调/adapter），**执行与隔离**（共享按需、预留吞吐、专用端点、自管节点），**管理接口**（身份、网络、日志、计费与数据处理边界）。硬件类型、Python开发体验、模型市场与计费模式是不同维度，一个平台可能同时提供多种形态。

共享按需通常适合变化大、可接受容量波动的请求；预留/专用容量用固定投入换更可规划的吞吐；自管保留调度、模型和缓存控制，也承担驱动、更新、值班与故障恢复。预留容量不必等于某租户独占一块实体GPU，更不保证网络、排队和端到端P99；要读取供应商对容量单位和超额流量的具体合同。

AWS Bedrock的inference profile可把调用绑定到模型和一个/多个区域，application profile用于用量与费用归属。CloudWatch的调用指标与账单成本分配是两个环节：标签还需按费用分配流程启用，不能说“一个usage图自动完成准确成本归属”。Azure的资源组/subscription标签**不会自动继承到子资源**，需要显式标签或Policy；资源标签也不等于每请求的user/tenant/task账本。GCP的项目、labels和账单导出同样要与请求计数对账。三者的目录、部署类型和日志策略使用前核实，不用“哪家最透明”代替验证。

备援是选择而非统一强制“双供应商”。先列出相关故障：区域、账号/配额、模型端点、网络和共享上游；两家代理同一上游不一定独立。若fallback换模型，要先评输出schema、质量、工具权限、上下文截断、日志和数据位置。主服务超时后重试涉及外部效果时，还需请求ID和幂等回执。备援费用包括空闲、复制状态、额外评测、网络、运维及切换错误；不能固定写“额外13%”“两家一定便宜”。来源课“Azure OpenAI目录无Llama”却比较它的Llama405B延迟自相矛盾，50/75ms及所谓25ms差不进入排名。

## 19. 把账单还原成相同工作负载

按token费可写 $C_{api}=(I p_I+O p_O)/10^6+C_{cache}+C_{other}$，I/O是输入/输出token数，p是对应百万token单价，cache项按供应商的创建/命中/存储规则，other包括网关、检索、工具等。按算力时间费则按**收费的就绪、执行、空闲、启动时段**计入 `Σ GPU_count×hourly_rate×billed_hours`，另加CPU/内存/存储/出网和运维。每prediction收费还要固定一次prediction的输入、输出、步数和失败计费边界。Replicate官方说明私有模型通常会计设置、空闲与活跃时间，不能把品牌统一等于每次prediction。

有预留容量时，用观察窗T和相同输入/输出混合计算盈亏。若每小时全负载能完成q个合格请求，api每合格请求需c元，而一小时专用投入h元，则简化util盈亏点是 `u*=h/(q c)`。u大于1说明即使满负载也不省钱；u很小也不证明突发有足够容量。这里只计同质量、同SLO的能力，重试与无效输出会改变q和c。按总日token除某peak tok/min是假定完美打包，不能推真实占用时间、延迟或容量。

例：教学API输出0.9元/M，专用0.55元/min，满负载输出0.9M/min，24小时预留。专用792元/天，API满负载1166.4元/天，交点约67.9%；源课正文30%与其代码参数不一致。另一个教学预留10元/hr、每小时2M输出、API10元/M，交点50%。这只是输入算式，均不代表供应商报价。混合输入/输出的吞吐权重、实际峰值限制和容量步长要独立计算。

批处理折扣必须对应可延迟的工作。40%量移到半价token层，在同输入输出组成下可将原token费用乘0.8；但GPU租价加1元/hr属于另一合同，不能再把整张GPU账单机械乘0.8。业务比较用**每合格请求费用**及总费用，不让失败、超时或质量差的便宜token美化结果。

下面的标准库程序验证两种盈亏交点、容量/SLO筛选和不可行方案。虚拟输入是显式教学假设，没有请求供应商或测GPU。

```python
import math
from fractions import Fraction

def reserve_vs_api(util, hourly, out_per_hour, per_million):
    values = (util, hourly, out_per_hour, per_million)
    if any(isinstance(x, bool) or not isinstance(x, (int, float))
           or not math.isfinite(x) for x in values):
        raise ValueError('有限数值，布尔值不是业务数量')
    if not 0 <= util <= 1 or min(hourly, out_per_hour, per_million) <= 0:
        raise ValueError('util在0..1，其余为正')
    return hourly, util * out_per_hour / 1e6 * per_million

cross = Fraction(55, 100) / (Fraction(9, 10) * Fraction(9, 10))
assert cross == Fraction(55, 81)
a, b = reserve_vs_api(.5, 10., 2_000_000., 10.)
assert a == b == 10.
# 便宜但不满足峰值或首token约束的端点先淘汰，再比较钱。
plans = [{'name': 'cheap', 'cost': 1., 'rps': 4., 'p99_ms': 2000.},
         {'name': 'ready', 'cost': 3., 'rps': 10., 'p99_ms': 400.}]
def pick(plans, peak_rps, ttft_bound):
    def number(x):
        return (not isinstance(x, bool) and isinstance(x, (int, float))
                and math.isfinite(x) and x >= 0)
    if not number(peak_rps) or not number(ttft_bound):
        raise ValueError('容量/SLO边界必须有限非负')
    if any(not all(number(p.get(k)) for k in ('rps', 'p99_ms')) for p in plans):
        raise ValueError('先核实方案能力与延迟')
    eligible = [p for p in plans if p['rps'] >= peak_rps
                and p['p99_ms'] <= ttft_bound]
    if any(not number(p.get('cost')) for p in eligible):
        raise ValueError('合格方案的报价必须有限非负')
    return min(eligible, key=lambda p: p['cost'])['name'] if eligible else None
assert pick(plans, 8., 500.) == 'ready'
assert pick(plans, 12., 500.) is None
ineligible_without_cost = {'name': 'slow', 'rps': 4., 'p99_ms': 2000.}
assert pick([ineligible_without_cost, plans[1]], 8., 500.) == 'ready'
for bad_cost in (float('nan'), -1., True):
    try: pick([dict(plans[1], cost=bad_cost)], 8., 500.)
    except ValueError: pass
    else: raise AssertionError('非法报价不能成为最低价合格方案')
for bad_bound in (float('nan'), -1., True):
    try: pick(plans, bad_bound, 500.)
    except ValueError: pass
    else: raise AssertionError('非法峰值需求必须拒绝')
    try: pick(plans, 8., bad_bound)
    except ValueError: pass
    else: raise AssertionError('非法SLO必须拒绝')
for bad in (True, float('nan'), -1., 2.):
    try: reserve_vs_api(bad, 10., 2_000_000., 10.)
    except ValueError: pass
    else: raise AssertionError('非法util必须拒绝')
print('教学盈亏：50%与55/81；先SLO/容量后成本；不可行及非法数值拒绝')
```

## 20. 扩副本、加节点与分布式排程分开

应用控制器决定准备多少prefill/decode或完整服务副本；资源供给器为Pending工作准备满足约束的节点；scheduler负责把pod/工作组放到资源上。已有空闲GPU却Pending，检查requests、taint/toleration、affinity、拓扑、显存/CPU需求和gang组条件；无可匹配节点还要查供应商容量、配额、节点启动及镜像/模型准备。看pod事件、节点ready时间、scheduler等待和application队列，别按品牌名猜原因。

GPU duty-cycle反映采样窗中设备忙的比例，不直接等于请求量、SM有效算力或SLO余量；HBM预分配也不等于活跃KV块压力。但这些指标仍是有用的剖析信号，不能一律禁止。用等待队列/等待时间、运行请求数、活跃KV、TTFT/ITL、合格请求率联合建控制器。HPA通常按CPU起步，DCGM需要接入自定义指标；若目标70%、测值100%，比例式HPA会倾向扩容，而非源课“已经满所以不扩”。扩容迟滞、采样窗、max限制和冷启成本另查。

多pod组成的TP/PP工作组，需要全组满足资源再启动，避免一部分已经占资源却等剩余成员。单pod一次请求多GPU通常本就要满足整个pod，不能把它与多pod gang混为一谈。拓扑是带宽/延迟约束：GPU数量够但NVLink、跨节点网络或rank布局不符仍可能不可用。不是所有TP>1都要求同一个scheduler产品。

Karpenter的`WhenEmpty`缩小consolidation候选范围，`consolidateAfter`抑制频繁变动；它不撤销drift、过期、故障修复、spot中断或人工删除。当前文档还按disruption-cost解释empty的边界，因此不要将一段YAML叫“绝不驱逐”。完整控制包括按实际版本设置disruption budget/PDB、ready/停止接新请求、drain、grace期、租约和可恢复回执。PDB也不能阻止所有非自愿故障。

prefill与decode拆开后，应按各自队列、成本、服务率及KV转移测量控制；源“prefill只队列、decode只KV”只是起点。等待增加可能源于网络或CPU，盲目扩GPU不一定有效。预测突发、保持最低ready量或队列限流须与**就绪延迟**相连，而不只是desired replicas；§19的每日量均摊不处理分钟峰值。

## 21. 平台与扩缩容原练习、测验的核对

**托管平台01：五项练习。** ① 盈亏利用率按§19显式费率/输入输出组成算，源玩具输出场景是50%，不能概括所有70B。② 两模型部署先核实时效目录；可经网关分别路由，fallback需任务质量/schema和权限对照、超时/退避/幂等，不能默认互换。③ 医疗场景先由负责人核对具体服务/区域、合同与数据处理要求，再在同分布测P99；产品页认证标志与P50不是BAA或sub100ms证明。④ 无profile时按账单账户/区域/模型/调用与重试/cache/输出长度溯源，有profile按tag对账；没有遥测不能承诺查出所需分钟数。⑤ 100M/月要补输入输出比例、确切模型、地区、保留/预留时长及峰值，再按§19归一比较，不捏造最低价。

**01七道测验。** ① 同一API访问Claude/Llama/Cohere可把Bedrock列为候选，但需目录/region核实；② Azure OpenAI特指OpenAI模型服务，不等整个Azure平台只能此类模型；③ 原25ms答案缺可比部署证据，改为同模型/配置/区域/负载实测；④ application inference profile可跟踪usage并用tags归属cost，CloudWatch不等账单；⑤ 40–60%非定律，输入算式决定交点；⑥ 双供应商的理由是经验证的故障与能力备援，不是每月能力轮换定律或认证要求；⑦ 归属透明度取决于资源/请求tag、账本和导出，不采用平台优劣排名。

**平台经济02：五项练习。** ① 源0.55/min、0.9M/min、API0.9/M在24h预留条件交点55/81≈67.9%，见真实算式例。② 图像、chat、语音分别按质量/输出单位、延迟和费用筛选，网关保留能力差异，不能强行统一token费。③ 同合同40%半价得0.8倍；GPU小时涨价另按实际收费时间算。④ 逐一核验专用容量、所需合同和范围，不按品牌直接选三家“合规”，FinOps仍需请求归属与对账。⑤ 若每prediction输出n token，API费为1000*n*p/1e6，专用按实际billed时段；10与10000/day的交点依n、输入、预留和峰值，题干不足以唯一判断。

**02六道测验。** ① 自定义硬件/GPU平台/API市场是交叉的分类维度；② 原30%由其代码自己否定，见55/81；③ Modal提供Python式服务接口，但冷启不是统一2–4s；④ LoRA与base相同费率是需逐型号/tier核实的合同，不作永久特性；⑤ 客户需求按具体服务合同筛选，不能由Baseten名字保证所有要求；⑥ “vLLM/SGLang占80%”无可核统计，不证明自定义引擎只有营销，仍比较质量/SLO/成本/维护。

**GPU扩缩03：五项练习。** ① 原模拟只比较人为控制器阈值，且15s tick每卡只接一条2.4s请求、到达率被除10，不把差异当DCGM/KAI效果；真正对比固定请求事件、服务/启动分布、组约束和超时分母。② NodePool方案要明确GPU型号/架构/容量类型、requests/tolerations、region/拓扑、disruption/drain及最低ready量；YAML只是经版本核对的计划，本批未部署。③ Pending按§20节点供给、单pod可行性、工作组和拓扑分层排查。④ 两池各量队列/服务时间/KV转移和SLO，prefill队列与decode活跃KV可先观察，不只一个固定指标。⑤ 60次事件/day缺请求数、失败分布、重载时长及单位损失，不能由P99>10s算钱；先算GPU重载费、失败请求/credits及独立业务损失。

**03六道测验。** ① DCGM不是HPA通用默认，也不是唯一负载信号；② gang减部分组占位等待，不消除冷启；③ consolidation可能移动运行pod，需drain和恢复控制；④ 固定快40%没有统一样本，测节点创建到ready全链；⑤ 两池分别控制并量转移瓶颈；⑥ WhenEmpty+1h仅限制自愿整合条件，不免疫全部驱逐。源输出文件的一律拒绝单节点、TP>1必须KAI等条件不继承。

本节增量来源：AI Engineering from Scratch固定`3be078b`，Phase17第01–03课，整理2026-10-10。[Bedrock inference profiles](https://docs.aws.amazon.com/bedrock/latest/userguide/inference-profiles.html)、[Azure tags](https://learn.microsoft.com/en-us/azure/azure-resource-manager/management/tag-resources)、[Karpenter disruption](https://karpenter.sh/docs/concepts/disruption/)、[Replicate pricing](https://replicate.com/pricing)只核对应管理/计费含义，不保存现价榜、客户适用性保证或未运行的云部署。原动态图的固定latency、单位token成本和ceil(qps/cap)是示意，不包含真实预算、冷启、排队和控制器。
