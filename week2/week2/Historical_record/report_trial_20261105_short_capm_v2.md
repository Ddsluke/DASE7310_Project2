# Week 2 portfolio snapshot

> **TRIAL ONLY - DO NOT SUBMIT.** This run uses the last available data before the `2026-11-06` cutoff.

- Cutoff (valuation date): **2026-11-06** (Friday close)
- Actual price date used: **2026-10-30**
- Trading week: **2026-11-06 -> 2026-11-13**
- Strategy: `capm`
- Capital at start: **HKD 1,000,000.00**
- Sum of weights: 1.000000; gross exposure: 1.0696; shorts: 2
- Variant: `trial_20261105_short_capm_v2`; reason: 执行日为2026-11-05，早于11-06截点；仅使用截至2026-10-30的最后一个完整周五收盘做试运行；按教授要求允许做空并用[-15%,40%]；v2将提交表六位权重调平为1。

## Submission table

| Code | Name | Price (HKD) | Weight | Capital (HKD) | Shares |
|---|---|---:|---:|---:|---:|
| 9988 | Alibaba Group Holding | 97.0500 | -2.6234% | -26,233.76 | -270.311783 |
| 0066 | MTR Corporation | 33.3200 | 38.2446% | 382,445.64 | 11477.960503 |
| 1398 | ICBC | 7.8950 | 14.2320% | 142,320.40 | 18026.650109 |
| 3988 | Bank of China | 6.1450 | 25.9262% | 259,262.20 | 42190.756772 |
| 0981 | SMIC | 42.9800 | 3.2027% | 32,027.39 | 745.169679 |
| 0005 | HSBC Holdings | 135.7000 | 7.7979% | 77,978.59 | 574.639595 |
| 1810 | Xiaomi Group-W | 26.4800 | -0.8588% | -8,587.68 | -324.308101 |
| 0016 | Sun Hung Kai Properties | 108.9000 | 3.8191% | 38,190.99 | 350.697787 |
| 1113 | CK Asset Holdings | 46.1600 | 4.6262% | 46,262.22 | 1002.214402 |
| 0700 | Tencent Holdings | 383.6000 | 5.6334% | 56,334.00 | 146.856092 |

Notes: shares follow the course formula `h = c / p` (fractional shares; no board-lot rounding).
`capital_check` in `portfolio.csv` uses the rounded shares and is the internally consistent value.
