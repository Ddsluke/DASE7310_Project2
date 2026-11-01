# Week 2 行动指南：从 GMV 到 CAPM 市场观点

> **截止**：2026-11-08（周日）23:59
> **估值截点**：2026-11-06（周五）收盘
> **交易周**：2026-11-09 → 2026-11-13
> **本周目标**：从“无观点”的 GMV，沿有效前沿往上走一小步，加入 CAPM 市场观点；仍然纯多头、10 只全持有、满仓。

---

## 1. 本周时间线

| 时间 | 动作 |
|---|---|
| 11/6（周五）收盘后 | `refresh-data --end 2026-11-06`；`evaluate --week 1` 记录第一周实际收益 |
| 11/7（周六） | `build --week 2 --strategy capm --lam 15`；生成并核对提交表 |
| 11/8（周日）23:59 | 上传 `weeks/week2/submission.xlsx` 到 Moodle |
| 11/13（下周五）收盘后 | `evaluate --week 2`，记录第二周实际收益 |

---

## 2. 本周方法：CAPM 观点

### 2.1 公式

课程 Lecture 4 的 CAPM / SML：

```
μ_s = r_f + β_s × (μ_market − r_f)
```

- `β_s`：股票 s 对 HSI 的敏感度，用最近 **104 周**周收益回归估计；
- `r_f`：无风险利率，取 **2%/年**；
- `μ_market − r_f`：市场风险溢价，取 **5%/年**；
- 因为组合约束是 `Σw = 1`，给所有 μ 加同一个常数不改变权重，**真正起作用的是 β 的横截面差异**。

### 2.2 优化问题

```
max_w   μ'w − (λ/2) w'Σw
s.t.    Σ_s w_s = 1
        0.01 ≤ w_s ≤ 0.25
```

- Σ：104 周协方差，30% 收缩（和 Week 1 相同）；
- λ = **15**：保守设置，让组合只从 GMV 往上走一小步；
- 纯多头，不做空；
- 单票 1%–25%，10 只都持有。

### 2.3 为什么用 CAPM，而不是样本均值

| 做法 | 问题 |
|---|---|
| 样本均值 | 中芯 0981 的 104 周平均年化收益约 41%，优化器会给它 25%；但它最近 4 周跌了 32%、年化波动 56.6%。这是典型的估计误差。 |
| CAPM | 只用 β 一个横截面维度，参数少、可解释，是课程 Lecture 4 的均衡模型。 |
| 信号（Week 3） | 用动量/近高点/低波动，数据驱动，稳定性更好。 |

Week 2 用 CAPM 的目的不是“跑赢”，而是**在报告里展示从“无观点”到“有观点”的第一步**：

> GMV（只用 Σ）→ CAPM（加入市场观点 μ）→ Signal（加入相对选股观点）→ Adaptive（调整观点置信度）。

### 2.4 为什么 λ = 15

- λ 越大越保守，越接近 GMV；
- λ = 15 时，组合的预期年化波动大约 **9–10%**，比 Week 1 的 GMV（约 8.8%）只高一点；
- 这样既表达了“高 β 应该多配”的观点，又不会把组合变成高 β 科技赌注。

如果 `build` 出来的组合年化波动 > 11%，把 λ 提高到 20；如果 < 8.5%，把 λ 降到 10。

---

## 3. 操作步骤（复制即可）

```powershell
$env:MKL_THREADING_LAYER = 'SEQUENTIAL'
$py = 'C:\Users\Administrator\miniforge3\envs\dase7310\python.exe'
cd D:\Backup\Documents\dase7310\DASE7310_GP2_Repo

# 1) 11/6 收盘后：刷新数据（raw + hfq + HSI）
& $py portfolio.py refresh-data --end 2026-11-06

# 2) 记录 Week 1 实际收益（会写 ledger.md）
& $py portfolio.py evaluate --week 1

# 3) 生成 Week 2 组合（CAPM，λ=15）
& $py portfolio.py build --week 2 --cutoff 2026-11-06 --strategy capm --lam 15

# 4) 生成一个 GMV 参考组合（不提交，只用于对比）
& $py portfolio.py build --week 2 --cutoff 2026-11-06 --strategy gmv --variant ref_gmv

# 5) 提交前核对
Get-Content weeks\week2\params.json
```

提交文件：

- **Moodle**：`weeks\week2\submission.xlsx`
- 同内容 CSV：`weeks\week2\submission.csv`
- 参数/β/权重：`weeks\week2\params.json`
- GMV 参考：`weeks\week2\portfolio_ref_gmv.csv`

---

## 4. 预期权重（用 10/30 数据的预览，不是最终值）

下面是**假设截点仍是 10/30** 时 CAPM λ=15 的权重，用于你理解方向；11/6 实际数据出来后，权重会变，以 `submission.xlsx` 为准。

