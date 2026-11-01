# DASE7310 GP2 — Portfolio Construction & Weekly Rebalancing

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
GMV_EXPLAINED_ZH.md           Chinese explainer: covariance matrix and GMV
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
- Backtest (2021–2026, weekly, gross): 8.39% p.a., 8.41% vol, Sharpe 1.00, max DD
  −11.3%; 4-week 5th percentile −3.1%. It beat EW in the weak 2021–23 period
  (+3.7% vs +1.2%) but lagged in the 2024–26 rally (+17.0% vs +18.1%).

### Week 2 — Mean–variance efficient frontier with shrunk means
- Lecture 3: move up from GMV along the frontier.
- `mu_shrunk = 0.5 * sample_mean + 0.5 * grand_mean` (shrinkage toward the
  cross-sectional average), same covariance and constraints, target vol ~11–12%.
- Compare with GMV and EW on the first realised week before adopting.

### Week 3 — Signal-based expected return
- Replace the sample mean with a robust composite signal: 12-week momentum +
  distance from the 52-week high + low volatility (equal-weight z-scores).
- Still long-only, same floor/cap. The composite has a positive rank IC in every
  year of the sample (near-high IC 0.09, t ≈ 3.3), unlike raw sample means.

### Week 4 — Adaptive rule
- Pre-registered: if cumulative active return vs EW is below −5pp at a rebalance,
  cut the tilt multiplier `k` to 1.0 (shrink toward EW/GMV); otherwise keep it.
- Record the decision and its reason in `params.json`.

`k` (used by the `tilt` strategy) is the **active-bet multiplier**, not leverage:
start from EW, scale every deviation from EW by `k`, keep `sum w = 1`. With
`k = 1` the tilt is the base 10% tracking-error tilt; `k = 2` doubles the active
positions; `k = 3` triples them. In the current long-only implementation, negative
tilts are clipped to zero, so large `k` mainly increases concentration.

---

## 6. Benchmark set for the report

| Benchmark | Course link | Why include |
|---|---|---|
| Equal weight (1/10) | Lecture 2 diversification | The naive portfolio every group can replicate |
| GMV (long-only) | Lecture 2/3 | Risk-only portfolio; our week-1 starting point |
| Tangency / max Sharpe | Lecture 3 | Uses sample means; shows estimation error |
| Top-4 momentum | — | Concentrated version of the signal |
| Signal tilt (k = 1/2/3) | Lecture 3 + robust μ | Our proposed evolution |

Backtest table (`research/backtest_summary.csv`, 2021-01 → 2026-10, weekly, gross):

| Strategy | Ann. ret | Ann. vol | Sharpe | Max DD | Active vs EW | 4w p05 |
|---|---:|---:|---:|---:|---:|---:|
| GMV | 8.39% | 8.41% | 1.00 | −11.3% | +1.93% | −3.1% |
| Tilt k=1 | 8.12% | 12.19% | 0.70 | −19.6% | +2.07% | −4.6% |
| Tilt k=2 | 10.79% | 11.92% | 0.92 | −15.0% | +4.48% | −4.2% |
| Tilt k=3 | 11.47% | 11.92% | 0.97 | −13.5% | +5.09% | −4.2% |
| Top-4 | 9.90% | 13.41% | 0.77 | −23.2% | +3.86% | −4.6% |
| Tangency | 4.64% | 12.82% | 0.42 | −31.5% | −1.12% | −5.6% |
| Equal weight | 5.31% | 16.23% | 0.40 | −33.0% | 0 | −6.2% |

The 2024–26 sub-period is a strong bull market; 2021–23 is weak. GMV is the most
stable across both (Sharpe 0.50 / 1.76), which is why it is the week-1 anchor. The
tilt strategies have higher full-sample returns but rely on the recent regime.

---

## 7. Report / presentation material already collected

- Method evolution chain: EW → GMV → shrunk-mean MV → signal tilt → adaptive rule.
- Signal IC by year (`research/scan_ic.csv`): momentum and near-52-week-high are
  positive in most years; 1-week reversal is not a reliable signal.
- The 0981 (SMIC) case: 46–57% annualised vol, −32% in the four weeks to 30 Oct 2026.
  Any portfolio that overweights it bears a large idiosyncratic risk; GMV gives it
  only 1.7%.
- Estimation error: the unconstrained tangency portfolio has a −31.5% max drawdown
  and is the worst benchmark, a direct illustration of why shrinking means matters.
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
