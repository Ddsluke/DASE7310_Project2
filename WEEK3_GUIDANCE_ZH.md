# Week 3 行动指南：信号观点（动量 + 近高点 + 低波动）

> **截止**：2026-11-15（周日）23:59
> **估值截点**：2026-11-13（周五）收盘
> **交易周**：2026-11-16 → 2026-11-20
> **本周目标**：从 Week 2 的“市场观点（CAPM）”，切换到“相对选股观点（信号）”；仍然纯多头、10 只全持有、满仓。
>
> **报告关联**：本周的信号组合是 proposed method 的核心；最终报告要把它和 `BENCHMARKS_ZH.md` 里的六类课程 benchmark 对比（1/N、GMV、有效前沿、切点、两基金、CAPM/HSI）。

---

## 1. 本周时间线

| 时间 | 动作 |
|---|---|
| 11/13（周五）收盘后 | `refresh-data --end 2026-11-13`；`evaluate --week 2` 记录第二周实际收益 |
| 11/14（周六） | `build --week 3 --strategy signal --lam 8`；生成并核对 |
| 11/15（周日）23:59 | 上传 `weeks/week3/submission.xlsx` 到 Moodle |
| 11/20（下周五）收盘后 | `evaluate --week 3`，记录第三周实际收益 |

---

## 2. 本周方法：复合信号观点

### 2.1 信号定义

对每只股票，在截点日计算三个横截面 z 分数，等权平均：

```
z_s = ( z(12 周动量)
      + z(距 52 周高点的距离)
      + z(−26 周波动率) ) / 3
```

- **12 周动量**：过去 12 周累计收益，越高越好；
- **距 52 周高点**：`P_t / max(P over 52w) − 1`，越接近 0（越靠近高点）越好；
- **低波动**：过去 26 周年化波动率的负值，越低波动越好。

这三个信号的 rank IC 在 2020–2026 的每一年都为正（near-high 平均 IC 0.09，t≈3.3），比原始样本均值稳得多。

### 2.2 把信号变成 μ

```
μ_s = κ × z_s
```

- κ = **2%/年 per 1 个 z**（一个温和的映射）；
- 因为 `Σw = 1`，κ 的绝对大小只影响“观点强度”，不影响方向；
- 然后解均值-方差：

```
max_w   μ'w − (λ/2) w'Σw
s.t.    Σ_s w_s = 1
        0.01 ≤ w_s ≤ 0.25
```

- λ = **8**：中等偏保守；
- 协方差：104 周、30% 收缩（与前两周一致）；
- 纯多头，10 只全持有。

### 2.3 为什么 Week 3 用信号，而不是继续 CAPM

| 观点类型 | 回答的问题 | 课程连接 |
|---|---|---|
| GMV（Week 1） | 不考虑收益，风险最低的组合是什么？ | Lecture 2/3 |
| CAPM（Week 2） | 如果市场风险有溢价，高 β 应该多配吗？ | Lecture 4 |
| 信号（Week 3） | 哪些股票相对更强/更弱？ | 特征/因子模型（课程外延伸） |

Week 3 是第一次真正“选股”：不是预测大盘，而是说“过去 3 个月强、接近 52 周高点、波动低的股票，下周更可能继续强”。

---

## 3. 操作步骤（复制即可）

```powershell
$env:MKL_THREADING_LAYER = 'SEQUENTIAL'
$py = 'C:\Users\Administrator\miniforge3\envs\dase7310\python.exe'
cd D:\Backup\Documents\dase7310\DASE7310_GP2_Repo

# 1) 11/13 收盘后：刷新数据
& $py portfolio.py refresh-data --end 2026-11-13

# 2) 记录 Week 2 实际收益
& $py portfolio.py evaluate --week 2

# 3) 生成 Week 3 组合（信号，λ=8）
& $py portfolio.py build --week 3 --cutoff 2026-11-13 --strategy signal --lam 8

# 4) 参考组合（不提交，用于报告对比）
& $py portfolio.py build --week 3 --cutoff 2026-11-13 --strategy gmv --variant ref_gmv
& $py portfolio.py build --week 3 --cutoff 2026-11-13 --strategy capm --lam 15 --variant ref_capm

# 5) 核对
Get-Content weeks\week3\params.json
```

提交文件：

- **Moodle**：`weeks\week3\submission.xlsx`
- 同内容 CSV：`weeks\week3\submission.csv`
- 参数/信号值/权重：`weeks\week3\params.json`
- 参考组合：`portfolio_ref_gmv.csv`、`portfolio_ref_capm.csv`

### 备选：直接 tilt

如果觉得 `signal` 的 μ 映射不好解释，可以用等价的直接 tilt：

```powershell
& $py portfolio.py build --week 3 --cutoff 2026-11-13 --strategy tilt --k 2
```

`k=2` 是主动仓位倍数（不是杠杆），效果和 `signal --lam 5–10` 接近。
**两周不要混用**：要么一直用 `signal`，要么一直用 `tilt`，报告里好解释。

---

## 4. 预期权重（用 10/30 数据的预览，不是最终值）

下面是**假设截点仍是 10/30** 时 `signal --lam 8` 的权重，用于理解方向；11/13 实际数据出来后以 `submission.xlsx` 为准。

