# 数据说明与更新指南 / Data Guide

> 适用：`DASE7310_GP2_Repo`
> 数据源：新浪财经（AkShare），日线 + 周线，HSI/HSTECH 指数
> 当前数据截止：**2026-10-30**
> 相关代码：`portfolio.py` 的 `refresh_data()`、`load_data()`、`prices_asof()`

---

## 0. 一句话结论

**我们用的两套价格是：**

| 文件 | 复权方式 | AkShare 参数 | 用途 |
|---|---|---|---|
| `data/weekly_closes_raw.csv` | **不复权 / unadjusted** | `adjust=""` | 算股数 `h = c/p`、算资本 `C = p*h` |
| `data/weekly_closes_hfq.csv` | **后复权 / backward-adjusted** | `adjust="hfq"` | 算收益率、信号、协方差、回测 |

**我们没有用前复权（qfq）。** 代码里没有任何地方传 `adjust="qfq"`。

---

## 1. 三种复权的区别（为什么不能混）

| 类型 | 最新价 | 历史价 | 适合做什么 | 本项目 |
|---|---|---|---|---|
| **不复权 raw** | 真实市价 | 当时的真实成交价 | 算股数、算资本、真实持仓 | ✅ 用于股数/资本 |
| **后复权 hfq** | 按最早价放大/缩小 | 以最早价为基准调整，去除分红/拆股 | 算总收益、动量、波动、协方差 | ✅ 用于信号/风险 |
| **前复权 qfq** | 真实市价 | 按最新价调整历史价 | 画长期走势图、做收益率 | ❌ 本项目不用 |

### 关键点：为什么不能用 qfq 算股数

- 前复权把**历史价格**按最新分红/拆股调整，最新价仍然等于真实价；
- 但历史价格已经不是当时的真实成交价；
- 课程公式 `h = c / p` 里的 `p` 是**当时的真实收盘价**；
- 如果用 qfq 的历史价去回算历史股数/资本，会得到“假设今天的分红已经发生”的假价格；
- 所以我们用 **raw** 算股数，用 **hfq** 算收益率/信号。

> 注意：因为 qfq 的最新价 = raw 的最新价，**只看最后一行无法区分 raw 和 qfq**。要区分，必须看历史价或看抓取参数。我们的 `raw` 是 `adjust=""` 抓的，所以是真正的不复权。

---

## 2. 当前数据的证据

### 2.1 抓取参数（代码里写死）

`portfolio.py` 的 `refresh_data()`：

```python
for tag, adjust in [("raw", ""), ("hfq", "hfq")]:
    px, source = _fetch_stocks(START, end, adjust, prefer=prefer)
```

- `raw` → `stock_hk_daily(symbol=..., adjust="")`
- `hfq` → `stock_hk_daily(symbol=..., adjust="hfq")`
- **没有 `qfq`**。

### 2.2 价格对照（2020-01-03 / 2026-10-30）

| 股票 | raw 2020-01-03 | raw 2026-10-30 | hfq 2020-01-03 | hfq 2026-10-30 |
|---|---:|---:|---:|---:|
| 0700 腾讯 | 383.00 | 383.60 | 1936.28 | 2196.93 |
| 0005 汇丰 | 60.40 | 135.70 | 527.45 | 952.05 |
| 0981 中芯 | 12.64 | 42.98 | 1.264 | 4.298 |

- raw 的历史价（腾讯 2020 年 383、汇丰 60.4）是当时的真实市价；
- hfq 的历史价明显被放大/缩小（腾讯 1936、汇丰 527、中芯 1.264）；
- 两者在 2026-10-30 的比值不是 1（汇丰约 7 倍、中芯约 0.1 倍），说明 hfq 确实是复权序列；
- **如果 raw 是 qfq**，它的最新价仍会是 42.98/383.6/135.7（和 raw 一样），但历史价会被分红调整；我们的 raw 历史价是真实价，所以是**不复权**。

### 2.3 `meta.json` 里的审计字段

