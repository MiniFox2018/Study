# 《深入理解 AI Agent》来源保全

> 原仓库：<https://github.com/bojieli/ai-agent-book>  
> 保全基准提交：`dbc046eb896ac4e39aa19c7774c8bf49583b89a6`  
> 许可证：Apache License 2.0

## 已完整保全

### 中文教材主干

- 根目录中文 README、中文索引和 EPUB 说明
- `book/introduction.md`
- `book/chapter1.md` ～ `book/chapter10.md`
- `book/afterword.md`
- `book/reference-answers.md`
- `docs/zh-CN/README.md`
- `docs/zh-CN/LEARNING.md`
- Apache-2.0 `LICENSE`

正文中的代码块随 Markdown 一并保留。

### 实验知识层

- 10 个章节实验总览 README：10/10
- 直属实验 README：110/110
- 实验 Ledger：8/8（源仓库第 1～8 章提供）
- 根级依赖描述：`pyproject.toml`
- API/运行环境示例：`.env.example`

实验 README 保留实验目的、设计、运行方法、验收标准和结果解释；没有镜像整个实验源码和运行产物。

### 正文配图

- SVG：132/132，完整保全并保持原相对路径。
- PNG：正文引用 3 个路径，其中 2 个路径实际指向同一个二进制 Blob。

当前 GitHub 连接器无法无损读取并重新写入这 3 个二进制 PNG，因此做可恢复登记：

| 原路径 | 大小 | Git Blob SHA |
| --- | ---: | --- |
| `book/images/attention-visualization.png` | 2,578,612 B | `3cbb27b4a689af0c2c0f8e21965875ef26d02ee0` |
| `book/images/fig2-7.png` | 2,578,612 B | `3cbb27b4a689af0c2c0f8e21965875ef26d02ee0` |
| `book/images/n8n-workflow.png` | 162,795 B | `58c32989c47c7f8261f93b9c5d68de57cd38ae33` |

前两个路径内容完全相同。

## 未镜像的内容

为保持 Study 仓库作为知识库而不是上游仓库的完整二进制备份，以下内容不做全量复制：

- 非简体中文翻译版本；
- 110 个实验目录中的完整源码与第三方 vendored 仓库；
- 训练权重、缓存、日志、验证产物和大体积数据；
- MP4/MOV/WAV/MP3 等媒体；
- PDF/EPUB 构建产物。

如后续需要复现某个实验，再按实验粒度选择性吸收代码。

## 当前吸收状态

- 21 个核心设计模式：**21/21 已写入第二来源增量内容**。
- 独立保留：4 个专题扩展。
- 原书 10 章与当前知识库对应关系：见 [吸收映射](./吸收映射.md)。
- 完整中文原始资料：位于 [source/](./source/)。
