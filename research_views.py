# -*- coding: utf-8 -*-
"""GP2 研究：从“无观点”的 GMV 到“有观点”的均值-方差组合。

核心思想
--------
- 无观点：min w'Σw  -> GMV。
- 有观点：把观点写成预期收益 μ，解
      max  μ'w - (λ/2) w'Σw
      s.t. Σw = 1, 0.01 <= w <= 0.25
  λ 越大越保守（越接近 GMV）；λ 越小越激进（越接近“全押最高 μ”）。
- 注意：给所有 μ 加同一个常数、或整体乘一个正数，不改变最优权重（因为 Σw=1）。
  真正改变组合的是 **横截面上的相对观点**（哪只比哪只更好）。

用法: python research_views.py
输出: research/views_frontier.csv
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize

import portfolio as gp

HERE = Path(__file__).resolve().parent
RESEARCH = HERE / "research"
S = gp.STOCKS


def mv_weights(mu_active: np.ndarray, cov: np.ndarray, lam: float,
               floor: float = 0.01, cap: float = 0.25) -> pd.Series:
    n = len(mu_active)
    cons = [{"type": "eq", "fun": lambda w: w.sum() - 1}]
    res = minimize(lambda w: -(mu_active @ w - 0.5 * lam * (w @ cov @ w)),
                   np.ones(n) / n, method="SLSQP", bounds=[(floor, cap)] * n,
                   constraints=cons, options={"maxiter": 2000, "ftol": 1e-14})
    w = pd.Series(res.x, index=S)
    return w / w.sum()


def main():
    raw, hfq, ret, idx, meta = gp.load_data()
    h = ret.dropna().tail(104)
    cov = gp.shrink_cov(h, 104, 0.30)       # 优化用（收缩后）
    cov_sample = h.cov().values * 52         # 检查“真实”风险用
    mu_sample = h.mean().values * 52
    grand = float(mu_sample.mean())

    sig = gp.composite_signal(ret).values
    m = idx["hsi"].reindex(h.index)
    beta = np.array([np.cov(h[s], m, ddof=1)[0, 1] / np.var(m, ddof=1) for s in S])
    capm = beta * 0.05
    capm = capm - capm.mean()

    views = {
        "sample mean": mu_sample - grand,
        "signal z": sig * 0.02,
        "CAPM beta": capm,
    }

    rows = []
    # 无观点 = GMV
    w_gmv = gp.gmv_weights(ret, 104, 0.01, 0.25)
    rows.append({"view": "GMV (no view)", "lambda": np.inf, "vol_sample%": np.nan,
                 "active_ret%": 0.0, **{s: float(w_gmv[s]) * 100 for s in S},
                 "_w": w_gmv})

    for name, mu_active in views.items():
        for lam in [1, 2, 5, 10, 20, 50, 100]:
            w = mv_weights(mu_active, cov, lam)
            rows.append({
                "view": name, "lambda": lam,
                "vol_sample%": float(np.sqrt(w.values @ cov_sample @ w.values)) * 100,
                "active_ret%": float(mu_active @ w.values) * 100,
                **{s: float(w[s]) * 100 for s in S},
                "_w": w,
            })

    df = pd.DataFrame(rows)
    df.drop(columns="_w").to_csv(RESEARCH / "views_frontier.csv", index=False)

    print("=== GMV (no view) weights (%) ===")
    print((w_gmv * 100).round(1).to_string())
    print(f"vol at sample cov: {np.sqrt(w_gmv.values @ cov_sample @ w_gmv.values)*100:.2f}%")

    for name in views:
        print(f"\n=== View: {name} (weights in %, vol checked at sample cov) ===")
        sub = df[df.view == name][["lambda", "vol_sample%", "active_ret%"] + S]
        print(sub.round(1).to_string(index=False))

    print("\nInterpretation:")
    print("- lambda large  -> conservative, close to GMV")
    print("- lambda small  -> aggressive, loads the view")
    print("- sample-mean view is unstable (loads 0981); signal view is stable")


if __name__ == "__main__":
    main()
