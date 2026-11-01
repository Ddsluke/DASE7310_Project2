# DASE7310 GP2 团队执行指南（给同学，也给同学的 AI）

> 这份文档是给**接下来负责第 2/3/4 周和最终报告**的同学看的。
> 目标：任何人拿到这份文档 + 仓库，都能独立跑出当周组合、核对、提交、记录，并且知道报告里该怎么写。
>
> 仓库：`D:\Backup\Documents\dase7310\DASE7310_GP2_Repo`
> 远程：https://github.com/Ddsluke/DASE7310_Project2
>
> 建议阅读顺序：
> 1. 本文档（规则 + 流程 + 分工）
> 2. `WEEK2_GUIDANCE_ZH.md`（第 2 周具体操作）
> 3. `WEEK3_GUIDANCE_ZH.md`（第 3 周具体操作）
> 4. `BENCHMARKS_ZH.md`（老师要求的 benchmark 对比）
> 5. `GMV_EXPLAINED_ZH.md` / `VIEWS_EXPLAINED_ZH.md`（原理，选读）

---

## 0. 先记住五条铁律

1. **估值截点必须是“目标交易周开始前的那个周五”**，不是随便一个日期。
2. **算股数用未复权真实收盘价**；算信号/协方差才用后复权。
3. **第二周起，C_{i-1} 是上一周实际剩下的资本**，不是固定的 1,000,000。
4. **提交快照只增不改**：旧文件不覆盖；要改就新建 `_variant` 并写修订说明。
5. **提交前必须核对 Moodle 真的上传成功**（GP1 Week 4 就栽在这里）。

---

## 1. 项目规则与时间线

### 1.1 官方规则（以 `Group-Project-2_2026.pdf` 为准）

| 项目 | 内容 |
|---|---|
| 股票池 | 9988、0066、1398、3988、0981、0005、1810、0016、1113、0700 |
| 初始资本 | HKD 1,000,000，必须满仓（`Σw = 1`） |
| 做空 | 官方允许；**我们组不做空** |
| 周内策略 | Buy-and-hold，周内股数不变 |
| 再平衡 | 第 2/3/4 周开始前各一次，**全程最多 3 次** |
| 交易周 | 11/2–6、11/9–13、11/16–20、11/23–27 |
| 提交 | **11/1、11/8、11/15、11/22**，周日 23:59 前 |
| 报告 + 互评 | **11/30**，正文 5 页（不含封面/目录） |
| 口头展示 | **11/23、11/30**，10 分钟，覆盖 GP1 + GP2 |
| 评分 | 周度排名 30%、展示与参与 30%、报告 20%、互评 20% |

> 大纲 Lecture 1 还写着“5 周、10/26–11/29、5 次调整”，和官方 PDF 冲突。
> **按 PDF 的 Table 1 走**；保险起见在群里/课上确认一句。

### 1.2 每周时间线

| 时间 | 动作 |
|---|---|
| 周五收盘后 | `refresh-data` 拉最新数据；`evaluate` 记录上一周实际收益 |
| 周六 | `build` 生成下一周组合；跑参考组合（GMV/CAPM）做对比 |
| 周日 23:59 前 | 上传 `weeks/weekN/submission.xlsx` 到 Moodle；确认上传成功 |
| 下周五收盘后 | `evaluate --week N` 记录实际收益 |

---

## 2. 数据口径（最容易错的地方）

### 2.1 raw vs hfq

| 用途 | 用哪个价格 | 原因 |
|---|---|---|
| 信号、协方差、回测收益 | **hfq（后复权）** | 总回报，分红/拆股已处理 |
| 股数 `h = c/p`、资本 `C = p*h` | **raw（未复权真实收盘价）** | 课程公式的 `p` 是真实市价 |

例子（2026-10-30）：

- 汇丰 0005：真实收盘 **135.70**，后复权 **952.05**（约 7 倍）；
- 中芯 0981：真实收盘 **42.98**，后复权 **4.298**（约 1/10）。

用复权价算股数会差几倍，直接错。

### 2.2 周价格与截点

- 周价格 = 每周 **W-FRI** 最后一根已实现收盘价；
- 第 i 周的估值日 = 第 i 周开始前的那个周五；
- 第 1 周：2026-10-30；第 2 周：2026-11-06；第 3 周：2026-11-13；第 4 周：2026-11-20。

