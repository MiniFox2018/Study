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
