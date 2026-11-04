# 课程 Benchmark 对照：老师讲过的六个方法，我们怎么一一对比

> 对应项目要求：`Group-Project-2_2026.pdf` 的
> **“Comparison between your proposed method and the benchmark methods (which I have covered in the class).”**
>
> 对应代码：`research_benchmarks.py`
> 输出：`research/benchmark_summary.csv`、`benchmark_4w_distribution.csv`、
> `frontier_20261030.csv`、`frontier_points.csv`、`two_fund_check.csv`
>
> 数据：10 只港股，2021-01-08 至 2026-10-30，周频，后复权总收益，无交易成本。

---

## 0. 一句话结论

老师课上讲过的 benchmark，按 Lecture 2–4 可以归成 **六类**：

| # | Benchmark | 课程出处 | 我们的实现 |
|---|---|---|---|
| 1 | 等权 1/N | Lecture 2, slide 21–23 | `EW` |
| 2 | 全局最小方差 GMV | Lecture 2, slide 29–32；Lecture 3, slide 11 | `GMV_uncon`（课程公式） / `GMV_con`（纯多头 1%–25%） |
| 3 | 均值-方差有效前沿 | Lecture 3, slide 13–22 | `frontier_20261030.csv` / `frontier_points.csv` |
| 4 | 切点组合 / 最大 Sharpe | Lecture 3, slide 25–32 | `Tangency_uncon`（课程公式） / `Tangency_uncon_cap2`（gross≤2） / `Tangency_con`（纯多头） |
| 5 | 两基金定理 | Lecture 3, slide 23 | `two_fund_check.csv` |
| 6 | CAPM / SML / 市场组合 | Lecture 4, slide 9–17 | `CAPM_con`；`Market_HSI` |

我们的 proposed method 是 **Signal_con**（第 3 周的复合信号 + 均值-方差），
最终报告如果采用第 4 周的自适应版本，就把 `Signal_con` 换成最终的 `Adaptive` 再跑一遍同样的表。

---

## 1. 每个 benchmark 的课程公式与我们的实现

### 1.1 等权 1/N（Lecture 2）

课程在 diversification 部分专门分析了 `x_i = 1/n` 的组合方差：

```
Var(R_p) = (1/n) AvgVar + (1 − 1/n) AvgCov
```

我们的实现：

```
w_s = 1/10,  s = 1,...,10
```

用途：最朴素的分散化基准；任何“聪明”方法至少应该跑赢它，否则没有意义。

---

### 1.2 全局最小方差 GMV（Lecture 2/3）

课程公式（Lecture 2 slide 31，Lecture 3 slide 11）：

```
min_x  x'Σx   s.t.  x'e = 1
x* = Σ⁻¹e / (e'Σ⁻¹e)
```

其中 `e = (1,...,1)'`。

我们有两个版本：

| 版本 | 约束 | 说明 |
|---|---|---|
| `GMV_uncon` | 无（允许做空） | 严格按课程公式；平均 gross 1.16，平均 3.5 个空头 |
| `GMV_con` | 纯多头，1% 下限 / 25% 上限 | 我们实际可提交的版本；第 1 周用的就是它 |

**1% 下限的细节**：`GMV_con` 的 **9988、1810、0700** 三只正好在 1% 下限。不设下限时，优化器会把它们设为 **0**（三只的年化波动分别是 46.1%、40.6%、28.4%，相对银行/港铁太高）；1% 下限保证 10 只都持有。代价是：样本协方差波动 **8.53% → 8.77%**，104 周样本均值 **15.78% → 15.36%**。完整的 0%/0.5%/1%/2% 敏感性表见 `WEEK1_REPORT_EN.md` §3.4。

**报告写法**：

> “The unconstrained GMV follows the closed-form solution `Σ⁻¹e/(e'Σ⁻¹e)` from Lecture 2. Because our group does not short, we also report a constrained version with `0.01 ≤ w_s ≤ 0.25`. The constrained version has a slightly higher volatility (8.41% vs 7.89%) but is implementable and holds all ten stocks.”

---

### 1.3 均值-方差有效前沿（Lecture 3）

课程给了两种等价写法（slide 20–21）：

```
min_x  x'Σx   s.t.  μ'x = R,  x'e = 1
max_x  μ'x    s.t.  x'Σx = σ²,  x'e = 1
```

