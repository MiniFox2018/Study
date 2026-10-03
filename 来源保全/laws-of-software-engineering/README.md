# Laws of Software Engineering｜来源记录与覆盖说明

## 1. 来源

- 来源名称：*Laws of Software Engineering - Printable Card Deck*
- 用户上传文件：`Laws of Software Engineering - Printable Card Deck _ Laws of Software Engineering.pdf`
- 官方站点：<https://lawsofsoftwareengineering.com/>
- PDF 页数：28
- 页面规格：A4
- 文件大小：1,056,704 bytes
- 用户上传 PDF SHA-256：`4ba05be1232bec2e087ebd9e36e4c636533e0eac12b03f2e6ddbb1e7ccf2cb84`
- PDF 生成时间（文件元数据）：2026-10-03
- 吸收时间：2026-10-03
- 主知识库：[软件工程定律与工程决策](../../计算机科学基础/05-1-软件工程定律与工程决策.md)

> 按 Study 规则，本仓库不长期保存该原始 PDF；需要重新获取时从官方站点查找 Printable Card Deck。

## 2. 原资料结构

原资料共 56 个编号条目，按 7 组排列。卡牌正面给出名称、核心命题、作者/年代和 See also；背面给出 3 条 Key Takeaways。

| 分组 | 编号 | 数量 | Study 落位 |
|---|---:|---:|---|
| Architecture | 1–9 | 9 | 05-1 第一部分 |
| Teams | 10–18 | 9 | 05-1 第二部分 |
| Planning | 19–24 | 6 | 05-1 第三部分 |
| Quality | 25–35 | 11 | 05-1 第四部分 |
| Scale | 36–38 | 3 | 05-1 第五部分 |
| Design | 39–44 | 6 | 05-1 第六部分 |
| Decisions | 45–56 | 12 | 05-1 第七部分 |
| **合计** | **1–56** | **56** | **全部覆盖** |

## 3. 逐项覆盖清单

### Architecture 1–9

1. Hyrum's Law
2. Gall's Law
3. Law of Leaky Abstractions
4. Tesler's Law / Conservation of Complexity
5. CAP Theorem
6. Second-System Effect
7. Fallacies of Distributed Computing
8. Law of Unintended Consequences
9. Zawinski's Law

### Teams 10–18

10. Conway's Law
11. Brooks's Law
12. Dunbar's Number
13. Ringelmann Effect
14. Price's Law
15. Putt's Law
16. Peter Principle
17. Bus Factor
18. Dilbert Principle

### Planning 19–24

19. Premature Optimization / Knuth's Optimization Principle
20. Parkinson's Law
21. Ninety-Ninety Rule
22. Hofstadter's Law
23. Goodhart's Law
24. Gilb's Law

### Quality 25–35

25. Boy Scout Rule
26. Murphy's Law / Sod's Law
27. Postel's Law
28. Broken Windows Theory
29. Technical Debt
30. Linus's Law
31. Kernighan's Law
32. Testing Pyramid
33. Pesticide Paradox
34. Lehman's Laws of Software Evolution
35. Sturgeon's Law

### Scale 36–38

36. Amdahl's Law
37. Gustafson's Law
38. Metcalfe's Law

### Design 39–44

39. YAGNI
40. DRY
41. KISS
42. SOLID Principles
43. Law of Demeter
44. Principle of Least Astonishment

### Decisions 45–56

45. Dunning-Kruger Effect
46. Hanlon's Razor
47. Occam's Razor
48. Sunk Cost Fallacy
49. The Map Is Not the Territory
50. Confirmation Bias
51. Hype Cycle & Amara's Law
52. Lindy Effect
53. First Principles Thinking
54. Inversion
55. Pareto Principle / 80-20 Rule
56. Cunningham's Law

## 4. 吸收方式

不是把卡牌逐字翻译后再保存一套，而是：

1. 保留 56 条的编号、原分组、核心命题与关键 takeaway；
2. 中文化术语，同时保留必要英文名称用于检索；
3. 对每条补充工程用法、误用边界或学习例子；
4. 把 Amdahl's Law 补成可计算公式与小例子；
5. 把 CAP、DRY、SOLID、Postel、Dunning-Kruger、Dunbar、Price、Metcalfe、Sturgeon 等容易被口号化使用的条目补充适用边界；
6. 增加架构、团队、代码评审、故障复盘四组检查表和 12 个学习自测；
7. 与 Study 既有软件工程、并行计算、Docker、Linux、LLM 工程章节交叉连接，避免建立孤立知识岛。

## 5. 时效与准确性处理

这批内容大多属于长期工程原则，不因年代较早自动淘汰。但“Law”在这里不是统一的科学类别，因此主库做了以下区分：

- **数学/计算约束**：如 Amdahl's Law、CAP，需要按严格条件理解；
- **工程经验原则**：如 YAGNI、DRY、KISS、Testing Pyramid，需要结合项目约束；
- **组织与行为启发式**：如 Dunbar、Price、Peter、Dilbert，不当作精确预测公式；
- **认知工具**：如 Confirmation Bias、Sunk Cost、First Principles、Inversion，用于改善决策过程；
- **修辞性/经验性比例**：如 Sturgeon's “90%” 与 Pareto “80/20”，不把数字当固定统计事实。

原卡牌中对具体数据库的 CAP 归类仅作为示意，Study 主库不把数据库永久贴成固定 CP/AP 标签；实际行为应依据版本、配置、拓扑和操作语义判断。

## 6. 未保留内容

- 不保存原始 PDF 二进制；
- 不复制卡牌版式、配色与装饰图标；
- 不把站点 URL 列表复制成第二套学习资料；
- 不把作者/年代当主要学习主线；需要追溯时可回原来源。

## 7. 完整性结论

本次以 PDF 28 页为输入，对 56 个编号条目建立了逐项覆盖清单。主知识库已经包含全部条目的中文解释和核心 takeaway，并针对容易误用的内容补充边界，因此后续学习这些软件工程定律时无需依赖原 PDF。
