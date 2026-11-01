# DASE7310 GP2 — Portfolio Construction & Weekly Rebalancing

> **中文版 / Chinese version:** [README.md](README.md)

**Remote:** https://github.com/Ddsluke/DASE7310_Project2

**Documentation:** [中文主 README](README.md) · [Team playbook](TEAM_GUIDANCE_ZH.md) ·
[Course benchmarks](BENCHMARKS_ZH.md) · [Week 2 guide](WEEK2_GUIDANCE_ZH.md) ·
[Week 3 guide](WEEK3_GUIDANCE_ZH.md) · [Week 1 report](WEEK1_REPORT_EN.md)

Group Project II: invest **HKD 1,000,000** across the same 10 HKEX stocks used in GP1,
over the four trading weeks **2–27 November 2026**. Long-only by group choice; weekly
rebalancing with at most **three adjustments**.

This repo is the single source of truth for the portfolio snapshots, the research
evidence, and the weekly ledger. Snapshots are **append-only**: never overwrite a
submitted week; add a new file / variant instead.

---

## 1. Rules (from `Group-Project-2_2026.pdf`, dated 26 Oct 2026)

| Item | Value |
|---|---|
| Stock pool | 9988, 0066, 1398, 3988, 0981, 0005, 1810, 0016, 1113, 0700 |
| Initial capital | HKD 1,000,000, fully allocated (`sum_s w_s = 1`) |
| Short selling | Permitted by the project; **not used by this group** |
| Holding period | Buy-and-hold within each trading week |
| Rebalancing | Before each new week, max **3 adjustments** total (weeks 2, 3, 4) |
| Trading weeks | Nov 2–6, Nov 9–13, Nov 16–20, Nov 23–27 |
| Submission deadlines | **Nov 1, Nov 8, Nov 15, Nov 22** (Sun 23:59, HK time) |
| Report + peer eval | **Nov 30** (5 pages, excluding cover/TOC) |
| Oral presentation | **Nov 23 and Nov 30** (10 min, covers GP1 + GP2) |
| Grading | Weekly ranking 30%, presentation & participation 30%, report 20%, peer 20% |

Formulas used for every snapshot:

```
w_{s,i} = c_{s,i-1} / C_{i-1}
h_{s,i} = c_{s,i-1} / p_{s,i-1}
C_i     = sum_s p_{s,i} * h_{s,i}
R_i     = (C_i - C_{i-1}) / C_{i-1}
```

> **Date discrepancy:** the Lecture 1 syllabus still says "five weeks, Oct 26 – Nov 29,
> five adjustments". The official GP2 PDF (26 Oct) says four weeks, Nov 2–27, three
> adjustments, and the PDF's Table 1 is the authoritative submission list. This repo
> follows the PDF. Confirm with the instructor/TA if in doubt.

---

## 2. Data convention (important)

| Purpose | Price series | Why |
|---|---|---|
| Signals, covariance, backtest returns | **hfq** (后复权) | Total-return series; corporate actions removed |
| Share count `h = c / p` and capital `C = p*h` | **raw** (未复权真实收盘价) | The course's `p` is the actual market close; adjusted prices are not tradeable |

Using hfq prices for share counts would be badly wrong: e.g. HSBC's hfq price is
952.05 while its actual close is 135.70 (a 7× difference), and SMIC's hfq price is
4.298 vs an actual 42.98.

Weekly prices are the last realised close of each **W-FRI** week. The valuation date
for week *i* is the Friday before it starts:

| Week | Valuation date (cutoff) | Trading week |
|---|---|---|
| 1 | 2026-10-30 | 2026-11-02 → 2026-11-06 |
| 2 | 2026-11-06 | 2026-11-09 → 2026-11-13 |
| 3 | 2026-11-13 | 2026-11-16 → 2026-11-20 |
| 4 | 2026-11-20 | 2026-11-23 → 2026-11-27 |

Shares are computed by the course formula and kept to 6 decimals. The formula allows
fractional shares; board-lot rounding would leave capital uninvested and violate the
"fully allocated" requirement. `integer_lots` is shown for reference only.

---

## 3. Repo layout