### 2.3 公式

```
w_{s,i} = c_{s,i-1} / C_{i-1}
h_{s,i} = c_{s,i-1} / p_{s,i-1}
C_i     = Σ_s p_{s,i} × h_{s,i}
R_i     = (C_i − C_{i-1}) / C_{i-1}
```

- 第 1 周：`C_0 = 1,000,000`；
- 第 2 周起：`C_{i-1}` 是上一周实际剩余资本（脚本自动从上一周 `portfolio.csv` 的股数 × 新截点价算出来）；
- 小数股保留 6 位，**不按每手取整**（课程公式允许小数股；取整会剩现金，违反“fully allocated”）。

---

## 3. 代码架构

### 3.1 环境

```powershell
$env:MKL_THREADING_LAYER = 'SEQUENTIAL'   # 必须，否则 sklearn/scipy 可能原生崩溃
$py = 'C:\Users\Administrator\miniforge3\envs\dase7310\python.exe'
cd D:\Backup\Documents\dase7310\DASE7310_GP2_Repo
```

Python 3.12、pandas 3.0、numpy 2.5、scipy 1.18、akshare 1.19、openpyxl。

### 3.2 三个主命令

```powershell
# 1) 拉数据：raw + hfq + HSI/HSTECH
& $py portfolio.py refresh-data --end 2026-11-06

# 2) 生成组合（第 2 周示例：CAPM，λ=15）
& $py portfolio.py build --week 2 --cutoff 2026-11-06 --strategy capm --lam 15

# 3) 目标周结束后记录实际收益（append-only）
& $py portfolio.py evaluate --week 1
```

### 3.3 支持的策略

| `--strategy` | 含义 | 关键参数 |
|---|---|---|
| `gmv` | 全局最小方差（纯多头 1–25%） | 无 |
| `capm` | CAPM/SML 观点 + 均值-方差 | `--lam`（默认 10，建议 15）、`--rf`、`--premium` |
| `signal` | 复合信号（12 周动量 + 近 52 周高 + 低波动）+ 均值-方差 | `--lam`（建议 8） |
| `tilt` | 直接对 EW 做信号倾斜（不估 μ） | `--k`（建议 2） |
| `ew` | 等权 1/10 | 无 |
| `tangency` | 切点组合（课程公式 + 约束） | `--rf` |
| `top4` | 前 4 名集中（robustness） | 无 |

### 3.4 目录

```
portfolio.py                 主脚本：refresh-data / build / evaluate
research_*.py                研究脚本（信号、GMV、观点、benchmark、回测）
data/                        raw/hfq 日线、周线、周收益、HSI、meta.json
weeks/weekN/                 每周快照（submission.xlsx/csv、portfolio.csv、params.json、report.md）
research/                    所有研究输出（CSV）
ledger.md                    周度实际收益台账（append-only）
```

---

## 4. 每周标准流程（照着做）

### 4.1 周五收盘后（约 18:00 后）

```powershell
$env:MKL_THREADING_LAYER = 'SEQUENTIAL'
$py = 'C:\Users\Administrator\miniforge3\envs\dase7310\python.exe'
cd D:\Backup\Documents\dase7310\DASE7310_GP2_Repo

# 1) 刷新数据
& $py portfolio.py refresh-data --end 2026-11-06

# 2) 记录上一周实际收益（第 1 周示例）
& $py portfolio.py evaluate --week 1

# 3) 检查数据是否真的到本周五
Get-Content data\meta.json
```

`meta.json` 里 `raw_last_weekly` 必须 = 本周五；如果不是，**不要提交**，先查数据源。

### 4.2 周六：生成组合

第 2 周（CAPM）：

```powershell
& $py portfolio.py build --week 2 --cutoff 2026-11-06 --strategy capm --lam 15

# 参考组合（不提交，只对比）
& $py portfolio.py build --week 2 --cutoff 2026-11-06 --strategy gmv --variant ref_gmv
```

第 3 周（信号）：

```powershell
& $py portfolio.py build --week 3 --cutoff 2026-11-13 --strategy signal --lam 8

# 参考组合
& $py portfolio.py build --week 3 --cutoff 2026-11-13 --strategy gmv --variant ref_gmv
& $py portfolio.py build --week 3 --cutoff 2026-11-13 --strategy capm --lam 15 --variant ref_capm
```