| 代码 | 名称 | 预览权重 |
|---|---|---:|
| 0066 | 港铁 | 25.0% |
| 1398 | 工行 | 25.0% |
| 3988 | 中行 | 25.0% |
| 0005 | 汇丰 | 10.7% |
| 1113 | 长实 | 7.7% |
| 0016 | 新鸿基 | 2.6% |
| 0981 | 中芯 | 1.0% |
| 0700 | 腾讯 | 1.0% |
| 9988 | 阿里 | 1.0% |
| 1810 | 小米 | 1.0% |

和 Week 2 CAPM 相比：

- 1398 从 19.6% 升到 25%；
- 3988/0066 保持 25%；
- 1113 从 6.5% 升到 7.7%；
- 0981 从 2.4% 降到 1.0%，0700 从 2.1% 降到 1.0%；
- 组合更集中在地产/银行/港铁这些“强 + 低波”的股票上。

如果 11/13 的数据让某些股票的信号翻转（比如 0981 反弹、动量转正），权重会相应变化——这就是“按实际表现演进”。

---

## 5. 提交前检查（30 秒）

- [ ] `params.json` 的 `cutoff` = **2026-11-13**；
- [ ] `strategy` = `signal`，`lam` = 8，`signals` 已写入 10 个 z 值；
- [ ] `capital_prev` = Week 2 实际剩余资本；
- [ ] 10 行，`Sum of weights = 1`，无负权重，单票 ≥ 1%；
- [ ] `Number of Shares × Price ≈ Capital Allocated`；
- [ ] Moodle 上传成功。

---

## 6. 决策规则与应急预案

| 情况 | 处理 |
|---|---|
| `signal` 组合和 Week 2 CAPM 几乎一样 | 正常；说明信号和 β 观点方向一致。报告里写“两个不同观点收敛到相似组合”，是稳健性证据 |
| 某个信号 z 极端（比如 > 3 或 < −3） | 检查数据是否有拆股/异常；必要时把 z 缩尾到 ±3（`winsorize`），并在 `params.json` 记录 |
| 组合年化波动 > 10.5% | 把 λ 提到 12–15 |
| 组合年化波动 < 8% | 把 λ 降到 5，让观点表达更充分 |
| Week 2 累计主动收益 < −5pp | 按预注册规则，Week 3 仍用信号，但把 λ 从 8 提到 12（更保守）；在 `params.json` 写 `risk_off_trigger` |
| 数据刷新失败 | 检查 `meta.json`；不要用旧数据提交 |
| 组里不想用信号 | 退回 `--strategy gmv`，把 Week 3 当作“回到基准”；报告里说明为什么放弃观点 |

---

## 7. 为 Week 4 预注册的规则

Week 4（11/22 截止，截点 11/20）不再换新模型，而是**调整观点置信度**。请在 Week 3 提交时就写好规则：

```
cumulative_active = Σ_{i=1..3} (R_i − R_EW,i)
if cumulative_active < −5pp:
    Week 4: use signal with λ=20 (or target vol 8–9%), i.e., shrink toward GMV
elif cumulative_active > +5pp:
    Week 4: keep signal λ=8, but cap single name at 20%
else:
    Week 4: keep signal λ=8–10, no change
```

规则写进 `weeks/week4/params.json` 的 `rule` 字段，事后不改。这样报告里可以写：

> “The Week 4 portfolio was not a new model; it was the same signal view with a pre-registered confidence update based on the first three weeks' realised active return.”

---

## 8. 记录与报告素材

提交后保留：

- `params.json`：10 个 z 值、λ、权重、C_{i-1}；
- `submission.xlsx` / `.csv`；
- `report.md`；
- `portfolio_ref_gmv.csv`、`portfolio_ref_capm.csv`；
- 11/20 后：`realized.csv`、`realized_summary.json`。

报告里可以写：

> “Week 3 replaced the CAPM equilibrium mean with a characteristic-based signal (12-week momentum, proximity to the 52-week high, low volatility). The signal has a positive rank IC in every year of the sample; the resulting portfolio is more concentrated in the high-score names (0066, 1398, 3988, 1113) and reduces 0981/0700 to the 1% floor. The realised return and active return vs EW are recorded in `ledger.md`.”

---

## 9. 常见问题

**Q：为什么信号里要加“低波动”？**
A：因为港股高波动股票（0981、9988、1810）在样本里经常出现“高波动 ≠ 高收益”。低波动是一个独立的、稳定的横截面特征；三个信号等权，可以互相抵消一部分噪声。

**Q：κ=2% 是怎么来的？**
A：没有唯一答案，是一个温和的映射。它只影响观点强度，不影响方向；如果你把 κ 改成 1% 或 4%，等价于把 λ 改成 16 或 4。报告里固定写清楚 κ 和 λ 即可。

**Q：信号会不会过拟合？**
A：我们用 2020–2026 全样本看 IC，每年为正，不是只在某一年有效；另外第 2 周 CAPM、第 1 周 GMV 都是独立基准，可以对比。报告里要如实写“信号在 2021–23 弱市也有正 IC，但强度不高”。

**Q：如果 0981 反弹，信号组合会怎样？**
A：信号会把 0981 压到 1% 下限，所以反弹时组合会跑输等权。这是“低波动 + 动量”观点的代价；报告里可以作为“weakness”写。

**Q：Week 3 跑输等权，Week 4 要不要换回去？**
A：按预注册规则：只有累计主动收益 < −5pp 才降风险（提高 λ），不是“一周跑输就换模型”。这样避免事后追改。
