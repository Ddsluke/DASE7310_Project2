# DASE7310 Group Project II — Week 1 Report

**Portfolio construction and weekly rebalancing**
**Data cutoff:** 30 October 2026 (Friday close)
**Trading week:** 2–6 November 2026
**Submission:** 1 November 2026, 23:59 (HK time)

---

## Executive summary

Week 1 establishes the group's **no-view benchmark**: a long-only **Global Minimum
Variance (GMV)** portfolio across the ten HKEX stocks from Group Project I.

The portfolio is fully invested in HKD 1,000,000, holds all ten names, and uses only
the covariance matrix — no expected-return forecasts. The motivation is direct: GP1
showed that weekly mean returns are close to unpredictable, and a mean-variance
optimizer fed with noisy sample means produces unstable, concentrated weights. GMV
avoids that failure mode and gives the group a transparent risk benchmark against
which the later, view-based portfolios can be judged.

The resulting portfolio has an estimated annualised volatility of **8.8%** (sample
covariance), a beta of **0.32** against the HSI, and a backtested maximum drawdown of
**−11.3%** over 2021–2026, compared with **−33.0%** for equal weight.

---

## 1. Project rules and timeline

The official `Group-Project-2_2026.pdf` (26 October 2026) specifies:

| Item | Rule |
|---|---|
| Stock pool | 9988, 0066, 1398, 3988, 0981, 0005, 1810, 0016, 1113, 0700 |
| Initial capital | HKD 1,000,000, fully allocated (`sum_s w_s = 1`) |
| Short selling | Permitted; **not used by this group** |
| Holding period | Buy-and-hold within each trading week |
| Rebalancing | Before a new week, at most **three adjustments** in total |
| Trading weeks | 2–6 Nov, 9–13 Nov, 16–20 Nov, 23–27 Nov 2026 |
| Submissions | 1, 8, 15, 22 November (Sunday 23:59) |
| Report and peer evaluation | 30 November 2026 |
| Oral presentation | 23 and 30 November 2026 |

The formulas used for every snapshot are:

```
w_{s,i} = c_{s,i-1} / C_{i-1}
h_{s,i} = c_{s,i-1} / p_{s,i-1}
C_i     = sum_s p_{s,i} * h_{s,i}
R_i     = (C_i - C_{i-1}) / C_{i-1}
```

> **Note on the syllabus discrepancy.** Lecture 1 still shows “five weeks, 26 Oct –
> 29 Nov, five adjustments”. The official GP2 PDF (26 October) supersedes it with four
> weeks, 2–27 November and three adjustments. This report follows the PDF.

---

## 2. Data and conventions

### 2.1 Price series

Two price series are used, for different purposes:

| Purpose | Series | Reason |
|---|---|---|
| Signals, covariance, backtests | **hfq** (dividend-adjusted) | Total-return series; corporate actions removed |
| Share count and capital | **raw** (unadjusted) | The course's `p` is the actual market close |

This distinction is material. On 30 October 2026, HSBC's raw close was **HKD 135.70**
while its hfq price was **952.05** (a 7× difference); SMIC's raw close was **42.98**
while its hfq price was **4.298** (a 0.1× difference). Using adjusted prices for
`h = c / p` would produce share counts that are wrong by a factor of several.

### 2.2 Sample and window

| Item | Value |
|---|---|
| Stocks | 10 |
| Weekly return observations | **356** (10 Jan 2020 – 30 Oct 2026) |
| Current covariance window | **104 weeks** (8 Nov 2024 – 30 Oct 2026) |
| Annualisation | weekly covariance × 52 |
| Weekly price | last realised close of each W-FRI week |

### 2.3 Week 1 valuation

The course defines `p_{s,0}` as the closing price at the end of the week before the
trading week. For Week 1 this is **Friday 30 October 2026**, so the submission uses
the 30 October raw closes.

---

## 3. Methodology: Global Minimum Variance

### 3.1 Why GMV first

The mean-variance problem requires two inputs:

