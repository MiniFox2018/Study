# D2L 逐文件覆盖核验

> 历史记录说明（2026-10-02 补充）：下文的“本轮/当前/已核验”指 2026-10-01 的来源整理记录及所列版本。本次内容审查未重跑全部原网站、PDF、Notebook 或历史 SHA 比较；章节映射只证明已有落位，不能证明逐条知识正确、全部细节已保留、代码在当前环境可运行或读者已掌握。

> 来源：<https://github.com/d2l-ai/d2l-zh>  
> 基线 commit：`e6b18ccea71451a55fcd861d7b96fddf2587b09a`  
> 核验时间：2026-10-01  
> 规则：排除 `*_origin.md` 英文对照副本；正文中文 Markdown 按章节全部进入覆盖检查。

## 覆盖表

| D2L 章节 | 中文正文文件 | Study 落位 |
|---|---|---|
| 引言 | `index.md` | 07 深度学习基础 / 专题 01 |
| 预备知识 | `autograd.md`<br>`calculus.md`<br>`index.md`<br>`linear-algebra.md`<br>`lookup-api.md`<br>`ndarray.md`<br>`pandas.md`<br>`probability.md` | 01 线性代数 / 02 概率统计 / 14 工具生态 |
| 线性神经网络 | `image-classification-dataset.md`<br>`index.md`<br>`linear-regression-concise.md`<br>`linear-regression-scratch.md`<br>`linear-regression.md`<br>`softmax-regression-concise.md`<br>`softmax-regression-scratch.md`<br>`softmax-regression.md` | 04 经典监督学习 / 专题 01 |
| 多层感知机 | `backprop.md`<br>`dropout.md`<br>`environment.md`<br>`index.md`<br>`kaggle-house-price.md`<br>`mlp-concise.md`<br>`mlp-scratch.md`<br>`mlp.md`<br>`numerical-stability-and-init.md`<br>`underfit-overfit.md`<br>`weight-decay.md` | 05 泛化 / 07 深度学习基础 / 专题 01 |
| 深度学习计算 | `custom-layer.md`<br>`deferred-init.md`<br>`index.md`<br>`model-construction.md`<br>`parameters.md`<br>`read-write.md`<br>`use-gpu.md` | 专题 01 |
| 卷积神经网络 | `channels.md`<br>`conv-layer.md`<br>`index.md`<br>`lenet.md`<br>`padding-and-strides.md`<br>`pooling.md`<br>`why-conv.md` | 专题 02 |
| 现代卷积神经网络 | `alexnet.md`<br>`batch-norm.md`<br>`densenet.md`<br>`googlenet.md`<br>`index.md`<br>`nin.md`<br>`resnet.md`<br>`vgg.md` | 专题 02 |
| 循环神经网络 | `bptt.md`<br>`index.md`<br>`language-models-and-dataset.md`<br>`rnn-concise.md`<br>`rnn-scratch.md`<br>`rnn.md`<br>`sequence.md`<br>`text-preprocessing.md` | 专题 03 |
| 现代循环神经网络 | `beam-search.md`<br>`bi-rnn.md`<br>`deep-rnn.md`<br>`encoder-decoder.md`<br>`gru.md`<br>`index.md`<br>`lstm.md`<br>`machine-translation-and-dataset.md`<br>`seq2seq.md` | 专题 03 |
| 注意力机制 | `attention-cues.md`<br>`attention-scoring-functions.md`<br>`bahdanau-attention.md`<br>`index.md`<br>`multihead-attention.md`<br>`nadaraya-waston.md`<br>`self-attention-and-positional-encoding.md`<br>`transformer.md` | 专题 04 |
| 优化算法 | `adadelta.md`<br>`adagrad.md`<br>`adam.md`<br>`convexity.md`<br>`gd.md`<br>`index.md`<br>`lr-scheduler.md`<br>`minibatch-sgd.md`<br>`momentum.md`<br>`optimization-intro.md`<br>`rmsprop.md`<br>`sgd.md` | 03 数值优化 / 专题 05 |
| 计算性能 | `async-computation.md`<br>`auto-parallelism.md`<br>`hardware.md`<br>`hybridize.md`<br>`index.md`<br>`multiple-gpus-concise.md`<br>`multiple-gpus.md`<br>`parameterserver.md` | 13 机器学习系统 / 专题 06 |
| 计算机视觉 | `anchor.md`<br>`bounding-box.md`<br>`fcn.md`<br>`fine-tuning.md`<br>`image-augmentation.md`<br>`index.md`<br>`kaggle-cifar10.md`<br>`kaggle-dog.md`<br>`multiscale-object-detection.md`<br>`neural-style.md`<br>`object-detection-dataset.md`<br>`rcnn.md`<br>`semantic-segmentation-and-dataset.md`<br>`ssd.md`<br>`transposed-conv.md` | 专题 07 |
| NLP：预训练 | `approx-training.md`<br>`bert-dataset.md`<br>`bert-pretraining.md`<br>`bert.md`<br>`glove.md`<br>`index.md`<br>`similarity-analogy.md`<br>`subword-embedding.md`<br>`word-embedding-dataset.md`<br>`word2vec-pretraining.md`<br>`word2vec.md` | 08/09 主干 / 专题 08 |
| NLP：应用 | `finetuning-bert.md`<br>`index.md`<br>`natural-language-inference-and-dataset.md`<br>`natural-language-inference-attention.md`<br>`natural-language-inference-bert.md`<br>`sentiment-analysis-and-dataset.md`<br>`sentiment-analysis-cnn.md`<br>`sentiment-analysis-rnn.md` | 专题 08 |
| 深度学习工具附录 | `aws.md`<br>`contributing.md`<br>`d2l.md`<br>`index.md`<br>`jupyter.md`<br>`sagemaker.md`<br>`selecting-servers-gpus.md` | 14 工具生态（仅长期原则） |

## 非正文仓库内容处理

以下内容经过结构审计，但不作为知识正文迁移：

- `*_origin.md`：英文原文对照，与中文正文重复；
- `.github/`、`ci/`、`static/`：项目构建、发布和站点基础设施；
- `graffle/`、大量 `img/`：源图/素材层，不作为独立知识点；
- `config.ini`、`setup.py`、`.gitmodules`：仓库构建配置；
- `STYLE_GUIDE.md`、`TERMINOLOGY.md`：D2L 项目自身翻译/写作规范；
- AWS、SageMaker、历史 Jupyter/安装操作：只保留工具与系统原则，具体步骤执行时查当前官方文档。

## 完整性口径

“完整吸收”指：

1. 每个 D2L 中文正文章节均有明确落位；
2. 每个非 `_origin` 正文文件均进入覆盖核验；
3. 长期有效的算法、推导、模型、训练/调试和系统原则进入 Study；
4. 与现有主干重复的内容去重，不复制第二份同义知识；
5. 2023 年旧 API、安装、云平台和 benchmark 不作为 2026 年现行结论。

该表用于后续增删改查：若 D2L 来源版本变化，可按原章节/文件定位差异，而无需重新建立平行教材目录。
