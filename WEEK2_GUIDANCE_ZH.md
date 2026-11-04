# Week 2 行动指南：CAPM 市场观点 + 做空

> **截止**：2026-11-08（周日）23:59
> **估值截点**：2026-11-06（周五）收盘
> **交易周**：2026-11-09 → 2026-11-13
> **本周目标**：从 Week 1 的 long-only GMV，沿有效前沿往上走一小步，加入 CAPM 市场观点；**从本周起使用官方允许的做空**（short cap −15%）。
>
> **报告关联**：本周的 CAPM 组合是最终报告 benchmark comparison 的一部分（Lecture 4 的 CAPM/SML 基准）。完整的六类课程 benchmark 对照见 `BENCHMARKS_ZH.md`。

---

## 1. 本周时间线

| 时间 | 动作 |
|---|---|
| 11/6（周五）收盘后 | `refresh-data --end 2026-11-06`；`evaluate --week 1` 记录第一周实际收益 |
| 11/7（周六） | `build --week 2 --strategy capm --lam 15 --floor -0.15 --cap 0.30`；生成并核对提交表 |
| 11/8（周日）23:59 | 上传 `weeks/week2/submission.xlsx` 到 Moodle |
| 11/13（下周五）收盘后 | `evaluate --week 2`，记录第二周实际收益 |

> **不要用 11/2–11/4 的涨跌回填 Week 1**；Week 2 的最终权重必须用 **11/6 截点**的数据重算。11/2–11/4 只能用于事前研究/预案，不能替代 11/6 的 build。

---

## 2. 本周方法：CAPM 观点 + 小空头

### 2.1 公式

课程 Lecture 4 的 CAPM / SML：

```
μ_s = r_f + β_s × (μ_market − r_f)
```

- `β_s`：股票 s 对 HSI 的敏感度，用最近 **104 周**周收益回归估计；
- `r_f`：无风险利率，取 **2%/年**；
- `μ_market − r_f`：市场风险溢价，取 **5%/年**；
- 因为组合约束是 `Σw = 1`，给所有 μ 加同一个常数不改变权重，**真正起作用的是 β 的横截面差异**。

### 2.2 优化问题（含做空）

```
max_w   μ'w − (λ/2) w'Σw
s.t.    Σ_s w_s = 1
        −0.15 ≤ w_s ≤ 0.30
```

- Σ：104 周协方差，30% 收缩（和 Week 1 相同）；
- λ = **15**：保守设置，让组合只从 GMV 往上走一小步；
- **允许做空**：单只最低 −15%，最高 +30%；
- 10 只股票都出现在表里；负权重表示空头（负资本、负股数）；
- 预期 gross ≈ 1.05–1.15，不是高杠杆。

### 2.3 为什么从 Week 2 开始做空

官方 PDF 第 1 页明确写：

> “This entire amount must be fully allocated across the 10 selected stocks; **short positions are permitted**.”

我们组的做法：

- Week 1 已经按 long-only GMV 提交，**不改权重**；
- Week 2 起使用做空许可，但只开**小空头**（单只 ≤15%）；
- 空头主要用于表达“相对弱”的股票（如 9988/1810），不是加杠杆。

> **诚实提示**：2021–2026 回测里，short-enabled 版本的 Sharpe 低于 long-only 版本（Signal 0.73 vs 0.81；CAPM 0.64 vs 0.72；GMV 0.65 vs 0.78），因为被做空的高波动科技股在 2024–26 反弹。我们仍然使用做空，是因为项目明确允许、且它能表达负向观点；但 short book 保持很小（≤15%），并在报告里如实写“shorting did not improve the backtest Sharpe”。

### 2.4 为什么用 CAPM，而不是样本均值

| 做法 | 问题 |
|---|---|
| 样本均值 | 中芯 0981 的 104 周平均年化收益约 41%，优化器会给它 25%；但它最近 4 周跌了 32%、年化波动 56.6%。这是典型的估计误差。 |
| CAPM | 只用 β 一个横截面维度，参数少、可解释，是课程 Lecture 4 的均衡模型。 |
| 信号（Week 3） | 用动量/近高点/低波动，数据驱动，稳定性更好。 |