| Input | Meaning | GMV uses it? |
|---|---|---|
| `Σ` (covariance matrix) | Risk: how volatile each stock is, and how they co-move | Yes |
| `μ` (expected returns) | View: how much each stock is expected to earn | No |

GMV solves:

```
min_w   w'Σw
s.t.    1'w = 1
        0.01 <= w_s <= 0.25
```

It is the “no-view” portfolio. Its only implicit assumption is that the historical
covariance matrix is a reasonable description of future risk. This is deliberate:
GP1's central finding was that weekly return forecasts are extremely noisy, so the
first week should establish a risk benchmark rather than a return bet.

### 3.2 Covariance estimation

For ten stocks, the covariance matrix has 55 independent parameters (10 variances and
45 covariances). With 104 weekly observations, the sample matrix is noisy and its
inverse can amplify estimation error. We therefore use a **30% shrinkage toward the
diagonal**:

```
Σ_shrunk = 0.7 * Σ_sample + 0.3 * diag(Σ_sample)
```

- Variances are unchanged;
- Covariances (and correlations) are multiplied by 0.7;
- The matrix is better conditioned and the optimizer is more stable.

A Ledoit–Wolf estimate on the same window gives a shrinkage intensity of **5.9%**, much
lower than 30%. The GMV weights are nevertheless stable: moving from 0% to 30% changes
1398 from 24.5% to 21.2% and 1113 from 1.0% to 4.1%, but the portfolio remains the same
bank/transport core. Ledoit–Wolf versus 30% differs by at most 1.2 percentage points on
any single name. The choice of 30% is therefore a robustness haircut, not a critical
parameter.

**Risk reporting.** The 7.85% volatility computed from the shrunk matrix understates
risk. Checked against the sample covariance, the same portfolio has an annualised
volatility of **8.77%**. This report uses **8.8%** as the conservative risk estimate.

### 3.3 Optimisation

The constrained problem is a convex quadratic program. It is solved with
**SciPy's SLSQP** (`scipy.optimize.minimize`, `method="SLSQP"`), starting from equal
weights, with bounds `[0.01, 0.25]`, the equality constraint `sum(w) = 1`, and a
tolerance of `1e-14`. Because the objective is convex and the constraints are linear,
the solution is the global minimum. The code checks `res.success` and raises an error
if the solver fails.

For reference, the unconstrained closed-form solution is:

```
w = Σ^{-1} 1 / (1' Σ^{-1} 1)
```

On our data this solution shorts 9988 (−3.6%) and 1810 (−1.7%) and puts 39.7% in 0066
and 29.2% in 3988. Those short positions are not permitted by the group's long-only
choice, which is why the constrained numerical solution is used.

### 3.4 Implementation constraints: the 1% floor and 25% cap

The course GMV is unconstrained. Our submission adds two implementation constraints:

```
0.01 <= w_s <= 0.25
```

**Why the 1% floor?** The project requires the portfolio to be fully allocated
**across the ten selected stocks**. Without a floor, the optimizer sets three names to
zero: 9988 (46.1% annualised volatility), 1810 (40.6%) and 0700 (28.4%), because their
volatilities are high relative to the low-volatility bank/transport core. A zero weight
would still use the ten-stock universe, but it would not hold all ten names; the 1%
floor removes that ambiguity. The 25% cap prevents the opposite problem: without it,
GMV puts about 39.7% in 0066 and 29.2% in 3988.

**What does the floor cost?** The table below compares the constrained GMV at different
floors (cap fixed at 25%, same 104-week covariance). Volatility is checked against the
**sample** covariance, and the expected return is the in-sample 104-week mean; it is
shown only to illustrate the direction of the constraint cost, not as a forecast.