```json
{
  "raw_adjust": "",
  "hfq_adjust": "hfq",
  "price_convention": "raw = unadjusted; hfq = backward-adjusted; qfq is NOT used"
}
```

以后每次 `refresh-data` 都会写这三个字段，方便审计。

---

## 3. 数据文件说明

| 文件 | 内容 | 用途 |
|---|---|---|
| `data/daily_closes_raw.csv` | 未复权日线（date, stock_code, close） | 股东行动/真实价格检查 |
| `data/daily_closes_hfq.csv` | 后复权日线 | 收益率/信号 |
| `data/weekly_closes_raw.csv` | 未复权周收盘（W-FRI） | **算股数/资本** |
| `data/weekly_closes_hfq.csv` | 后复权周收盘（W-FRI） | **算信号/协方差** |
| `data/weekly_returns_raw.csv` | 未复权周收益 | 辅助检查 |
| `data/weekly_returns_hfq.csv` | 后复权周收益 | 信号/协方差/回测 |
| `data/index_closes.csv` | HSI / HSTECH 周收盘 | CAPM 的 β、市场基准 |
| `data/index_returns.csv` | HSI / HSTECH 周收益 | CAPM/市场对比 |
| `data/meta.json` | 数据源、刷新时间、最后日期、复权参数 | 审计/复现 |

---

## 4. 怎么更新数据（每周）

### 4.1 标准命令

```powershell
$env:MKL_THREADING_LAYER = 'SEQUENTIAL'
$py = 'C:\Users\Administrator\miniforge3\envs\dase7310\python.exe'
cd D:\Backup\Documents\dase7310\DASE7310_GP2_Repo

# 拉取到本周五（示例：2026-11-06）
& $py portfolio.py refresh-data --end 2026-11-06
```

### 4.2 参数

| 参数 | 默认 | 说明 |
|---|---|---|
| `--end` | 今天 | 数据截止日；每周用**目标交易周前的周五** |
| `--source` | `sina` | `sina` / `auto` / `eastmoney`；本网络下东财常被拒，建议保持 `sina` |

### 4.3 它会做什么

1. 拉 10 只股票的**日线**，分别保存 raw（`adjust=""`）和 hfq（`adjust="hfq"`）；
2. 用 `W-FRI` 重采样，取每周最后一根已实现收盘价；
3. 计算周收益（`pct_change`）；
4. 拉 HSI / HSTECH 周收盘与周收益；
5. 写 `data/` 下所有 CSV；
6. 写 `data/meta.json`（来源、刷新时间、最后日期、复权参数）。

### 4.4 更新后必须检查

```powershell
Get-Content data\meta.json
```

确认：

- [ ] `raw_last_weekly` = 本周五；
- [ ] `hfq_last_weekly` = 本周五；
- [ ] `raw_adjust` = `""`，`hfq_adjust` = `"hfq"`；
- [ ] `raw_last_daily_date` 里 10 只股票都是本周五（或本周最后一个交易日）；
- [ ] `data/weekly_closes_raw.csv` 最后一行是 10 只股票的真实收盘价；
- [ ] `data/weekly_closes_hfq.csv` 最后一行存在且无 NaN；
- [ ] `data/index_returns.csv` 最后一行有 HSI/HSTECH。

### 4.5 然后生成组合

```powershell
# 第 2 周示例
& $py portfolio.py build --week 2 --cutoff 2026-11-06 --strategy capm --lam 15
```

`build` 会自动用 **raw** 价格算 `h = c/p`，用 **hfq** 算信号/协方差。

---

## 5. 每周标准流程（和 README 对应）

| 时间 | 动作 |
|---|---|
| 周五收盘后 | `refresh-data --end 本周五`；`evaluate --week 上一周` |
| 周六 | `build --week N --cutoff 本周五`；核对 6 项；生成参考组合 |
| 周日 23:59 前 | 上传 `weeks/weekN/submission.xlsx` 到 Moodle；确认成功 |
| 下周五收盘后 | `evaluate --week N`，更新 `ledger.md` |

