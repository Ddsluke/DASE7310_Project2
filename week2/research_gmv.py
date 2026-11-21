# -*- coding: utf-8 -*-
"""GP2 教学/复现：协方差矩阵与 GMV 的每一步。

用法: python research_gmv.py
输出: research/covariance_104w.csv, correlation_104w.csv,
      research/gmv_weights.csv, research/gmv_risk_contributions.csv
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

import portfolio as gp

HERE = Path(__file__).resolve().parent
RESEARCH = HERE / "research"
WIN = 104
SHRINK = 0.30


def main():
    raw, hfq, ret, idx, meta = gp.load_data()
    r = ret.dropna()
    h = r.tail(WIN)
    S = gp.STOCKS

    cov_sample = h.cov().values * 52
    cov_shrunk = gp.shrink_cov(h, WIN, SHRINK)
    corr = h.corr()

    cov_df = pd.DataFrame(cov_shrunk, index=S, columns=S)
    cov_df.insert(0, "stock_code", S)
    cov_df.to_csv(RESEARCH / "covariance_104w.csv", index=False)
    corr_df = corr.copy()
    corr_df.insert(0, "stock_code", S)
    corr_df.to_csv(RESEARCH / "correlation_104w.csv", index=False)

    # 无约束闭式解：w = Sigma^{-1} 1 / (1' Sigma^{-1} 1)
    inv = np.linalg.inv(cov_shrunk)
    one = np.ones(len(S))
    w_unconstrained = inv @ one / (one @ inv @ one)

    # 带约束：纯多头、1% 下限、25% 上限（数值二次规划）
    w_constrained = gp.gmv_weights(r, WIN, floor=0.01, cap=0.25)

    # 风险贡献：RC_s = w_s * (Sigma w)_s / (w' Sigma w)
    def risk_contrib(w):
        mrc = cov_shrunk @ w.values
        rc = w.values * mrc
        return pd.Series(rc / rc.sum() * 100, index=S)

    out = pd.DataFrame({
        "vol_ann%": np.sqrt(np.diag(cov_shrunk)) * 100,
        "w_unconstrained%": w_unconstrained * 100,
        "w_constrained%": w_constrained.values * 100,
        "risk_contrib%": risk_contrib(w_constrained).values,
    }, index=S)
    out.to_csv(RESEARCH / "gmv_weights.csv", index_label="stock_code")

    print(f"Window: {h.index[0].date()} -> {h.index[-1].date()} ({len(h)} weeks)")
    print(f"Shrinkage: {SHRINK:.0%} toward diagonal")
    print("\n=== GMV solutions ===")
    print(out.round(2).to_string())
    print(f"\nUnconstrained: vol {np.sqrt(w_unconstrained @ cov_shrunk @ w_unconstrained)*100:.2f}%, "
          f"sum {w_unconstrained.sum():.4f}, shorts {(w_unconstrained < 0).sum()}")
    print(f"Constrained:   vol {np.sqrt(w_constrained.values @ cov_shrunk @ w_constrained.values)*100:.2f}%, "
          f"sum {w_constrained.sum():.4f}, shorts {(w_constrained < 0).sum()}")

    # ---- shrinkage sensitivity: how much do the GMV weights move? ----
    from scipy.optimize import minimize

    def gmv_with(cov: np.ndarray) -> pd.Series:
        n = len(S)
        cons = [{"type": "eq", "fun": lambda w: w.sum() - 1}]
        res = minimize(lambda w: w @ cov @ w, np.ones(n) / n, method="SLSQP",
                       bounds=[(0.01, 0.25)] * n, constraints=cons,
                       options={"maxiter": 1000, "ftol": 1e-14})
        w = pd.Series(res.x, index=S)
        return w / w.sum()

    rows = []
    for d in [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.7, 1.0]:
        cov_d = (1 - d) * cov_sample + d * np.diag(np.diag(cov_sample))
        w = gmv_with(cov_d)
        rows.append({"shrinkage": d,
                     "vol_at_sample%": float(np.sqrt(w.values @ cov_sample @ w.values)) * 100,
                     **{s: float(w[s]) * 100 for s in S}})
    sens = pd.DataFrame(rows)
    sens.to_csv(RESEARCH / "shrinkage_sensitivity.csv", index=False)

    try:
        from sklearn.covariance import LedoitWolf
        lw = LedoitWolf().fit(h.values)
        w_lw = gmv_with(lw.covariance_ * 52)
        print(f"\nLedoit-Wolf estimated shrinkage: {lw.shrinkage_:.3f}")
        print("LW GMV weights (%): " + " ".join(f"{s}:{w_lw[s]*100:.1f}" for s in S))
        print(f"LW vol at sample cov: {np.sqrt(w_lw.values @ cov_sample @ w_lw.values)*100:.2f}%")
    except Exception as exc:  # noqa: BLE001
        print(f"[LW] skipped: {exc}")

    print("\n=== GMV weight sensitivity to fixed shrinkage (vol checked at sample cov) ===")
    print(sens.round(2).to_string(index=False))


if __name__ == "__main__":
    main()