| Floor | 9988 | 1810 | 0700 | 0981 | Sample vol | In-sample mean | Names at floor |
|---:|---:|---:|---:|---:|---:|---:|---|
| 0% | 0.00% | 0.00% | 0.00% | 2.01% | 8.53% | 15.78% | 3 names at zero |
| 0.5% | 0.50% | 0.50% | 0.50% | 1.84% | 8.64% | 15.57% | 3 |
| **1% (submitted)** | **1.00%** | **1.00%** | **1.00%** | **1.68%** | **8.77%** | **15.36%** | **3** |
| 2% | 2.00% | 2.00% | 2.00% | 2.00% | 9.09% | 15.06% | 4 (0981 also) |

At the 1% floor, the cost relative to the unconstrained GMV is **+0.24pp of sample
volatility** (8.53% → 8.77%) and **−0.42pp of in-sample expected return** (15.78% →
15.36%). The three floor names contribute 2.5% (9988), 2.0% (1810) and 1.4% (0700) of
total portfolio risk, so the floor is a small but non-trivial diversification
constraint.

The floor and cap are **our implementation choices**, not part of the theoretical GMV.
In the benchmark comparison we therefore report both `GMV_uncon` (the course formula,
which allows zero and short positions) and `GMV_con` (the implementable version with the
1% floor and 25% cap).

---

## 4. Week 1 portfolio

**Initial capital:** HKD 1,000,000.00
**Valuation date:** 30 October 2026
**Strategy:** GMV, long-only, 104-week covariance, 30% shrinkage, 1% floor / 25% cap

| Code | Name | Price (HKD) | Weight | Capital (HKD) | Shares |
|---|---|---:|---:|---:|---:|
| 9988 | Alibaba Group Holding | 97.050 | 1.0000% | 10,000.00 | 103.039670 |
| 0066 | MTR Corporation | 33.320 | 25.0000% | 250,000.00 | 7,503.001200 |
| 1398 | ICBC | 7.895 | 21.2352% | 212,352.32 | 26,897.064161 |
| 3988 | Bank of China | 6.145 | 25.0000% | 250,000.00 | 40,683.482506 |
| 0981 | SMIC | 42.980 | 1.6762% | 16,761.92 | 389.993487 |
| 0005 | HSBC Holdings | 135.700 | 13.5712% | 135,711.64 | 1,000.085743 |
| 1810 | Xiaomi Group-W | 26.480 | 1.0000% | 10,000.00 | 377.643505 |
| 0016 | Sun Hung Kai Properties | 108.900 | 6.4628% | 64,628.07 | 593.462569 |
| 1113 | CK Asset Holdings | 46.160 | 4.0546% | 40,546.05 | 878.380619 |
| 0700 | Tencent Holdings | 383.600 | 1.0000% | 10,000.00 | 26.068821 |
| **Total** | | | **100%** | **1,000,000.00** | |

All ten stocks are held. Weights sum to 1.000000. Shares follow `h = c / p` to six
decimals; no board-lot rounding is applied, because the course formula allows
fractional shares and board-lot rounding would leave capital uninvested. The sum of
`shares × price` is HKD 999,999.9998, a rounding difference of HKD 0.0002.

Three names (9988, 1810, 0700) sit at the 1% floor. This is a deliberate implementation
constraint: without it, the optimizer would set them to zero because of their high
volatilities. The cost is small (+0.24pp sample volatility and −0.42pp in-sample mean);
see §3.4 for the sensitivity table.

---

## 5. Risk analysis

### 5.1 Portfolio risk and beta

| Metric | Value |
|---|---|
| Annualised volatility (shrunk covariance) | 7.85% |
| Annualised volatility (sample covariance) | **8.77%** |
| Beta vs HSI (104-week regression) | **0.32** |
| Largest single-name weight | 25.00% (0066, 3988) |
| Number of short positions | 0 |

A beta of 0.32 means the portfolio is defensive: a 10% move in the HSI is associated
with roughly a 3.2% move in the portfolio, before stock-specific effects.

### 5.2 Sector exposure

| Sector | Weight |
|---|---:|
| Banks (1398, 3988, 0005) | 59.8% |
| Transport (0066) | 25.0% |
| Property (0016, 1113) | 10.5% |
| Technology (9988, 0981, 1810, 0700) | 4.7% |