Week 2 用 CAPM 的目的不是“跑赢”，而是**在报告里展示从“无观点”到“有观点”的第一步**：

> GMV（只用 Σ）→ CAPM（加入市场观点 μ）→ Signal（加入相对选股观点）→ Adaptive（调整观点置信度）。

### 2.5 为什么 λ = 15

- λ 越大越保守，越接近 GMV；
- λ = 15 + short cap −15% 时，组合的预期年化波动约 **8.2%**（样本协方差口径），和 Week 1 的 GMV（8.8%）接近；
- 这样既表达了“高 β 应该多配”的观点，又不会把组合变成高 β 科技赌注。

如果 `build` 出来的组合年化波动 > 10.5%，把 λ 提高到 20；如果 gross > 1.3，检查是否空头过大。

---

## 3. 操作步骤（复制即可）

```powershell
$env:MKL_THREADING_LAYER = 'SEQUENTIAL'
$py = 'C:\Users\Administrator\miniforge3\envs\dase7310\python.exe'
cd D:\Backup\Documents\dase7310\DASE7310_GP2_Repo

# 1) 11/6 收盘后：刷新数据（raw + hfq + HSI）
& $py portfolio.py refresh-data --end 2026-11-06

# 2) 记录 Week 1 实际收益（会写 ledger.md）
& $py portfolio.py evaluate --week 1

# 3) 生成 Week 2 组合（CAPM + short，λ=15，floor=-15%，cap=30%）
& $py portfolio.py build --week 2 --cutoff 2026-11-06 --strategy capm --lam 15 --floor -0.15 --cap 0.30

# 4) 参考组合（不提交，只用于对比）
& $py portfolio.py build --week 2 --cutoff 2026-11-06 --strategy gmv --floor -0.15 --cap 0.30 --variant ref_gmv_short

# 5) 提交前核对
Get-Content weeks\week2\params.json
```

提交文件：

- **Moodle**：`weeks\week2\submission.xlsx`
- 同内容 CSV：`weeks\week2\submission.csv`
- 参数/β/权重：`weeks\week2\params.json`
- GMV short 参考：`weeks\week2\portfolio_ref_gmv_short.csv`

---

## 4. 预期权重（用 10/30 数据的预览，不是最终值）

下面是**假设截点仍是 10/30** 时 CAPM λ=15、floor=−15%、cap=30% 的权重，用于理解方向；11/6 实际数据出来后，权重会变，以 `submission.xlsx` 为准。

| 代码 | 名称 | 预览权重 |
|---|---|---:|
| 0066 | 港铁 | +30.0% |
| 3988 | 中行 | +27.8% |
| 1398 | 工行 | +16.0% |
| 0005 | 汇丰 | +9.6% |
| 1113 | 长实 | +6.0% |
| 0016 | 新鸿基 | +5.7% |
| 0700 | 腾讯 | +5.3% |
| 0981 | 中芯 | +3.1% |
| 1810 | 小米 | **−0.8%** |
| 9988 | 阿里 | **−2.6%** |
| **合计** | | **100%**（gross 1.07，2 个空头） |

和 Week 1 long-only GMV 相比：

- 0066 从 25% 升到 30%，3988 从 25% 升到 27.8%；
- 1398 从 21.2% 降到 16.0%，0005 从 13.6% 降到 9.6%；
- 9988、1810 从 1% 变成小空头（−2.6%、−0.8%）；
- 组合仍然是“银行/港铁为主”，只是多了两个小空头。

---

## 5. 提交前检查（30 秒）

- [ ] `params.json` 的 `cutoff` = **2026-11-06**；
- [ ] `strategy` = `capm`，`lam` = 15，`floor` = −0.15，`cap` = 0.30，`beta` 已写入；
- [ ] `capital_prev` = Week 1 实际剩余资本（不是固定的 1,000,000；Week 1 实际约 998,704.94 到 11/4，最终以 11/6 估值为准）；
- [ ] `submission.xlsx` 的 Summary：`Sum of weights = 1`；
- [ ] 10 行，空头 ≥ −15%，多头 ≤ 30%；
- [ ] `n_short` 与表里的负权重数量一致；
- [ ] `Number of Shares × Price ≈ Capital Allocated`（空头为负资本/负股数）；
- [ ] Moodle 上传成功（截图/确认）。