我们的实现（`frontier_weights`）：

```
min_x  x'Σx   s.t.  μ'x = target,  x'e = 1,  0.01 ≤ w ≤ 0.25
```

- `μ`：104 周样本均值（年化）；
- `Σ`：104 周协方差，30% 收缩；
- 目标收益从 GMV 的预期收益开始，向上取 15 个点；
- 输出：`research/frontier_20261030.csv`（每个点的 target return、vol、10 个权重）。

**注意**：这是一条 **long-only + 1%–25%** 的有效前沿，不是课程里允许做空的那条。
报告里要写清楚，否则和 `Tangency_uncon` 不可比。

---

### 1.4 切点组合 / 最大 Sharpe（Lecture 3）

课程公式（slide 29–31）：

```
Sharpe(x) = (μ(x) − r_f) / σ(x)
x* ∝ Σ⁻¹ μ̃,   μ̃ = μ − r_f
```

我们有三版本：

| 版本 | 约束 | 结果 |
|---|---|---|
| `Tangency_uncon` | 无（课程公式原样） | **不可实施**：平均 gross 34.75，worst week −652%，年化波动 363.7% |
| `Tangency_uncon_cap2` | 课程公式 + gross ≤ 2.0 | 可比较的版本；年化 10.44%，波动 14.71%，Sharpe 0.57 |
| `Tangency_con` | 允许做空，w ∈ [−10%, 40%] | clipped 切点；年化 8.26%，波动 14.25%，Sharpe 0.44 |

**为什么原始切点组合会爆炸？**

- 用 104 周样本均值估 10 个 μ；
- 协方差矩阵接近奇异；
- `Σ⁻¹μ̃` 会把很小的估计误差放大成巨大的多空仓位；
- 这是 Markowitz 的经典“估计误差”问题，也是我们第 1 周不用 μ、从 GMV 开始的原因。

**报告写法**：

> “The textbook tangency portfolio `Σ⁻¹(μ−r_f)` is mathematically correct but not implementable with sample means: over the backtest its average gross exposure is 34.8 and its worst week is −652%. We therefore report a gross-capped version (gross ≤ 2) and a long-only version. This is a direct illustration of estimation error, and it motivates the shrinkage and constraints used in our proposed method.”

---

### 1.5 两基金定理（Lecture 3 slide 23）

课程说：任何有效组合都可以写成两个有效组合的线性组合。

我们的检查：

```
w(α) = α · w_GMV + (1 − α) · w_Tangency
```

- 用 `GMV_uncon`（课程公式）和 `Tangency_uncon_cap2`（gross≤2）作为两个基金；
- 对每个方法，选 α 使其预期收益与该方法相同；
- 比较 `w(α)` 与该方法的 L1 权重距离。

结果（`research/two_fund_check.csv`）：

| 方法 | α（GMV 权重） | L1 权重距离 | 方法波动 | 两基金波动 |
|---|---:|---:|---:|---:|
| GMV_con | 1.013 | **0.046** | 7.86% | 7.84% |
| CAPM_con | 1.039 | **0.104** | 7.90% | 7.83% |
| Signal_con | 0.975 | **0.174** | 7.91% | 7.86% |
| Tilt_k2 | 1.004 | 0.329 | 8.05% | 7.85% |
| Top4 | 1.033 | 0.582 | 10.07% | 7.83% |
| EW | 1.010 | **0.897** | 14.31% | 7.84% |

读法：

- GMV_con、CAPM_con、Signal_con 的 L1 距离只有 0.05–0.17，说明它们**非常接近 GMV–切点这条两基金线**；
- EW 的距离 0.897，远离线，说明等权不在有效前沿附近；
- 两基金定理在**无约束**下严格成立；我们是 long-only + 1%–25%，所以是“近似成立”，报告里要写清楚。

**报告写法**：

> “As a consistency check, we decompose each portfolio into the two-fund span of GMV and the gross-capped tangency portfolio. The proposed signal portfolio has an L1 weight distance of 0.17 from the two-fund combination, compared with 0.90 for equal weight. This is consistent with the two-fund theorem: the proposed portfolio lies close to the efficient frontier, while equal weight does not. The decomposition is approximate because our implementation is long-only with 1%–25% caps.”

---

### 1.6 CAPM / SML / 市场组合（Lecture 4）

课程公式（slide 10–17）：

