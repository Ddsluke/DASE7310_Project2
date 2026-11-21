# -*- coding: utf-8 -*-
"""DASE7310 GP2 - 投资组合构建与周度再平衡流水线（single-script pipeline）

用法（在 repo 根目录、使用 dase7310 环境）:
    python portfolio.py refresh-data --end 2026-10-30
    python portfolio.py build --week 1 --cutoff 2026-10-30 --strategy gmv
    python portfolio.py build --week 2 --cutoff 2026-11-06 --strategy gmv
    python portfolio.py evaluate --week 1

口径（冻结）:
- 信号/协方差：新浪后复权(hfq)周收益（含股息的总回报，适合估计动量与风险）。
- 组合会计：新浪未复权(raw)周五收盘价（课程公式中的 p 是真实收盘价；股数必须按真实价计算）。
- 周价格：每周 W-FRI 最后一根已实现收盘价。
- 组合机制严格按 Group-Project-2_2026.pdf:
    c_{s,0} = w_{s,1} * C_0,  h_{s,1} = c_{s,0} / p_{s,0},  C_i = sum_s p_{s,i} h_{s,i},
    R_i = (C_i - C_{i-1}) / C_{i-1},  w_{s,i} = c_{s,i-1} / C_{i-1}.
- 初始资本 C_0 = HKD 1,000,000；满仓（sum_s w = 1）；默认纯多头。
- 再平衡上限 3 次（第 2/3/4 周开始时各一次）；周内 buy-and-hold，股数不变。
- 提交文件与参数快照只增不改；目标周结束后追加 realized 文件。
"""
from __future__ import annotations

import argparse
import json
import re
import time
from datetime import date, datetime
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
WEEKS = HERE / "weeks"
RESEARCH = HERE / "research"

STOCKS = ["9988", "0066", "1398", "3988", "0981", "0005", "1810", "0016", "1113", "0700"]
NAMES = {
    "9988": "Alibaba Group Holding",
    "0066": "MTR Corporation",
    "1398": "ICBC",
    "3988": "Bank of China",
    "0981": "SMIC",
    "0005": "HSBC Holdings",
    "1810": "Xiaomi Group-W",
    "0016": "Sun Hung Kai Properties",
    "1113": "CK Asset Holdings",
    "0700": "Tencent Holdings",
}
SECTOR = {
    "9988": "E-commerce", "0066": "Transport", "1398": "Bank", "3988": "Bank",
    "0981": "Semiconductor", "0005": "Bank", "1810": "Consumer tech",
    "0016": "Property", "1113": "Property", "0700": "Internet",
}
LOT_SIZE = {"9988": 100, "0066": 500, "1398": 1000, "3988": 1000, "0981": 500,
            "0005": 400, "1810": 200, "0016": 1000, "1113": 1000, "0700": 100}
START = "2020-01-01"
INITIAL_CAPITAL = 1_000_000.0

# 目标周（交易周）与估值日（前一周五收盘）
WEEK_DATES = {
    "1": {"cutoff": "2026-10-30", "end": "2026-11-06"},
    "2": {"cutoff": "2026-11-06", "end": "2026-11-13"},
    "3": {"cutoff": "2026-11-13", "end": "2026-11-20"},
    "4": {"cutoff": "2026-11-20", "end": "2026-11-27"},
}


# ----------------------------------------------------------------------------- data layer
def _fetch_stocks(start: str, end: str, adjust: str, prefer: str = "sina", attempts: int = 3):
    """整批来源表决：同一源内任一股票失败 -> 整批切换下一个源。"""
    import akshare as ak

    orders = {"auto": ["eastmoney", "sina"], "eastmoney": ["eastmoney"], "sina": ["sina"]}
    last_exc: Exception | None = None
    for source in orders[prefer]:
        for attempt in range(1, attempts + 1):
            frames = []
            try:
                for code in STOCKS:
                    if source == "eastmoney":
                        d = ak.stock_hk_hist(symbol=code.zfill(5), period="daily",
                                             start_date=start.replace("-", ""),
                                             end_date=end.replace("-", ""), adjust=adjust)
                        d = d.rename(columns={"日期": "date", "收盘": "close"})
                    else:
                        d = ak.stock_hk_daily(symbol=code.zfill(5), adjust=adjust)
                        d = d.rename(columns={"日期": "date", "收盘": "close"})
                    d = d[["date", "close"]].copy()
                    d["date"] = pd.to_datetime(d["date"])
                    d["close"] = pd.to_numeric(d["close"], errors="raise")
                    d = d[d["date"].between(start, end)].sort_values("date")
                    if (d.empty or not np.isfinite(d["close"]).all()
                            or (d["close"] <= 0).any() or d["date"].duplicated().any()):
                        raise ValueError(f"{code}: invalid prices from {source}/{adjust}")
                    d["stock_code"] = code
                    frames.append(d)
                return pd.concat(frames, ignore_index=True), source
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                print(f"[refresh] {source}/{adjust} attempt {attempt}/{attempts} failed: "
                      f"{type(exc).__name__}: {exc}", flush=True)
                if attempt < attempts:
                    time.sleep(2)
    raise RuntimeError(f"No data refreshed (tried {orders[prefer]}). Last error: {last_exc}") from last_exc