This is the main weakness of the GMV portfolio: it is effectively a defensive
bank/transport/property portfolio. The concentration is a direct consequence of the
covariance structure — these names have the lowest volatilities and the lowest
correlations with the technology block.

### 5.3 Risk contributions

Risk contribution is `RC_s = w_s * (Σw)_s / (w'Σw)`:

| Code | Weight | Risk contribution |
|---|---:|---:|
| 3988 | 25.00% | 24.5% |
| 1398 | 21.24% | 22.5% |
| 0066 | 25.00% | 19.9% |
| 0005 | 13.57% | 14.4% |
| 0016 | 6.46% | 6.8% |
| 1113 | 4.05% | 4.3% |
| 9988 | 1.00% | 2.5% |
| 1810 | 1.00% | 2.0% |
| 0981 | 1.68% | 1.8% |
| 0700 | 1.00% | 1.4% |

Although 0066 and 3988 both have 25% weights, their risk contributions differ (19.9% vs
24.5%) because 3988 is highly correlated with 1398 (ρ = 0.81), so the bank block adds
more portfolio risk than its capital weight alone suggests.

---

## 6. Course benchmark comparison

The project brief asks for a comparison with **the benchmark methods covered in class**.
Lectures 2–4 define six benchmark families: equal weight (1/N), the global minimum
variance portfolio, the mean-variance efficient frontier, the tangency / maximum-Sharpe
portfolio, the two-fund theorem, and the CAPM / market portfolio. The full mapping,
formulas and report-ready text are in `BENCHMARKS_ZH.md`; this section summarises the
results.

**Protocol.** Weekly rebalancing, 2021-01-08 to 2026-10-30, 296 weeks, hfq total
returns, gross of transaction costs. Sharpe ratios use the course definition
`(annual return − 2%) / annual volatility`. The long-only methods use a 104-week
covariance with 30% shrinkage and 1%/25% caps; the “unconstrained” rows use the course
formula and are shown separately.

### 6.1 Main comparison

| Method | Course link | Constraints | Ann. ret | Ann. vol | Sharpe | Max DD | Active vs EW |
|---|---|---|---:|---:|---:|---:|---:|
| **Signal (proposed)** | characteristic view | long-only 1–25% | **8.70%** | **8.41%** | **0.80** | **−11.6%** | **+2.22%** |
| GMV_uncon | Lecture 2/3 formula | shorts allowed | 8.13% | 7.89% | 0.78 | −10.7% | +1.65% |
| GMV_con | Lecture 2/3 + constraints | long-only, 1% floor / 25% cap | 8.39% | 8.41% | 0.76 | −11.3% | +1.93% |
| Tilt k=2 (robustness) | direct signal tilt | long-only | 10.79% | 11.92% | 0.74 | −15.0% | +4.48% |
| CAPM_con | Lecture 4 CAPM/SML | long-only 1–25% | 8.03% | 8.50% | 0.71 | −12.5% | +1.61% |
| Top-4 (robustness) | concentrated signal | long-only | 9.90% | 13.41% | 0.59 | −23.2% | +3.86% |
| Tangency_uncon_cap2 | Lecture 3 + gross≤2 | shorts, gross≤2 | 10.44% | 14.71% | 0.57 | −27.3% | +4.53% |
| Tangency_con | Lecture 3 + clips | long-short, w ∈ [−10%, 40%] | 8.26% | 14.25% | 0.44 | −30.3% | +2.48% |
| Equal weight | Lecture 2, 1/N | long-only | 5.31% | 16.23% | 0.20 | −33.0% | 0 |
| Market (HSI) | Lecture 4 market proxy | passive index | −3.76% | 22.25% | −0.26 | −49.3% | −7.85% |

> `GMV_con` uses the 1% floor / 25% cap from §3.4; `GMV_uncon` is the pure course
> formula. The floor is binding for 9988, 1810 and 0700 and is the main reason the two
> GMV rows differ.