```
μ_i = r_f + β_i (μ_M − r_f)
β_i = σ_im / σ_m²
R_i − r_f = α_i + β_i (R_M − r_f) + ε_i
```

我们的实现：

| 版本 | 说明 |
|---|---|
| `CAPM_con` | 用 HSI 作为市场组合，估 β；`μ = 2% + β × 5%`；再做均值-方差（λ=15，纯多头 1%–25%） |
| `Market_HSI` | 直接用 HSI 周收益作为被动市场基准 |

注意：

- HSI 不是 10 只股票的组合，不能直接提交；它是**市场组合的代理**（Lecture 4 slide 9 说 S&P 500 或 broad index funds 是 proxy）；
- 2021–2026 恒指年化 −3.76%、波动 22.25%、最大回撤 −49.25%，是一个熊市基准；
- 我们的所有 long-only 组合都跑赢 HSI，但这主要是因为 HSI 在样本期表现极差，不能直接说“我们比市场强”。

**报告写法**：

> “We use the HSI as the market proxy for the CAPM benchmark, following Lecture 4. The HSI is not restricted to the ten-stock universe and is therefore a reference rather than an implementable alternative. Over 2021–2026 the HSI returned −3.76% p.a. with 22.25% volatility and a −49.25% maximum drawdown; all long-only portfolios beat it, but the comparison is not risk-adjusted and the period is a severe bear market for Hong Kong equities.”

---

## 2. 主对比表（报告可以直接用）

**样本**：2021-01-08 → 2026-10-30，296 周，周频再平衡，后复权总收益，无交易成本。
**Sharpe**：`(年化收益 − 2%) / 年化波动`（课程定义）。

| 方法 | 课程出处 | 约束 | 年化 | 波动 | Sharpe | 最大回撤 | 主动 vs EW |
|---|---|---|---:|---:|---:|---:|---:|
| **Signal_con（proposed）** | 第 3 周信号 | 纯多头 1–25% | **8.70%** | **8.41%** | **0.80** | **−11.6%** | **+2.22%** |
| GMV_uncon | L2/L3 公式 | 允许做空 | 8.13% | 7.89% | 0.78 | −10.7% | +1.65% |
| GMV_con | L2/L3 + 实现约束 | 纯多头，1% 下限 / 25% 上限 | 8.39% | 8.41% | 0.76 | −11.3% | +1.93% |
| Tilt_k2（robustness） | 我们的直接 tilt | 纯多头 | 10.79% | 11.92% | 0.74 | −15.0% | +4.48% |
| CAPM_con | L4 CAPM/SML | 纯多头 1–25% | 8.03% | 8.50% | 0.71 | −12.5% | +1.61% |
| Top4（robustness） | 我们的集中版 | 纯多头 | 9.90% | 13.41% | 0.59 | −23.2% | +3.86% |
| Tangency_uncon_cap2 | L3 切点 + gross≤2 | 允许做空，gross≤2 | 10.44% | 14.71% | 0.57 | −27.3% | +4.53% |
| Tangency_con | L3 切点 + clip | 允许做空，w∈[−10%, 40%] | 8.26% | 14.25% | 0.44 | −30.3% | +2.48% |
| EW | L2 1/N | 纯多头 | 5.31% | 16.23% | 0.20 | −33.0% | 0 |
| Market_HSI | L4 市场代理 | 被动指数 | −3.76% | 22.25% | −0.26 | −49.3% | −7.85% |

> `GMV_con` 的 1% 下限对 **9988、1810、0700** 是 binding；`GMV_uncon` 是纯课程公式。两者的差异主要来自下限/约束，详见 §1.2 和 `WEEK1_REPORT_EN.md` §3.4。
>
> 主表是 **long-only（Week 1 口径）**；Week 2 起的 short-enabled 版本见 §2.1。

**诊断（不要放进主表，放 appendix）**：

| 方法 | 年化 | 波动 | 最大回撤 | 平均 gross | worst week |
|---|---:|---:|---:|---:|---:|
| Tangency_uncon（课程公式原样） | −11.21% | 363.72% | −102.9% | 34.75 | −652.2% |

**读法**：

