# -*- coding: utf-8 -*-
"""GP2 研究：信号 IC、相关结构、课程 benchmark 的滚动表现。

用法: python research_scan.py [cutoff]
输出: research/scan_ic.csv, research/scan_portfolios.csv, 控制台摘要
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE
DATA = ROOT / "data"
RESEARCH = ROOT / "research"

STOCKS = ["9988", "0066", "1398", "3988", "0981", "0005", "1810", "0016", "1113", "0700"]


def load():
    closes = pd.read_csv(DATA / "weekly_closes.csv", index_col=0, parse_dates=True)[STOCKS]
    returns = closes.pct_change(fill_method=None)
    idx = None
    p = DATA / "index_returns.csv"
    if p.exists():
        idx = pd.read_csv(p, index_col=0, parse_dates=True)
    return closes, returns, idx


def signals(returns: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Each signal is known at end of week t (uses data up to t); target is return t+1."""
    out = {}
    out["rev1"] = -returns                                   # short-term reversal
    out["mom4"] = returns.rolling(4).sum()                   # 1-month momentum
    out["mom12"] = returns.rolling(12).sum()                 # 3-month momentum
    out["mom26"] = returns.rolling(26).sum()                 # 6-month momentum
    out["mom52"] = returns.rolling(52).sum()                 # 12-month momentum
    out["mom12_1"] = returns.shift(4).rolling(8).sum()       # 12-1 style
    out["lowvol"] = -returns.rolling(26).std()               # low volatility
    out["nearhigh"] = -(1 - returns.add(1).cumprod()
                        / returns.add(1).cumprod().rolling(52).max())  # distance from 52w high
    return out


def ic_table(returns: pd.DataFrame, sigs: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    fwd = returns.shift(-1)
    for name, s in sigs.items():
        # cross-sectional Spearman rank IC per week
        ic = s.corrwith(fwd, axis=1, method="spearman").dropna()
        rows.append({
            "signal": name, "n_weeks": len(ic), "mean_ic": ic.mean(), "std_ic": ic.std(),
            "ic_ir": ic.mean() / ic.std() if ic.std() > 0 else np.nan,
            "t_stat": ic.mean() / (ic.std() / np.sqrt(len(ic))) if len(ic) > 2 else np.nan,
            "pos_share": (ic > 0).mean(),
        })
    return pd.DataFrame(rows).sort_values("ic_ir", ascending=False)


def zscore(s: pd.Series) -> pd.Series:
    sd = s.std()
    return (s - s.mean()) / sd if sd and np.isfinite(sd) and sd > 0 else s * 0


def weights_equal(hist: pd.DataFrame) -> pd.Series:
    return pd.Series(1.0 / len(STOCKS), index=STOCKS)


def weights_gmv(hist: pd.DataFrame, shrink: float = 0.3) -> pd.Series:
    cov = hist.tail(52).cov().values * 52
    n = len(cov)
    cov = (1 - shrink) * cov + shrink * np.diag(np.diag(cov))
    inv = np.linalg.pinv(cov)
    one = np.ones(n)
    w = inv @ one / (one @ inv @ one)
    return pd.Series(w, index=STOCKS).clip(-0.5, 1.5)


def weights_tangency(hist: pd.DataFrame, mu_win: int = 104, shrink: float = 0.3) -> pd.Series:
    mu = hist.tail(mu_win).mean().values * 52
    cov = hist.tail(104).cov().values * 52
    n = len(cov)
    cov = (1 - shrink) * cov + shrink * np.diag(np.diag(cov))
    inv = np.linalg.pinv(cov)
    w = inv @ mu
    w = w / np.abs(w).sum()          # full investment, allow shorts
    return pd.Series(w, index=STOCKS).clip(-0.8, 1.8)


def weights_tilt(hist: pd.DataFrame, signal: pd.Series, tilt: float = 0.4,
                 cov_win: int = 104) -> pd.Series:
    """EW core + tilt on cross-sectional z-score, scaled to a target tracking error."""
    z = zscore(signal.reindex(STOCKS).fillna(0))
    w = pd.Series(1.0 / len(STOCKS), index=STOCKS) + tilt * z / len(STOCKS)
    # risk scale: target ex-ante TE vs EW
    cov = hist.tail(cov_win).cov().values * 52
    d = w.values - 1.0 / len(STOCKS)
    te = float(np.sqrt(d @ cov @ d))
    if te > 0:
        w = pd.Series(1.0 / len(STOCKS) + (0.06 / te) * d, index=STOCKS)
    return w.clip(-0.3, 0.5)


def backtest(returns: pd.DataFrame, sigs: dict[str, pd.DataFrame], start: str = "2024-01-05",
             end: str | None = None) -> pd.DataFrame:
    end = end or str(returns.index[-1].date())
    rets = returns.loc[start:end]
    rows = []
    for dt in rets.index:
        hist = returns.loc[:dt].iloc[:-1]  # strictly before dt
        if len(hist) < 60:
            continue
        fwd = returns.loc[dt]
        if fwd.isna().any():
            continue
        cand = {
            "EW": weights_equal(hist),
            "GMV52": weights_gmv(hist),
            "Tangency": weights_tangency(hist),
            "Tilt_rev1": weights_tilt(hist, sigs["rev1"].loc[dt]),
            "Tilt_mom12": weights_tilt(hist, sigs["mom12"].loc[dt]),
            "Tilt_mom12_1": weights_tilt(hist, sigs["mom12_1"].loc[dt]),
            "Tilt_lowvol": weights_tilt(hist, sigs["lowvol"].loc[dt]),
        }
        for name, w in cand.items():
            rows.append({"date": dt, "strategy": name, "ret": float(w @ fwd),
                         "turnover": float((w - cand["EW"]).abs().sum())})
    df = pd.DataFrame(rows)
    return df


def summarize(bt: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for name, g in bt.groupby("strategy"):
        r = g.set_index("date")["ret"]
        nav = (1 + r).cumprod()
        dd = (nav / nav.cummax() - 1).min()
        rows.append({
            "strategy": name, "weeks": len(r),
            "ann_ret": (nav.iloc[-1] ** (52 / len(r)) - 1),
            "ann_vol": r.std() * np.sqrt(52),
            "sharpe": r.mean() / r.std() * np.sqrt(52) if r.std() > 0 else np.nan,
            "max_dd": dd, "hit": (r > 0).mean(),
            "cum": nav.iloc[-1] - 1,
        })
    return pd.DataFrame(rows).sort_values("sharpe", ascending=False)


def main():
    cutoff = sys.argv[1] if len(sys.argv) > 1 else None
    closes, returns, idx = load()
    if cutoff:
        returns = returns.loc[:cutoff]
    RESEARCH.mkdir(exist_ok=True)
    sigs = signals(returns)
    ic = ic_table(returns, sigs)
    ic.to_csv(RESEARCH / "scan_ic.csv", index=False)
    print("\n=== Cross-sectional rank IC (next-week return) ===")
    print(ic.round(3).to_string(index=False))

    print("\n=== Correlation (last 104w) ===")
    print(returns.tail(104).corr().round(2).to_string())
    print("\n=== Annualized vol (last 104w, %) ===")
    print((returns.tail(104).std() * np.sqrt(52) * 100).round(1).to_string())

    bt = backtest(returns, sigs)
    bt.to_csv(RESEARCH / "scan_portfolios_detail.csv", index=False)
    summ = summarize(bt)
    summ.to_csv(RESEARCH / "scan_portfolios.csv", index=False)
    print("\n=== Strategy backtest (weekly rebalance, gross) ===")
    print(summ.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
