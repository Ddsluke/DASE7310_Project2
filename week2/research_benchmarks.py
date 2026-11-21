# -*- coding: utf-8 -*-
"""GP2 课程 benchmark 对比：1/N、GMV、切点、CAPM、市场组合、有效前沿。

对应课程：
- Lecture 2: 1/N diversification, GMV (two assets and n assets)
- Lecture 3: mean-variance frontier, two-fund theorem, tangency / max Sharpe
- Lecture 4: CAPM / SML, beta regression, market portfolio

用法: python research_benchmarks.py
输出:
  research/benchmark_weekly.csv       weekly returns of every method
  research/benchmark_summary.csv      performance table
  research/benchmark_4w_distribution.csv
  research/frontier_20261030.csv      efficient frontier at the final cutoff
  research/frontier_points.csv        where each method sits vs the frontier
  research/two_fund_check.csv         two-fund theorem check
  research/benchmark_final_weights.csv
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

import portfolio as gp

HERE = Path(__file__).resolve().parent
RESEARCH = HERE / "research"
S = gp.STOCKS
RF = 0.02
PREMIUM = 0.05


def cap_gross(w: pd.Series, gross_cap: float = 2.0) -> pd.Series:
    """把围绕 1/N 的主动偏离按比例缩小，使总敞口不超过 gross_cap。
    课程公式本身不限制杠杆；这是为了让它可实施、可比较。"""
    n = len(w)
    dev = w - 1 / n
    gross = 1.0 + dev.abs().sum()
    if gross > gross_cap:
        w = 1 / n + dev * ((gross_cap - 1.0) / (gross - 1.0))
    return w


def metrics(r: pd.Series, rf: float = RF) -> dict:
    nav = (1 + r).cumprod()
    ann_ret = nav.iloc[-1] ** (52 / len(r)) - 1
    ann_vol = r.std() * np.sqrt(52)
    return {
        "ann_ret%": ann_ret * 100,
        "ann_vol%": ann_vol * 100,
        "sharpe_rf": (ann_ret - rf) / ann_vol if ann_vol > 0 else np.nan,
        "max_dd%": (nav / nav.cummax() - 1).min() * 100,
        "worst_wk%": r.min() * 100,
        "hit%": (r > 0).mean() * 100,
        "cum%": (nav.iloc[-1] - 1) * 100,
    }


def main():
    raw, hfq, ret, idx, meta = gp.load_data()
    ret = ret.dropna(how="all")
    rows = []
    final_w = {}
    last_dt = ret.loc["2021-01-08":].index[-1]

    for dt in ret.loc["2021-01-08":].index:
        hist = ret.loc[:dt].iloc[:-1]
        if len(hist) < 60:
            continue
        fwd = ret.loc[dt]
        if fwd.isna().any():
            continue
        idx_hist = idx.loc[:dt].iloc[:-1]

        methods: dict[str, pd.Series] = {
            "EW": pd.Series(1 / len(S), index=S),
            "GMV_uncon": gp.gmv_unconstrained(hist),
            "GMV_con": gp.gmv_weights(hist),
            "Tangency_uncon": gp.tangency_unconstrained(hist, rf=RF),
            "Tangency_uncon_cap2": cap_gross(gp.tangency_unconstrained(hist, rf=RF), 2.0),
            "Tangency_con": gp.tangency_weights(hist, rf=RF),
            "Top4": gp.top4_weights(hist),
            "Tilt_k2": gp.tilt_weights(hist, k=2.0)[0],
        }
        mu_capm, _ = gp.capm_mu(hist, idx_hist, rf=RF, premium=PREMIUM)
        methods["CAPM_con"] = gp.mv_weights(hist, mu_capm, lam=15)
        mu_sig = gp.composite_signal(hist) * 0.02
        methods["Signal_con"] = gp.mv_weights(hist, mu_sig, lam=8)

        for name, w in methods.items():
            rows.append({
                "date": dt, "strategy": name,
                "ret": float(w.values @ fwd.values),
                "gross": float(w.abs().sum()),
                "n_short": int((w < 0).sum()),
            })
            if dt == last_dt:
                final_w[name] = w

        rows.append({"date": dt, "strategy": "Market_HSI",
                     "ret": float(idx.loc[dt, "hsi"]), "gross": 1.0, "n_short": 0})

    df = pd.DataFrame(rows)
    df.to_csv(RESEARCH / "benchmark_weekly.csv", index=False)

    # ---- summary ----
    ew = df[df.strategy == "EW"].set_index("date")["ret"]
    mkt = df[df.strategy == "Market_HSI"].set_index("date")["ret"]
    summary = []
    for name, g in df.groupby("strategy"):
        r = g.set_index("date")["ret"]
        m = metrics(r)
        active_ew = r - ew.reindex(r.index)
        active_mkt = r - mkt.reindex(r.index)
        m.update({
            "strategy": name,
            "active_ew_ann%": active_ew.mean() * 52 * 100,
            "ir_ew": active_ew.mean() / active_ew.std() * np.sqrt(52) if active_ew.std() > 0 else np.nan,
            "hit_ew%": (active_ew > 0).mean() * 100,
            "active_mkt_ann%": active_mkt.mean() * 52 * 100,
            "avg_gross": g["gross"].mean(),
            "avg_n_short": g["n_short"].mean(),
        })
        summary.append(m)
    summ_all = pd.DataFrame(summary).set_index("strategy")
    cols = ["ann_ret%", "ann_vol%", "sharpe_rf", "max_dd%", "worst_wk%", "hit%",
            "active_ew_ann%", "ir_ew", "hit_ew%", "active_mkt_ann%",
            "avg_gross", "avg_n_short", "cum%"]
    summ_all = summ_all[cols]
    # 原始未加杠杆约束的切点组合单独放诊断文件；主表用 gross<=2 的版本
    diag = summ_all.loc[["Tangency_uncon"]]
    summ = summ_all.drop(index=["Tangency_uncon"])
    summ.to_csv(RESEARCH / "benchmark_summary.csv")
    diag.to_csv(RESEARCH / "benchmark_diagnostics.csv")
    print("=== Course benchmark comparison (2021-01 to 2026-10, weekly, gross) ===")
    print(summ.sort_values("sharpe_rf", ascending=False).round(2).to_string())
    print("\n=== Diagnostic: raw unconstrained tangency (not investable) ===")
    print(diag.round(2).to_string())

    # ---- 4-week distribution ----
    wide = df.pivot(index="date", columns="strategy", values="ret")
    r4 = (1 + wide).rolling(4).apply(lambda a: np.prod(a) - 1).dropna()
    dist_all = pd.DataFrame({
        "median%": r4.median() * 100,
        "p05%": r4.quantile(.05) * 100,
        "p95%": r4.quantile(.95) * 100,
        "P(<0)%": (r4 < 0).mean() * 100,
        "P(<-5)%": (r4 < -0.05).mean() * 100,
        "P(>+5)%": (r4 > 0.05).mean() * 100,
    }).sort_values("median%", ascending=False)
    dist = dist_all.drop(index=["Tangency_uncon"], errors="ignore")
    dist.to_csv(RESEARCH / "benchmark_4w_distribution.csv")
    dist_all.loc[["Tangency_uncon"]].to_csv(RESEARCH / "benchmark_diagnostics_4w.csv")
    print("\n=== Rolling 4-week distribution ===")
    print(dist.round(2).to_string())

    # ---- final weights ----
    fw_all = pd.DataFrame(final_w).T
    fw_all.index.name = "strategy"
    fw = fw_all.drop(index=["Tangency_uncon"])
    fw.to_csv(RESEARCH / "benchmark_final_weights.csv")
    fw_all.loc[["Tangency_uncon"]].to_csv(RESEARCH / "benchmark_diagnostics_weights.csv")
    print("\n=== Final weights (cutoff 2026-10-30, %) ===")
    print((fw * 100).round(1).to_string())

    # ---- efficient frontier at the final cutoff ----
    hist = ret.dropna().tail(104)
    mu = hist.mean() * 52
    cov = gp.shrink_cov(hist, 104)
    w_gmv = gp.gmv_weights(hist)
    gmv_ret = float(mu.values @ w_gmv.values)
    targets = np.linspace(gmv_ret, float(mu.max()), 15)
    frows = []
    for t in targets:
        w = gp.frontier_weights(hist, mu, float(t))
        if w is None:
            continue
        frows.append({
            "target_return%": t * 100,
            "vol%": float(np.sqrt(w.values @ cov @ w.values)) * 100,
            **{s: float(w[s]) * 100 for s in S},
        })
    frontier = pd.DataFrame(frows)
    frontier.to_csv(RESEARCH / "frontier_20261030.csv", index=False)

    points = []
    for name, w in final_w.items():
        if name == "Tangency_uncon":
            continue
        points.append({
            "strategy": name,
            "exp_ret%": float(mu.values @ w.values) * 100,
            "vol%": float(np.sqrt(w.values @ cov @ w.values)) * 100,
            "gross": float(w.abs().sum()),
        })
    pts = pd.DataFrame(points).set_index("strategy")
    # 有效前沿在同一 vol 下的可实现最高收益（线性插值）
    if not frontier.empty:
        fv = frontier.sort_values("vol%")
        pts["frontier_ret_at_same_vol%"] = np.interp(pts["vol%"], fv["vol%"], fv["target_return%"])
        pts["efficiency_gap%"] = pts["exp_ret%"] - pts["frontier_ret_at_same_vol%"]
    pts.to_csv(RESEARCH / "frontier_points.csv")
    print("\n=== Position vs efficient frontier (in-sample, 104w) ===")
    print(pts.round(2).to_string())

    # ---- two-fund theorem check ----
    # 用课程公式的 GMV 与“gross<=2”的切点组合作为两个基金；
    # 未加约束的原始切点组合权重极端，不适合做两基金分解。
    w_tan = cap_gross(gp.tangency_unconstrained(hist, rf=RF), 2.0)
    mu_gmv = float(mu.values @ w_gmv.values)
    mu_tan = float(mu.values @ w_tan.values)
    trows = []
    for name, w in final_w.items():
        if name == "Tangency_uncon":
            continue
        mu_m = float(mu.values @ w.values)
        denom = mu_tan - mu_gmv
        alpha = (mu_tan - mu_m) / denom if abs(denom) > 1e-10 else np.nan
        w_c = alpha * w_gmv + (1 - alpha) * w_tan
        trows.append({
            "strategy": name,
            "alpha_gmv": alpha,
            "l1_weight_gap": float((w_c - w).abs().sum()),
            "vol_method%": float(np.sqrt(w.values @ cov @ w.values)) * 100,
            "vol_twofund%": float(np.sqrt(w_c.values @ cov @ w_c.values)) * 100,
            "ret_gap%": float(mu.values @ (w_c - w)) * 100,
        })
    tf = pd.DataFrame(trows).set_index("strategy")
    tf.to_csv(RESEARCH / "two_fund_check.csv")
    print("\n=== Two-fund theorem check (alpha*GMV + (1-alpha)*Tangency) ===")
    print(tf.round(3).to_string())


if __name__ == "__main__":
    main()
