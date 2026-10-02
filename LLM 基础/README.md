# LLM 基础

> 主要来源：Sebastian Raschka, *Build a Large Language Model (From Scratch)*  
> 新增来源：Henry Ndubuaku, *Maths, CS & AI Compendium* Chapter 07  
> Compendium 基准提交：`9850ee574a370bc1cde59de98b394e953775b67d`  
> 核验时间：2026-10-01  
> 整理语言：中文

## 定位

本目录回答：**一个现代语言模型从语言结构、文本表示，到 Transformer、训练、生成和微调，底层到底怎样工作？**

不追逐短期型号；只保存长期机制。

## 学习路径

1. [整体框架](./01-整体框架.md)
2. [文本、Tokenizer 与 Embedding](./02-文本-Tokenizer与Embedding.md)
3. [Attention 机制](./03-Attention机制.md)
4. [Transformer 与 GPT 架构](./04-Transformer与GPT架构.md)
5. [预训练、损失与文本生成](./05-预训练-损失与文本生成.md)
6. [微调、指令跟随与偏好优化](./06-微调-指令跟随与偏好优化.md)
7. [训练与推理优化、LoRA](./07-训练推理优化与LoRA.md)
8. [语言学与经典 NLP](./08-语言学与经典NLP.md)
9. [现代语言模型架构与高级生成](./09-现代语言模型架构与生成.md)

## 核心链路

```text
语言结构 / 文本
→ Tokenizer
→ Embedding
→ Attention / Sequence Modeling
→ Transformer / Alternative Sequence Models
→ Next-token Distribution
→ Pretraining
→ Finetuning / Alignment
→ Decoding / Evaluation
```

## 分工

- 通用数学、CNN/RNN、图学习： [AI 算法基础](../AI%20%E7%AE%97%E6%B3%95%E5%9F%BA%E7%A1%80/README.md)
- 运行、微调、服务化、推理系统： [LLM 工程实践](../LLM%20%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/README.md)
- Agent 系统组合： [Agentic Design Patterns](../Agentic%20Design%20Patterns/README.md)

具体模型清单、GPU 跑分、旧安装命令和短期接口不进入本目录。

## 第一次学习怎样走

先具备矩阵乘法、概率分布、对数、梯度和 Python 列表的基础。不会时回到 [AI 算法基础](../AI%20算法基础/README.md) 按需补，不必先读完所有数学章节。

| 阶段 | 阅读 | 可以自己核对的完成证据 |
|---|---|---|
| 看懂数据流 | 01～02 | 解释 ID 与向量区别；手工写出输入/目标错位 |
| 看懂模型内部 | 03～04 | 算一次两位置 Attention；核对残差与输出形状 |
| 看懂训练与生成 | 05～06 | 算交叉熵/PPL；区分 attention mask 与 loss mask |
| 看懂资源与方法选择 | 07 | 计算 LoRA 参数量、普通 KV 缓存有效载荷 |
| 补语言与架构视野 | 08～09 | 用反例解释静态词向量、top-p、MoE 的边界 |

每章先读原理，再手做例子，最后合上正文回答自检。答错就回到对应概念，不必立即开始大模型训练；纸笔或几行标准库 Python 足以验证多数入门计算。读到 GQA、MLA、MoE 等变体时，先掌握它改善哪个瓶颈即可。

内容整理不等于你已经学过。个人练习可记录“未读 → 能解释 → 能计算/运行 → 能改条件并排错”，只有实际产物或回答才作为完成证据。2026-10-02 补齐了 9 章的教学例子与答案，并修正关键概念条件；尚不等于完整复现原书所有代码和实验。