| 代码 | 名称 | 预览权重 |
|---|---|---:|
| 0066 | 港铁 | 25.0% |
| 3988 | 中行 | 25.0% |
| 1398 | 工行 | 19.6% |
| 0005 | 汇丰 | 10.8% |
| 0016 | 新鸿基 | 6.6% |
| 1113 | 长实 | 6.5% |
| 0981 | 中芯 | 2.4% |
| 0700 | 腾讯 | 2.1% |
| 9988 | 阿里 | 1.0% |
| 1810 | 小米 | 1.0% |

和 Week 1 GMV 相比：

- 1398 从 21.2% 降到 19.6%；
- 0005 从 13.6% 降到 10.8%；
- 1113 从 4.1% 升到 6.5%；
- 0700 从 1.0% 升到 2.1%，0981 从 1.7% 升到 2.4%（高 β 略微加仓）。

变化很小，这是故意的：**Week 2 是“弱观点”，不是“全押科技”**。

---

## 5. 提交前检查（30 秒）

- [ ] `params.json` 的 `cutoff` = **2026-11-06**；
- [ ] `strategy` = `capm`，`lam` = 15，`beta` 已写入；
- [ ] `capital_prev` = Week 1 实际剩余资本（不是固定的 1,000,000）；
- [ ] `submission.xlsx` 的 Summary：`Sum of weights = 1`；
- [ ] 10 行，全部权重 ≥ 1%，无负权重；
- [ ] `Number of Shares × Price ≈ Capital Allocated`；
- [ ] Moodle 上传成功（截图/确认）。

---

## 6. 决策规则与应急预案

| 情况 | 处理 |
|---|---|
| `refresh-data` 失败 | 检查 `data/meta.json` 的 `raw_last_weekly` 是否 = 2026-11-06；不要用 10/30 的旧数据提交 |
| `build` 报 “capm strategy requires HSI” | 检查 `data/index_returns.csv` 是否存在；没有就先用 `--strategy gmv`，并在 `params.json` 记下原因 |
| CAPM 组合年化波动 > 11% | 把 `--lam` 提到 20 |
| CAPM 组合和 GMV 几乎一样（最大差 < 1pp） | 正常，说明观点很弱；保留 CAPM，报告里写“week 2 只做了小幅倾斜” |
| Week 1 GMV 主动收益 < −5pp | 不要因为一周噪声就推翻框架；仍用 CAPM λ=15，但在 `params.json` 记下 “one-week noise, no rule trigger” |
| 组里不想用 CAPM | 退回 `--strategy gmv`，把 Week 2 当作“重复基准”；但报告里要说明为什么没有加观点 |

---

## 7. 记录与报告素材

提交后，在 `weeks/week2/` 里保留：

- `params.json`：β、λ、r_f、premium、权重、C_{i-1}；
- `submission.xlsx` / `.csv`：提交值；
- `report.md`：自动生成的快照说明；
- `portfolio_ref_gmv.csv`：GMV 参考权重，用于对比；
- 11/13 后：`realized.csv`、`realized_summary.json`。

报告里可以写：

> “Week 2 introduced the CAPM equilibrium view. The portfolio moved only slightly from GMV: 1398 21.2% → 19.6%, 0005 13.6% → 10.8%, 1113 4.1% → 6.5%, 0700 1.0% → 2.1%. This is intentional: with λ = 15, the view is expressed but the risk model still dominates. The realised return and the active return vs EW are recorded in `ledger.md`.”

---

## 8. 常见问题

**Q：为什么不用样本均值？**
A：0981 的 104 周平均年化收益约 41%，样本均值优化会给它 25%，但它最近 4 周跌了 32%、波动 56.6%。这是估计误差，不是观点。CAPM 只用 β，参数少得多。

**Q：λ=15 是什么单位？**
A：没有单位，是风险厌恶系数。它只在 `μ'w − (λ/2)w'Σw` 里和 μ、Σ 的相对大小有关。换 μ 的尺度（比如把 premium 从 5% 改成 3%）等价于换 λ，所以报告里要固定写清楚 r_f、premium、λ。

**Q：CAPM 组合还是重仓银行，这不是没观点吗？**
A：观点是“高 β 多配”，但风险模型和 25% 上限会把它拉回来。Week 2 是弱观点，Week 3 的信号观点会更强。报告里可以把“观点强度”作为一条主线。

**Q：premium 取 5% 有依据吗？**
A：可以用长期港股风险溢价假设，也可以做敏感性（3%/5%/7%）。因为 `Σw=1`，premium 的绝对水平不改变权重，只改变报告里的预期收益数字；真正影响权重的是 β 的横截面差异。

**Q：如果 Week 2 跑输等权怎么办？**
A：一周结果不能说明 CAPM 无效。按预注册规则，只有累计主动收益 < −5pp 才调整；而且 Week 3 会换一个不同的观点（信号），报告里正好可以对比“市场观点 vs 选股观点”。
