<div align="center">

# Math Modeling Solver

**从一道数学建模题，到可复现模型、论文级图表与完整竞赛论文。**

[![Codex Skill](https://img.shields.io/badge/Codex-Skill-111827?logo=openai&logoColor=white)](./SKILL.md)
![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![MATLAB](https://img.shields.io/badge/MATLAB-Supported-EF6C00)
![Figures](https://img.shields.io/badge/Figures-SVG%20%7C%20PDF%20%7C%20300dpi-2563EB)
![Tests](https://img.shields.io/badge/Tests-22%2F22%20passing-16A34A)

面向数学建模竞赛的端到端 Agent Skill，建议搭配matlab的官方mcp使用，直接向codex发送指令：帮我配置一下这个mcp，链接：https://github.com/matlab/matlab-mcp-server


</div>

![Math Modeling Solver scientific figure](assets/images/modeling-evidence-figure.png)
<img width="1272" height="510" alt="微信图片_20260715092244_582_35" src="https://github.com/user-attachments/assets/d14101d5-a326-4f1b-8fd3-e73005a2c4f0" />

## 它是什么

Math Modeling Solver 不是只会罗列算法的提示词集合。它是一套以证据为中心的数学建模工作流，把题目拆解、数据检查、模型选择、代码执行、鲁棒性验证、科学绘图和论文写作连接为一个可审计过程。

它要求每个关键结论都能追溯到真实数据、执行代码、结果表、图、公式或可靠来源，并通过五道证据门阻止“代码没有运行、图表没有来源、论文数字互相矛盾”等常见问题进入最终交付。

## 版本更新日志

### v2.0.0 - 诊断优先与 MATLAB 原生增强（2026-07-18）

- 新增得分差距诊断门：优化前量化理论上界、基线、参考值、分项目差距和加权敏感度。
- 新增代理模型—精确仿真一致性门：Beam Search、MPC 等扩大搜索前至少逐步核对 50 个状态转移。
- 新增硬约束动作掩码规范：违法动作不再依靠事后惩罚或修复，而是在搜索前排除。
- 新增实验预算、晋级阈值与停止规则，以及 `exploratory → candidate → independently_validated → frozen → manuscript` 结果生命周期。
- 新增 MATLAB MCP、MATLAB 优化器与 MATLAB 原生论文绘图路线，不再强制定量图跨语言转到 Python。
- 新增 `word-only`、`paper-bundle`、`code-only` 与自定义交付配置；只交 Word 时保留底层证据，但不强制提交冗余数据附件。
- 新增 4 个可执行诊断/实验工具和配套回归测试。

## 核心能力

| 模块 | 能做什么 | 主要产出 |
| --- | --- | --- |
| 题目拆解 | 识别目标、约束、子问题、依赖关系和隐藏假设 | 问题契约、子问题图、数据需求 |
| 数据审计 | 对 CSV、Excel、MAT 等文件执行类型、缺失、异常、单位、泄漏和拆分检查 | JSON/CSV/HTML 审计报告、风险清单、处理方案 |
| 模型选择 | 建立可解释基线，比较候选模型并控制复杂度 | 方法决策、数学公式、验证计划 |
| 优化诊断 | 计算得分上界、参考差距、分项价值，核对精确状态转移并屏蔽非法动作 | 差距报告、一致性报告、实验预算与晋级记录 |
| 编程求解 | 生成并执行 Python 或 MATLAB 模型 | 源代码、运行命令、结果文件 |
| 结果验证 | 完成基线对照、误差分析、敏感性、鲁棒性和不确定性检验 | 指标表、扰动实验、适用边界 |
| 科学绘图 | 从论文结论和数据结构选择图表，生成定量图与模型架构图 | SVG、PDF、300 dpi PNG、灰度图 |
| 论文写作 | 以论点和证据组织摘要、模型、结果、讨论与结论 | 论文大纲、正文、术语账本 |
| 交付审计 | 检查代码、数字、图表、论文和复现信息的一致性 | JSON/Markdown 审计报告 |

## 证据门工作流

![证据门工作流：通过后推进，未通过则修复、补证或标记 blocked](assets/images/evidence-gate-workflow.svg)


五道门分别检查：

1. `Intake`：目标、约束、子问题和数据来源是否明确。
2. `Method`：基线、候选方法、可行性试验和验证设计是否完整。
3. `Computation`：代码是否真实运行，输入、环境、命令和输出能否复现。
4. `Evidence`：结论是否经过公平对照、误差分析和稳健性验证。
5. `Manuscript`：论文中的数字、图表、术语、单位和引用是否一致。

上游数据、假设、方法或参数改变时，受影响的下游结果必须重新运行，不能继续沿用旧结论。

对带评分函数或离散事件仿真的优化题，Method 与 Computation 之间还增加三项专门门槛：先分析得分差距，再把硬约束编码为动作掩码，最后核对代理模型与精确仿真的逐步一致性。高分但不可行或状态转移不一致的结果不能晋级为论文结果。

## 可执行数据审计

`scripts/audit_dataset.py` 把数据审计从人工模板升级为可复现程序，支持 CSV、TSV、分隔文本/DAT、Excel 多工作表和二维 MAT 变量。它会保留输入文件 SHA-256，并检查：

- 字段类型、缺失率、重复行、常量列；
- IQR 异常值、极端偏态、非有限值和混合单位；
- 类别不平衡、目标副本及近乎完美的目标相关；
- 时间乱序、训练—验证时间交叉和分组穿越；
- 高维小样本风险与匹配数据结构的验证划分建议；
- MAT 复数矩阵；高维数组和结构体会要求显式轴定义。

审计结果同时输出 JSON、字段级 CSV 和可浏览 HTML。自动标记是待核验证据，不会擅自删除异常值，也不能在缺少“特征何时可用”的业务定义时宣称不存在未来信息泄漏。

## 往年题型盲测

`scripts/blind_modeling_benchmark.py` 用“公开题包 → 独立方案冻结 → 隔离评分”测试题型路由、基线选择、验证设计和数据风险识别。Agent 在作答阶段只能看到题目、附件、公开标签目录和 Skill；所有运行冻结后才加载评分表，因此测量的是泛化能力而不是题解记忆。

仓库包含一个三题型试验集，覆盖机组优化排班、移动场景超分辨定位和大规模竞赛评审。题目文件不进入仓库，公开清单只保存外部链接与 SHA-256。评分同时报告：

- 与隔离评分表的一致性；
- 多次独立运行的任务族、基线、验证规则和数据风险 Jaccard 稳定性；
- 每道子问题的路由、基线、验证和风险分项结果。

下面不是功能示意图，而是 3 道往年题、11 个子问题、3 次相互隔离的独立运行所得的真实评分结果：

[![往年题型盲测结果：三次独立运行平均正确率 99.1%，跨运行稳定性 90.6%](assets/images/blind-benchmark-dashboard.png)](assets/images/blind-benchmark-dashboard.svg)

<p align="center"><sub>点击图片可查看可编辑 SVG。结果来自方案冻结后的隔离评分；这是当前三题型回归基线，不是泛化能力的最终证明。</sub></p>


稳定不等于正确，单个公开试验集上的高分也不等于已经泛化。详细隔离规则见 [`blind-benchmarking.md`](references/blind-benchmarking.md)。

## 论文级绘图系统

绘图流程先回答“这张图要证明什么”，再决定使用哪种图。系统会检查变量类型、样本量、分组、单位、基线、不确定性和验证方式，并要求每张图只有一个主结论。

### 定量图

- 方法比较与不确定性；
- 预测曲线、置信区间和验证分界；
- 优化收敛与约束违例；
- 分组原始点与分布摘要；
- Pareto 前沿与可行解；
- 单因素/双因素敏感性热图；
- 中文字体、色盲友好配色和灰度冗余编码。

### 模型架构图

使用 JSON 描述节点和关系，由代码生成流水线、分层系统、反馈闭环或基线—方案对照图。输出保留为可编辑 SVG/PDF，不依赖手工拖拽。

![Code-native modeling closed loop](assets/images/modeling-closed-loop.png)

### 图表交付与审计

每张正式图应包含：

- 一句话视觉结论和读者问题；
- 面板职责、指标、单位、基线与不确定性；
- 源数据、生成脚本和确定性命令；
- SVG/PDF 矢量主文件、300 dpi PNG 和灰度预览；
- 自动 QA JSON 与最终尺寸人工预览。

图包审计器会检查缺失坐标轴、过小字号、文字越界、DPI、最终尺寸、矢量文字、源数据、统计说明和复现命令。AI 生成图片不能充当定量结果证据。

## 支持的模型族

- **综合评价**：TOPSIS、AHP、熵权法、DEA、灰色关联、组合评价。
- **预测分类**：GM(1,1)、ARIMA、回归、随机森林、XGBoost、SVM、神经网络。
- **优化决策**：线性规划、整数规划、动态规划、遗传算法、粒子群、模拟退火、多目标优化。
- **网络路径**：最短路、最大流、中心性、选址、调度、路径规划。
- **机理仿真**：微分方程、状态转移、排队、库存、可靠性、Monte Carlo、Agent-based 模型。
- **统计分析**：聚类、PCA、假设检验、时间序列、生存分析、因果设计。

仓库包含 Python 与 MATLAB 基线模板。模板用于快速建立可执行起点，不能替代针对真实数据的适配、执行和验证。论文图可使用 Python/Matplotlib 或 MATLAB 原生生成；两条路线都必须保留源数据、生成代码、统计定义、矢量/位图导出和最终尺寸视觉检查。跨语言 CSV/MAT 交接是可选路线，不是强制要求。

## 安装

### Codex

Windows PowerShell：

```powershell
git clone https://github.com/YANG985-CMD/Math-Modeling-Solver.git `
  "$HOME\.codex\skills\math-modeling-solver"
```

macOS / Linux：

```bash
git clone https://github.com/YANG985-CMD/Math-Modeling-Solver.git \
  ~/.codex/skills/math-modeling-solver
```

重新启动 Codex 会话后，可直接调用：

```text
$math-modeling-solver
```

## 快速开始

### 1. 直接解决建模题

```text
使用 $math-modeling-solver 解决这道数学建模题。
先拆分子问题、审计数据并建立简单基线，再比较候选模型。
代码必须真实运行，最后给出稳健性分析、论文级图表和结论边界。
```

### 2. 初始化可审计项目

```powershell
python scripts/init_modeling_project.py D:\modeling\problem-a `
  --mode formal --questions 3 --delivery-profile word-only
```

生成的工作区包含问题契约、数据审计、方法决策、结果冻结、图表契约、论文契约、主张—证据账本和复现清单。

### 3. 优化前分析得分差距

```powershell
python scripts/analyze_score_gap.py score-contract.json `
  --out-dir results/diagnostics/score-gap
```

输入为加权归一化评分契约；输出 JSON 与 CSV，分别给出理论上界、基线、参考差距、分项优先级与单位边际价值。若真实评分函数不是加权归一化和式，应按真实公式自行推导，不能套用该工具。

### 4. 核对代理模型与精确仿真

```powershell
python scripts/check_transition_fidelity.py `
  surrogate-trajectory.json exact-trajectory.json `
  --min-steps 50 --out results/diagnostics/transition-fidelity.json
```

两条轨迹必须使用相同初态、动作序列和事件时间，并逐步给出 `state`、`action` 与 `feasible_actions`。状态、时间、动作集合或精确可行性任一不一致都会失败。

### 5. 审计真实数据

```powershell
uv run --with pandas --with scipy --with openpyxl --with xlrd `
  python scripts/audit_dataset.py D:\modeling\problem-a\input\data.xlsx `
  --target label --time timestamp --group subject_id --split split `
  --out-dir D:\modeling\problem-a\audit\dataset
```

如果没有某个角色列，删除对应参数即可。Excel 默认检查全部工作表；MAT 默认检查所有可转为二维表的变量。

### 6. 生成绘图示例

```powershell
python assets/code/python/demo_modeling_figure.py `
  --out build/figure-demo
```

### 7. 生成模型架构图

```powershell
python scripts/build_modeling_diagram.py --demo `
  --out build/diagram/modeling-loop
```

也可以从 [`modeling-diagram-spec-template.json`](assets/templates/modeling-diagram-spec-template.json) 创建自己的 JSON 结构图。

### 8. 审计图表和项目

```powershell
python scripts/audit_figure_bundle.py `
  build/figure-demo/figure-contract.json `
  --root build/figure-demo --strict

python scripts/audit_modeling_project.py D:\modeling\problem-a
```

## 三种运行模式

| 模式 | 使用场景 | 数据规则 |
| --- | --- | --- |
| `formal` | 正式竞赛、课程论文或项目交付 | 只使用真实、可追溯数据 |
| `demo` | 教学、结构演示和环境测试 | 可使用明确标注的合成数据 |
| `blocked` | 缺少关键数据、定义或授权 | 记录阻塞，不伪造结果继续写作 |

## 四种交付配置

| 配置 | 最终交付 | 工作区仍需保留 |
| --- | --- | --- |
| `word-only` | 一个嵌入必要图表的 DOCX | 代码、源数据、运行记录、图表 QA |
| `paper-bundle` | 论文、代码、结果、完整图包与审计记录 | 全部证据链 |
| `code-only` | 可执行代码、测试、命令与结果摘要 | 输入契约与验证诊断 |
| `custom` | 用户明确约定的文件 | 支撑最终主张所需的底层证据 |

交付配置只决定“交什么”，不降低真实性、可行性、仿真一致性或复现要求。

## 项目交付结构

```text
problem-a/
├─ input/                         # 题目与原始数据
├─ planning/
│  ├─ problem-contract.json       # 目标、约束与子问题
│  ├─ method-decision.json        # 基线、候选模型与验证方案
│  ├─ experiments.json            # 假设、预算、停止规则与结果晋级
│  ├─ figure-contract.json        # 图表结论、数据与导出要求
│  └─ data-audit.csv              # 数据来源与质量检查
├─ src/                           # 可执行代码
├─ results/
│  ├─ tables/
│  ├─ figures/
│  └─ frozen-results.json         # 论文采用的权威数字
├─ paper/
│  ├─ manuscript-contract.json    # 论文论点、证据与边界
│  ├─ terminology-ledger.csv      # 术语、符号和单位
│  └─ main.md
└─ audit/
   ├─ reproducibility-manifest.json
   ├─ claim-evidence-ledger.csv
   └─ latest-audit.md
```

## 典型用法

```text
使用 $math-modeling-solver 检查这个时间序列方案是否存在数据泄漏，
设计滚动验证，并把论文中的预测结论映射到真实结果表。
```

```text
使用 $math-modeling-solver 检查 TOPSIS 排名为什么不稳定，
设计权重扰动实验，并判断是否需要组合评价模型。
```

```text
使用 $math-modeling-solver 根据已有结果重构论文图表。
每张图先确定一个主结论，再生成 SVG、PDF、PNG、灰度图和 QA 报告。
```

```text
使用 $math-modeling-solver 写数学建模竞赛论文。
先冻结权威结果和术语，再组织摘要、模型、结果、验证、讨论与结论。
```

## Skill 结构

```text
math-modeling-solver/
├─ SKILL.md
├─ agents/openai.yaml
├─ scripts/
│  ├─ init_modeling_project.py
│  ├─ audit_dataset.py
│  ├─ analyze_score_gap.py
│  ├─ check_transition_fidelity.py
│  ├─ register_experiment.py
│  ├─ promote_validated_candidate.py
│  ├─ blind_modeling_benchmark.py
│  ├─ audit_modeling_project.py
│  ├─ audit_figure_bundle.py
│  └─ build_modeling_diagram.py
├─ references/                    # 按任务渐进加载的方法参考
├─ benchmarks/                    # 只含外部链接、哈希、响应模板和隔离评分契约
├─ assets/
│  ├─ templates/                  # 问题、方法、图表和论文契约
│  ├─ code/python/                # 算法与科学绘图工具
│  ├─ code/matlab/                # MATLAB 算法基线
│  └─ images/                     # README 展示图
└─ tests/
```

## 验证开发环境

使用 `uv` 运行完整测试：

```powershell
uv run --with matplotlib --with numpy --with pillow --with pandas `
  --with scipy --with openpyxl --with xlrd `
  python -m unittest discover -s tests -v
```

验证 Skill 结构：

```powershell
uv run --with pyyaml python `
  "$HOME\.codex\skills\.system\skill-creator\scripts\quick_validate.py" .
```

## 质量边界

- 不虚构数据、运行结果、评价指标、引用或图片结论。
- 先运行简单基线，再根据可观察失败决定是否增加复杂度。
- 时间、分组和空间数据必须使用结构匹配的验证方案。
- 代表性轨迹不能替代总体统计证据。
- 优化收敛图必须同时检查约束可行性。
- 论文中的每个重要主张都必须链接到可核验的证据。
- 明确报告不确定性、失败情形、适用范围和未解决风险。

## 许可证

本项目采用 [PolyForm Noncommercial License 1.0.0](LICENSE)：

- 个人学习、研究、实验及其他非商业用途可免费使用、修改和分发；
- 禁止将本项目或其衍生作品用于任何商业用途；
- 商业使用、商业集成或商业分发需要事先联系仓库所有者并取得单独授权。

本许可证包含商业用途限制，因此属于源码可用许可证，并非 OSI 认可的开源许可证。

---

如果你需要的是一个能从题目一直工作到可复现论文交付的数学建模 Agent，直接从 `$math-modeling-solver` 开始。

<!-- skill-provenance:v1;owner=YANG985-CMD;id=YANG985-CMD-MMS-2026-v7;path=README.md;sha256=8005fc3ea057d93edf0dc1a43557a14c03f3c4206301f342130471cda4218f2a;pub=0ofp8dKKJWMQK0LUC4dZDC8cynCRQlggy7cVeq7NfBo=;sig=zXiNk6Ly8czR1V_Vh7Cips6LS52xsu-lpRQub5lhKs5BMDXeXzbf2e6bbwhxs5kxdxuJ732VFFS_t65kDvO8Bw== -->
