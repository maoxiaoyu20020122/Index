import argparse
import math
import os
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats


INDEXES = {
    "CSI500": "000905.SH",
    "CSI1000": "000852.SH",
    "STAR50": "000688.SH",
}


def max_drawdown(nav: pd.Series) -> float:
    dd = nav / nav.cummax() - 1.0
    return float(dd.min())


def perf_stats(ret: pd.Series) -> dict:
    ret = ret.dropna()
    if ret.empty:
        return {}
    nav = (1 + ret).cumprod()
    ann_ret = nav.iloc[-1] ** (252 / len(ret)) - 1
    ann_vol = ret.std(ddof=0) * math.sqrt(252)
    sharpe = ann_ret / ann_vol if ann_vol > 0 else np.nan
    return {
        "ann_ret": ann_ret,
        "ann_vol": ann_vol,
        "sharpe": sharpe,
        "max_drawdown": max_drawdown(nav),
        "win_rate": (ret > 0).mean(),
        "n_days": len(ret),
    }


def load_from_tushare(ts_code: str, start_date: str, end_date: str, token: str) -> pd.DataFrame:
    import tushare as ts

    pro = ts.pro_api(token)
    frames = []
    step_starts = pd.date_range(start=start_date, end=end_date, freq="YS").strftime("%Y%m%d").tolist()
    if start_date not in step_starts:
        step_starts = [start_date] + step_starts
    step_ends = (pd.to_datetime(step_starts[1:]) - pd.Timedelta(days=1)).strftime("%Y%m%d").tolist() + [end_date]
    for s, e in zip(step_starts, step_ends):
        df = pro.index_daily(ts_code=ts_code, start_date=s, end_date=e)
        frames.append(df)
    raw = pd.concat(frames, ignore_index=True).drop_duplicates(["ts_code", "trade_date"])
    raw["trade_date"] = pd.to_datetime(raw["trade_date"])
    raw = raw.sort_values("trade_date").set_index("trade_date")
    cols = ["open", "high", "low", "close", "vol", "amount"]
    return raw[cols].apply(pd.to_numeric, errors="coerce")


def get_index_data(name: str, ts_code: str, start_date: str, end_date: str, token: str, data_dir: Path) -> pd.DataFrame:
    data_dir.mkdir(parents=True, exist_ok=True)
    path = data_dir / f"{name}_{ts_code}_{start_date}_{end_date}.csv"
    if path.exists():
        df = pd.read_csv(path, parse_dates=["trade_date"]).set_index("trade_date")
        return df.sort_index()
    df = load_from_tushare(ts_code, start_date, end_date, token)
    df.to_csv(path, index_label="trade_date")
    return df


