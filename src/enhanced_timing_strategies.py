import math
from pathlib import Path

import numpy as np
import pandas as pd

from index_timing_research import (
    INDEXES,
    build_external_features,
    build_factors,
    get_external_index_panel,
    get_index_data,
    get_optional_external_tables,
    perf_stats,
    zscore,
)


START_DATE = "20150101"
END_DATE = "20260902"
DATA_DIR = Path("data")
OUT_DIR = Path("outputs")


def orienting_ic(factors: pd.DataFrame, close: pd.Series, horizon: int, window: int) -> pd.DataFrame:
    realized = close.pct_change(horizon)
    out = {}
    for col in factors:
        out[col] = factors[col].shift(horizon).rolling(window, min_periods=max(120, window // 2)).corr(realized)
    return pd.DataFrame(out)


def factor_win_rate(factors: pd.DataFrame, close: pd.Series, horizon: int, window: int) -> pd.DataFrame:
    realized = close.pct_change(horizon)
    out = {}
    for col in factors:
        signal = np.sign(factors[col].shift(horizon))
        hit = (signal == np.sign(realized)).astype(float)
        hit[(signal == 0) | realized.isna()] = np.nan
        out[col] = hit.rolling(window, min_periods=max(120, window // 2)).mean()
    return pd.DataFrame(out)


def icir_weighted_score(factors: pd.DataFrame, close: pd.Series, horizon: int = 20, window: int = 252) -> pd.Series:
    ic = orienting_ic(factors, close, horizon, window)
    ic_mean = ic.rolling(window, min_periods=max(120, window // 2)).mean()
    ic_std = ic.rolling(window, min_periods=max(120, window // 2)).std(ddof=0)
    icir = ic_mean / ic_std.replace(0, np.nan)
    oriented = pd.DataFrame({c: zscore(factors[c], 252) * np.sign(ic_mean[c]) for c in factors})
    weights = icir.abs().where(icir.abs().rank(axis=1, ascending=False) <= 10)
    weights = weights.div(weights.sum(axis=1), axis=0)
    return (oriented * weights).sum(axis=1)


def icwr_weighted_score(factors: pd.DataFrame, close: pd.Series, horizon: int = 20, window: int = 252) -> pd.Series:
    wr = factor_win_rate(factors, close, horizon, window)
    ic = orienting_ic(factors, close, horizon, window)
    oriented = pd.DataFrame({c: zscore(factors[c], 252) * np.sign(ic[c]) for c in factors})
    weights = (wr - 0.5).clip(lower=0)
    weights = weights.where(weights.rank(axis=1, ascending=False) <= 10)
    weights = weights.div(weights.sum(axis=1), axis=0)
    return (oriented * weights).sum(axis=1)


def offensive_defensive_score(factors: pd.DataFrame) -> pd.Series:
    parts = []
    for col in [
        "ext_CHINEXT_mom_20d",
        "ext_CHINEXT_amount_ratio_20d",
        "ext_hsgt_north_money_20d",
        "int_amount_ratio_20d",
        "int_price_volume_confirm",
    ]:
        if col in factors:
            parts.append(zscore(factors[col], 252))
    risk_on = pd.concat(parts, axis=1).mean(axis=1)

    defensive_parts = []
    for col in ["int_neg_vol_20d", "int_amplitude_20d", "ext_shibor_3m_level", "ext_shibor_on_level"]:
        if col in factors:
            defensive_parts.append(zscore(factors[col], 252))
    defensive = pd.concat(defensive_parts, axis=1).mean(axis=1)
    return 0.7 * risk_on + 0.3 * defensive


TARGETED_FACTOR_SPECS = {
    "CSI500": [
        ("ext_CHINEXT_mom_20d", 1, 1.2),
        ("ext_CHINEXT_amount_ratio_20d", 1, 1.0),
        ("ext_hsgt_north_money_20d", 1, 0.8),
        ("int_amount_ratio_20d", 1, 0.8),
        ("int_neg_vol_20d", -1, 0.6),
        ("int_donchian_60d", -1, 0.5),
    ],
    "CSI1000": [
        ("ext_CHINEXT_mom_20d", 1, 1.2),
        ("ext_CHINEXT_amount_ratio_20d", 1, 1.0),
        ("int_amount_ratio_20d", 1, 1.0),
        ("ext_hsgt_north_money_20d", 1, 0.8),
        ("int_neg_vol_20d", -1, 0.7),
        ("int_amplitude_20d", -1, 0.5),
    ],
    "STAR50": [
        ("ext_CHINEXT_amount_ratio_20d", 1, 1.2),
        ("int_amount_ratio_20d", 1, 1.2),
        ("ext_hsgt_north_money_20d", 1, 0.8),
        ("ext_shibor_3m_level", 1, 0.7),
        ("int_donchian_60d", -1, 0.6),
        ("int_ma_20_60_gap", -1, 0.5),
    ],
}


def targeted_report_score(index_name: str, factors: pd.DataFrame) -> pd.Series:
    parts = []
    for col, direction, weight in TARGETED_FACTOR_SPECS[index_name]:
        if col in factors:
            parts.append(weight * direction * zscore(factors[col], 252))
    return pd.concat(parts, axis=1).mean(axis=1)


def timing_returns(close: pd.Series, score: pd.Series, mode: str, cost_bps: float = 2.0) -> pd.Series:
    ret = close.pct_change()
    score = score.shift(1)
    pos = pd.Series(0.0, index=close.index)
    if mode == "zero_threshold":
        pos[score > 0] = 1.0
        pos[score < -0.3] = 0.0
    elif mode == "top_quantile":
        q60 = score.rolling(252, min_periods=120).quantile(0.60)
        q30 = score.rolling(252, min_periods=120).quantile(0.30)
        pos[score > q60] = 1.0
        pos[score.between(q30, q60)] = 0.5
        pos[score < q30] = 0.0
    elif mode == "weekly_hold":
        raw = (score > score.rolling(252, min_periods=120).quantile(0.55)).astype(float)
        pos = raw.where(np.arange(len(raw)) % 5 == 0).ffill().fillna(0.0)
    elif mode == "monthly_hold":
        raw = (score > score.rolling(252, min_periods=120).quantile(0.55)).astype(float)
        month_change = close.index.to_period("M") != close.index.to_period("M").shift(1)
        pos = raw.where(month_change).ffill().fillna(0.0)
    else:
        raise ValueError(mode)
    turnover = pos.diff().abs().fillna(pos.abs())
    return pos * ret - turnover * cost_bps / 10000


def benchmark_stats(index_name: str, strategy_ret: pd.Series) -> dict:
    path = DATA_DIR / f"{index_name}_{INDEXES[index_name]}_{START_DATE}_{END_DATE}.csv"
    px = pd.read_csv(path, parse_dates=["trade_date"]).set_index("trade_date").sort_index()
    bench = px["close"].pct_change().reindex(strategy_ret.index)
    return perf_stats(bench.loc[strategy_ret.dropna().index])


def main() -> None:
    token = ""
    external_panel = get_external_index_panel(START_DATE, END_DATE, token, DATA_DIR)
    optional_tables = get_optional_external_tables(START_DATE, END_DATE, token, DATA_DIR)
    rows = []
    daily_rows = []
    for name, code in INDEXES.items():
        df = get_index_data(name, code, START_DATE, END_DATE, token, DATA_DIR)
        factors = pd.concat(
            [
                build_factors(df).add_prefix("int_"),
                build_external_features(df["close"], external_panel, optional_tables),
            ],
            axis=1,
        )
        strategies = {
            "report_icir_12m_20d": icir_weighted_score(factors, df["close"], horizon=20, window=252),
            "report_icwr_12m_20d": icwr_weighted_score(factors, df["close"], horizon=20, window=252),
            "report_icir_6m_20d": icir_weighted_score(factors, df["close"], horizon=20, window=126),
            "report_icwr_6m_20d": icwr_weighted_score(factors, df["close"], horizon=20, window=126),
            "report_offensive_defensive": offensive_defensive_score(factors),
            f"targeted_{name}": targeted_report_score(name, factors),
            f"targeted_{name}_smooth20": targeted_report_score(name, factors).rolling(20, min_periods=5).mean(),
        }
        for strat_name, score in strategies.items():
            for mode in ["zero_threshold", "top_quantile", "weekly_hold", "monthly_hold"]:
                ret = timing_returns(df["close"], score, mode)
                stat = perf_stats(ret)
                bench = benchmark_stats(name, ret)
                stat.update(
                    {
                        "index": name,
                        "strategy": strat_name,
                        "mode": mode,
                        "benchmark_ann_ret": bench.get("ann_ret"),
                        "benchmark_sharpe": bench.get("sharpe"),
                        "benchmark_max_drawdown": bench.get("max_drawdown"),
                    }
                )
                rows.append(stat)
                daily_rows.append(pd.DataFrame({"trade_date": ret.index, "index": name, "strategy": strat_name, "mode": mode, "strategy_ret": ret}))

    out = pd.DataFrame(rows).sort_values("sharpe", ascending=False)
    OUT_DIR.mkdir(exist_ok=True)
    out.to_csv(OUT_DIR / "enhanced_strategy_performance.csv", index=False)
    pd.concat(daily_rows, ignore_index=True).to_csv(OUT_DIR / "enhanced_daily_strategy_returns.csv", index=False)
    top = out.head(20).copy()
    top.to_csv(OUT_DIR / "enhanced_top20.csv", index=False)

    compare_rows = []
    for rank, row in enumerate(out.head(10).itertuples(index=False), 1):
        compare_rows.append(
            {
                "rank": rank,
                "index": row.index,
                "strategy": row.strategy,
                "mode": row.mode,
                "strategy_ann_ret": row.ann_ret,
                "benchmark_ann_ret": row.benchmark_ann_ret,
                "excess_ann_ret": row.ann_ret - row.benchmark_ann_ret,
                "strategy_ann_vol": row.ann_vol,
                "strategy_sharpe": row.sharpe,
                "benchmark_sharpe": row.benchmark_sharpe,
                "sharpe_diff": row.sharpe - row.benchmark_sharpe,
                "strategy_max_drawdown": row.max_drawdown,
                "benchmark_max_drawdown": row.benchmark_max_drawdown,
                "drawdown_improvement": row.max_drawdown - row.benchmark_max_drawdown,
                "strategy_win_rate": row.win_rate,
                "n_days": row.n_days,
            }
        )
    compare = pd.DataFrame(compare_rows)
    compare.to_csv(OUT_DIR / "enhanced_top10_vs_benchmark.csv", index=False)

    md = ["# 研报策略增强实验结果\n", "排序口径：策略夏普从高到低。"]
    md.append(top.to_markdown(index=False, floatfmt=".4f"))
    md.append("\n## 前十增强策略与基准对比")
    md.append(compare.to_markdown(index=False, floatfmt=".4f"))
    (OUT_DIR / "enhanced_summary.md").write_text("\n".join(md), encoding="utf-8")
    print(top.to_string(index=False))


if __name__ == "__main__":
    main()
