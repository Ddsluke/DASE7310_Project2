# Week 2 portfolio snapshot

> **Submission status:** READY FOR MANUAL REVIEW

- Cutoff (valuation date): **2026-11-06** (Friday close)
- Actual price date used: **2026-11-06**
- Trading week: **2026-11-06 -> 2026-11-13**
- Strategy: `capm`
- Parameters: lambda = **15.0**; bounds = **[-15%, 30%]**; `r_f` = **2.00%**; market premium = **5.00%**
- Capital at start: **HKD 1,021,677.17**
- Sum of weights: 1.000000; gross exposure: 1.0716; shorts: 2
- Ex-ante annualised volatility: **7.52%** (shrunk covariance); **8.18%** (sample covariance)
- Variant: `cap30_20261108_final`; reason: cap=0.30最终同步版本：更新权重、资本、股数、风险指标、参数和核对输出；保留cap40历史归档及先前cap30构建。

## Submission table

| Code | Name | Price (HKD) | Weight | Capital (HKD) | Shares |
|---|---|---:|---:|---:|---:|
| 9988 | Alibaba Group Holding | 104.9000 | -2.5443% | -25,994.33 | -247.801083 |
| 0066 | MTR Corporation | 34.3000 | 30.0000% | 306,503.15 | 8935.951917 |
| 1398 | ICBC | 7.9500 | 16.5365% | 168,949.29 | 21251.482715 |
| 3988 | Bank of China | 6.1200 | 28.3734% | 289,884.73 | 47366.785333 |
| 0981 | SMIC | 45.5800 | 3.1095% | 31,769.16 | 696.997755 |
| 0005 | HSBC Holdings | 137.5000 | 9.9220% | 101,370.70 | 737.241434 |
| 1810 | Xiaomi Group-W | 30.3800 | -1.0339% | -10,563.01 | -347.696246 |
| 0016 | Sun Hung Kai Properties | 117.7000 | 5.0152% | 51,239.36 | 435.338675 |
| 1113 | CK Asset Holdings | 49.1200 | 5.6726% | 57,955.50 | 1179.875898 |
| 0700 | Tencent Holdings | 419.8000 | 4.9490% | 50,562.63 | 120.444570 |

Notes: shares follow the course formula `h = c / p` (fractional shares; no board-lot rounding).
`capital_check` in `portfolio.csv` uses the rounded shares and is the internally consistent value.
