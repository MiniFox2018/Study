# LLM 基础

> 主要来源：<https://github.com/rasbt/LLMs-from-scratch>  
> 来源项目：Sebastian Raschka, *Build a Large Language Model (From Scratch)*  
> 核验时间：2026-10-01  
> 来源基准提交：`817de229cfe412360bb76c78e09e2bfd77018d49`  
> 许可证：Apache License 2.0  
> 整理语言：中文

## 定位

本目录负责回答：**一个现代大语言模型从文本输入到训练、生成和微调，底层到底是怎么工作的？**

这里不做原仓库镜像，也不追逐短期模型版本。只保留当前仍有长期价值、能够帮助理解和实际工作的核心知识。

## 学习路径

1. [整体框架](./01-整体框架.md)
2. [文本、Tokenizer 与 Embedding](./02-文本-Tokenizer与Embedding.md)
3. [Attention 机制](./03-Attention机制.md)
4. [Transformer 与 GPT 架构](./04-Transformer与GPT架构.md)
5. [预训练、损失与文本生成](./05-预训练-损失与文本生成.md)
6. [微调、指令跟随与偏好优化](./06-微调-指令跟随与偏好优化.md)
7. [训练与推理优化、LoRA](./07-训练推理优化与LoRA.md)

## 核心链路

```text
原始文本
  ↓
Tokenizer / Token IDs
  ↓
Token Embedding + Positional Information
  ↓
Causal Self-Attention
  ↓
Transformer Blocks
  ↓
Logits / Next-token Prediction
  ↓
Pretraining
  ↓
Task / Instruction Finetuning
  ↓
Evaluation & Alignment
  ↓
Efficient Inference / Deployment
```

## 本次明确不收录

根据项目规则，以下内容不作为长期知识写入：

- 某一代模型的具体型号清单；
- 某张 GPU 上的瞬时跑分；
- 易变化的 Python/PyTorch 安装步骤；
- 只对特定版本有效的接口写法；
- 某个模型仓库的临时下载方法；
- 纯 UI 演示和环境排障细节。

需要具体实现时，可回到来源仓库按当前版本核验。

## 与 Agent 知识库的关系

LLM 基础负责“**模型本身怎么工作**”；Agentic Design Patterns 负责“**如何把模型、上下文、工具和工作流组合成 Agent 系统**”。

两者不重复建模，但相互引用：

- [Agentic Design Patterns](../Agentic%20Design%20Patterns/README.md)
- [模型后训练专题](../Agentic%20Design%20Patterns/06-专题扩展/04-模型后训练.md)