---

## 6. 决策规则与应急预案

| 情况 | 处理 |
|---|---|
| `refresh-data` 失败 | 检查 `data/meta.json` 的 `raw_last_weekly` 是否 = 2026-11-06；不要用 10/30 的旧数据提交 |
| `build` 报 “capm strategy requires HSI” | 检查 `data/index_returns.csv` 是否存在；没有就先用 `--strategy gmv --floor -0.15 --cap 0.30`，并在 `params.json` 记下原因 |
| 组合年化波动 > 10.5% | 把 `--lam` 提到 20 |
| gross > 1.30 | 把 `--floor` 从 −0.15 收到 −0.10，或把 λ 提到 20 |
| 空头数量 > 3 只 | 正常；但检查是否超过单只 −15% 下限 |
| Week 1 主动收益 < −5pp | 不要因为一周噪声就推翻框架；仍用 CAPM λ=15，但在 `params.json` 记下 “one-week noise, no rule trigger” |
| 组里不想用做空 | 退回 `--floor 0.01 --cap 0.25`（long-only CAPM）；报告里说明为什么放弃 short |

---

## 7. 记录与报告素材

提交后，在 `weeks/week2/` 里保留：

- `params.json`：β、λ、r_f、premium、floor、cap、权重、C_{i-1}；
- `submission.xlsx` / `.csv`：提交值；
- `report.md`：自动生成的快照说明；
- `portfolio_ref_gmv_short.csv`：short GMV 参考权重；
- 11/13 后：`realized.csv`、`realized_summary.json`。

报告里可以写：

> “Week 2 introduced the CAPM equilibrium view and, for the first time, used the project's explicit short-selling permission. The portfolio remains dominated by the low-volatility bank/transport core, with small shorts in 9988 (−2.6%) and 1810 (−0.8%). The short book is capped at −15% per name; gross exposure is 1.07. In the 2021–2026 backtest, the short-enabled CAPM portfolio had a lower Sharpe than the long-only version (0.64 vs 0.72), so we keep the short book small and treat it as a relative-view tool rather than a return enhancer.”

---

## 8. 常见问题

**Q：为什么 Week 2 开始做空？**
A：官方 PDF 第 1 页明确写 “short positions are permitted”。Week 1 已经按 long-only 提交，不改；Week 2 起使用小空头表达相对弱的股票。

**Q：做空会不会被 margin/借券成本吃掉？**
A：项目公式没有计交易成本/借券成本，`R_i` 只按价格变动算。报告里要注明 “gross of borrow/margin costs”；实际中空头有借券费和保证金要求，所以 short cap 保持 −15%。

**Q：backtest 说 short 降低 Sharpe，为什么还做？**
A：因为项目允许，而且它能表达负向观点；但我们把空头限制在 −15%，并如实报告 lower Sharpe。如果组里更看重回测 Sharpe，可以退回 long-only CAPM，把做空留到 Week 3/4。

**Q：λ=15 是什么单位？**
A：没有单位，是风险厌恶系数。它只在 `μ'w − (λ/2)w'Σw` 里和 μ、Σ 的相对大小有关。换 μ 的尺度（比如把 premium 从 5% 改成 3%）等价于换 λ，所以报告里要固定写清楚 r_f、premium、λ。

**Q：CAPM 组合还是重仓银行，这不是没观点吗？**
A：观点是“高 β 多配”，但风险模型和 30% 上限会把它拉回来。Week 2 是弱观点，Week 3 的信号观点会更强。报告里可以把“观点强度”作为一条主线。

**Q：如果 Week 2 跑输等权怎么办？**
A：一周结果不能说明 CAPM 无效。按预注册规则，只有累计主动收益 < −5pp 才调整；而且 Week 3 会换一个不同的观点（信号），报告里正好可以对比“市场观点 vs 选股观点”。
