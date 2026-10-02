# Microsoft Data Science for Beginners — 来源保全

- 原仓库：<https://github.com/microsoft/Data-Science-For-Beginners>
- 吸收基准提交：`4d2ac427ad6f022e73a75c4f46a28bbb7978ec3f`
- 简体中文翻译树：`d661810457df155cc2774e4878ced5a2d8281373`
- 核验时间：2026-10-01
- 许可证：MIT

本目录用于保存课程的原始学习上下文；日常学习请从 [数据科学基础](../../%E6%95%B0%E6%8D%AE%E7%A7%91%E5%AD%A6%E5%9F%BA%E7%A1%80/README.md) 进入。

## 已保全

- 56 个简体中文 Markdown：20 课正文、作业、章节说明及相关解答说明；
- 25 个 `.ipynb` 文件：其中 24 个可解析为 Notebook，另一个第 19 课解答是上游已有的空文件，不是有效实验；
- 12 个课程数据文件；
- 6 个 examples 文件（5 个 Python 示例 + README）；
- 原始 MIT LICENSE；
- [MANIFEST.md](./MANIFEST.md)：上游文件路径、Blob SHA、大小与本地对应关系。

## 未保全

- GitHub Actions、站点构建脚本、贡献/社区治理文件；
- quiz-app 前端；
- 多语言重复副本；
- 未被现有课程直接引用的图片和站点包装资源。

2026-10-02 已按上游固定提交补齐现有课文引用的 135 个资源（图片及表格），位于 `资源/`；已修复迁移造成的相对链接及 12 个 Notebook 的数据路径。原始 Blob SHA 仍保留，本地修订后校验值见[来源完整性记录](../../维护/来源完整性.json)。

原文的历史云平台步骤不作为当前操作指南；Notebook 中内嵌输出是原作者历史记录。本次没有将 25 个文件全部执行。课程实验使用边界见[来源使用说明](../../维护/来源使用说明.md)。