第 4 周（自适应）：

```powershell
# 先看前 3 周累计主动收益（ledger.md 或 realized_summary.json）
# 若累计主动收益 < -5pp：λ 提高到 20；否则保持 λ=8
& $py portfolio.py build --week 4 --cutoff 2026-11-20 --strategy signal --lam 8
```

### 4.3 提交前 6 项检查

- [ ] `params.json` 的 `cutoff` = 本周五；
- [ ] `strategy` / `lam` / `k` 与预期一致；
- [ ] `capital_prev` = 上周实际剩余资本（第 2 周起不是 1,000,000）；
- [ ] `submission.xlsx` 的 Summary：`Sum of weights = 1`；
- [ ] 10 行，全部权重 ≥ 1%（我们不做空，没有负权重）；
- [ ] `Number of Shares × Price ≈ Capital Allocated`；
- [ ] Moodle 上传成功（截图/确认）。

### 4.4 目标周结束后

```powershell
& $py portfolio.py evaluate --week 2
```

生成 `weeks/week2/realized.csv`、`realized_summary.json`，并往 `ledger.md` 追加一行。

---

## 5. 方法路线图（报告的主线）

| 周 | 方法 | 回答的问题 | 关键参数 |
|---|---|---|---|
| 1 | **GMV** | 不考虑收益，风险最低的组合是什么？ | 104 周 Σ、30% 收缩、1–25% |
| 2 | **CAPM / SML** | 高 β 是否应该多配？ | β 用 HSI 回归、λ=15 |
| 3 | **复合信号** | 哪些股票相对更强/更弱？ | 12 周动量 + 近高点 + 低波、λ=8 |
| 4 | **自适应** | 前 3 周表现是否支持这个观点？ | 累计主动收益 < −5pp → 提高 λ |

报告里要讲清楚：**为什么从 GMV 开始**（GP1 证明周收益均值不可预测；GMV 只用 Σ），
以及**每一步加了多少观点、风险如何变化**。

---

## 6. 老师要求的 benchmark 对比（重点）

项目 PDF 明确要求：

> “Comparison between your proposed method and the benchmark methods (which I have covered in the class).”

老师 Lecture 2–4 讲过的 benchmark 是**六类**，不是随便找几个策略：

| # | Benchmark | 课程 | 我们的实现 |
|---|---|---|---|
| 1 | 等权 1/N | Lecture 2 | `EW` |
| 2 | GMV | Lecture 2/3 | `GMV_uncon`（公式） / `GMV_con`（纯多头） |
| 3 | 有效前沿 | Lecture 3 | `frontier_20261030.csv` / `frontier_points.csv` |
| 4 | 切点 / 最大 Sharpe | Lecture 3 | `Tangency_uncon_cap2` / `Tangency_con` |
| 5 | 两基金定理 | Lecture 3 | `two_fund_check.csv` |
| 6 | CAPM / SML / 市场组合 | Lecture 4 | `CAPM_con` / `Market_HSI` |

**详细公式、主对比表、有效前沿缺口、两基金检查、报告写法**都在：

```
BENCHMARKS_ZH.md
```

### 6.1 报告 comparison 小节的最低要求

1. **表 1**：主对比表（年化、波动、Sharpe、最大回撤、主动 vs EW）。
   - 数据文件：`research/benchmark_summary.csv`。
2. **表 2 / 图**：有效前沿 + 各方法的位置（效率缺口）。
   - 数据文件：`research/frontier_20261030.csv`、`frontier_points.csv`。
3. **一段解释**：GMV、CAPM、Tangency、EW 各自的表现和原因。
4. **一段限制**：in-sample、无交易成本、无借券成本、HSI 是熊市基准。

### 6.2 三个必须讲清楚的点

- **课程公式 vs 可实施版**：GMV 和 Tangency 的课程公式允许做空；我们组 long-only，所以同时报告 `_uncon` 和 `_con`。这不是“改公式”，而是“公式 + 约束”。
- **原始切点组合为什么会爆炸**：样本均值 + 近奇异协方差 → `Σ⁻¹μ̃` 权重极端（平均 gross 34.75、worst week −652%）。这是估计误差的经典证据，也是我们从 GMV 开始的原因。
- **两基金定理**：严格成立需要无约束；我们的检查是 long-only 近似。GMV_con/CAPM/Signal 的 L1 距离 0.05–0.17，EW 0.90，说明 proposed 接近两基金线，EW 远离。

