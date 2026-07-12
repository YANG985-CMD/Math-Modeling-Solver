# Math Modeling Playbook

面向数学建模竞赛与应用项目的证据门控 Agent Skill。它不仅给出“该用什么模型”，还要求模型真正运行、结果能够复现、图表能够追溯、论文论证与数字保持一致。

> 项目目标：把判题、建模、编程、验证和写作连成一条可审计的流水线，让复杂方法服务于证据，而不是服务于“看起来高级”。

## v2.1 核心升级

| 能力 | 解决的问题 | 产出 |
| --- | --- | --- |
| 子问题路由与依赖图 | 多问之间输入输出混乱 | 子问题契约、依赖关系、候选模型 |
| 三种运行模式 | 缺数据时容易偷偷造数 | formal / demo / blocked 明确标记 |
| 基线优先与复杂度测试 | 为炫技盲目堆叠模型 | 基线、失败证据、升级理由 |
| 五道证据门 | 方案写了却没跑、结果未经验证 | Intake → Method → Computation → Evidence → Manuscript |
| 数据与泄漏审计 | 验证集污染、时间穿越、单位错误 | 数据审计表与拆分策略 |
| 可复现运行清单 | 换电脑或换队员后无法复现 | 命令、环境、依赖、随机种子、输入输出 |
| 结果冻结 | 论文、图表和代码里的数字不一致 | frozen-results.json 唯一权威结果集 |
| 结论—证据账本 | 论文结论找不到数据支撑 | 每条结论对应代码、表格、图片和验证状态 |
| 图表先立合同 | 先套模板、图多但论证弱 | 核心信息、面板任务、数据来源、统计与导出 QA |
| 论证优先写作 | 按章节堆文字、术语漂移 | 一句话论点、段落任务、术语账本、证据边界 |
| AI 图片边界 | 示意图和数据证据混淆 | 解释性生图可用，但不得伪装为经验数据 |
| 自动审计 | 交稿前靠人工排雷不完整 | JSON + Markdown 门控审计报告 |

## 工作流

~~~mermaid
flowchart LR
    A[题目与数据] --> G1{Intake}
    G1 --> B[候选模型与基线]
    B --> G2{Method}
    G2 --> C[代码执行与复现]
    C --> G3{Computation}
    G3 --> D[对照、敏感性与鲁棒性]
    D --> G4{Evidence}
    G4 --> E[冻结数字、图表合同与论证写作]
    E --> G5{Manuscript}
    G5 --> F[可复现交付]
    G1 -.失败.-> X[修复或 blocked]
    G2 -.失败.-> X
    G3 -.失败.-> X
    G4 -.失败.-> X
    G5 -.失败.-> X
~~~

上游数据、假设、方法或代码发生变化时，下游结果会被视为过期，需要从受影响的门重新验证。

## 支持的任务

- 综合评价：TOPSIS、AHP、熵权、DEA、灰色关联及组合模型
- 预测与分类：ARIMA、GM(1,1)、线性/逻辑模型、随机森林、XGBoost、SVM、LSTM
- 优化决策：LP、MILP、动态规划、GA、PSO、SA、多目标优化
- 网络与路径：最短路、最大流、中心性、调度与路径规划
- 机制与仿真：ODE、状态转移、排队、库存、可靠性、Monte Carlo、Agent-based
- 统计与无监督：回归、聚类、PCA、假设检验、生存与因果设计

仓库保留 15 个 Python 与 7 个 MATLAB 算法模板，并将它们置于基线比较、执行验证和证据审计之下。

## 快速安装

克隆到 Codex 技能目录：

~~~powershell
git clone https://github.com/YANG985-CMD/math-modeling-playbook.git "$HOME\.codex\skills\math-modeling-playbook"
~~~

重新启动 Codex 会话后，可直接提出数学建模请求。

## 新项目初始化

在 Skill 根目录运行：

~~~powershell
python scripts/init_modeling_project.py D:\modeling\problem-a --mode formal --questions 3
~~~

脚本会创建以下可审计工作区：