The proposed signal portfolio has the highest Sharpe ratio in the group and a maximum
drawdown close to GMV, while equal weight has the worst risk-adjusted performance. The
CAPM portfolio adds only a small tilt and does not improve on GMV in this sample; this
is an honest result and motivates the switch to the signal view in Week 3.

### 6.2 Position on the efficient frontier

The long-only frontier is computed at the 30 October 2026 cutoff using the same 104-week
sample mean and covariance. The “efficiency gap” is the portfolio's expected return
minus the frontier return at the same volatility (in-sample).

| Method | Expected return | Volatility | Frontier return at same vol | Gap |
|---|---:|---:|---:|---:|
| Equal weight | 15.31% | 14.31% | 22.69% | **−7.38%** |
| GMV_con | 15.29% | 7.86% | 15.39% | **−0.10%** |
| Signal_con | 15.48% | 7.91% | 15.71% | **−0.22%** |
| CAPM_con | 15.16% | 7.90% | 15.66% | **−0.50%** |
| GMV_uncon | 14.41% | 7.33% | 15.36% | −0.94% |
| Tilt k=2 | 15.34% | 8.05% | 16.48% | −1.14% |
| Top-4 | 15.19% | 10.07% | 20.32% | −5.13% |
| Tangency_con | 20.51% | 10.06% | 20.31% | +0.20%* |
| Tangency_uncon_cap2 | 20.57% | 10.09% | 20.36% | +0.22%* |

\* The tangency rows allow short positions, so they can lie slightly **above** the
long-only frontier. Part of the positive 0.2pp gap is the shorting effect and part is
grid interpolation error (the frontier is evaluated on 15 target-return points). They
are not directly comparable with the long-only methods.

The constrained GMV, the CAPM portfolio and the proposed signal portfolio lie within
0.1–0.5 percentage points of the frontier. Equal weight lies 7.4 percentage points
below it. This is direct evidence that equal weight is not an efficient portfolio and
that the proposed method is close to the frontier. The comparison is in-sample: the
frontier uses the same 104-week moments as the portfolios, so it is an illustration,
not an out-of-sample performance claim.

### 6.3 Two-fund theorem check

Lecture 3's two-fund theorem says that any efficient portfolio can be written as a
combination of two efficient portfolios. We decompose each method as
`α · GMV + (1 − α) · gross-capped tangency`, choosing α to match its expected return:

| Method | α (GMV) | L1 weight distance | Method vol | Two-fund vol |
|---|---:|---:|---:|---:|
| GMV_con | 1.013 | **0.046** | 7.86% | 7.84% |
| CAPM_con | 1.039 | **0.104** | 7.90% | 7.83% |
| Signal_con | 0.975 | **0.174** | 7.91% | 7.86% |
| Equal weight | 1.010 | **0.897** | 14.31% | 7.84% |

The proposed portfolios are close to the GMV–tangency span (L1 distance 0.05–0.17),
while equal weight is far from it (0.90). The theorem holds exactly only without
constraints; our implementation is long-only with 1%/25% caps, so this is an
approximate check.

### 6.4 The unconstrained tangency portfolio

The textbook tangency formula `x* ∝ Σ⁻¹(μ − r_f)` is mathematically correct, but with
sample means and a nearly singular covariance matrix it is not implementable. Over the
backtest it has an average gross exposure of **34.75**, an annualised volatility of
**363.7%**, a worst week of **−652%**, and an annualised return of **−11.2%**. We
therefore report a gross-capped version (gross ≤ 2) and a long-only version in the main
table, and keep the raw version as a diagnostic. This is a direct illustration of
Markowitz estimation error, and it is the reason the Week 1 portfolio starts from GMV
rather than from a sample-mean tangency portfolio.

### 6.5 Tail behaviour

Over rolling four-week windows:

| Strategy | Median | 5th percentile | P(return < −5%) | P(return > +5%) |
|---|---:|---:|---:|---:|
| Signal_con | 0.37% | −2.88% | 1.02% | 4.78% |
| GMV_con | 0.33% | −3.12% | 0.68% | 5.12% |
| Equal weight | 0.06% | −6.22% | 10.24% | 13.99% |

