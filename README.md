# Math Modeling Playbook

面向数学建模竞赛的可复用 Agent Skill，提供从题目拆解、模型选择、算法实现到论文组织的端到端工作流。适用于需要快速判题、选择模型、调用 Python/MATLAB 模板、规划竞赛节奏或撰写建模论文的场景。

## 核心功能

- **快速判题与拆解**：识别评价、预测、优化、分类等任务类型，拆分子问题、目标和约束。
- **模型选择**：给出 2–3 组候选模型，说明适用条件、假设、风险和最简可行路线。
- **完整建模流程**：覆盖数据预处理、模型构建、求解、验证、敏感性分析和论文结构。
- **竞赛时间管理**：提供 24 小时、12 小时和 6 小时压缩工作模式。
- **论文写作支持**：附带问题分析模板和竞赛论文大纲模板。
- **组合模型升级**：判断何时需要从单模型升级，并提供评价、预测和优化组合方案。
- **AI 提示词模板**：提供题目分析、模型选择、代码适配和论文写作提示词。

## 支持的模型与算法

| 类型 | 方法 |
| --- | --- |
| 综合评价 | TOPSIS、AHP、熵权法、DEA、灰色关联 |
| 预测 | ARIMA、GM(1,1)、GM(1,1)-Markov、PCA-SVM、SVM-PSO |
| 优化 | 线性规划、整数规划、遗传算法、粒子群、GA-SA |
| 组合模型 | AHP-熵权、TOPSIS-灰色关联、DEA-TOPSIS、PCA-SVM、GM(1,1)-Markov、SVM-PSO、GA-SA |

仓库包含 15 个 Python 模板和 7 个 MATLAB 模板，可根据题目数据格式和约束条件直接改造。

## 目录结构

```text
math-modeling-playbook/
├─ SKILL.md                         # 技能入口与任务路由
├─ agents/openai.yaml              # Agent 展示信息与默认提示词
├─ references/                     # 建模方法论与竞赛工作流
│  ├─ problem-triage.md
│  ├─ model-selection.md
│  ├─ standard-workflow.md
│  ├─ algorithm-templates.md
│  ├─ competition-timeline.md
│  ├─ paper-writing.md
│  ├─ ai-prompt-patterns.md
│  ├─ advanced-model-combinations.md
│  └─ when-to-upgrade-model-complexity.md
└─ assets/
   ├─ templates/                    # 问题分析与论文大纲模板
   └─ code/
      ├─ python/                    # Python 算法模板
      └─ matlab/                    # MATLAB 算法模板
```

## 安装

将仓库克隆到 Codex 技能目录：

```powershell
git clone https://github.com/YANG985-CMD/math-modeling-playbook.git `
  "$HOME\.codex\skills\math-modeling-playbook"
```

重新启动 Codex 会话后，即可通过数学建模相关请求触发该技能。

## 使用示例

```text
帮我快速判断这道数学建模题属于什么类型，并给出最简单可行的模型路线。
```

```text
我只有 12 小时完成这道题，请给出建模、编程和论文写作安排。
```

```text
这是一道综合评价题，请比较 TOPSIS、AHP 和熵权法，并指出最合适的代码模板。
```

```text
当前单模型表现不稳定，帮我判断是否应升级为组合模型，并设计验证方案。
```

## 工作原则

该技能优先选择可解释、可验证、能在竞赛时间内落地的方案。只有当基线模型存在明确缺陷并且验证证据充分时，才建议升级模型复杂度。