~~~text
problem-a/
├─ input/                         # 原始输入
├─ planning/
│  ├─ problem-contract.json       # 问题、目标、约束、子问题
│  ├─ method-decision.json        # 基线、候选方法、验证方案
│  ├─ figure-contract.json        # 图表信息、面板证据与导出 QA
│  └─ data-audit.csv              # 数据来源与质量检查
├─ src/                           # 可执行代码
├─ results/
│  ├─ tables/
│  ├─ figures/
│  └─ frozen-results.json         # 论文采用的权威数字
├─ paper/
│  ├─ manuscript-contract.json    # 一句话论点、受众、证据与边界
│  ├─ terminology-ledger.csv      # 术语、符号、单位统一标准
│  └─ main.md
└─ audit/
   ├─ reproducibility-manifest.json
   ├─ claim-evidence-ledger.csv
   └─ latest-audit.md
~~~

交付前执行：

~~~powershell
python scripts/audit_modeling_project.py D:\modeling\problem-a
~~~

只有五道门全部通过时，命令才以成功状态退出；失败报告会指出缺失的文件、证据或批准项。

## 使用示例

~~~text
把这道题拆成子问题和依赖图，先给最简单基线，再比较三个候选模型。
~~~

~~~text
按 formal 模式完成这个预测题。检查时间泄漏，建立滚动验证，
把每个论文结论映射到结果表，最后运行项目审计。
~~~

~~~text
我的 TOPSIS 排名不稳定。先证明基线的失败，再决定是否升级为
TOPSIS-灰色关联组合模型，并给出权重扰动实验。
~~~

~~~text
先给每张图写一句话结论和面板证据地图，再用真实结果生成 SVG/PDF；
审查重复面板、颜色一致性、误差定义和最终尺寸可读性。
~~~

~~~text
先锁定论文的一句话论点、读者顺序和术语账本，再按“问题—基线差距—
模型—公平比较—鲁棒性—决策意义—边界”组织全文。
~~~

~~~text
只剩 6 小时，请保留可解释基线，删掉来不及验证的复杂模型，
给出建模、代码、验证和写作的最小闭环。
~~~

## Skill 目录

~~~text
math-modeling-playbook/
├─ SKILL.md
├─ agents/openai.yaml
├─ scripts/
│  ├─ init_modeling_project.py
│  └─ audit_modeling_project.py
├─ references/
│  ├─ evidence-gated-workflow.md
│  ├─ data-and-reproducibility.md
│  ├─ validation-playbook.md
│  ├─ task-family-router.md
│  ├─ figure-contract-and-qa.md
│  ├─ argument-first-paper-writing.md
│  └─ ...                         # 模型选择、论文、时间线等
├─ assets/
│  ├─ templates/
│  └─ code/python/、code/matlab/
└─ tests/
~~~

## 设计原则

1. 真实证据优先于漂亮叙述。
2. 简单且验证充分的模型优先于未经验证的复杂模型。
3. 代码、数字、图片和论文必须形成可追溯链。
4. 缺少真实数据时明确阻塞或切换演示模式，不伪造正式结果。
5. 每次模型升级都要回答：基线哪里失败、新组件解决什么、是否公平比较。
6. 数据图必须由可追溯数据和代码生成；AI 生图只用于明确标注的解释性内容。

## 公开项目调研与致谢

v2.1 在公开资料调研基础上独立设计和实现。我们比较了以下项目的工作流思想，并重新组织为本仓库的“问题契约—五道证据门—图表合同—论证合同—结果冻结—结论账本”体系；没有复制未授权项目的代码或文案。

- [MathModelAgent](https://github.com/jihe520/MathModelAgent)：端到端建模、人工确认与容错流程参考。调研时未检测到标准仓库许可证，因此仅作功能基准。
- [LLM-MM-Agent](https://github.com/usail-hkust/LLM-MM-Agent)：子任务分解、依赖执行与迭代评审的研究思路，GPL-3.0。
- [MathModeling-skills](https://github.com/zhnnky329/MathModeling-skills)：模块化任务与质量门设计参考，MIT。
- [EZ_math_model](https://github.com/woodfishhhh/EZ_math_model)：正式/演示模式与交付物组织参考，MIT。
- [math-modeling-skill](https://github.com/XiaoMaColtAI/math-modeling-skill)：角色分工和复现清单参考。调研时未检测到标准仓库许可证，因此仅作功能基准。
- [nature-skills](https://github.com/Yuan1z0825/nature-skills)：结论优先的科研图表、论证优先写作、术语一致性与投稿前 QA 思想参考，Apache-2.0。

所有新增工作流、模板、审计器、测试与文案均在本仓库中重新设计和实现。引用这些项目是为了让设计来源透明，也便于社区复核差异。