GMV and the signal portfolio roughly halve the left tail of equal weight, at the cost
of a thinner right tail. For a four-week competition in which the downside is a
B-range grade and the upside is a top-three finish, this is a deliberate trade-off:
Week 1 prioritises not blowing up while the group establishes its process.

### 6.6 Sub-period stability

| Period | GMV return | EW return | GMV Sharpe | EW Sharpe |
|---|---:|---:|---:|---:|
| 2021–2023 (weak market) | 3.69% | 1.16% | 0.50 | 0.15 |
| 2024–2026 (strong rebound) | 16.97% | 18.06% | 1.76 | 1.06 |
| Full sample | 8.39% | 5.31% | 1.00 | 0.40 |

These sub-period figures come from `research_backtest.py` (Sharpe computed with
`r_f = 0`), so they are not directly comparable with the main table above; they are
shown to illustrate regime stability. GMV beat equal weight in the weak 2021–23 period
and lagged slightly in the 2024–26 rally, the expected pattern for a defensive
portfolio.

---

## 7. Why GMV is a good starting point

1. **It uses only the input we can estimate relatively well.** The covariance matrix is
   noisy, but far less noisy than ten individual expected returns.
2. **It is the first optimisation result in the course.** Lecture 2 derives the GMV
   portfolio; Lecture 3 places it at the left end of the efficient frontier. The method
   is therefore easy to explain and defend.
3. **It creates a clean benchmark.** Every later method — CAPM, signal tilt, adaptive
   rule — can be compared with GMV and equal weight on the same realised weeks.
4. **It is implementable.** Long-only, ten names, 1%–25% caps, fully invested, no short
   borrow, no leverage.
5. **It has a defensible risk profile.** 8.8% volatility and a −11.3% backtested maximum
   drawdown are appropriate for the first week of a four-week competition.

---

## 8. Strengths and weaknesses

### Strengths

- No expected-return estimation, so no “garbage in, garbage out” from noisy means;
- Low volatility and low drawdown;
- Stable across the 2021–23 and 2024–26 regimes;
- Transparent, reproducible, and easy to explain to the instructor;
- All ten stocks are held, satisfying the “across the 10 stocks” requirement.

### Weaknesses

- Concentrated in low-volatility sectors: banks 59.8%, transport 25.0%, property 10.5%,
  technology 4.7%;
- Beta of 0.32, so it will lag in a strong market rebound;
- Covariance estimation error remains; the 30% shrinkage is a heuristic, not an
  optimum;
- The 1% floor forces small positions in 9988, 1810 and 0700; relative to the
  unconstrained GMV it adds 0.24pp of sample volatility and gives up 0.42pp of in-sample
  expected return;
- It ignores all return information, including strong momentum or valuation signals;
- It is a pure risk-minimisation portfolio, not a return-maximisation portfolio.

These weaknesses are exactly what Weeks 2–4 are designed to address, one layer at a
time.

---

## 9. Next steps: Weeks 2–4

| Week | Method | Purpose |
|---|---|---|
| 2 | **CAPM equilibrium view**: `μ_s = r_f + β_s × premium`, conservative λ ≈ 15 | Move one step up the efficient frontier from GMV; introduce a market view |
| 3 | **Signal view**: 12-week momentum + proximity to the 52-week high + low volatility | Introduce a relative stock view; more stable than sample means |
| 4 | **Adaptive confidence**: pre-registered rule based on cumulative active return vs EW | Adjust the strength of the view, not the model |

The CAPM view is deliberately conservative: on the 30 October data, λ = 15 moves 1398
from 21.2% to 19.6%, 0005 from 13.6% to 10.8%, 1113 from 4.1% to 6.5%, and 0700 from
1.0% to 2.1%. The signal view is stronger: it moves 1398 to 25%, keeps 0066 and 3988 at
25%, raises 1113 to about 7.7%, and pushes 0981/0700 to the 1% floor.