1. **GMV_con** 和 **GMV_uncon** 都跑赢 EW（+1.9% / +1.7% 年化主动），但差距不大；GMV 的价值在低波动、低回撤。
2. **CAPM_con** 没有明显改善（+1.6% 主动，Sharpe 0.71 vs GMV 0.76）；这是一个诚实的结果，说明“市场观点”在样本期没有带来风险调整后的提升。
3. **Signal_con** 是 proposed method 中 Sharpe 最高的（0.80），主动 +2.22%，最大回撤 −11.6%，和 GMV 同一水平但收益更高。
4. **Tangency**（课程公式）在允许做空时收益更高，但波动/回撤大；原始版本不可实施。
5. **EW** 是最差的长期方法（Sharpe 0.20，最大回撤 −33%），说明“分散化”不等于“等权”。
6. **HSI** 在样本期是负收益，所有组合都跑赢它，但要说明这是熊市基准，不能过度解读。

### 2.1 做空后的 proposed method（Week 2 起）

从 Week 2 起，proposed method 使用官方允许的做空（floor −15% / cap 30%）。同一 2021–2026 协议下：

| 策略 | 年化 | 波动 | Sharpe | 最大回撤 | 主动 vs EW | 平均 gross |
|---|---:|---:|---:|---:|---:|---:|
| Signal_long（Week 1 口径） | 8.83% | 8.40% | 0.81 | −11.6% | +2.89% | 1.00 |
| **Signal_short（Week 3 起）** | 7.86% | 7.99% | 0.73 | **−10.3%** | +1.96% | 1.24 |
| GMV_long（Week 1） | 8.53% | 8.40% | 0.78 | −11.3% | +2.62% | 1.00 |
| GMV_short | 7.10% | 7.90% | 0.65 | −11.0% | +1.25% | 1.15 |
| CAPM_long | 8.15% | 8.49% | 0.72 | −12.5% | +2.27% | 1.00 |
| **CAPM_short（Week 2 起）** | 7.24% | 8.15% | 0.64 | −12.5% | +1.40% | 1.08 |
| EW | 4.72% | 16.26% | 0.17 | −33.0% | 0 | 1.00 |

**读法**：

- 做空**降低 Sharpe**（Signal 0.81→0.73，CAPM 0.72→0.64，GMV 0.78→0.65），因为被做空的高波动科技股在 2024–26 反弹；
- 做空**降低波动/回撤**（Signal 最大回撤 −11.6%→−10.3%）；
- 我们仍然从 Week 2 使用做空，是因为项目明确允许、且它能表达负向观点；但 short book 保持很小（单只 ≤ −15%），报告里要如实写“shorting did not improve backtest Sharpe”。

> 最终报告的 benchmark comparison 要同时放 long-only（Week 1）和 short-enabled（Week 2+）两套行，避免把“Week 1 的 long-only”与“Week 2+ 的 short”混为一谈。

---

## 3. 有效前沿对比（in-sample，104 周）

**设置**：截点 2026-10-30，104 周窗口，long-only 1%–25%，μ = 样本均值，Σ = 30% 收缩。

| 方法 | 预期收益 | 波动 | 同波动下的前沿收益 | 效率缺口 |
|---|---:|---:|---:|---:|
| EW | 15.31% | 14.31% | 22.69% | **−7.38%** |
| GMV_con | 15.29% | 7.86% | 15.39% | **−0.10%** |
| Signal_con | 15.48% | 7.91% | 15.71% | **−0.22%** |
| CAPM_con | 15.16% | 7.90% | 15.66% | **−0.50%** |
| GMV_uncon | 14.41% | 7.33% | 15.36% | −0.94% |
| Tilt_k2 | 15.34% | 8.05% | 16.48% | −1.14% |
| Top4 | 15.19% | 10.07% | 20.32% | −5.13% |
| Tangency_con | 20.51% | 10.06% | 20.31% | +0.20%* |
| Tangency_uncon_cap2 | 20.57% | 10.09% | 20.36% | +0.22%* |

\* 切点组合允许做空，因此可以落在 long-only 前沿的**上方**；正的 0.2% 一部分来自空头，一部分来自 15 个网格点的插值误差。它不是 long-only 前沿上的点，不能和纯多头方法严格比较。

**读法**：

- GMV_con、Signal_con、CAPM_con 距离前沿只有 **0.1–0.5pp**，说明它们基本在有效前沿上；
- EW 距离前沿 **7.4pp**，这是“等权不在有效前沿”的直接证据；
- Top4 距离前沿 5.1pp，说明集中动量虽然收益高，但风险调整后离前沿很远；
- 这张表是 in-sample 的（μ 和 Σ 都来自同一窗口），报告里要注明“in-sample illustration, not out-of-sample performance”。

