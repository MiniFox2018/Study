# Maths, CS & AI Compendium 来源保全

> 来源：<https://github.com/HenryNdubuaku/maths-cs-ai-compendium>  
> 作者：Henry Ndubuaku  
> 许可证：Apache License 2.0  
> 保全基准提交：`9850ee574a370bc1cde59de98b394e953775b67d`  
> 核验/吸收时间：2026-10-01  
> 原始默认分支：`main`

## 已保全

源仓库 **第 1～18 章全部 94 个 Markdown 章节文件**已经按原路径保存在本目录，同时保留：

- `README.md`
- `llms.txt`
- `LICENSE`

因此正文中的公式、代码块、例子、表格和章节关系均可在 Study 内直接恢复，不依赖原网页。

## 主库与保全层分工

- **中文主知识库**：去重、过滤过时实现、按现有知识结构吸收；
- **本目录**：保留源正文和版本证据，防止主库精简时丢失细节。

详细去向见：[吸收映射](./吸收映射.md)。

## 第 19～20 章

源仓库还存在 Chapter 19 Applied AI 与 Chapter 20 Bleeding Edge AI，但当前多数文件为空或仅数百字占位：

- 不视为成熟章节；
- 不进入主知识库；
- 后续来源真正补完时再重新评估。

## 未迁移的仓库工程文件

MkDocs、GitHub Actions、MCP Server、样式和部署脚本属于源仓库自身工程设施，不是本次学习知识，不进入 Study 主库。

## SVG 图示

源仓库包含 263 个 SVG 知识图示。由于 GitHub 连接器无法跨仓库直接复用 Blob，逐个复制会触发单次调用限制，因此本次保留完整恢复清单而不机械复制图文件：

- [SVG 图示恢复清单](./images/MANIFEST.md)

清单记录每个图的原路径、Blob SHA 和字节数。正文知识不依赖这些图才能理解；若后续需要离线视觉镜像，可按 SHA 分批恢复。