---

## 6. 常见问题

### Q1：为什么不用前复权（qfq）？

前复权的最新价 = 真实价，但历史价被最新分红调整；用它回算历史股数/资本会失真。我们的原则是：

- **raw（不复权）算股数/资本**；
- **hfq（后复权）算收益率/信号/协方差**；
- **qfq 只适合画图，不适合本项目会计**。

### Q2：数据源失败怎么办？

- 默认 `--source sina`；
- 如果新浪失败，可以试 `--source auto`（先东财后新浪）或 `--source eastmoney`；
- 本网络下东财经常 `ConnectionError`，所以默认新浪；
- 如果整批失败，脚本会重试 3 次，最后报错；**不要用旧数据提交**。

### Q3：周五是假期，没有收盘价怎么办？

- `W-FRI` 重采样会取该周最后一个交易日；
- `prices_asof` 允许截点前最后一个周价格在 7 天内；
- 如果 `meta.json` 的 `raw_last_weekly` 不是本周五但仍是本周最后一个交易日，通常可以接受；报告里注明“本周最后交易日”。

### Q4：数据会被新浪修订吗？

会。历史复权因子/价格可能被数据源修订。所以：

- 每周的 `weeks/weekN/` 快照是**冻结**的；
- `data/` 是“当前 vintage”，每次 refresh 会覆盖；
- 复现旧周请用 `weeks/weekN/` 里的 `portfolio.csv` / `params.json`，或者 checkout 当时的 git commit；
- 不要把新数据回填到旧快照。

### Q5：分红/拆股会影响组合吗？

- hfq 已经处理分红/拆股，收益率/信号不受影响；
- raw 是真实价，分红除净日会出现价格跳空；
- 课程公式没有显式分红项，所以 4 周组合会计按 raw 价格；
- 如果持有期内有拆股/并股，raw 股数会需要按公司行动调整；本项目 4 周窗口内暂无此类事件，报告里可注明“no corporate actions in the holding period”。

### Q6：怎么确认 `raw` 不是 `qfq`？

- 看代码：`refresh_data()` 里 `("raw", "")`，即 `adjust=""`；
- 看 `meta.json`：`raw_adjust=""`；
- 看历史价：2020-01-03 腾讯 raw = 383.0（真实价），如果是 qfq 会被分红调整到更低；
- 看 `hfq/raw` 比值：2026-10-30 汇丰约 7.0、中芯约 0.1，说明 hfq 是复权序列；raw 是真实价。

### Q7：可以只更新某几只股票吗？

当前脚本是**整批**更新 10 只 + 指数；不做单只更新。这样可以保证同一批数据源、同一 vintage，避免混源。

### Q8：更新后需要 commit 吗？

建议每次 `refresh-data` 后 commit `data/`，这样：

- 数据 vintage 可追溯；
- 旧快照复现时知道当时用的是哪批数据；
- 报告里可以写“data vintage: `meta.json` refresh_time”。

---

## 7. 数据 vintage 与复现

- `data/meta.json` 记录：`requested_start`、`requested_end`、`refresh_time`、`raw_source`、`hfq_source`、`raw_last_weekly`、`hfq_last_weekly`、`raw_adjust`、`hfq_adjust`；
- 每周快照 `weeks/weekN/params.json` 记录 `cutoff`、`capital_prev`、权重、`data_source`、`data_last_weekly`；
- 要复现某周，用该周的 `portfolio.csv` + `params.json` + 当周 `submission.xlsx`；
- 不要用今天重新拉的数据去重算旧周的提交值（分红/复权因子可能已变）。

---

## 8. 一句话总结

> **`weekly_closes_raw.csv` = 不复权，`weekly_closes_hfq.csv` = 后复权，没有前复权。**
> 算股数用 raw，算信号/协方差用 hfq；每周五收盘后跑 `refresh-data --end 本周五`，检查 `meta.json` 和最后一行价格，再 `build`。