The progression is:

```
GMV (no view) -> CAPM (market view) -> Signal (relative stock view) -> Adaptive (confidence update)
```

This gives the final report a coherent methodological narrative rather than a sequence
of unrelated models.

---

## 10. Reproducibility

```powershell
$env:MKL_THREADING_LAYER = 'SEQUENTIAL'
$py = 'C:\Users\Administrator\miniforge3\envs\dase7310\python.exe'
cd D:\Backup\Documents\dase7310\DASE7310_GP2_Repo

# Refresh raw + hfq prices and HSI/HSTECH
& $py portfolio.py refresh-data --end 2026-10-30

# Build the Week 1 GMV portfolio
& $py portfolio.py build --week 1 --cutoff 2026-10-30 --strategy gmv

# After the trading week ends
& $py portfolio.py evaluate --week 1
```

Key files:

| File | Content |
|---|---|
| `weeks/week1/submission.xlsx` | Moodle-ready submission table |
| `weeks/week1/submission.csv` | Same table as CSV |
| `weeks/week1/portfolio.csv` | Full internal table (prices, weights, capital, shares) |
| `weeks/week1/params.json` | Cutoff, method, parameters, weights |
| `research/covariance_104w.csv` | Annualised 10×10 covariance matrix |
| `research/correlation_104w.csv` | 10×10 correlation matrix |
| `research/gmv_weights.csv` | Unconstrained vs constrained GMV weights and risk contributions |
| `research/shrinkage_sensitivity.csv` | GMV weights across shrinkage intensity |
| `research/backtest_summary.csv` | Strategy performance, full sample and sub-periods |
| `research/benchmark_summary.csv` | Course benchmark comparison (1/N, GMV, tangency, CAPM, HSI) |
| `research/frontier_20261030.csv` | Long-only efficient frontier at the cutoff |
| `research/frontier_points.csv` | Where each method sits vs the frontier |
| `research/two_fund_check.csv` | Two-fund theorem check |
| `BENCHMARKS_ZH.md` | Full mapping of the six course benchmark families and report-ready text |

---

## Appendix A — Formulas

**Covariance matrix.** For weekly returns `r_t` (10×1) with mean `r_bar`:

```
Σ_sample = (1 / (T - 1)) * sum_t (r_t - r_bar)(r_t - r_bar)'
Σ_shrunk = 0.7 * Σ_sample + 0.3 * diag(Σ_sample)
Σ_annual = 52 * Σ_shrunk
```

**GMV, unconstrained:**

```
w = Σ^{-1} 1 / (1' Σ^{-1} 1)
```

**GMV, constrained (our submission):**

```
min_w   w'Σw
s.t.    1'w = 1
        0.01 <= w_s <= 0.25
```

The 1% floor and 25% cap are **implementation constraints**, not part of the theoretical
GMV. Without the floor, the optimizer sets 9988, 1810 and 0700 to zero; the floor keeps
all ten stocks held. The sensitivity table and the cost of the floor are in §3.4.

**Portfolio variance:** `w'Σw`.

**Risk contribution:** `RC_s = w_s * (Σw)_s / (w'Σw)`.

**Week 1 accounting:**

```
c_{s,0} = w_{s,1} * 1,000,000
h_{s,1} = c_{s,0} / p_{s,0}
C_1     = sum_s p_{s,1} * h_{s,1}
R_1     = (C_1 - 1,000,000) / 1,000,000
```

---

## Appendix B — Course references

- Lecture 2: return and risk, diversification, covariance, global minimum variance
  portfolio (two assets and more than two assets).
- Lecture 3: Lagrange multiplier, mean-variance efficient frontier, two-fund theorem,
  Sharpe ratio, tangency portfolio.
- Lecture 4: CAPM, security market line, beta estimation via regression.

---

*This report is an internal Week 1 summary for the group. It is not the final
five-page submission; the final report will integrate Weeks 1–4, the benchmark
comparison, and the performance evaluation.*