```
portfolio.py                  single pipeline: refresh-data / build / evaluate
research_scan.py              signal IC, correlation, first strategy scan
research_portfolios.py        tilt / top-k / GMV comparison
research_backtest.py          walk-forward backtest of all production strategies
research_gmv.py               covariance matrix + GMV step-by-step (teaching/repro)
research_views.py             from no-view GMV to mean-variance views (CAPM / signal)
research_benchmarks.py        course benchmark comparison, frontier, two-fund check
GUIDE_ZH.md                   Chinese Week 1 action guide
TEAM_GUIDANCE_ZH.md           full team playbook (rules, workflow, benchmarks, roles)
BENCHMARKS_ZH.md              course benchmark mapping and comparison
WEEK1_REPORT_EN.md            English Week 1 report (internal, not the final submission)
WEEK2_GUIDANCE_ZH.md          Week 2 guide: CAPM equilibrium view
WEEK3_GUIDANCE_ZH.md          Week 3 guide: signal view
GMV_EXPLAINED_ZH.md           Chinese explainer: covariance matrix and GMV
VIEWS_EXPLAINED_ZH.md         Chinese explainer: how to express views in weeks 2-4
data/
  daily_closes_raw.csv        unadjusted daily closes (accounting)
  daily_closes_hfq.csv        adjusted daily closes (signals)
  weekly_closes_raw.csv       Friday closes, raw
  weekly_closes_hfq.csv       Friday closes, hfq
  weekly_returns_hfq.csv      weekly total returns
  index_closes.csv            HSI / HSTECH
  meta.json                   vintage, source, last data date
weeks/weekN/
  submission.xlsx             Moodle-ready: Summary / Submission / Details / Notes
  submission.csv              same table as CSV
  portfolio.csv               full internal table (prices, weights, capital, shares)
  params.json                 cutoff, method, parameters, weights, capital
  report.md                   human-readable snapshot
  realized.csv                appended after the week ends (never edits predictions)
  realized_summary.json       weekly return, EW benchmark, active return
research/
  scan_ic.csv                 cross-sectional rank IC of candidate signals
  covariance_104w.csv         annualised 10x10 covariance matrix (shrunk)
  correlation_104w.csv        10x10 correlation matrix
  gmv_weights.csv             unconstrained vs constrained GMV weights + risk contributions
  shrinkage_sensitivity.csv   GMV weights across shrinkage intensity (0-100%)
  views_frontier.csv          weights for sample-mean / CAPM / signal views at several lambda
  benchmark_summary.csv       course benchmark performance (1/N, GMV, tangency, CAPM, HSI)
  benchmark_4w_distribution.csv
  benchmark_final_weights.csv
  frontier_20261030.csv       long-only efficient frontier at the final cutoff
  frontier_points.csv         where each method sits vs the frontier
  two_fund_check.csv          two-fund theorem check
  backtest_summary.csv        full / 2021-23 / 2024-26 performance by strategy
  backtest_4w_distribution.csv rolling 4-week return distribution
  week1_variants/             week-1 alternatives (EW, GMV, tilt k=1/3, top4)
ledger.md                     append-only weekly record of realised returns
```

---

## 4. Weekly workflow

```powershell
$env:MKL_THREADING_LAYER = 'SEQUENTIAL'
$py = 'C:\Users\Administrator\miniforge3\envs\dase7310\python.exe'

# 0) Friday after close: refresh both raw and hfq prices
& $py portfolio.py refresh-data --end 2026-11-06

# 1) Build the next week's portfolio (uses previous week's submitted shares for C_{i-1})
& $py portfolio.py build --week 2 --cutoff 2026-11-06 --strategy gmv

# 2) Check the snapshot, then upload weeks/week2/submission.xlsx to Moodle
#    Checklist: cutoff correct, 10 stocks, sum weights = 1, C matches, shares = c/p

# 3) After the trading week ends: record realised values (append-only)
& $py portfolio.py evaluate --week 1
```

The `build` command for week *N* reads `weeks/week{N-1}/portfolio.csv` and values the
submitted shares at the new cutoff, so `C_{i-1}` is the actual remaining capital, not
the initial 1,000,000.

