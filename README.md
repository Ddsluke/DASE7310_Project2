# DASE7310 Group Project 2 — 投资组合构建与周度再平衡

**Portfolio Construction & Weekly Rebalancing**

> 仓库 / Repo: [Ddsluke/DASE7310_Project2](https://github.com/Ddsluke/DASE7310_Project2)
> 数据截至 / Data through: **2026-10-30**
> 第一周提交 / Week 1 submission: **2026-11-01**
> 当前状态 / Status: Week 1 GMV snapshot ready; Week 2/3/4 pipeline ready.

**快速链接 / Quick links**:
[第 1 周提交](weeks/week1/submission.xlsx) ·
[队友执行手册](TEAM_GUIDANCE_ZH.md) ·
[数据更新指南](DATA_ZH.md) ·
[课程 benchmark](BENCHMARKS_ZH.md) ·
[第 2 周指南](WEEK2_GUIDANCE_ZH.md) ·
[第 3 周指南](WEEK3_GUIDANCE_ZH.md) ·
[英文 README](README_EN.md)

---

## 目录 / Contents

- [一句话 / At a glance](#user-content-0-一句话--at-a-glance)
- [快速开始 / Quick start](#user-content-1-快速开始--quick-start)
- [仓库文件导引 / Repository map](#user-content-2-仓库文件导引--repository-map)
- [计划 / Plan](#user-content-3-计划--plan双语)
- [每周思路 / Weekly methodology](#user-content-4-每周思路--weekly-methodology双语)
- [结果位置 / Where to find results](#user-content-5-结果位置--where-to-find-results双语)
- [数据 / Data](#user-content-6-数据--data双语)
- [课程 benchmark 速查](#user-content-7-课程-benchmark-速查--course-benchmark-quick-reference)
- [提交前检查清单](#user-content-8-提交前检查清单--pre-submission-checklist)
- [常见坑 / Common pitfalls](#user-content-9-常见坑--common-pitfalls)
- [环境 / Environment](#user-content-10-环境--environment)
- [文档阅读顺序 / Reading order](#user-content-11-文档阅读顺序--reading-order)

---

## 0. 一句话 / At a glance

**中文**：用 GP1 的 10 只港股，在 HKD 1,000,000、满仓、纯多头的约束下，做 4 周的组合构建与周度再平衡；方法从“无观点”的 GMV 出发，逐步加入 CAPM 市场观点、信号选股观点，最后按实际表现调整观点置信度。

**English**: Build and rebalance a HKD 1,000,000 long-only portfolio of the same ten HKEX stocks over four weeks. The method starts from the no-view GMV portfolio, then adds a CAPM market view, a characteristic-based stock view, and finally a pre-registered adaptive confidence rule.

---

## 1. 快速开始 / Quick start

```powershell
$env:MKL_THREADING_LAYER = 'SEQUENTIAL'
$py = 'C:\Users\Administrator\miniforge3\envs\dase7310\python.exe'
cd D:\Backup\Documents\dase7310\DASE7310_GP2_Repo

# 拉数据 / refresh raw + hfq prices and HSI/HSTECH
& $py portfolio.py refresh-data --end 2026-11-06

# 生成下一周组合 / build next week's portfolio
& $py portfolio.py build --week 2 --cutoff 2026-11-06 --strategy capm --lam 15

# 目标周结束后记录实际收益 / record realised results (append-only)
& $py portfolio.py evaluate --week 1
```

---

## 2. 仓库文件导引 / Repository map

| 文件 / File | 中文说明 / Chinese | English |
|---|---|---|
| [`README.md`](README.md) | 本文件：中文文件导引 + 双语计划 | This file: Chinese guide + bilingual plan |
| [`README_EN.md`](README_EN.md) | 完整英文技术说明 | Full English technical README |
| [`TEAM_GUIDANCE_ZH.md`](TEAM_GUIDANCE_ZH.md) | **队友执行手册**：规则、流程、分工、AI prompt | Team playbook: rules, workflow, roles, AI prompt |
| [`GUIDE_ZH.md`](GUIDE_ZH.md) | 第 1 周中文行动指南 | Week 1 action guide (Chinese) |
| [`WEEK2_GUIDANCE_ZH.md`](WEEK2_GUIDANCE_ZH.md) | 第 2 周 CAPM 操作指南 | Week 2 CAPM guide |
| [`WEEK3_GUIDANCE_ZH.md`](WEEK3_GUIDANCE_ZH.md) | 第 3 周信号操作指南 | Week 3 signal guide |
| [`BENCHMARKS_ZH.md`](BENCHMARKS_ZH.md) | **课程六类 benchmark 对照**（老师要求） | Course benchmark mapping and comparison |
| [`GMV_EXPLAINED_ZH.md`](GMV_EXPLAINED_ZH.md) | 协方差矩阵 + GMV 原理 | Covariance matrix and GMV explainer |
| [`VIEWS_EXPLAINED_ZH.md`](VIEWS_EXPLAINED_ZH.md) | 如何表达观点（CAPM/信号/自适应） | How to express views in Weeks 2–4 |
| [`DATA_ZH.md`](DATA_ZH.md) | **数据口径与更新指南**（raw/hfq/无 qfq） | Data conventions and refresh guide |
| [`WEEK1_REPORT_EN.md`](WEEK1_REPORT_EN.md) | 第 1 周英文报告（内部版，非最终提交） | Week 1 English report (internal draft) |
| [`portfolio.py`](portfolio.py) | 主脚本：`refresh-data / build / evaluate` | Main pipeline |
| [`research_benchmarks.py`](research_benchmarks.py) | 课程 benchmark 对比 + 有效前沿 + 两基金 | Course benchmarks, frontier, two-fund check |
| [`research_backtest.py`](research_backtest.py) | 策略 walk-forward 回测 | Strategy backtest |
| [`research_views.py`](research_views.py) | 无观点 → 有观点的权重路径 | View intensity path |
| [`research_gmv.py`](research_gmv.py) | 协方差 + GMV 复现 | Covariance and GMV reproduction |
| [`research_scan.py`](research_scan.py) | 信号 IC / 相关性扫描 | Signal IC and correlation scan |
| [`research_portfolios.py`](research_portfolios.py) | 组合方案比较 | Portfolio comparison |
| [`requirements.txt`](requirements.txt) | Python 依赖 | Python dependencies |
| [`data/`](data/) | 原始/后复权价格、周收益、指数、meta | Raw/hfq prices, returns, indices, metadata |
| [`weeks/`](weeks/) | 每周提交快照与实际结果 | Weekly submission snapshots and realised results |
| [`research/`](research/) | 所有研究 CSV 输出 | All research CSV outputs |
| [`ledger.md`](ledger.md) | 周度实际收益台账（append-only） | Weekly realised-return ledger |

---

## 3. 计划 / Plan（双语）

| 周 / Week | 估值截点 / Cutoff | 提交截止 / Submit by | 方法 / Method | 输出 / Output |
|---|---|---|---|---|
| **1** | 2026-10-30 | 2026-11-01 | **GMV**：只用协方差，纯多头 1%–25% / risk-only global minimum variance | [week1/submission.xlsx](weeks/week1/submission.xlsx) |
| **2** | 2026-11-06 | 2026-11-08 | **CAPM / SML + short**：`μ_s = r_f + β_s × premium`，λ=15，floor −15% / cap 30% / market view | [weeks/](weeks/)（`build --week 2` 生成） |
| **3** | 2026-11-13 | 2026-11-15 | **Signal + short**：12 周动量 + 距 52 周高点 + 低波动，λ=8，floor −15% / cap 30% / relative stock view | [weeks/](weeks/)（`build --week 3` 生成） |
| **4** | 2026-11-20 | 2026-11-22 | **Adaptive + short**：按前 3 周累计主动收益调整 λ / confidence update | [weeks/](weeks/)（`build --week 4` 生成） |
| — | — | **2026-11-30** | 5 页报告 + 互评 / 5-page report + peer evaluation | 最终报告 / final report（待写 / to be written） |
| — | — | **2026-11-23 / 30** | 10 分钟展示，覆盖 GP1 + GP2 / 10-min presentation | slides（待写 / to be written） |

**规则 / Rules**：HKD 1,000,000；`Σw = 1`；10 只股票；周内 buy-and-hold；全程最多 3 次调整（第 2/3/4 周各一次）。**做空**：官方明确允许；Week 1 已提交 long-only；Week 2 起使用 `--floor -0.15 --cap 0.30`。

> **1% 下限 / 1% floor**：`GMV_con` 的 9988、1810、0700 三只正好在 1% 下限；不设下限时优化器会把它们设为 0。1% 下限保证 10 只都持有，代价是样本波动 8.53%→8.77%、样本均值 15.78%→15.36%。这是**实现约束**，不是理论 GMV；完整敏感性表见 [WEEK1_REPORT_EN.md](WEEK1_REPORT_EN.md) §3.4。
>
> **官方口径 / Official interpretation**：全部资本必须投到 10 只股票（**no cash / 空仓**）；`Σw = 1` 由 “fully allocated” + `w = c/C` + `C = Σph` 隐含；单只零权重未被明确禁止，1% 下限是我们避免歧义的保守做法；做空官方明确允许（p.1：“short positions are permitted”）；Week 1 已提交 long-only，Week 2 起使用 `--floor -0.15 --cap 0.30`。逐条原文见 [TEAM_GUIDANCE_ZH.md](TEAM_GUIDANCE_ZH.md) §1.3。

**English**: HKD 1,000,000 fully invested in ten stocks; buy-and-hold within each week; at most three rebalancing adjustments (before Weeks 2, 3 and 4). Week 1 is long-only; from Week 2 the group uses the project's short-selling permission with a −15% per-name short cap and a +30% long cap.

---

## 4. 每周思路 / Weekly methodology（双语）

### Week 1 — GMV（无观点 / no view）

**中文**：只用协方差矩阵 `Σ`，不估期望收益 `μ`。解 `min w'Σw s.t. Σw = 1, 0.01 ≤ w ≤ 0.25`。这是有效前沿的**最左端点**，也是唯一不需要 μ 的前沿点。104 周协方差、30% 收缩、SLSQP 求解。

**English**: Use only the covariance matrix; no expected returns. Solve the long-only global minimum-variance problem with 1%–25% caps. GMV is the left endpoint of the efficient frontier and the only frontier point that does not require a `μ` forecast.

**为什么 / Why**：GP1 证明周收益均值几乎不可预测；GMV 避开最难的输入，先建立风险基准。 / GP1 showed weekly mean returns are nearly unpredictable; GMV avoids the noisiest input and establishes a risk benchmark.

### Week 2 — CAPM / SML（市场观点 / market view）

**中文**：`μ_s = r_f + β_s × (μ_M − r_f)`，β 用 HSI 回归；λ=15，floor −15%、cap 30%，开始使用小空头。预期波动约 8.2%（样本协方差口径），gross 约 1.07。

**English**: Use the CAPM/SML expected return with HSI as the market proxy; λ=15 with a −15% short cap and a +30% long cap. Expected volatility ≈ 8.2% (sample covariance), gross ≈ 1.07. This is the first week with short positions.

**注意 / Note**：把 μ 往横截面总均值收缩只是加一个常数，不改变权重；真正的观点是 β 的横截面差异。 / Shrinking all means toward the grand mean is just adding a constant and does not change weights; the view is the cross-sectional difference in beta.

### Week 3 — Signal（相对选股观点 / relative stock view）

**中文**：复合 z 分数 = 12 周动量 + 距 52 周高点 + 低波动；`μ_s = κ × z_s`，κ=2%/年；λ=8，floor −15%、cap 30%。继续使用小空头（9988/1810/0700 等弱科技）。信号在样本内每年 IC 为正，比原始样本均值稳。

**English**: Build a composite z-score from 12-week momentum, proximity to the 52-week high, and low volatility; use `μ_s = κ z_s` (κ = 2% p.a. per z) with λ=8, a −15% short cap and a +30% long cap. The short book expresses negative views on the weakest names. The signal has a positive rank IC in every year of the sample and is more stable than raw sample means.

### Week 4 — Adaptive（调整观点置信度 / confidence update）

**中文**：不换模型。按前 3 周累计主动收益（组合 − 等权）调整观点强度：< −5pp 时提高 λ 到 20、把 floor 从 −15% 收到 −10%（缩小空头），回到 GMV；> +5pp 时维持但不加杠杆。规则提前写进 `params.json`，事后不改。

**English**: Do not switch models. Adjust the strength of the view based on the first three weeks' cumulative active return vs equal weight: if below −5pp, raise λ to 20 and tighten the short cap from −15% to −10% toward GMV; if above +5pp, keep the view without adding leverage. Pre-register the rule in `params.json`.

---

## 5. 结果位置 / Where to find results（双语）

### 5.1 每周提交与结果 / Weekly submissions and realised results

| 内容 / Item | 位置 / Location |
|---|---|
| Moodle 提交表 / Moodle submission | [weeks/week1/submission.xlsx](weeks/week1/submission.xlsx)（Week 1 示例；Week N 为 `weeks/weekN/submission.xlsx`） |
| 同内容 CSV / same table as CSV | [weeks/week1/submission.csv](weeks/week1/submission.csv) |
| 完整内部表（价格、权重、资本、股数）/ full table | [weeks/week1/portfolio.csv](weeks/week1/portfolio.csv) |
| 参数、截点、方法、权重 / parameters | [weeks/week1/params.json](weeks/week1/params.json) |
| 人类可读快照 / human-readable snapshot | [weeks/week1/report.md](weeks/week1/report.md) |
| 目标周实际结果 / realised results | `weeks/weekN/realized.csv`、`realized_summary.json`（目标周结束后生成） |
| 周度台账 / weekly ledger | [ledger.md](ledger.md)（append-only） |

### 5.2 课程 benchmark 与研究 / Course benchmarks and research

| 内容 / Item | 位置 / Location |
|---|---|
| 课程 benchmark 主表 / main benchmark table | [research/benchmark_summary.csv](research/benchmark_summary.csv) |
| 4 周收益分布 / 4-week distribution | [research/benchmark_4w_distribution.csv](research/benchmark_4w_distribution.csv) |
| 各方法最终权重 / final weights | [research/benchmark_final_weights.csv](research/benchmark_final_weights.csv) |
| 有效前沿 / efficient frontier | [research/frontier_20261030.csv](research/frontier_20261030.csv) |
| 各方法离前沿的缺口 / frontier gaps | [research/frontier_points.csv](research/frontier_points.csv) |
| 两基金定理检查 / two-fund check | [research/two_fund_check.csv](research/two_fund_check.csv) |
| 做空 vs 纯多头回测 / short vs long-only backtest | [research/short_backtest_weekly.csv](research/short_backtest_weekly.csv) |
| 原始切点组合诊断 / raw tangency diagnostic | [research/benchmark_diagnostics.csv](research/benchmark_diagnostics.csv) |
| 策略回测 / strategy backtest | [research/backtest_summary.csv](research/backtest_summary.csv) |
| 信号 IC / signal IC | [research/scan_ic.csv](research/scan_ic.csv) |
| 协方差 / covariance | [research/covariance_104w.csv](research/covariance_104w.csv) |
| 相关系数 / correlation | [research/correlation_104w.csv](research/correlation_104w.csv) |
| GMV 权重与风险贡献 / GMV weights & risk contributions | [research/gmv_weights.csv](research/gmv_weights.csv) |
| 收缩敏感性 / shrinkage sensitivity | [research/shrinkage_sensitivity.csv](research/shrinkage_sensitivity.csv) |
| 观点强度路径 / view intensity path | [research/views_frontier.csv](research/views_frontier.csv) |

### 5.3 报告与展示 / Report and presentation

| 内容 / Item | 位置 / Location |
|---|---|
| 第 1 周英文报告（内部版）/ Week 1 report draft | [WEEK1_REPORT_EN.md](WEEK1_REPORT_EN.md) |
| 课程 benchmark 报告写法 / report-ready benchmark text | [BENCHMARKS_ZH.md](BENCHMARKS_ZH.md) |
| 最终 5 页报告 / final 5-page report | **待写 / to be written**（建议基于 [WEEK1_REPORT_EN.md](WEEK1_REPORT_EN.md) + [BENCHMARKS_ZH.md](BENCHMARKS_ZH.md)） |
| 展示 slides / presentation | **待写 / to be written**（建议按 [TEAM_GUIDANCE_ZH.md](TEAM_GUIDANCE_ZH.md) 第 8 节） |

> **规则 / Rule**：报告里每个数字都必须能指到上面的 CSV/JSON；表下面写 `Source: research/xxx.csv`。

---

## 6. 数据 / Data（双语）

### 6.1 数据文件 / Data files

| 文件 / File | 中文说明 / Chinese | English |
|---|---|---|
| [`data/weekly_closes_raw.csv`](data/weekly_closes_raw.csv) | **未复权**周收盘价，用于算股数和资本 | **Raw** weekly closes; used for shares and capital |
| [`data/weekly_closes_hfq.csv`](data/weekly_closes_hfq.csv) | **后复权**周收盘价，用于算信号/协方差 | **hfq** weekly closes; used for signals and covariance |
| [`data/weekly_returns_raw.csv`](data/weekly_returns_raw.csv) | 未复权周收益 | Raw weekly returns |
| [`data/weekly_returns_hfq.csv`](data/weekly_returns_hfq.csv) | 后复权周收益 | hfq weekly returns |
| [`data/daily_closes_raw.csv`](data/daily_closes_raw.csv) | 未复权日线 | Raw daily closes |
| [`data/daily_closes_hfq.csv`](data/daily_closes_hfq.csv) | 后复权日线 | hfq daily closes |
| [`data/index_closes.csv`](data/index_closes.csv) | HSI / HSTECH 周收盘 | HSI / HSTECH weekly closes |
| [`data/index_returns.csv`](data/index_returns.csv) | HSI / HSTECH 周收益 | HSI / HSTECH weekly returns |
| [`data/meta.json`](data/meta.json) | 数据源、刷新时间、最后日期 | Source, refresh time, last available date |

### 6.2 口径 / Conventions

**中文**：

- 数据源：新浪财经（AkShare），后复权/未复权两套；本网络下东方财富常被拒，脚本整批切新浪。
- 周价格：每周 **W-FRI** 最后一根已实现收盘价。
- 算股数：`h = c / p`，`p` 用**未复权真实收盘价**；保留 6 位小数，不按每手取整。
- 算信号/协方差：用**后复权**总收益；104 周窗口、30% 收缩。
- 初始资本 `C_0 = 1,000,000`；第二周起 `C_{i-1}` 是上一周实际剩余资本。
- 组合约束：`Σw = 1`、10 只都持有；Week 1 单票 1%–25%、不做空；Week 2 起单票 −15%–30%、允许做空。

**English**:

- Source: Sina Finance via AkShare; both raw and hfq series. Eastmoney is often blocked on this network, so the pipeline falls back batch-wise.
- Weekly price: last realised close of each **W-FRI** week.
- Shares: `h = c / p` using **raw** closes; 6 decimals, no board-lot rounding.
- Signals/covariance: **hfq** total returns; 104-week window, 30% shrinkage.
- Initial capital `C_0 = 1,000,000`; from Week 2, `C_{i-1}` is the actual remaining capital.
- Constraints: `Σw = 1`, all ten stocks held, 1%–25% per name, long-only.

**更新数据 / Refresh**: 每周五收盘后运行 `refresh-data --end 本周五`；完整步骤、验证清单和常见问题见 [DATA_ZH.md](DATA_ZH.md)。

### 6.3 股票池 / Universe

`9988 阿里巴巴 / Alibaba`, `0066 港铁 / MTR`, `1398 工行 / ICBC`, `3988 中行 / BOC`,
`0981 中芯 / SMIC`, `0005 汇丰 / HSBC`, `1810 小米 / Xiaomi`, `0016 新鸿基 / SHK Properties`,
`1113 长实 / CK Asset`, `0700 腾讯 / Tencent`.

---

## 7. 课程 benchmark 速查 / Course benchmark quick reference

项目 PDF 要求对比“老师课上讲过的 benchmark methods”。Lecture 2–4 的六类是：

| # | Benchmark | 课程 / Lecture | 我们的文件 / Our file |
|---|---|---|---|
| 1 | 等权 1/N / equal weight | Lecture 2 | [`EW`](research/benchmark_summary.csv) in `benchmark_summary.csv` |
| 2 | GMV | Lecture 2/3 | [`GMV_uncon` / `GMV_con`](research/benchmark_final_weights.csv) |
| 3 | 有效前沿 / efficient frontier | Lecture 3 | [frontier_20261030.csv](research/frontier_20261030.csv)、[frontier_points.csv](research/frontier_points.csv) |
| 4 | 切点 / max Sharpe | Lecture 3 | [`Tangency_uncon_cap2` / `Tangency_con`](research/benchmark_final_weights.csv) |
| 5 | 两基金定理 / two-fund theorem | Lecture 3 | [two_fund_check.csv](research/two_fund_check.csv) |
| 6 | CAPM / SML / 市场组合 | Lecture 4 | [`CAPM_con` / `Market_HSI`](research/benchmark_summary.csv) |

**完整公式、主表、报告写法**：[BENCHMARKS_ZH.md](BENCHMARKS_ZH.md)（中文）。
**Full formulas, tables and report-ready English**: [README_EN.md](README_EN.md) Section 6.

> **Lecture 5–7 不是 GP2 benchmark**：它们是衍生品/固定收益（对冲、利率、期货、期权），主要服务 final exam 和 presentation。详见 [BENCHMARKS_ZH.md 第 8 节](BENCHMARKS_ZH.md#user-content-8-lecture-57-与-gp2-的关系已逐页检查)。

---

## 8. 提交前检查清单 / Pre-submission checklist

- [ ] `params.json` 的 `cutoff` = 本周五 / cutoff is the correct Friday;
- [ ] `capital_prev` = 上周实际剩余资本 / previous week's actual remaining capital;
- [ ] 10 行，`Σw = 1`；Week 1：无负权重、单票 ≥ 1%；Week 2 起：空头 ≥ −15%、多头 ≤ 30% / ten rows, sum to 1; Week 1 no shorts, each ≥ 1%; Week 2+ short ≥ −15%, long ≤ 30%;
- [ ] `股数 × 价格 ≈ 资本` / `shares × price ≈ capital`;
- [ ] Excel 与 CSV 数字一致 / Excel and CSV agree;
- [ ] Moodle 上传成功 / Moodle upload confirmed;
- [ ] [ledger.md](ledger.md) 已记录上一周实际结果 / previous week's realised result is in the ledger.

---

## 9. 常见坑 / Common pitfalls

1. **截点错周 / wrong cutoff**：第 2 周用 11/6，不是 10/30。
2. **用复权价算股数 / adjusted prices for shares**：会差几倍；记住“信号 hfq，股数 raw”。
3. **忘记用上周剩余资本 / ignoring `C_{i-1}`**：第 2 周起不是 1,000,000。
4. **权重和不为 1 / weights don't sum to 1**：提交前看 Summary。
5. **Moodle 没传成功 / upload not confirmed**：GP1 Week 4 的教训。
6. **改旧快照 / editing old snapshots**：只增不改；要改就新建 `_variant` + 修订说明。
7. **把 `k` 当杠杆 / treating `k` as leverage**：`k` 只放大主动偏离，权重和始终为 1。
8. **把 HSI 当可提交组合 / treating HSI as investable**：HSI 只是市场 benchmark，不是 10 只股票的组合。

---

## 10. 环境 / Environment

```powershell
$env:MKL_THREADING_LAYER = 'SEQUENTIAL'
$py = 'C:\Users\Administrator\miniforge3\envs\dase7310\python.exe'
```

Python 3.12、pandas 3.0、numpy 2.5、scipy 1.18、akshare 1.19、scikit-learn 1.9、openpyxl。
完整依赖见 [requirements.txt](requirements.txt)；环境锁定见 [README_EN.md](README_EN.md) 第 8 节。

---

## 11. 文档阅读顺序 / Reading order

1. **[README.md](README.md)**（本文件）— 5 分钟了解仓库和计划。
2. **[TEAM_GUIDANCE_ZH.md](TEAM_GUIDANCE_ZH.md)** — 要执行第 2/3/4 周的人必读；含 AI prompt。
3. **[WEEK2_GUIDANCE_ZH.md](WEEK2_GUIDANCE_ZH.md)** / **[WEEK3_GUIDANCE_ZH.md](WEEK3_GUIDANCE_ZH.md)** — 当周具体操作。
4. **[BENCHMARKS_ZH.md](BENCHMARKS_ZH.md)** — 写报告 comparison 小节必读。
5. **[GMV_EXPLAINED_ZH.md](GMV_EXPLAINED_ZH.md)** / **[VIEWS_EXPLAINED_ZH.md](VIEWS_EXPLAINED_ZH.md)** — 想理解原理时读。
6. **[README_EN.md](README_EN.md)** — 需要完整英文技术说明时读。