def refresh_data(end: str | None = None, prefer: str = "sina"):
    end = end or date.today().strftime("%Y-%m-%d")
    DATA.mkdir(parents=True, exist_ok=True)
    meta = {
        "requested_start": START,
        "requested_end": end,
        "refresh_time": datetime.now().isoformat(timespec="seconds"),
        # 数据口径（可审计）/ data convention (auditable):
        # raw = 不复权 unadjusted (AkShare adjust="")
        # hfq = 后复权 backward-adjusted (AkShare adjust="hfq")
        # qfq (前复权) is NOT used anywhere in this project.
        "raw_adjust": "",
        "hfq_adjust": "hfq",
        "price_convention": "raw = unadjusted; hfq = backward-adjusted; qfq is NOT used",
    }

    for tag, adjust in [("raw", ""), ("hfq", "hfq")]:
        px, source = _fetch_stocks(START, end, adjust, prefer=prefer)
        wide = px.pivot(index="date", columns="stock_code", values="close").sort_index()
        closes = wide.resample("W-FRI").last()[STOCKS]
        closes.to_csv(DATA / f"weekly_closes_{tag}.csv")
        closes.pct_change(fill_method=None).to_csv(DATA / f"weekly_returns_{tag}.csv")
        px.sort_values(["date", "stock_code"]).to_csv(DATA / f"daily_closes_{tag}.csv", index=False)
        meta[f"{tag}_source"] = source
        meta[f"{tag}_last_weekly"] = str(closes.index[-1].date())
        meta[f"{tag}_last_daily_date"] = {
            c: str(px.loc[px.stock_code == c, "date"].max().date()) for c in STOCKS}
        print(f"[refresh] {tag}: source={source} weekly_rows={len(closes)} "
              f"last_weekly={closes.index[-1].date()}")

    try:
        import akshare as ak
        idx = {}
        for sym, name in [("HSI", "hsi"), ("HSTECH", "hstech")]:
            d = ak.stock_hk_index_daily_sina(symbol=sym)
            d = d.rename(columns={"日期": "date", "收盘": "close"})
            d["date"] = pd.to_datetime(d["date"])
            d["close"] = pd.to_numeric(d["close"], errors="raise")
            idx[name] = d[d["date"].between(START, end)].set_index("date")["close"]
        idx_closes = pd.DataFrame({k: v.resample("W-FRI").last() for k, v in idx.items()})
        idx_closes.to_csv(DATA / "index_closes.csv")
        idx_closes.pct_change(fill_method=None).to_csv(DATA / "index_returns.csv")
        meta["index_source"] = "Sina Finance (stock_hk_index_daily_sina)"
        meta["index_last_weekly"] = str(idx_closes.index[-1].date())
    except Exception as exc:  # noqa: BLE001
        print(f"[refresh] index failed (non-fatal): {type(exc).__name__}: {exc}")
        meta["index_source"] = None

    (DATA / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return meta


def load_data():
    meta = json.loads((DATA / "meta.json").read_text(encoding="utf-8"))
    raw = pd.read_csv(DATA / "weekly_closes_raw.csv", index_col=0, parse_dates=True)[STOCKS]
    hfq = pd.read_csv(DATA / "weekly_closes_hfq.csv", index_col=0, parse_dates=True)[STOCKS]
    ret = hfq.pct_change(fill_method=None)
    idx = None
    if (DATA / "index_returns.csv").exists():
        idx = pd.read_csv(DATA / "index_returns.csv", index_col=0, parse_dates=True)
    return raw, hfq, ret, idx, meta


def data_coverage(raw: pd.DataFrame, hfq: pd.DataFrame, idx: pd.DataFrame | None,
                  meta: dict, cutoff: str) -> dict:
    """Return auditable data-vintage metadata for a portfolio build."""
    cutoff_ts = pd.Timestamp(cutoff)
    raw_last = raw.index.max()
    hfq_last = hfq.index.max()
    idx_last = idx.index.max() if idx is not None and not idx.empty else None
    daily = meta.get("raw_last_daily_date", {}) or {}
    daily_complete = bool(daily) and all(
        pd.Timestamp(daily.get(stock, "1900-01-01")) >= cutoff_ts for stock in STOCKS)
    raw_complete = bool(raw_last is not None and raw_last >= cutoff_ts)
    hfq_complete = bool(hfq_last is not None and hfq_last >= cutoff_ts)
    index_complete = bool(idx_last is not None and idx_last >= cutoff_ts)
    return {
        "raw_last_weekly": str(raw_last.date()) if raw_last is not None else None,
        "hfq_last_weekly": str(hfq_last.date()) if hfq_last is not None else None,
        "index_last_weekly": str(idx_last.date()) if idx_last is not None else None,
        "raw_daily_complete": daily_complete,
        "raw_complete": raw_complete,
        "hfq_complete": hfq_complete,
        "index_complete": index_complete,
    }


def validate_build_request(cutoff: str, strategy: str, trial: bool,
                           variant: str | None, variant_reason: str | None,
                           coverage: dict) -> None:
    """Prevent a future/incomplete cutoff from silently producing an official build."""
    cutoff_date = pd.Timestamp(cutoff).date()
    if cutoff_date > date.today() and not trial:
        raise ValueError(
            f"cutoff {cutoff_date} is in the future; use --trial with a named "
            "--variant and --reason for a dry run")
    if trial and not variant:
        raise ValueError("--trial requires --variant so an official submission is never overwritten")
    if variant and not variant_reason:
        raise ValueError("--variant requires --reason for the audit trail")

    required = ["raw_complete", "hfq_complete"]
    if strategy == "capm":
        required.append("index_complete")
    incomplete = [name for name in required if not coverage[name]]
    if not trial and (incomplete or not coverage["raw_daily_complete"]):
        details = ", ".join(incomplete + (
            [] if coverage["raw_daily_complete"] else ["raw_daily_complete"]))
        raise ValueError(
            f"cutoff data for {cutoff} is incomplete ({details}); run "
            f"'refresh-data --end {cutoff}' and do not submit stale data")


def prices_asof(closes: pd.DataFrame, cutoff: str) -> pd.Series:
    cutoff = pd.Timestamp(cutoff)
    px = closes.loc[:cutoff]
    if px.empty:
        raise ValueError(f"no prices on/before {cutoff}")
    last = px.index[-1]
    if (cutoff - last).days > 7:
        raise ValueError(f"last weekly price {last.date()} is more than 7 days before cutoff {cutoff.date()}")
    return px.iloc[-1]


# ----------------------------------------------------------------------------- signals / weights
def zs(s: pd.Series) -> pd.Series:
    sd = s.std()
    return (s - s.mean()) / sd if sd and np.isfinite(sd) and sd > 0 else s * 0


def composite_signal(ret: pd.DataFrame) -> pd.Series:
    """12 周动量 + 距 52 周高点 + 低波动，等权 z 分数。"""
    hist = ret.dropna()
    mom = hist.tail(12).sum()
    wealth = (1 + hist).cumprod()
    high = wealth.iloc[-1] / wealth.tail(52).max() - 1
    vol = -hist.tail(26).std()
    return (zs(mom) + zs(high) + zs(vol)) / 3


def shrink_cov(ret: pd.DataFrame, win: int = 104, shrink: float = 0.3) -> np.ndarray:
    cov = ret.dropna().tail(win).cov().values * 52
    return (1 - shrink) * cov + shrink * np.diag(np.diag(cov))


def tilt_weights(ret: pd.DataFrame, te: float = 0.10, k: float = 1.0,
                 long_cap: float = 0.35, short_cap: float = 0.0) -> tuple[pd.Series, pd.Series]:
    """EW 锚点 + 跟踪误差预算内的信号倾斜；k 放大/缩小主动仓位（默认纯多头）。"""
    hist = ret.dropna()
    n = len(STOCKS)
    sig = composite_signal(ret)
    d = sig.values / n
    cov = shrink_cov(hist)
    te_act = float(np.sqrt(d @ cov @ d))
    scale = te / te_act if te_act > 0 else 0.0
    base = pd.Series(np.clip(1 / n + scale * d, 0.0, 0.40), index=STOCKS)
    w = 1 / n + k * (base - 1 / n)
    w = w.clip(short_cap, long_cap)
    w = w / w.sum()
    return w, sig


def gmv_weights(ret: pd.DataFrame, win: int = 104, floor: float = 0.01,
                cap: float = 0.25) -> pd.Series:
    """课程 Lecture 2 的全局最小方差组合（纯多头 + 分散约束）。

    求解器: scipy.optimize.minimize(method="SLSQP")。
    问题是凸二次规划（目标 w'Σw 凸、约束线性），所以局部最优 = 全局最优。
    """
    from scipy.optimize import minimize

    cov = shrink_cov(ret, win)
    n = len(STOCKS)
    cons = [{"type": "eq", "fun": lambda w: w.sum() - 1}]
    res = minimize(lambda w: w @ cov @ w, np.ones(n) / n, method="SLSQP",
                   bounds=[(floor, cap)] * n, constraints=cons,
                   options={"maxiter": 1000, "ftol": 1e-14})
    if not res.success:
        raise RuntimeError(f"GMV optimizer failed: {res.message}")
    w = pd.Series(res.x, index=STOCKS)
    return w / w.sum()


def gmv_unconstrained(ret: pd.DataFrame, win: int = 104) -> pd.Series:
    """课程 Lecture 2/3 的原始 GMV 闭式解（允许做空）：
    x* = Σ⁻¹e / (e'Σ⁻¹e)
    """
    cov = shrink_cov(ret, win)
    inv = np.linalg.inv(cov)
    one = np.ones(len(STOCKS))
    return pd.Series(inv @ one / (one @ inv @ one), index=STOCKS)


def tangency_unconstrained(ret: pd.DataFrame, win: int = 104, rf: float = 0.02) -> pd.Series:
    """课程 Lecture 3 slide 31 的切点组合（允许做空）：
    x* ∝ Σ⁻¹ μ̃,  μ̃ = μ − r_f
    归一化到 sum(x*) = 1。
    """
    hist = ret.dropna()
    mu = hist.tail(win).mean().values * 52
    inv = np.linalg.pinv(shrink_cov(hist, win))
    w = inv @ (mu - rf)
    if not np.isfinite(w).all() or abs(w.sum()) < 1e-10:
        return pd.Series(1 / len(STOCKS), index=STOCKS)
    return pd.Series(w / w.sum(), index=STOCKS)


def frontier_weights(ret: pd.DataFrame, mu: pd.Series, target_return: float,
                     floor: float = 0.01, cap: float = 0.25) -> pd.Series | None:
    """有效前沿上的一个点：min w'Σw s.t. μ'w = target, 1'w = 1, floor<=w<=cap。"""
    from scipy.optimize import minimize

    cov = shrink_cov(ret, 104)
    n = len(STOCKS)
    cons = [
        {"type": "eq", "fun": lambda w: w.sum() - 1},
        {"type": "eq", "fun": lambda w: mu.values @ w - target_return},
    ]
    res = minimize(lambda w: w @ cov @ w, np.ones(n) / n, method="SLSQP",
                   bounds=[(floor, cap)] * n, constraints=cons,
                   options={"maxiter": 2000, "ftol": 1e-14})
    if not res.success:
        return None
    w = pd.Series(res.x, index=STOCKS)
    return w / w.sum()


def tangency_weights(ret: pd.DataFrame, win: int = 104, cap: float = 0.40,
                     rf: float = 0.02) -> pd.Series:
    """切点组合的实现版（纯多头 + 上下限）。基于 Lecture 3 的 Σ⁻¹μ̃。"""
    hist = ret.dropna()
    mu = hist.tail(win).mean().values * 52
    inv = np.linalg.pinv(shrink_cov(hist, win))
    w = inv @ (mu - rf)
    if not np.isfinite(w).all() or abs(w.sum()) < 1e-8:
        return pd.Series(1 / len(STOCKS), index=STOCKS)
    w = w / w.sum()
    w = pd.Series(np.clip(w, -0.10, cap), index=STOCKS)
    w = w / w.sum()
    dev = w - 1 / len(STOCKS)
    gross = float(dev.abs().sum()) + 1.0
    if gross > 2.0:
        w = 1 / len(STOCKS) + dev * (1.0 / (gross - 1.0))
    return w


def top4_weights(ret: pd.DataFrame, core: float = 0.5) -> pd.Series:
    sig = composite_signal(ret)
    top = sig.nlargest(4).index
    w = pd.Series(core / len(STOCKS), index=STOCKS)
    w[top] += (1 - core) / 4
    return w


def capm_beta(ret: pd.DataFrame, idx_ret: pd.DataFrame) -> pd.Series:
    """用 HSI 周收益回归估计每只股票的 beta（Lecture 4）。"""
    h = ret.dropna()
    m = idx_ret["hsi"].reindex(h.index).dropna()
    h = h.loc[m.index]
    return pd.Series([np.cov(h[s], m, ddof=1)[0, 1] / np.var(m, ddof=1) for s in STOCKS],
                     index=STOCKS)


def capm_mu(ret: pd.DataFrame, idx_ret: pd.DataFrame, rf: float = 0.02,
            premium: float = 0.05) -> tuple[pd.Series, pd.Series]:
    beta = capm_beta(ret, idx_ret)
    mu = rf + beta * premium
    return mu, beta


def mv_weights(ret: pd.DataFrame, mu: pd.Series, lam: float = 10.0,
               floor: float = 0.01, cap: float = 0.25) -> pd.Series:
    """均值-方差：max mu'w - (lam/2) w'cov w, s.t. 1'w=1, floor<=w<=cap。

    只依赖 mu 的横截面差异；给所有 mu 加常数不会改变权重（因为 1'w=1）。
    """
    from scipy.optimize import minimize

    cov = shrink_cov(ret, 104)
    n = len(STOCKS)
    mu_act = mu.values - mu.values.mean()
    cons = [{"type": "eq", "fun": lambda w: w.sum() - 1}]
    res = minimize(lambda w: -(mu_act @ w - 0.5 * lam * (w @ cov @ w)),
                   np.ones(n) / n, method="SLSQP", bounds=[(floor, cap)] * n,
                   constraints=cons, options={"maxiter": 2000, "ftol": 1e-14})
    if not res.success:
        raise RuntimeError(f"MV optimizer failed: {res.message}")
    w = pd.Series(res.x, index=STOCKS)
    return w / w.sum()


def target_weights(ret: pd.DataFrame, strategy: str, k: float = 2.0,
                   te: float = 0.10, lam: float = 10.0, rf: float = 0.02,
                   premium: float = 0.05, floor: float = 0.01, cap: float = 0.25,
                   idx_ret: pd.DataFrame | None = None) -> tuple[pd.Series, pd.Series | None]:
    if strategy == "ew":
        return pd.Series(1 / len(STOCKS), index=STOCKS), None
    if strategy == "gmv":
        return gmv_weights(ret, floor=floor, cap=cap), None
    if strategy == "tangency":
        return tangency_weights(ret, cap=cap, rf=rf), None
    if strategy == "top4":
        return top4_weights(ret), composite_signal(ret)
    if strategy == "capm":
        if idx_ret is None:
            raise ValueError("capm strategy requires HSI index returns")
        mu, beta = capm_mu(ret, idx_ret, rf=rf, premium=premium)
        return mv_weights(ret, mu, lam=lam, floor=floor, cap=cap), beta
    if strategy == "signal":
        mu = composite_signal(ret) * 0.02
        return mv_weights(ret, mu, lam=lam, floor=floor, cap=cap), composite_signal(ret)
    return tilt_weights(ret, te=te, k=k, long_cap=cap, short_cap=floor)


# ----------------------------------------------------------------------------- build
def previous_capital(week: int, raw: pd.DataFrame, cutoff: str) -> tuple[float, pd.DataFrame | None]:
    """C_{i-1}: 第 1 周为 100 万；之后按上一周提交的股数以本周截点价估值。"""
    if week <= 1:
        return INITIAL_CAPITAL, None
    prev_dir = WEEKS / f"week{week - 1}"
    path = prev_dir / "portfolio.csv"
    if not path.exists():
        raise FileNotFoundError(f"missing {path}; run build --week {week - 1} first")
    prev = pd.read_csv(path, dtype={"stock_code": str})
    prev["stock_code"] = prev["stock_code"].str.zfill(4)
    if "shares_rounded" in prev.columns:
        prev["shares"] = prev["shares_rounded"]
    px = prices_asof(raw, cutoff)
    prev["price_cutoff"] = prev["stock_code"].map(px)
    prev["value_cutoff"] = prev["shares"] * prev["price_cutoff"]
    capital = float(prev["value_cutoff"].sum())
    return capital, prev


def cumulative_active(week: int) -> float | None:
    """第 1..week-1 周累计主动收益（组合 - 等权），用于预注册的去风险规则。"""
    total = 0.0
    found = False
    for w in range(1, week):
        p = WEEKS / f"week{w}" / "realized_summary.json"
        if p.exists():
            total += json.loads(p.read_text(encoding="utf-8"))["active_return"]
            found = True
    return total if found else None


def build(week: int, cutoff: str, strategy: str = "gmv", k: float = 2.0, te: float = 0.10,
          lam: float = 10.0, rf: float = 0.02, premium: float = 0.05,
          floor: float = 0.01, cap: float = 0.25,
          variant: str | None = None, variant_reason: str | None = None,
          trial: bool = False):
    raw, hfq, ret, idx, meta = load_data()
    coverage = data_coverage(raw, hfq, idx, meta, cutoff)
    validate_build_request(cutoff, strategy, trial, variant, variant_reason, coverage)
    px = prices_asof(raw, cutoff)
    ret_upto = ret.loc[:cutoff]

    if variant is not None and not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", variant):
        raise ValueError("variant may contain only letters, digits, underscores and hyphens")
    suffix = f"_{variant}" if variant else ""
    out = WEEKS / f"week{week}"
    out.mkdir(parents=True, exist_ok=True)
    target_names = [
        f"portfolio{suffix}.csv", f"params{suffix}.json",
        f"submission{suffix}.xlsx", f"submission{suffix}.csv",
        f"report{suffix}.md",
    ]
    existing = [name for name in target_names if (out / name).exists()]
    if existing:
        raise FileExistsError(
            f"refusing to overwrite week{week} outputs: {', '.join(existing)}; "
            "use a new --variant with --reason")

    # 预注册的去风险规则：若累计主动收益 < -5pp，k 降为 1.0（第 2 周起生效）
    k_effective, override = k, None
    if strategy == "tilt" and week > 1:
        ca = cumulative_active(week)
        if ca is not None and ca < -0.05 and k > 1.0:
            k_effective = 1.0
            override = f"cumulative active return {ca:+.2%} < -5pp: k cut from {k} to 1.0"

    w, aux = target_weights(ret_upto, strategy, k_effective, te, lam=lam, rf=rf,
                            premium=premium, floor=floor, cap=cap, idx_ret=idx)
    hist_cov = ret_upto.dropna().tail(104)
    cov_shrunk = shrink_cov(hist_cov, 104)
    cov_sample = hist_cov.cov().values * 52
    vol_shrunk = float(np.sqrt(w.values @ cov_shrunk @ w.values))
    vol_sample = float(np.sqrt(w.values @ cov_sample @ w.values))

    capital_prev, prev = previous_capital(week, raw, cutoff)
    c = w * capital_prev
    shares = c / px

    df = pd.DataFrame({
        "stock_code": STOCKS,
        "stock_name": [NAMES[s] for s in STOCKS],
        "sector": [SECTOR[s] for s in STOCKS],
        "price": px.reindex(STOCKS).round(4).values,
        "weight": w.reindex(STOCKS).values,
        "capital": c.reindex(STOCKS).values,
        "shares": shares.reindex(STOCKS).values,
        "lot_size": [LOT_SIZE[s] for s in STOCKS],
    })
    df["integer_lots"] = np.floor(df["shares"] / df["lot_size"])
    df["shares_rounded"] = df["shares"].round(6)
    df["capital_check"] = df["shares_rounded"] * df["price"]

    # 以四舍五入后的股数重新计算，保证提交表内部一致
    capital_check = float(df["capital_check"].sum())
    df["weight_check"] = df["capital_check"] / capital_check

    df.to_csv(out / f"portfolio{suffix}.csv", index=False)

    price_date = str(raw.loc[:cutoff].index[-1].date())
    cutoff_complete = (
        price_date == str(pd.Timestamp(cutoff).date())
        and coverage["hfq_complete"]
        and (strategy != "capm" or coverage["index_complete"])
    )
    params = {
        "week": week,
        "cutoff": str(pd.Timestamp(cutoff).date()),
        "trading_week_end": WEEK_DATES[str(week)]["end"],
        "strategy": strategy,
        "k": (k_effective if strategy == "tilt" else None),
        "k_requested": (k if strategy == "tilt" else None),
        "k_override_reason": override,
        "tracking_error_budget": te if strategy == "tilt" else None,
        "floor": floor,
        "cap": cap,
        "lam": lam if strategy in ("capm", "signal") else None,
        "rf": rf if strategy == "capm" else None,
        "market_premium": premium if strategy == "capm" else None,
        "gmv_window": 104 if strategy == "gmv" else None,
        "gmv_floor": 0.01 if strategy == "gmv" else None,
        "gmv_cap": 0.25 if strategy == "gmv" else None,
        "capital_prev": capital_prev,
        "capital_check": capital_check,
        "sum_weights": float(df["weight"].sum()),
        "gross_exposure": float(df["weight"].abs().sum()),
        "n_short": int((df["weight"] < 0).sum()),
        "ex_ante_vol_shrunk%": round(vol_shrunk * 100, 2),
        "ex_ante_vol_sample%": round(vol_sample * 100, 2),
        "data_source": meta.get("raw_source"),
        "data_last_weekly": meta.get("raw_last_weekly"),
        "actual_price_date": price_date,
        "data_coverage": coverage,
        "cutoff_data_complete": cutoff_complete,
        "shorting_allowed": floor < 0,
        "trial": trial,
        "submission_ready": not trial and cutoff_complete,
        "variant": variant,
        "variant_reason": variant_reason,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "signals": ({s: round(float(aux[s]), 4) for s in STOCKS}
                    if strategy in ("tilt", "signal", "top4") and aux is not None else None),
        "beta": ({s: round(float(aux[s]), 4) for s in STOCKS}
                 if strategy == "capm" and aux is not None else None),
        "weights": {s: round(float(w[s]), 6) for s in STOCKS},
    }
    (out / f"params{suffix}.json").write_text(json.dumps(params, ensure_ascii=False, indent=2),
                                              encoding="utf-8")

    with pd.ExcelWriter(out / f"submission{suffix}.xlsx", engine="openpyxl") as xw:
        summary = pd.DataFrame({
            "Item": ["Week", "Cutoff (valuation date)", "Trading week end", "Strategy",
                     "Lambda", "Lower weight bound", "Upper weight bound",
                     "Risk-free rate", "Market risk premium",
                     "Ex-ante volatility, shrunk (%)", "Ex-ante volatility, sample (%)",
                     "Initial / remaining capital (HKD)", "Capital after share rounding (HKD)",
                     "Sum of weights", "Gross exposure", "Number of short positions",
                     "Shorting allowed", "Actual price date", "Trial run", "Submission ready"],
            "Value": [week, params["cutoff"], params["trading_week_end"], strategy,
                      params["lam"], params["floor"], params["cap"],
                      params["rf"], params["market_premium"],
                      params["ex_ante_vol_shrunk%"], params["ex_ante_vol_sample%"],
                      round(capital_prev, 2), round(capital_check, 2),
                      round(params["sum_weights"], 6), round(params["gross_exposure"], 4),
                      params["n_short"], params["shorting_allowed"], params["actual_price_date"],
                      params["trial"], params["submission_ready"]],
        })
        summary.to_excel(xw, sheet_name="Summary", index=False)
        sub = df[["stock_code", "stock_name", "price", "weight", "capital", "shares_rounded"]].copy()
        sub.columns = ["Stock Code", "Stock Name", "Price (HKD)", "Weight",
                       "Capital Allocated (HKD)", "Number of Shares"]
        sub["Weight"] = sub["Weight"].round(6)
        # Make the displayed six-decimal weights sum to exactly 1 without touching
        # the optimizer output or the share calculation.
        weight_residual = round(1.0 - float(sub["Weight"].sum()), 6)
        sub.loc[sub["Weight"].idxmax(), "Weight"] = round(
            float(sub.loc[sub["Weight"].idxmax(), "Weight"]) + weight_residual, 6)
        sub["Capital Allocated (HKD)"] = sub["Capital Allocated (HKD)"].round(2)
        sub.to_csv(out / f"submission{suffix}.csv", index=False)
        sub.to_excel(xw, sheet_name="Submission", index=False)
        df.to_excel(xw, sheet_name="Details", index=False)
        notes = pd.DataFrame({
            "Item": ["Valuation date (p_{s,i-1})", "Trading week", "Initial capital C_0",
                     "Weight formula", "Shares formula", "Capital formula", "Return formula",
                     "Share rounding", "Data source", "Submission status", "Variant reason"],
            "Value": [params["cutoff"], f"{params['cutoff']} to {params['trading_week_end']}",
                      f"HKD {params['capital_prev']:,.2f}", "w_s = c_s / C",
                      "h_s = c_s / p_s  (fractional shares)", "C_i = sum_s p_{s,i} * h_{s,i}",
                      "R_i = (C_i - C_{i-1}) / C_{i-1}",
                      "Shares are given to 6 decimals; course formula allows fractional shares",
                      "Sina Finance raw (unadjusted) Friday close",
                      "TRIAL ONLY - DO NOT SUBMIT" if trial else (
                          "Ready for manual review" if params["submission_ready"]
                          else "INCOMPLETE - DO NOT SUBMIT"),
                      variant_reason or ""],
        })
        notes.to_excel(xw, sheet_name="Notes", index=False)
        for sheet in ["Submission", "Details"]:
            ws = xw.book[sheet]
            start_col = 3 if sheet == "Submission" else 4
            for row in ws.iter_rows(min_row=2, min_col=start_col, max_col=6 if sheet == "Submission" else 12):
                if sheet == "Submission":
                    row[0].number_format = "#,##0.0000"
                    row[1].number_format = "0.0000%"
                    row[2].number_format = "#,##0.00"
                    row[3].number_format = "#,##0.000000"
                else:
                    row[1].number_format = "0.0000%"
                    row[2].number_format = "#,##0.00"
                    row[3].number_format = "#,##0.000000"
                    row[4].number_format = "0"
                    row[5].number_format = "0"
                    row[6].number_format = "#,##0.000000"
                    row[7].number_format = "#,##0.00"
                    row[8].number_format = "0.0000%"

    write_report(week, df, params, out, suffix)
    print(f"[build] week{week}{suffix}: strategy={strategy} k={params['k']} "
          f"capital={capital_prev:,.2f} gross={params['gross_exposure']:.2f}")
    print(f"[build] price_date={price_date} trial={trial} "
          f"submission_ready={params['submission_ready']}")
    if override:
        print(f"[build] rule override: {override}")
    print(df[["stock_code", "price", "weight", "capital", "shares"]].round(4).to_string(index=False))
    return df, params


def write_report(week: int, df: pd.DataFrame, params: dict, out: Path, suffix: str):
    lines = [
        f"# Week {week} portfolio snapshot",
        "",
        ("> **TRIAL ONLY - DO NOT SUBMIT.** This run uses the last available data before "
         f"the `{params['cutoff']}` cutoff." if params.get("trial")
         else f"> **Submission status:** {'READY FOR MANUAL REVIEW' if params.get('submission_ready') else 'INCOMPLETE - DO NOT SUBMIT'}"),
        "",
        f"- Cutoff (valuation date): **{params['cutoff']}** (Friday close)",
        f"- Actual price date used: **{params.get('actual_price_date', params['cutoff'])}**",
        f"- Trading week: **{params['cutoff']} -> {params['trading_week_end']}**",
        f"- Strategy: `{params['strategy']}`" + (f", k = {params['k']}" if params["k"] else ""),
        (f"- Parameters: lambda = **{params['lam']}**; bounds = "
         f"**[{params['floor']:.0%}, {params['cap']:.0%}]**; "
         f"`r_f` = **{params['rf']:.2%}**; market premium = **{params['market_premium']:.2%}**"
         if params["strategy"] == "capm" else
         f"- Weight bounds: **[{params['floor']:.0%}, {params['cap']:.0%}]**"),
        f"- Capital at start: **HKD {params['capital_prev']:,.2f}**",
        f"- Sum of weights: {params['sum_weights']:.6f}; gross exposure: {params['gross_exposure']:.4f}; "
        f"shorts: {params['n_short']}",
        (f"- Ex-ante annualised volatility: **{params['ex_ante_vol_shrunk%']:.2f}%** "
         f"(shrunk covariance); **{params['ex_ante_vol_sample%']:.2f}%** (sample covariance)"),
        (f"- Variant: `{params.get('variant')}`; reason: {params.get('variant_reason')}"
         if params.get("variant") else ""),
        "",
        "## Submission table",
        "",
        "| Code | Name | Price (HKD) | Weight | Capital (HKD) | Shares |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for _, r in df.iterrows():
        lines.append(f"| {r.stock_code} | {r.stock_name} | {r.price:.4f} | {r.weight:.4%} | "
                     f"{r.capital:,.2f} | {r.shares:.6f} |")
    lines += [
        "",
        "Notes: shares follow the course formula `h = c / p` (fractional shares; no board-lot rounding).",
        "`capital_check` in `portfolio.csv` uses the rounded shares and is the internally consistent value.",
    ]
    (out / f"report{suffix}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


# ----------------------------------------------------------------------------- evaluate
def evaluate(week: int):
    out = WEEKS / f"week{week}"
    pf = pd.read_csv(out / "portfolio.csv", dtype={"stock_code": str})
    pf["stock_code"] = pf["stock_code"].str.zfill(4)
    raw, hfq, ret, idx, meta = load_data()
    params = json.loads((out / "params.json").read_text(encoding="utf-8"))
    cutoff, end = params["cutoff"], params["trading_week_end"]

    p0 = prices_asof(raw, cutoff)
    px_end = raw.loc[:end]
    if px_end.empty or px_end.index[-1] < pd.Timestamp(end):
        print(f"[evaluate] target week not complete yet: last price {raw.index[-1].date()} < {end}")
        return None
    p1 = px_end.iloc[-1]

    df = pf.copy()
    df["p_start"] = df["stock_code"].map(p0)
    df["p_end"] = df["stock_code"].map(p1)
    df["c_start"] = df["shares_rounded"] * df["p_start"]
    df["c_end"] = df["shares_rounded"] * df["p_end"]
    df["stock_return"] = df["p_end"] / df["p_start"] - 1
    df["pnl"] = df["c_end"] - df["c_start"]
    df["contribution"] = df["pnl"] / df["c_start"].sum()

    c_start = float(df["c_start"].sum())
    c_end = float(df["c_end"].sum())
    r = c_end / c_start - 1
    ew_r = float(df["stock_return"].mean())
    summary = {
        "week": week, "cutoff": cutoff, "end": end,
        "capital_start": c_start, "capital_end": c_end, "return": r,
        "ew_return": ew_r, "active_return": r - ew_r,
        "hit_stocks": int((df["pnl"] > 0).sum()), "n_stocks": len(df),
        "worst_stock": str(df.loc[df["pnl"].idxmin(), "stock_code"]),
        "best_stock": str(df.loc[df["pnl"].idxmax(), "stock_code"]),
    }
    df.to_csv(out / "realized.csv", index=False)
    (out / "realized_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2),
                                               encoding="utf-8")
    append_ledger(summary)
    print(f"[evaluate] week{week}: C {c_start:,.2f} -> {c_end:,.2f}, R={r:+.4%}, "
          f"EW={ew_r:+.4%}, active={r - ew_r:+.4%}")
    print(df[["stock_code", "p_start", "p_end", "stock_return", "contribution"]].round(4).to_string(index=False))
    return summary


def append_ledger(summary: dict):
    path = HERE / "ledger.md"
    header = ("# GP2 周度台账（append-only）\n\n"
              "| Week | Cutoff | Week end | C start (HKD) | C end (HKD) | R | EW R | Active | Hit | Best | Worst |\n"
              "|---|---|---|---:|---:|---:|---:|---:|---:|---|---|\n")
    if not path.exists():
        path.write_text(header, encoding="utf-8")
    line = (f"| {summary['week']} | {summary['cutoff']} | {summary['end']} | "
            f"{summary['capital_start']:,.2f} | {summary['capital_end']:,.2f} | "
            f"{summary['return']:+.4%} | {summary['ew_return']:+.4%} | "
            f"{summary['active_return']:+.4%} | {summary['hit_stocks']}/10 | "
            f"{summary['best_stock']} | {summary['worst_stock']} |\n")
    with path.open("a", encoding="utf-8") as f:
        f.write(line)


def verify(week: int, expected_cutoff: str | None = None,
           variant: str | None = None) -> dict:
    """Run the six submission checks and write an auditable JSON result."""
    out = WEEKS / f"week{week}"
    suffix = f"_{variant}" if variant else ""
    params_path = out / f"params{suffix}.json"
    portfolio_path = out / f"portfolio{suffix}.csv"
    if not params_path.exists() or not portfolio_path.exists():
        raise FileNotFoundError(f"missing {params_path} or {portfolio_path}")

    params = json.loads(params_path.read_text(encoding="utf-8"))
    pf = pd.read_csv(portfolio_path, dtype={"stock_code": str})
    pf["stock_code"] = pf["stock_code"].str.zfill(4)
    raw, _, _, _, _ = load_data()

    checks: list[dict] = []
    cutoff_value = params["cutoff"]
    cutoff_ok = expected_cutoff is None or cutoff_value == str(pd.Timestamp(expected_cutoff).date())
    checks.append({
        "item": "cutoff",
        "status": "PASS" if cutoff_ok else "FAIL",
        "value": cutoff_value,
        "detail": "matches requested cutoff" if cutoff_ok else f"expected {expected_cutoff}",
    })

    if week == 1:
        capital_expected = INITIAL_CAPITAL
        capital_source = "C_0"
    else:
        prev_path = WEEKS / f"week{week - 1}" / "portfolio.csv"
        if not prev_path.exists():
            raise FileNotFoundError(f"missing {prev_path} for capital_prev check")
        prev = pd.read_csv(prev_path, dtype={"stock_code": str})
        prev["stock_code"] = prev["stock_code"].str.zfill(4)
        prev["shares"] = prev["shares_rounded"]
        px = prices_asof(raw, cutoff_value)
        capital_expected = float((prev["shares"] * prev["stock_code"].map(px)).sum())
        capital_source = "previous portfolio shares x raw cutoff prices"
    capital_diff = abs(float(params["capital_prev"]) - capital_expected)
    checks.append({
        "item": "capital_prev",
        "status": "PASS" if capital_diff <= 0.01 else "FAIL",
        "value": round(float(params["capital_prev"]), 2),
        "detail": f"{capital_source}; expected={capital_expected:.2f}, diff={capital_diff:.6f}",
    })

    submission_path = out / f"submission{suffix}.csv"
    if submission_path.exists():
        submission = pd.read_csv(submission_path, dtype={"Stock Code": str})
        weight_sum = float(submission["Weight"].sum())
        weight_source = "submission.csv weights (six-decimal submission values)"
    else:
        weight_sum = float(pf["weight"].sum())
        weight_source = "portfolio.csv optimizer weights"
    checks.append({
        "item": "sum_weights",
        "status": "PASS" if abs(weight_sum - 1.0) <= 1e-8 else "FAIL",
        "value": round(weight_sum, 10),
        "detail": weight_source,
    })

    codes = set(pf["stock_code"])
    rows_ok = len(pf) == len(STOCKS) and codes == set(STOCKS)
    bounds_ok = bool(pf["weight"].between(float(params["floor"]), float(params["cap"])).all())
    checks.append({
        "item": "ten_rows",
        "status": "PASS" if rows_ok and bounds_ok else "FAIL",
        "value": len(pf),
        "detail": (f"unique={len(codes)}; missing={sorted(set(STOCKS) - codes)}; "
                   f"bounds=[{params['floor']:.2f}, {params['cap']:.2f}]; "
                   f"min={pf['weight'].min():.6f}; max={pf['weight'].max():.6f}"),
    })

    value_from_shares = float((pf["shares_rounded"] * pf["price"]).sum())
    value_diff = abs(value_from_shares - float(params["capital_check"]))
    checks.append({
        "item": "shares_x_price",
        "status": "PASS" if value_diff <= 0.01 else "FAIL",
        "value": round(value_from_shares, 2),
        "detail": f"portfolio.csv shares_rounded x raw price; diff={value_diff:.6f}",
    })

    if params.get("trial"):
        moodle_status = "N/A"
        moodle_detail = "trial variant; do not upload"
    else:
        moodle_status = "PENDING"
        moodle_detail = "manual check required in Moodle"
    checks.append({
        "item": "Moodle_upload",
        "status": moodle_status,
        "value": moodle_status,
        "detail": moodle_detail,
    })

    result = {
        "week": week,
        "variant": variant,
        "trial": bool(params.get("trial")),
        "submission_ready": bool(params.get("submission_ready")),
        "cutoff": cutoff_value,
        "actual_price_date": params.get("actual_price_date"),
        "n_short": int(params.get("n_short", 0)),
        "shorting_allowed": bool(params.get("shorting_allowed")),
        "checks": checks,
    }
    result_path = out / f"verification{suffix}.json"
    result["written_to"] = str(result_path.relative_to(HERE))
    result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[verify] week{week}{suffix}: trial={result['trial']} "
          f"submission_ready={result['submission_ready']}")
    print(pd.DataFrame(checks).to_string(index=False))
    return result


# ----------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description="DASE7310 GP2 portfolio pipeline")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("refresh-data")
    p.add_argument("--end", default=None)
    p.add_argument("--source", choices=["auto", "eastmoney", "sina"], default="sina")
    p.set_defaults(func=lambda a: refresh_data(a.end, a.source))

    p = sub.add_parser("build")
    p.add_argument("--week", type=int, required=True)
    p.add_argument("--cutoff", default=None)
    p.add_argument("--strategy", choices=["gmv", "tilt", "ew", "tangency", "top4",
                                          "capm", "signal"], default="gmv")
    p.add_argument("--k", type=float, default=2.0)
    p.add_argument("--te", type=float, default=0.10)
    p.add_argument("--lam", type=float, default=10.0)
    p.add_argument("--rf", type=float, default=0.02)
    p.add_argument("--premium", type=float, default=0.05)
    p.add_argument("--floor", type=float, default=0.01,
                   help="lower weight bound; set negative to allow shorts (e.g. -0.15)")
    p.add_argument("--cap", type=float, default=0.25,
                   help="upper weight bound (e.g. 0.30 for the Week 2+ long-short setup)")
    p.add_argument("--variant", default=None)
    p.add_argument("--reason", default=None,
                   help="audit reason; required whenever --variant is used")
    p.add_argument("--trial", action="store_true",
                   help="allow a pre-cutoff dry run; requires --variant and --reason")
    p.set_defaults(func=lambda a: build(a.week, a.cutoff or WEEK_DATES[str(a.week)]["cutoff"],
                                        a.strategy, a.k, a.te, a.lam, a.rf, a.premium,
                                        a.floor, a.cap, a.variant, a.reason, a.trial))

    p = sub.add_parser("evaluate")
    p.add_argument("--week", type=int, required=True)
    p.set_defaults(func=lambda a: evaluate(a.week))

    p = sub.add_parser("verify")
    p.add_argument("--week", type=int, required=True)
    p.add_argument("--expected-cutoff", default=None)
    p.add_argument("--variant", default=None)
    p.set_defaults(func=lambda a: verify(a.week, a.expected_cutoff, a.variant))

    p = sub.add_parser("research")
    p.set_defaults(func=lambda a: print("run research_scan.py / research_portfolios.py / research_backtest.py"))

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