---

## 5. Method roadmap (deliberate, course-aligned progression)

The project asks the method to **evolve based on realised weekly performance**. We
start from the simplest result in the course and add one layer per week.

### Week 1 — Global Minimum Variance (GMV), long-only
- Lecture 2/3: `min w'Σw  s.t. 1'w = 1`.
- Only the covariance matrix is estimated; **no expected returns**. This is deliberate:
  GP1 showed weekly mean returns are essentially unpredictable, and sample means make
  Markowitz weights unstable.
- 104-week covariance, 30% shrinkage to diagonal, single-name floor 1% / cap 25%,
  long-only. All 10 stocks are held.
- Backtest (2021–2026, weekly, gross): 8.39% p.a., 8.41% vol, Sharpe 0.76
  (course definition, `r_f = 2%`), max DD −11.3%; 4-week 5th percentile −3.1%.
  It beat EW in the weak 2021–23 period (+3.7% vs +1.2%) but lagged in the 2024–26
  rally (+17.0% vs +18.1%).

### Week 2 — CAPM equilibrium view (Lecture 4)
- Lecture 4: `mu_s = r_f + beta_s * market_premium`; beta estimated by regression on HSI.
- This is a **market view** (high-beta stocks should earn more), not a stock-picking view.
- Use a conservative risk aversion (`lambda` large) or a 9–10% vol target, so the
  portfolio moves only slightly up the frontier from GMV.
- Note: shrinking all means toward the grand mean is just adding a constant; because
  `1'w = 1`, it does **not** change the optimal weights. Meaningful shrinkage must be
  toward zero, toward CAPM, or via Black–Litterman.
- Compare GMV, CAPM and EW on the first realised week before adopting.

### Week 3 — Signal-based relative view
- Replace the equilibrium mean with a robust composite signal: 12-week momentum +
  distance from the 52-week high + low volatility (equal-weight z-scores).
- This is a **relative stock view**: overweight the high-score names, underweight the
  low-score names. Still long-only, same floor/cap, 10–12% vol target.
- The composite has a positive rank IC in every year of the sample (near-high IC 0.09,
  t ≈ 3.3), unlike raw sample means. The sample-mean view would put 25% in SMIC (0981)
  because of its 41% historical mean; the signal view keeps it at 1%.

### Week 4 — Adaptive view confidence
- Pre-registered: if cumulative active return vs EW is below −5pp at a rebalance,
  cut the view strength (raise `lambda` / lower the vol target) back toward GMV;
  if above +5pp, keep the view but do not add leverage.
- Record the decision and its reason in `params.json`.

`k` (used by the `tilt` strategy) is the **active-bet multiplier**, not leverage:
start from EW, scale every deviation from EW by `k`, keep `sum w = 1`. With
`k = 1` the tilt is the base 10% tracking-error tilt; `k = 2` doubles the active
positions; `k = 3` triples them. In the current long-only implementation, negative
tilts are clipped to zero, so large `k` mainly increases concentration.

---

## 6. Benchmark set for the report

The project brief asks for a comparison with **the benchmark methods covered in class**.
Lectures 2–4 define six benchmark families (full mapping, formulas and report-ready text
in `BENCHMARKS_ZH.md`):

| # | Benchmark | Course | Our implementation |
|---|---|---|---|
| 1 | Equal weight (1/N) | Lecture 2 | `EW` |
| 2 | Global minimum variance | Lecture 2/3 | `GMV_uncon` (formula) / `GMV_con` (long-only 1–25%) |
| 3 | Mean-variance efficient frontier | Lecture 3 | `frontier_20261030.csv`, `frontier_points.csv` |
| 4 | Tangency / max Sharpe | Lecture 3 | `Tangency_uncon_cap2` (gross ≤ 2) / `Tangency_con` |
| 5 | Two-fund theorem | Lecture 3 | `two_fund_check.csv` |
| 6 | CAPM / SML / market portfolio | Lecture 4 | `CAPM_con`, `Market_HSI` |

Main table (`research/benchmark_summary.csv`, 2021-01 → 2026-10, weekly, gross,
Sharpe with `r_f = 2%`):

