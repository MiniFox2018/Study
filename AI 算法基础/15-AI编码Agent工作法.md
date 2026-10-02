# 15｜AI 编码 Agent 工作法

> 本章讲跨工具工作法，具体产品命令和自动读取规则须查当时文档。先修：文件路径、Git diff、一个能运行的小程序。

> 来源站点 2026 年新增 Claude Code / Codex 长篇教程。产品命令、配置字段和限制可能继续变化，本章只保留可跨工具复用的工作法。

## 1. AI Coding Agent 与普通聊天的区别

普通聊天：

```text
问题 → 回答
```

Coding Agent：

```text
理解仓库
→ 搜索上下文
→ 计划
→ 修改文件
→ 运行命令
→ 测试
→ 检查 diff
→ 继续修复
→ 提交结果
```

因此成功率主要取决于：

- context；
- tools；
- permissions；
- repository rules；
- verification loop。

## 2. 项目规则必须落仓

不要让关键规则只存在于一次聊天。

项目应包含规则文件，并确认当前 Agent 的读取方式，描述：

- 项目目标；
- 技术栈；
- 目录；
- build/test/lint；
- 禁止操作；
- 安全边界；
- 提交规范；
- 模块特例。

Study 的 `PROJECT_RULES.md` 承担规则记录职责，但任意文件名并不会被所有 Agent 自动识别。使用时应明确要求读取它，或由工具支持的项目入口引用。

## 3. 全局规则 vs 局部规则

大型仓库不应把所有规范塞进一个巨大文件。

更合理：

```text
Repo-level Rules
  ↓
Module Rules
  ↓
Task Context
```

原则：

- 全局只写长期通用内容；
- 模块特殊约束就近存放；
- 临时任务不要永久写入全局规则。

## 4. 规则要可执行

差的规则：

> 写好代码，注意测试。

好的规则：

> 修改支付模块后必须运行指定 test suite；新增 public function 必须补对应 unit test。

规则越可验证，Agent 越容易遵守。

## 5. Context Budget

上下文不是越多越好。

过多无关规则会：

- 稀释重要指令；
- 增加 token；
- 造成相互冲突；
- 降低搜索效率。

因此应优先给 Agent：

1. 当前任务；
2. 相关文件；
3. 当前模块规则；
4. 必要架构文档；
5. 测试结果。

## 6. 先探索再修改

复杂任务先回答：

- 入口在哪里？
- 数据怎么流？
- 谁调用它？
- 哪些测试覆盖？
- 是否已有类似实现？

推荐：

```text
Search
→ Read
→ Build Mental Model
→ Edit
```

不要第一眼看到文件就改。

## 7. Plan Mode

对于跨文件、架构级或高风险任务：

1. 先形成计划；
2. 明确改哪些文件；
3. 明确验证方法；
4. 再执行。

小修改不需要形式化长计划。

计划本身不能替代执行和测试。

## 8. Verification Loop

Agent 最重要能力不是“写代码”，而是闭环：

```text
Edit
→ Format
→ Lint
→ Unit Test
→ Integration Test
→ Build
→ Inspect Diff
→ Fix
```

如果无法运行某项验证，必须明确说明，而不是默认成功。

## 9. Test as Tool

测试不仅用于最终验收，也是 Agent 的信息来源。

失败测试可以帮助定位：

- contract；
- expected behavior；
- edge case；
- hidden dependency。

因此成熟仓库越容易被 Coding Agent 正确维护。

## 10. Git Diff

完成前必须检查：

- 是否修改了不相关文件；
- 是否留下 debug code；
- 是否误删内容；
- 是否增加秘密；
- 格式是否异常；
- generated file 是否需要提交。

Diff 是 Coding Agent 的最终自检界面之一。

## 11. Permission Boundary

Coding Agent 能执行命令，所以必须分级：

### Low Risk

- read；
- search；
- test；
- lint。

### Medium Risk

- edit；
- install dependency；
- generate files。

### High Risk

- delete；
- force push；
- production deploy；
- database migration；
- credentials；
- destructive command。

高风险操作需要更严格审批和沙箱。

## 12. Secret Safety

规则文件、Prompt 和代码中不要放：

- token；
- password；
- private key；
- production credential。

Agent 可读仓库，因此“写进 Markdown”也等同于暴露给工具链。

## 13. Subagent

复杂任务可拆：

```text
Explorer → 找相关代码
Reviewer → 找风险
Tester → 验证
Implementer → 修改
Manager → 汇总
```

适合并行的任务：

- 大仓库搜索；
- 独立模块审查；
- 安全/性能/测试不同维度 review。

不适合：

- 强依赖顺序；
- 多 Agent 同时编辑同一文件；
- 小任务。

## 14. Worktree / Isolation

多 Agent 并行写代码时，最好隔离工作区。

目的：

- 避免互相覆盖；
- 独立测试；
- 独立 diff；
- 更安全 merge。

## 15. Handoff

长任务和跨会话需要持久化：

- 当前目标；
- 已完成；
- 未完成；
- 重要发现；
- 已修改文件；
- 验证结果；
- 后续风险。

这正是“不要只依赖聊天记忆”的工程版本。

## 16. Rules as Living Documentation

当 Agent 重复犯同一个错误：

> 不要每次口头提醒，把规则写回仓库。

规则也要版本化，并允许修订。

## 17. 失败模式

常见：

- 没读项目规则；
- 搜索不充分；
- 过早修改；
- 只修症状不修根因；
- 不跑测试；
- 看到命令成功就宣布完成；
- 上下文塞太多；
- 自动化权限过大；
- 多 Agent 冲突写文件；
- 规则过长导致重要约束被淹没。

## 18. 与 Agentic Design Patterns 的关系

这一套工作流已经与以下模式互相连接：

- 工具使用；
- 规划；
- 异常恢复；
- 安全；
- 评估；
- 多智能体；
- 上下文工程。

更完整 Agent 设计进入：

- [Coding Agent 与通用 Agent](../Agentic%20Design%20Patterns/06-%E4%B8%93%E9%A2%98%E6%89%A9%E5%B1%95/02-Coding-Agent%E4%B8%8E%E9%80%9A%E7%94%A8Agent.md)

来源：<https://www.huaxiaozhuan.com/claude_code_codex_tutorials.html>  
说明：具体 Claude Code/Codex 命令、配置文件大小限制、SubAgent 产品行为属于高时效内容，使用时应核验各自当前官方文档。

## 把“帮我写好代码”改成可验收任务

练习任务：“在本地练习文件中实现列表均值，空列表抛出明确异常；示例 `[2, 4, 6]` 得 4；完成后展示 diff 和实际运行结果。”

执行时依次检查：任务是否明确输入输出；Agent 是否读过已有实现；修改是否局限于目标文件；正常输入和空输入是否真的运行过；输出日志与最终声明是否一致。

自查：Agent 说“测试通过”，但只给出自己写的预期结果，算验证吗？**答案：**不算。至少需要可重跑的命令及实际输出；再由你解释为什么会得到该结果，并亲手改一个输入验证。AI 完成任务不能直接等同于你已掌握实现。