**报告写法**：

> “Figure X plots the long-only efficient frontier at the 30 October 2026 cutoff. The constrained GMV, the CAPM portfolio and the proposed signal portfolio lie within 0.1–0.5 percentage points of the frontier, while equal weight lies 7.4 percentage points below it. The tangency portfolios lie on the frontier within the 0.2pp grid error. This is an in-sample illustration: the frontier uses the same 104-week sample mean and covariance as the portfolios, so it should not be read as out-of-sample performance.”

---

## 4. 两基金定理检查

见第 1.5 节。报告里可以放一张小表：

| 方法 | α（GMV） | L1 权重距离 | 方法波动 | 两基金波动 |
|---|---:|---:|---:|---:|
| GMV_con | 1.013 | 0.046 | 7.86% | 7.84% |
| CAPM_con | 1.039 | 0.104 | 7.90% | 7.83% |
| Signal_con | 0.975 | 0.174 | 7.91% | 7.86% |
| EW | 1.010 | 0.897 | 14.31% | 7.84% |

结论：proposed portfolio 接近 GMV–切点两基金线，EW 远离；与“EW 不在有效前沿”一致。

---

## 5. 报告里建议的 comparison 结构（约 1 页）

1. **一句话**：我们把 proposed method 与 Lecture 2–4 的六类 benchmark 对比。
2. **表 1**：主对比表（年化、波动、Sharpe、最大回撤、主动 vs EW）。
3. **表 2 / 图**：有效前沿 + 各方法的位置（效率缺口）。
4. **表 3**：两基金定理检查（可选，但很加分）。
5. **三段解读**：
   - GMV：低波动、低回撤，是第 1 周的合理起点；
   - CAPM：市场观点没有带来显著改善，说明样本期 β 溢价不稳定；
   - Tangency：课程公式正确，但样本均值 + 协方差求逆会放大误差；原始版本不可实施，约束版波动/回撤大；
   - EW：最差，说明等权不是有效组合；
   - Proposed：Sharpe 最高、回撤与 GMV 同水平、主动 +2.2%，且离前沿最近（0.2pp）。
6. **限制**：in-sample、无交易成本、无借券成本、无卖空限制（除了我们自己的 long-only）、HSI 是熊市基准。

---

## 6. 常见审稿问题（提前准备）

**Q1：你们说跑赢 EW，但 EW 的波动更高，风险调整了吗？**
A：主表有 Sharpe（用课程定义 `(μ−r_f)/σ`），并且有最大回撤、4 周分布。Signal_con 的 Sharpe 0.80 > EW 0.20，风险调整后也赢。

**Q2：为什么 GMV_uncon 和 GMV_con 不一样？**
A：课程公式允许做空，`GMV_uncon` 平均有 3.5 个空头、gross 1.16；Week 1 我们 long-only，所以提交版是 `GMV_con`（纯多头 1%–25%）。Week 2 起使用 short-enabled（floor −15% / cap 30%，见 §2.1）；两者收益/波动很接近，说明约束的代价不大。

**Q3：为什么 Tangency_uncon 的波动 363%？**
A：这是课程公式 `Σ⁻¹(μ−r_f)` 在样本均值 + 近奇异协方差下的典型爆炸。它不是我们编的，而是 Markowitz 估计误差的经典表现。我们用 gross≤2 和 long-only 两个版本让它可实施，并把原始版本放在 appendix 作为“为什么需要收缩/约束”的证据。

**Q4：两基金定理不是要求无约束吗？**
A：对，严格成立需要无约束。我们的检查是“约束版近似”：GMV_con/CAPM/Signal 的 L1 距离 0.05–0.17，说明它们接近两基金线；EW 0.90，远离。报告里明确写“approximate, because long-only with caps”。

**Q5：HSI 是市场组合吗？**
A：Lecture 4 说 S&P 500 或 broad index funds 是 market portfolio 的 proxy；对港股我们用 HSI。但 HSI 不是 10 只股票的 combos，不能直接提交；它只是 reference。样本期 HSI 年化 −3.76%，是熊市，不能把“跑赢 HSI”当成绝对能力。

