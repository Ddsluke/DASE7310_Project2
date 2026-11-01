# -*- coding: utf-8 -*-
"""GP2 研究 2：组合构建方案的稳健性比较（含子区间、集中度、做空）。

用法: python research_portfolios.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
RESEARCH = HERE / "research"
STOCKS = ["9988", "0066", "1398", "3988", "0981", "0005", "1810", "0016", "1113", "0700"]


def load():
    closes = pd.read_csv(DATA / "weekly_closes.csv", index_col=0, parse_dates=True)[STOCKS]
    return closes, closes.pct_change(fill_method=None)


def zs(s: pd.Series) -> pd.Series:
    sd = s.std()
    return (s - s.mean()) / sd if sd and np.isfinite(sd) and sd > 0 else s * 0


def composite(hist: pd.DataFrame) -> pd.Series:
    """12周动量 + 距52周高点 + 低波动 的等权 z 分数。"""
    mom = hist.tail(12).sum()
    high = -(1 - (1 + hist).cumprod().iloc[-1] / (1 + hist).cumprod().tail(52).max())
    vol = -hist.tail(26).std()
    return (zs(mom) + zs(high) + zs(vol)) / 3


def shrink_cov(hist: pd.DataFrame, win: int = 104, shrink: float = 0.3) -> np.ndarray:
    cov = hist.tail(win).cov().values * 52
    return (1 - shrink) * cov + shrink * np.diag(np.diag(cov))


def w_tilt(hist: pd.DataFrame, te_target: float, lo: float, hi: float,
           signal: pd.Series | None = None) -> pd.Series:
    sig = composite(hist) if signal is None else signal
    n = len(STOCKS)
    d = sig.values / n
    cov = shrink_cov(hist)
    te = float(np.sqrt(d @ cov @ d))
    scale = te_target / te if te > 0 else 0.0
    w = 1.0 / n + scale * d
    return pd.Series(np.clip(w, lo, hi) / np.clip(w, lo, hi).sum(), index=STOCKS)


def w_topk(hist: pd.DataFrame, k: int = 4, core: float = 0.5) -> pd.Series:
    sig = composite(hist)
    top = sig.nlargest(k).index
    w = pd.Series(core / len(STOCKS), index=STOCKS)
    w[top] += (1 - core) / k
    return w


def w_gmv(hist: pd.DataFrame, win: int = 52, shrink: float = 0.3) -> pd.Series:
    inv = np.linalg.pinv(shrink_cov(hist, win, shrink))
    one = np.ones(len(STOCKS))
    w = inv @ one / (one @ inv @ one)
    return pd.Series(np.clip(w, -0.3, 0.5), index=STOCKS)


def w_tangency(hist: pd.DataFrame, win: int = 104, shrink: float = 0.3) -> pd.Series:
    mu = hist.tail(win).mean().values * 52
    inv = np.linalg.pinv(shrink_cov(hist, win, shrink))
    w = inv @ mu
    w = w / np.abs(w).sum()
    return pd.Series(np.clip(w, -0.5, 1.0), index=STOCKS)


def run(closes: pd.DataFrame, returns: pd.DataFrame, start: str, end: str) -> pd.DataFrame:
    rows = []
    for dt in returns.loc[start:end].index:
        hist = returns.loc[:dt].iloc[:-1]
        if len(hist) < 60:
            continue
        fwd = returns.loc[dt]
        if fwd.isna().any():
            continue
        cand = {
            "EW": pd.Series(1 / 10, index=STOCKS),
            "GMV52": w_gmv(hist),
            "Tangency": w_tangency(hist),
            "Tilt_te5_longonly": w_tilt(hist, 0.05, 0.0, 0.35),
            "Tilt_te10_longonly": w_tilt(hist, 0.10, 0.0, 0.40),
            "Tilt_te15_longonly": w_tilt(hist, 0.15, 0.0, 0.50),
            "Tilt_te10_shorts": w_tilt(hist, 0.10, -0.15, 0.40),
            "Top4_50core": w_topk(hist, 4, 0.5),
            "Top4_20core": w_topk(hist, 4, 0.2),
        }
        for name, w in cand.items():
            rows.append({"date": dt, "strategy": name, "ret": float(w.values @ fwd.values)})
    return pd.DataFrame(rows)


def summarize(bt: pd.DataFrame, start: str) -> pd.DataFrame:
    rows = []
    for name, g in bt.groupby("strategy"):
        r = g.set_index("date")["ret"]
        nav = (1 + r).cumprod()
        dd = (nav / nav.cummax() - 1).min()
        rows.append({
            "strategy": name, "weeks": len(r),
            "ann_ret%": (nav.iloc[-1] ** (52 / len(r)) - 1) * 100,
            "ann_vol%": r.std() * np.sqrt(52) * 100,
            "sharpe": r.mean() / r.std() * np.sqrt(52),
            "max_dd%": dd * 100, "worst_wk%": r.min() * 100,
            "hit%": (r > 0).mean() * 100, "cum%": (nav.iloc[-1] - 1) * 100,
            "start": start,
        })
    return pd.DataFrame(rows)


def main():
    closes, returns = load()
    RESEARCH.mkdir(exist_ok=True)
    all_sum = []
    for start, end, label in [("2021-01-08", "2026-10-30", "full"),
                              ("2021-01-08", "2023-12-29", "2021-23"),
                              ("2024-01-05", "2026-10-30", "2024-26")]:
        bt = run(closes, returns, start, end)
        s = summarize(bt, label)
        all_sum.append(s)
        print(f"\n=== {label} ({start} ~ {end}) ===")
        print(s.drop(columns="start").round(2).sort_values("sharpe", ascending=False).to_string(index=False))
    out = pd.concat(all_sum, ignore_index=True)
    out.to_csv(RESEARCH / "portfolio_comparison.csv", index=False)
    print("\nsaved", RESEARCH / "portfolio_comparison.csv")

    # 当前最新信号与候选权重
    hist = returns.dropna()
    print("\n=== Latest composite z (as of", hist.index[-1].date(), ") ===")
    print(composite(hist).round(2).to_string())
    print("\n=== Candidate weights for week 1 ===")
    cand = {
        "EW": pd.Series(1 / 10, index=STOCKS),
        "GMV52": w_gmv(hist),
        "Tangency": w_tangency(hist),
        "Tilt_te5_longonly": w_tilt(hist, 0.05, 0.0, 0.35),
        "Tilt_te10_longonly": w_tilt(hist, 0.10, 0.0, 0.40),
        "Tilt_te15_longonly": w_tilt(hist, 0.15, 0.0, 0.50),
        "Tilt_te10_shorts": w_tilt(hist, 0.10, -0.15, 0.40),
        "Top4_50core": w_topk(hist, 4, 0.5),
        "Top4_20core": w_topk(hist, 4, 0.2),
    }
    print(pd.DataFrame(cand).round(3).to_string())


if __name__ == "__main__":
    main()