---

## 7. 最终报告（5 页）结构与分工

### 7.1 建议结构

| 页 | 内容 | owner |
|---|---|---|
| 1 | Introduction + method evolution（GMV → CAPM → Signal → Adaptive） | 报告 owner |
| 2 | Data & methodology（raw/hfq、104 周、Σ、约束、优化器） | 数据 owner |
| 3 | Weekly performance（R_i、C_i、主动收益 vs EW、ledger） | 数据 owner |
| 4 | **Benchmark comparison**（主表 + 前沿 + 两基金） | 研究 owner |
| 5 | Evaluation（优缺点）、potential improvements、conclusion | 报告 owner |
| 附录 | 每周权重、参数、复现命令（不计页数） | 数据 owner |

### 7.2 分工建议

| 角色 | 职责 |
|---|---|
| **Data/Ops owner** | 每周五 `refresh-data`、`evaluate`；周六 `build`；核对 6 项；上传 Moodle；维护 `ledger.md` |
| **Research owner** | 跑 `research_benchmarks.py`、`research_backtest.py`；维护 `research/`；确保报告里的每个数字都能在 CSV 里找到 |
| **Report owner** | 写 5 页正文；统一术语；检查页数；把表/图编号 |
| **Presentation owner** | 10 分钟 slides；按“方法链 + 每周结果 + benchmark + 改进”组织；排练 |
| **Reviewer** | 独立复算 2–3 个数字；检查 Moodle 截止；检查引用/数据口径 |

### 7.3 报告里每个数字的出处

| 报告里的数字 | 文件 |
|---|---|
| 每周 R_i、C_i | `weeks/weekN/realized_summary.json`、`ledger.md` |
| 主 benchmark 表 | `research/benchmark_summary.csv` |
| 4 周分布 | `research/benchmark_4w_distribution.csv` |
| 有效前沿缺口 | `research/frontier_points.csv` |
| 两基金检查 | `research/two_fund_check.csv` |
| 各方法最终权重 | `research/benchmark_final_weights.csv` |
| 信号 IC | `research/scan_ic.csv` |
| 收缩敏感性 | `research/shrinkage_sensitivity.csv` |

**规则**：报告里不允许出现“找不到出处”的数字。每个表下面写一句 “Source: research/xxx.csv”。

---

## 8. 展示（10 分钟）建议

| 时间 | 内容 |
|---|---|
| 0–2 min | GP1 一句话结论（周收益难预测，简单基准很难战胜）+ GP2 目标 |
| 2–5 min | 方法链：GMV → CAPM → Signal → Adaptive；每步一句“为什么” |
| 5–7 min | 每周实际收益、主动收益 vs EW、最好/最差股票 |
| 7–9 min | Benchmark comparison：主表 + 有效前沿 + 两基金（只讲结论，不念表） |
| 9–10 min | 优缺点、改进、分工 |

展示重点：

- 不要念公式；讲“为什么这样做”；
- 用一张图/一张表说明“proposed 离前沿 0.2pp，EW 离前沿 7.4pp”；
- 诚实讲 CAPM 没有显著改善、Tangency 原始版本不可实施——这比“我们模型最好”更加分。

---

## 9. 预注册与只增不改

### 9.1 预注册

每周提交前，把以下内容写进 `weeks/weekN/params.json`（`build` 会自动写大部分）：

- cutoff、strategy、λ / k、rf、premium；
- `capital_prev`；
- 权重、gross、空头数；
- 如果是自适应周，写 `rule` / `k_override_reason`。

**提交后不再改**。如果发现错误，新建 `_variant` + `amendment_YYYYMMDD.md`，说明“什么时候、为什么、改了什么”，旧文件保留。

### 9.2 台账

`ledger.md` 只追加，不改旧行。每周一行：

```
| Week | Cutoff | Week end | C start | C end | R | EW R | Active | Hit | Best | Worst |
```

---

## 10. 常见坑（按出现频率排序）

