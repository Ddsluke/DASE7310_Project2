# Week 1 revision candidates — 2026-11-04

**Context:** the instructor reopened the Week 1 submission because of a table-format
issue. The group has decided to enable short selling from **Week 2** (explicitly
permitted by the project brief, p.1: “short positions are permitted”).

**Hard rule:** every candidate below uses **data through 2026-10-30 only**. The realised
returns of 2–4 November are **not** used to choose weights. Using them would be
look-ahead bias: the Week 1 portfolio was due on 1 November, before the trading week.

## Files

| File | What it is | Use |
|---|---|---|
| `submission_longonly_onesheet.xlsx` | original long-only GMV, one-sheet format | **Path A**: format-only fix (recommended) |
| `submission_short_gmv_onesheet.xlsx` | short-enabled GMV, floor −15% / cap 30%, one-sheet | **Path B**: strategy revision, if explicitly allowed |
| `submission_short_capm.xlsx` | short-enabled CAPM (λ=15, floor −15% / cap 40%) | alternative |
| `submission_short_signal.xlsx` | short-enabled signal (λ=8, floor −15% / cap 40%) | alternative |
| `submission_short_gmv.xlsx` | short-enabled GMV, multi-sheet version | internal |

## Short-enabled GMV weights (Oct 30 data)

| Code | Weight |
|---|---:|
| 9988 | −3.58% |
| 0066 | +30.00% |
| 1398 | +17.46% |
| 3988 | +30.00% |
| 0981 | +2.68% |
| 0005 | +12.86% |
| 1810 | −1.70% |
| 0016 | +5.49% |
| 1113 | +4.17% |
| 0700 | +2.61% |
| **Total** | **100%** (gross 1.11, 2 shorts) |

## Post-hoc check (2–4 Nov, for evaluation only — not for selection)

| Portfolio | Return 30 Oct → 4 Nov |
|---|---:|
| Original long-only GMV (submitted) | **−0.13%** |
| Short-enabled GMV (−15%/30%) | −0.52% |
| Short-enabled CAPM (−15%/40%) | −0.10% |
| Short-enabled signal (−15%/40%) | −1.34% |

Banks fell (1398 −0.95%, 3988 −3.34%) while technology rallied (9988 +3.66%, 0981 +8.05%,
1810 +8.61%, 0700 +4.69%). The short-enabled GMV is long banks / short technology, so it
would have done **worse** this week. The only way to “fit” the week would be to go long
technology / short banks — which is pure hindsight and is not a valid Week 1 decision.

## Decision (2026-11-04)

- **Week 1:** keep the original long-only GMV weights; only the table format is fixed.
  No weights were changed. `submission.xlsx` is the one-sheet format; the original
  multi-sheet file is `submission_multisheet.xlsx`.
- **Week 2 onward:** use the short-selling permission with floor −15% / cap 30%; the
  first short-enabled portfolio is built at the **2026-11-06** cutoff.
- The 2–4 November returns are post-hoc evaluation only; they are **not** used for any
  Week 1 weight.
- **Not allowed:** choose Week 1 weights using 2–4 November returns.