| Method | Course link | Ann. ret | Ann. vol | Sharpe | Max DD | Active vs EW |
|---|---|---:|---:|---:|---:|---:|
| **Signal (proposed)** | characteristic view | **8.70%** | **8.41%** | **0.80** | **−11.6%** | **+2.22%** |
| GMV_uncon | Lecture 2/3 formula | 8.13% | 7.89% | 0.78 | −10.7% | +1.65% |
| GMV_con | Lecture 2/3 + constraints | 8.39% | 8.41% | 0.76 | −11.3% | +1.93% |
| Tilt k=2 | direct signal tilt | 10.79% | 11.92% | 0.74 | −15.0% | +4.48% |
| CAPM_con | Lecture 4 CAPM/SML | 8.03% | 8.50% | 0.71 | −12.5% | +1.61% |
| Top-4 | concentrated signal | 9.90% | 13.41% | 0.59 | −23.2% | +3.86% |
| Tangency_uncon_cap2 | Lecture 3 + gross ≤ 2 | 10.44% | 14.71% | 0.57 | −27.3% | +4.53% |
| Tangency_con | Lecture 3 + constraints | 8.26% | 14.25% | 0.44 | −30.3% | +2.48% |
| Equal weight | Lecture 2, 1/N | 5.31% | 16.23% | 0.20 | −33.0% | 0 |
| Market (HSI) | Lecture 4 market proxy | −3.76% | 22.25% | −0.26 | −49.3% | −7.85% |

> `Tangency_con` is clipped but still allows small short positions
> (`w ∈ [−10%, 40%]`), so it is not directly comparable with the long-only frontier.

Two additional course-linked checks:

- **Efficient frontier** (`research/frontier_points.csv`, in-sample 104w): GMV_con is
  0.10pp below the frontier, Signal_con 0.22pp, CAPM_con 0.50pp, while EW is 7.38pp
  below. The tangency portfolios are on the frontier within 0.2pp grid error.
- **Two-fund theorem** (`research/two_fund_check.csv`): the L1 weight distance from the
  GMV–tangency span is 0.046 for GMV_con, 0.104 for CAPM_con, 0.174 for Signal_con, and
  0.897 for EW. The theorem is exact only without constraints; our implementation is
  long-only with caps, so this is an approximate check.

> The raw unconstrained tangency formula `Σ⁻¹(μ − r_f)` is **not implementable** with
> sample means: average gross 34.8, 363.7% annualised volatility, −652% worst week. It is
> kept as a diagnostic in `research/benchmark_diagnostics.csv` and is the clearest
> illustration of why the Week 1 portfolio starts from GMV rather than from sample means.

---

## 7. Report / presentation material already collected

- Method evolution chain: GMV (no view) → CAPM (market view) → signal (relative view) →
  adaptive (confidence update).
- Signal IC by year (`research/scan_ic.csv`): momentum and near-52-week-high are
  positive in most years; 1-week reversal is not a reliable signal.
- The 0981 (SMIC) case: 46–57% annualised vol, −32% in the four weeks to 30 Oct 2026.
  Any portfolio that overweights it bears a large idiosyncratic risk; GMV gives it
  only 1.7%.
- Estimation error: the raw unconstrained tangency formula has average gross 34.8,
  363.7% annualised volatility and a −652% worst week; even the constrained version has
  a −30.3% max drawdown. This is the clearest illustration of why shrinking means and
  imposing constraints matters.
- Regime dependence: 2021–23 vs 2024–26 rankings flip for several strategies; a
  single 20-week window would overstate progress (the same lesson as GP1).

---

## 8. Environment

```powershell
$env:MKL_THREADING_LAYER = 'SEQUENTIAL'   # required before any sklearn/scipy fit on this machine
$py = 'C:\Users\Administrator\miniforge3\envs\dase7310\python.exe'
```

Python 3.12, pandas 3.0.6, numpy 2.5.3, scipy 1.18.1, akshare 1.19.1,
scikit-learn 1.9.1, openpyxl. Data source: Sina Finance via AkShare (Eastmoney is
blocked on this network; the pipeline falls back batch-wise).