def zscore(s: pd.Series, window: int = 252) -> pd.Series:
    mean = s.rolling(window, min_periods=max(20, window // 4)).mean()
    std = s.rolling(window, min_periods=max(20, window // 4)).std(ddof=0)
    return (s - mean) / std.replace(0, np.nan)


def build_factors(df: pd.DataFrame) -> pd.DataFrame:
    close = df["close"]
    amount = df["amount"]
    ret = close.pct_change()
    factors = pd.DataFrame(index=df.index)

    for w in [20, 60, 120, 240]:
        factors[f"mom_{w}d"] = close.pct_change(w)
        ma = close.rolling(w, min_periods=max(10, w // 2)).mean()
        factors[f"price_ma_gap_{w}d"] = close / ma - 1
        factors[f"ma_signal_{w}d"] = np.where(close > ma, 1.0, -1.0)

    factors["mom_120_minus_20"] = close.pct_change(120) - close.pct_change(20)
    factors["mom_fast_slow"] = close.pct_change(20) - close.pct_change(120)
    factors["ma_20_60_gap"] = close.rolling(20).mean() / close.rolling(60).mean() - 1
    factors["ma_60_120_gap"] = close.rolling(60).mean() / close.rolling(120).mean() - 1

    vol20 = ret.rolling(20).std(ddof=0) * math.sqrt(252)
    vol60 = ret.rolling(60).std(ddof=0) * math.sqrt(252)
    factors["neg_vol_20d"] = -vol20
    factors["neg_vol_60d"] = -vol60
    factors["vol_down"] = -(vol20 / vol60 - 1)
    factors["risk_adjusted_mom_60d"] = close.pct_change(60) / vol60
    factors["risk_adjusted_mom_120d"] = close.pct_change(120) / vol60

    amount_ma20 = amount.rolling(20).mean()
    amount_ma60 = amount.rolling(60).mean()
    up = (ret > 0).astype(float)
    factors["amount_ratio_20d"] = amount / amount_ma20 - 1
    factors["amount_ratio_60d"] = amount / amount_ma60 - 1
    factors["up_amount_share_20d"] = (amount * up).rolling(20).sum() / amount.rolling(20).sum()
    factors["price_volume_corr_20d"] = ret.rolling(20).corr(amount.pct_change())
    obv = (np.sign(ret.fillna(0)) * amount).cumsum()
    factors["obv_slope_20d"] = obv.diff(20) / amount.rolling(20).sum()

    high = df["high"]
    low = df["low"]
    factors["donchian_20d"] = close / high.rolling(20).max() - 1
    factors["donchian_60d"] = close / high.rolling(60).max() - 1
    factors["range_position_20d"] = (close - low.rolling(20).min()) / (high.rolling(20).max() - low.rolling(20).min())
    factors["range_position_60d"] = (close - low.rolling(60).min()) / (high.rolling(60).max() - low.rolling(60).min())
    factors["reversal_5d"] = -close.pct_change(5)
    factors["intraday_strength_20d"] = ((close - df["open"]) / df["open"]).rolling(20).mean()
    factors["amplitude_20d"] = -((high - low) / close).rolling(20).mean()
    factors["volatility_breakout"] = close.pct_change(20) * (amount / amount_ma20)

    trend_votes = pd.concat(
        [np.sign(factors[c]) for c in ["mom_20d", "mom_60d", "mom_120d", "ma_20_60_gap", "ma_60_120_gap"]],
        axis=1,
    )
    factors["trend_vote"] = trend_votes.mean(axis=1)
    factors["price_volume_confirm"] = factors["trend_vote"] * zscore(factors["amount_ratio_20d"])
    factors["defensive_trend"] = factors["trend_vote"] + zscore(factors["vol_down"])
    return factors.replace([np.inf, -np.inf], np.nan)


def rolling_oriented_score(factors: pd.DataFrame, close: pd.Series, horizon: int = 5, window: int = 504) -> pd.Series:
    realized = close.pct_change(horizon)
    scores = []
    for col in factors:
        x = factors[col]
        # At date t, this uses pairs whose forward h-day return is already known by t.
        past_ic = x.shift(horizon).rolling(window, min_periods=180).corr(realized)
        signal = zscore(x, 252) * np.sign(past_ic)
        scores.append(signal.rename(col))
    score_df = pd.concat(scores, axis=1)
    strength = score_df.abs().rolling(20, min_periods=5).mean()
    chosen = strength.rank(axis=1, ascending=False) <= 8
    return score_df.where(chosen).mean(axis=1)


def factor_ic(factors: pd.DataFrame, future_ret: pd.Series) -> pd.DataFrame:
    rows = []
    for col in factors:
        tmp = pd.concat([factors[col], future_ret], axis=1).dropna()
        tmp.columns = ["factor", "future_ret"]
        if len(tmp) < 80 or tmp["factor"].nunique() < 5:
            continue
        ic = tmp["factor"].corr(tmp["future_ret"], method="spearman")
        x = tmp["factor"]
        y = tmp["future_ret"]
        long = y[x >= x.rolling(252, min_periods=60).quantile(0.7)]
        short = y[x <= x.rolling(252, min_periods=60).quantile(0.3)]
        rows.append(
            {
                "factor": col,
                "spearman_ic": ic,
                "ic_t_stat": ic * math.sqrt((len(tmp) - 2) / max(1e-12, 1 - ic * ic)),
                "direction_win_rate": (np.sign(x) == np.sign(y)).mean(),
                "top_mean_ret": long.mean(),
                "bottom_mean_ret": short.mean(),
                "top_minus_bottom": long.mean() - short.mean(),
                "obs": len(tmp),
            }
        )
    out = pd.DataFrame(rows)
    return out.sort_values("spearman_ic", key=lambda s: s.abs(), ascending=False)


def timing_backtest(close: pd.Series, factors: pd.DataFrame, factor: str, cost_bps: float = 2.0) -> pd.Series:
    ret = close.pct_change()
    f = factors[factor]
    score = zscore(f).shift(1)
    pos = pd.Series(0.0, index=close.index)
    pos[score > 0] = 1.0
    pos[score < -0.5] = 0.0
    turnover = pos.diff().abs().fillna(pos.abs())
    return pos * ret - turnover * cost_bps / 10000


def composite_signal(factors: pd.DataFrame, selected: list[str]) -> pd.Series:
    if not selected:
        selected = ["trend_vote", "defensive_trend", "risk_adjusted_mom_60d", "price_volume_confirm"]
    parts = [zscore(factors[c]) for c in selected if c in factors]
    return pd.concat(parts, axis=1).mean(axis=1)


def run(args: argparse.Namespace) -> None:
    token = args.token or os.environ.get("TUSHARE_TOKEN", "")
    if not token:
        raise SystemExit("Missing Tushare token. Pass --token or set TUSHARE_TOKEN.")
    data_dir = Path(args.data_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    all_ic = []
    all_perf = []
    all_daily = []
    for name, code in INDEXES.items():
        df = get_index_data(name, code, args.start_date, args.end_date, token, data_dir)
        factors = build_factors(df)
        for h in [1, 5, 20]:
            future_ret = df["close"].pct_change(h).shift(-h)
            ic = factor_ic(factors, future_ret)
            ic.insert(0, "horizon", h)
            ic.insert(0, "index", name)
            all_ic.append(ic)

        ic1 = factor_ic(factors, df["close"].pct_change(5).shift(-5))
        selected = ic1.loc[ic1["spearman_ic"].abs() > 0.02, "factor"].head(6).tolist()
        comp = composite_signal(factors, selected)
        factors["composite"] = comp
        factors["rolling_ic_composite"] = rolling_oriented_score(factors, df["close"], horizon=5)
        selected = selected + ["composite", "rolling_ic_composite", "trend_vote", "defensive_trend"]
        for factor in dict.fromkeys(selected):
            strat = timing_backtest(df["close"], factors, factor, args.cost_bps)
            bench = df["close"].pct_change().reindex(strat.index)
            stats_row = perf_stats(strat)
            bench_row = perf_stats(bench.loc[strat.dropna().index])
            if stats_row:
                stats_row.update({"index": name, "factor": factor, "bench_sharpe": bench_row.get("sharpe")})
                all_perf.append(stats_row)
                daily = pd.DataFrame({"index": name, "factor": factor, "strategy_ret": strat})
                all_daily.append(daily.reset_index())

    ic_out = pd.concat(all_ic, ignore_index=True)
    perf_out = pd.DataFrame(all_perf).sort_values(["index", "sharpe"], ascending=[True, False])
    daily_out = pd.concat(all_daily, ignore_index=True)

    ic_out.to_csv(out_dir / "factor_ic.csv", index=False)
    perf_out.to_csv(out_dir / "timing_performance.csv", index=False)
    daily_out.to_csv(out_dir / "daily_strategy_returns.csv", index=False)

    summary = []
    summary.append("# 指数择时因子检验结果\n")
    summary.append(f"- 样本：{args.start_date} 至 {args.end_date}")
    summary.append(f"- 交易成本：单边 {args.cost_bps:.1f} bps")
    summary.append("- 信号：当日收盘形成，次一交易日生效\n")
    summary.append("## 夏普最高的策略")
    top = perf_out.groupby("index", group_keys=False).head(5)
    summary.append(top.to_markdown(index=False, floatfmt=".4f"))
    summary.append("\n## 5日未来收益 IC 绝对值最高的因子")
    top_ic = ic_out[ic_out["horizon"] == 5].groupby("index", group_keys=False).head(8)
    summary.append(top_ic.to_markdown(index=False, floatfmt=".5f"))
    (out_dir / "summary.md").write_text("\n".join(summary), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-date", default="20150101")
    parser.add_argument("--end-date", default="20260902")
    parser.add_argument("--token", default="")
    parser.add_argument("--data-dir", default="data")
    parser.add_argument("--out-dir", default="outputs")
    parser.add_argument("--cost-bps", type=float, default=2.0)
    return parser.parse_args()


if __name__ == "__main__":
    run(parse_args())
