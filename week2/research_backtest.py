# -*- coding: utf-8 -*-
"""GP2 回测：生产函数的 walk-forward 比较（周频再平衡，无交易成本）。

用法: python research_backtest.py
输出: research/backtest_summary.csv, research/backtest_weekly.csv
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

import portfolio as gp

HERE = Path(__file__).resolve().parent
RESEARCH = HERE / "research"
STRATS = {
    "EW": dict(strategy="ew"),
    "GMV": dict(strategy="gmv"),
    "Tangency": dict(strategy="tangency"),
    "Top4": dict(strategy="top4"),
    "Tilt_k1": dict(strategy="tilt", k=1.0),
    "Tilt_k2": dict(strategy="tilt", k=2.0),
    "Tilt_k3": dict(strategy="tilt", k=3.0),
}


def main():
    raw, hfq, ret, idx, meta = gp.load_data()
    ret = ret.dropna(how="all")
    rows = []
    for dt in ret.loc["2021-01-08":].index:
        hist = ret.loc[:dt].iloc[:-1]
        if len(hist) < 60:
            continue
        fwd = ret.loc[dt]
        if fwd.isna().any():
            continue
        for name, kw in STRATS.items():
            w, _ = gp.target_weights(hist, **kw)
            rows.append({"date": dt, "strategy": name, "ret": float(w.values @ fwd.values),
                         "gross": float(w.abs().sum())})
    bt = pd.DataFrame(rows)
    bt.to_csv(RESEARCH / "backtest_weekly.csv", index=False)

    out = []
    for name, g in bt.groupby("strategy"):
        for label, start, end in [("full", "2021", "2027"), ("2021-23", "2021", "2024"),
                                  ("2024-26", "2024", "2027")]:
            x = g.set_index("date")["ret"].loc[start:end]
            nav = (1 + x).cumprod()
            ew = bt[(bt.strategy == "EW")].set_index("date")["ret"].loc[x.index]
            active = x - ew
            out.append({
                "strategy": name, "period": label, "weeks": len(x),
                "ann_ret%": (nav.iloc[-1] ** (52 / len(x)) - 1) * 100,
                "ann_vol%": x.std() * np.sqrt(52) * 100,
                "sharpe": x.mean() / x.std() * np.sqrt(52),
                "max_dd%": (nav / nav.cummax() - 1).min() * 100,
                "active_ann%": active.mean() * 52 * 100,
                "ir": active.mean() / active.std() * np.sqrt(52) if active.std() > 0 else np.nan,
                "excess_hit%": (active > 0).mean() * 100,
                "gross": g["gross"].mean(),
            })
    s = pd.DataFrame(out)
    s.to_csv(RESEARCH / "backtest_summary.csv", index=False)
    for period in ["full", "2021-23", "2024-26"]:
        print(f"\n=== {period} ===")
        print(s[s.period == period].drop(columns="period").round(2)
              .sort_values("sharpe", ascending=False).to_string(index=False))

    # 4-week cumulative distribution (overlapping), full sample
    print("\n=== Rolling 4-week cumulative return distribution (full 2021-26) ===")
    wide = bt.pivot(index="date", columns="strategy", values="ret")
    r4 = (1 + wide).rolling(4).apply(lambda a: np.prod(a) - 1).dropna()
    dist = pd.DataFrame({
        "median%": r4.median() * 100, "p05%": r4.quantile(.05) * 100,
        "p95%": r4.quantile(.95) * 100, "P(<0)%": (r4 < 0).mean() * 100,
        "P(<-5)%": (r4 < -0.05).mean() * 100, "P(>+5)%": (r4 > 0.05).mean() * 100,
    }).sort_values("median%", ascending=False)
    print(dist.round(2).to_string())
    dist.to_csv(RESEARCH / "backtest_4w_distribution.csv")


if __name__ == "__main__":
    main()
