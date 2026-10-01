# UDL 官方 Notebook 来源保全

> 上游：<https://github.com/udlbook/udlbook/tree/main/Notebooks>  
> 上游 commit：`0d84a591362f1cc99c6dc2ce1c2544d559280681`  
> 保全时间：2026-10-01  
> 许可证：MIT（Copyright 2023 Simon Prince）

## 目的

这里保存 Understanding Deep Learning 官方章节 Notebook，使 Study 在日常学习时不需要再回官网寻找代码练习。

规则：

- Notebook 原样保全，不把它们当作主知识正文；
- 中文知识解释仍以 `深度学习专题/01～14` 为主；
- 上游版本变化时按 commit 做增量更新；
- 已知上游 issue 不擅自“修成另一个版本”，避免失去来源可追溯性；
- 若需要修复运行兼容性，应在 Study 中另建修正版并明确标注。

## 目录

保持上游 Chapter 结构：

```text
Chap01/
Chap02/
...
Chap21/
```

Chapter 14 官方没有章节 Notebook。

官网仍描述为 68 个练习；当前上游实际有 69 个 `.ipynb` 文件，其中 Chapter 20.2 另有 GPU 版本，因此“练习数”和“文件数”不同。

## 运行前检查

- [已知问题与兼容性](./已知问题.md)：记录当前仍 open 的上游 Notebook 问题及最小修复办法。

## 主知识入口

- [深度学习专题](../../README.md)
- [UDL 覆盖核验](../../UDL覆盖核验.md)