1. **截点错周**：第 2 周必须用 11/6，不是 10/30。`build` 会检查“截点前最后一个周五”，超过 7 天报错。
2. **用复权价算股数**：差几倍。记住“信号 hfq，股数 raw”。
3. **忘记用上周剩余资本**：第 2 周起 `C_{i-1}` 不是 1,000,000。`build` 会自动读上一周 `portfolio.csv`。
4. **权重和不为 1**：脚本会归一化；提交前仍要检查 Summary。
5. **Moodle 没传成功**：GP1 Week 4 的教训；提交后截图/确认。
6. **改旧文件**：快照只增不改；要改就新建 `_variant`。
7. **把 `k` 当杠杆**：`k` 只放大主动偏离，权重和始终为 1；不做空时它主要提高集中度。
8. **把 λ 当观点强度**：λ 越大越保守；观点强度也可以用目标波动表达，报告里固定一种说法。
9. **HSI 当可提交组合**：HSI 不是 10 只股票的组合，只是市场 benchmark。
10. **报告数字没有出处**：每个数字都要能指到 CSV/JSON。

---

## 11. 给同学 AI 的 Prompt（可以直接复制）

> 你在协助完成 DASE7310 Group Project 2。请先按顺序阅读仓库里的：
> `README.md`、`GUIDE_ZH.md`、`WEEK2_GUIDANCE_ZH.md`、`WEEK3_GUIDANCE_ZH.md`、`BENCHMARKS_ZH.md`。
>
> 然后遵守以下规则：
>
> 1. 工作目录：`D:\Backup\Documents\dase7310\DASE7310_GP2_Repo`；Python：`C:\Users\Administrator\miniforge3\envs\dase7310\python.exe`；运行前设置 `$env:MKL_THREADING_LAYER='SEQUENTIAL'`。
> 2. 每周流程：`refresh-data --end <cutoff>` → `evaluate --week <prev>` → `build --week <N> --cutoff <cutoff> --strategy <...>` → 核对 → 提交。
> 3. 绝不用复权价算股数；股数公式 `h = c / p`，`p` 用 `data/weekly_closes_raw.csv`（或 `prices_asof` 返回的 raw 价）。
> 4. 第二周起 `C_{i-1}` 必须来自上一周 `portfolio.csv` 的实际股数 × 新截点价；不要假设还是 1,000,000。
> 5. 不做空；所有权重 ≥ 1%，和 = 1，10 只都持有。
> 6. 不覆盖 `weeks/weekN/` 里已提交的文件；要改就新建 `_variant` 并在 `params.json` 写原因。
> 7. 所有数字必须来自 `portfolio.py` / `research_*.py` 的输出 CSV/JSON；不要自己编。
> 8. 报告 comparison 必须覆盖 `BENCHMARKS_ZH.md` 里的六类课程 benchmark（1/N、GMV、有效前沿、切点、两基金、CAPM/市场组合）。
> 9. 如果命令失败，先读报错和 `data/meta.json`，不要猜；不要用旧数据提交。
> 10. 每次提交前输出一份 6 项检查清单的结果（cutoff、capital_prev、sum weights、10 行、股数×价格、Moodle 上传）。
>
> 当前任务：<例如：生成 Week 2 的 CAPM 组合，cutoff 2026-11-06，λ=15，并核对提交表>。

---

## 12. 文件索引

| 文件 | 用途 |
|---|---|
| `README.md` | 英文完整说明（规则、数据、流程、方法） |
| `GUIDE_ZH.md` | 第 1 周中文行动指南 |
| `WEEK2_GUIDANCE_ZH.md` | 第 2 周 CAPM 操作指南 |
| `WEEK3_GUIDANCE_ZH.md` | 第 3 周信号操作指南 |
| `BENCHMARKS_ZH.md` | 课程 benchmark 对照（六类 + 主表 + 前沿 + 两基金） |
| `GMV_EXPLAINED_ZH.md` | 协方差矩阵 + GMV 原理 |
| `VIEWS_EXPLAINED_ZH.md` | 如何表达观点（CAPM/信号/自适应） |
| `WEEK1_REPORT_EN.md` | 第 1 周英文报告（内部版） |
| `portfolio.py` | 主脚本 |
| `research_benchmarks.py` | 课程 benchmark 对比 |
| `research_backtest.py` | 策略回测 |
| `research_views.py` | 观点强度/权重路径 |
| `research_gmv.py` | 协方差 + GMV 复现 |
| `research_scan.py` | 信号 IC / 相关性 |
| `weeks/weekN/` | 每周提交快照 |
| `research/` | 所有研究 CSV |
| `ledger.md` | 周度实际收益台账 |