**Q6：有效前沿是 in-sample 还是 out-of-sample？**
A：in-sample。μ 和 Σ 都来自同一个 104 周窗口，前沿上的点是用同一组 μ/Σ 算的。它的作用是“看方法离有效前沿有多远”，不是预测未来。Out-of-sample 的证据是 `benchmark_summary.csv` 的滚动回测。

---

## 7. 文件与复现

```powershell
$env:MKL_THREADING_LAYER = 'SEQUENTIAL'
$py = 'C:\Users\Administrator\miniforge3\envs\dase7310\python.exe'
cd D:\Backup\Documents\dase7310\DASE7310_GP2_Repo

& $py research_benchmarks.py
```

输出：

| 文件 | 内容 |
|---|---|
| `research/benchmark_summary.csv` | 主对比表 |
| `research/benchmark_4w_distribution.csv` | 4 周累计收益分布 |
| `research/benchmark_final_weights.csv` | 各方法在 10/30 的最终权重 |
| `research/benchmark_weekly.csv` | 每周收益明细（可复算 Sharpe/回撤） |
| `research/frontier_20261030.csv` | 有效前沿的 15 个点 |
| `research/frontier_points.csv` | 各方法在前沿上的位置与效率缺口 |
| `research/two_fund_check.csv` | 两基金定理检查 |
| `research/short_backtest_weekly.csv` | long-only vs short-enabled 的逐周回测（§2.1 表） |
| `research/benchmark_diagnostics.csv` | 原始切点组合的诊断（appendix 用） |

---

<a id="lecture57"></a>
## 8. Lecture 5–7 与 GP2 的关系（已逐页检查）

很多同学会问：“后面几讲是不是也有组合 benchmark？”答案是：**没有**。Lecture 5–7 是衍生品与固定收益，不是 GP2 的组合构建方法。

| Lecture | 主题 | 和 GP2 的关系 |
|---|---|---|
| **Lecture 5** | Derivatives markets、forward/futures、hedging strategies | 唯一相关的是 **minimum variance hedge ratio** `h* = ρ σ_S / σ_F` 和 hedge effectiveness `e = ρ²`（slide 29–31）。这是“用期货对冲”的比率，**不是** GMV 组合。GP2 只允许 10 只股票，不能用 HSI 期货，所以不作为 benchmark；可以作为“potential improvement”提一句。 |
| **Lecture 6** | Important interest rates、zero rates、bond pricing、forward rates、FRA | 和股票组合没有直接关系。唯一用到的是无风险利率 `r_f`；我们用 2% 的平坦利率。更精确的做法是用 HK 零息曲线（Lecture 6），但对 4 周组合影响是二阶的，可作为 improvement。 |
| **Lecture 7** | Futures/forward prices、stock index futures、margin、options | 和 GP2 直接相关的是 **short selling**（slide 4）和 **stock index futures**（slide 18–21）。项目第 1 页明确写 “short positions are permitted”，但我们组选择不做；HSI 期货/期权不在允许的股票池里。可以在报告里引用 short-selling 的保证金/借券成本，解释为什么我们选择 long-only。 |

**结论：**

- GP2 的 benchmark 全部在 **Lecture 2–4**：1/N、GMV、有效前沿、切点/最大 Sharpe、两基金定理、CAPM/SML/市场组合。
- Lecture 5–7 主要服务 **final exam（70%）** 和 **oral presentation**（课程 schedule 里的 futures、swaps、options、binomial trees、Black-Scholes），不是 GP2 的组合 comparison。
- 如果老师问“你们有没有考虑衍生品对冲”，可以答：
  > “We read the hedging material in Lecture 5. If HSI futures were allowed, the minimum-variance hedge ratio `h* = ρ σ_p / σ_f` could reduce market risk; the project restricts the universe to the ten stocks, so we stayed long-only and used the 1%/25% constraints instead.”

---

## 9. 一句话总结

> 老师讲过的 benchmark 不是“随便找几个策略”，而是 **1/N、GMV、有效前沿、切点/最大 Sharpe、两基金定理、CAPM/市场组合** 这六类。
> 我们的对比表要逐一覆盖，并说明“课程公式原样”和“可实施约束版”的区别；其中原始切点组合的爆炸正好证明“为什么不能直接用样本均值”，也是我们第 1 周从 GMV 开始的最好理由。
