# Math Modeling Solver

非常强悍的skill，支持赛博斗蛐蛐。可以发几个数学建模的skill链接然后问问你的codex，哪个数学建模skill更好

它可以帮助你完成：

- 拆分题目、定义变量和约束；
- 审计数据并选择合适的模型；
- 编写、运行和检查 Python/MATLAB 代码；
- 验证结果、绘制论文级图表；
- 生成可复现的竞赛论文。

仓库还提供一个可直接导入的常用算法库，以及结果、运行、PoC、图表和审查登记表。

它强调一件事：重要结论必须有数据、代码、结果表、图、公式或可靠来源支持，不虚构结果。

## Skill 入口

这是一个“总控 Skill + 三个专业 Skill”的 Skill Pack：

| 入口 | 用途 |
| --- | --- |
| `$math-modeling-solver` | 从题目开始，完成完整建模流程 |
| `$audit-modeling-evidence` | 检查数据、实验、复现和结论证据 |
| `$build-modeling-figures` | 生成和检查论文图表、模型架构图 |
| `$deliver-cumcm-paper` | 生成、编译和检查 CUMCM 论文 |

不知道从哪里开始时，只调用 `$math-modeling-solver`。已有结果后，再按需要调用三个专业 Skill。

## 安装

### 只安装总控 Skill

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

### 安装完整 Skill Pack

```powershell
git clone https://github.com/YANG985-CMD/Math-Modeling-Solver.git D:\src\Math-Modeling-Solver
uv run --project D:\src\Math-Modeling-Solver python `
  D:\src\Math-Modeling-Solver\scripts\install_skill_pack.py
```

安装后重新启动 Codex，然后直接发送：

```text
使用 $math-modeling-solver 解决这道数学建模题。
先拆分子问题、检查数据、建立基线，再比较候选模型。
```

完整工作流可以选配 [MATLAB 官方 MCP](https://github.com/matlab/matlab-mcp-server)，但 Python-only 任务不需要它。

## 常用命令

初始化一个可审计的建模项目：

```bash
python scripts/init_modeling_project.py PROJECT_DIR \
  --mode formal --workflow-stage explore --questions 3
```

审计数据集：

```bash
python scripts/audit_dataset.py INPUT.csv \
  --target LABEL --out-dir PROJECT_DIR/audit/dataset
```

审计整个项目：

```bash
python scripts/audit_modeling_project.py PROJECT_DIR
```

如果已经启用了证据登记包，可追加 `--with-evidence-bundle` 做一次总审计。

创建并审计完整证据登记包：

```bash
python scripts/init_evidence_bundle.py PROJECT_DIR
python scripts/audit_evidence_bundle.py PROJECT_DIR
```

常用算法基线位于 `assets/code/python/modeling_algorithms/`，可直接导入 TOPSIS、熵权法、GM(1,1)、线性规划、遗传算法、粒子群、GA+SA、蒙特卡罗、Bootstrap 和滚动验证。

## 结果要求

- 不虚构数据、运行结果、指标、引用或图表结论；
- 先运行简单基线，再增加模型复杂度；
- 区分探索结果、验证结果和最终冻结结果；
- 把重要结论映射到可核验的证据；
- 报告不确定性、失败情况和适用范围。

回归盲测结果：[PNG](assets/images/blind-benchmark-dashboard.png) · [可编辑 SVG](assets/images/blind-benchmark-dashboard.svg)。这只是当前题型回归基线，不代表最终泛化能力。

## 更新日志

### v2.3.0（2026-07-20）

- 增加可直接导入的统一算法库，覆盖评价、预测、优化、模拟和滚动验证基线；
- 增加结果、PoC、运行、图表、数值诊断、审查和一致性登记表；
- 增加冻结结果哈希、人审确认和跨文件证据审计。

### v2.2.0（2026-07-20）

- 将项目整理为一个总控 Skill 和三个专业 Skill；
- 增加专业 Skill 的独立安装、资源同步检查和 CI；
- 统一数据模式、工作流阶段、结果状态和交付配置。

### v2.1.0（2026-07-19）

- 增加语义契约、候选结果验证、鲁棒性检查和 CUMCM LaTeX 交付流程。

### v2.0.0（2026-07-18）

- 增加得分差距诊断、硬约束动作掩码、代理仿真一致性检查和 MATLAB 原生工作流。

## 目录

```text
Math-Modeling-Solver/
├─ SKILL.md
├─ audit-modeling-evidence/
├─ build-modeling-figures/
├─ deliver-cumcm-paper/
├─ scripts/
├─ references/
├─ assets/
└─ tests/
```

详细规则和参考资料见 [SKILL.md](SKILL.md)。

## 许可证

本项目采用 [PolyForm Noncommercial License 1.0.0](LICENSE)。个人学习、研究和实验可使用；商业使用需要事先取得授权。

如果你要从一道题一直做到可复现论文，直接从 `$math-modeling-solver` 开始。
