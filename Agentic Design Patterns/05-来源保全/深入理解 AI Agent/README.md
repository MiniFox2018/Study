# 《深入理解 AI Agent》来源保全

> 原仓库：<https://github.com/bojieli/ai-agent-book>  
> 保全基准提交：`dbc046eb896ac4e39aa19c7774c8bf49583b89a6`  
> 许可证：Apache License 2.0

## 已保全范围

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

2026-10-02 已按固定提交恢复这 3 个 PNG，并逐一验证 Git Blob SHA。登记如下：

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

## 迁移与实验边界（2026-10-02）

已修复来源正文中的失效相对链接：已保全内容仍链接本地，未镜像的实验源码与其他语言版本链接固定提交。上游本身缺少的结果 JSON 和架构图已在原位置注明，不能作为已复现实验的证据。正文与实验 README 可以阅读，但本目录不是可直接运行的完整实验工程。详见[来源使用说明](../../../维护/来源使用说明.md)。
