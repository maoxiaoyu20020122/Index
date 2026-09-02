import argparse
import math
import os
from pathlib import Path

import numpy as np
import pandas as pd

from index_timing_research import INDEXES, factor_ic, perf_stats, zscore
from enhanced_timing_strategies import benchmark_stats, timing_returns


PROJECT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_DIR / "data"
OUT_DIR = PROJECT_DIR / "outputs"


def month_ranges(start_date: str, end_date: str) -> list[tuple[str, str]]:
    periods = pd.period_range(pd.to_datetime(start_date), pd.to_datetime(end_date), freq="M")
    ranges = []
    for p in periods:
        start = max(p.start_time, pd.to_datetime(start_date))
        end = min(p.end_time, pd.to_datetime(end_date))
        ranges.append((start.strftime("%Y%m%d"), end.strftime("%Y%m%d")))
    return ranges


def load_index_weights(index_name: str, index_code: str, start_date: str, end_date: str, token: str) -> pd.DataFrame:
    path = DATA_DIR / f"constituents_{index_name}_{index_code}_{start_date}_{end_date}.csv"
    if path.exists():
        return pd.read_csv(path, parse_dates=["trade_date"])

    import tushare as ts

    pro = ts.pro_api(token)
    frames = []
    for s, e in month_ranges(start_date, end_date):
        part = pro.index_weight(index_code=index_code, start_date=s, end_date=e)
        if part is not None and not part.empty:
            part["trade_date"] = pd.to_datetime(part["trade_date"])
            latest = part["trade_date"].max()
            frames.append(part[part["trade_date"] == latest])
    if not frames:
        # Fallback: query the whole period. Some accounts return only latest snapshots.
        frames.append(pro.index_weight(index_code=index_code, start_date=start_date, end_date=end_date))
    out = pd.concat(frames, ignore_index=True).drop_duplicates(["index_code", "con_code", "trade_date"])
    out["trade_date"] = pd.to_datetime(out["trade_date"])
    out["weight"] = pd.to_numeric(out["weight"], errors="coerce")
    out.to_csv(path, index=False)
    return out


def trading_dates_from_index(index_name: str, index_code: str, start_date: str, end_date: str) -> list[str]:
    path = DATA_DIR / f"{index_name}_{index_code}_20150101_20260902.csv"
    if not path.exists():
        path = next(DATA_DIR.glob(f"{index_name}_{index_code}_*.csv"))
    df = pd.read_csv(path, parse_dates=["trade_date"])
    mask = (df["trade_date"] >= pd.to_datetime(start_date)) & (df["trade_date"] <= pd.to_datetime(end_date))
    return df.loc[mask, "trade_date"].dt.strftime("%Y%m%d").tolist()


def load_market_daily(start_date: str, end_date: str, token: str) -> pd.DataFrame:
    path = DATA_DIR / f"stock_daily_all_{start_date}_{end_date}.parquet"
    if path.exists():
        return pd.read_parquet(path)

    import tushare as ts

    pro = ts.pro_api(token)
    dates = trading_dates_from_index("CSI500", "000905.SH", start_date, end_date)
    frames = []
    for i, d in enumerate(dates, 1):
        part = pro.daily(trade_date=d)
        if part is not None and not part.empty:
            keep = ["ts_code", "trade_date", "open", "high", "low", "close", "pct_chg", "vol", "amount"]
            frames.append(part[keep])
        if i % 100 == 0:
            print(f"downloaded stock daily {i}/{len(dates)}")
    out = pd.concat(frames, ignore_index=True)
    out["trade_date"] = pd.to_datetime(out["trade_date"])
    for col in ["open", "high", "low", "close", "pct_chg", "vol", "amount"]:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    out.to_parquet(path, index=False)
    return out


def expand_monthly_weights(weights: pd.DataFrame, trade_dates: pd.DatetimeIndex) -> pd.DataFrame:
    rows = []
    weights = weights.sort_values("trade_date")
    for d in trade_dates:
        hist = weights[weights["trade_date"] <= d]
        if hist.empty:
            continue
        snap_date = hist["trade_date"].max()
        snap = hist[hist["trade_date"] == snap_date][["con_code", "weight"]].copy()
        snap["trade_date"] = d
        rows.append(snap)
    if not rows:
        return pd.DataFrame(columns=["trade_date", "con_code", "weight"])
    out = pd.concat(rows, ignore_index=True)
    out["weight"] = out["weight"] / out.groupby("trade_date")["weight"].transform("sum")
    return out


def build_constituent_features(index_name: str, index_code: str, start_date: str, end_date: str, token: str) -> pd.DataFrame:
    weights = load_index_weights(index_name, index_code, start_date, end_date, token)
    stock = load_market_daily(start_date, end_date, token)
    trade_dates = pd.to_datetime(trading_dates_from_index(index_name, index_code, start_date, end_date))
    daily_w = expand_monthly_weights(weights, pd.DatetimeIndex(trade_dates))
    if daily_w.empty:
        raise RuntimeError(f"No weights for {index_name}")

    panel = stock.merge(daily_w, left_on=["trade_date", "ts_code"], right_on=["trade_date", "con_code"], how="inner")
    panel = panel.sort_values(["ts_code", "trade_date"])
    g = panel.groupby("ts_code", group_keys=False)
    panel["ret_1d"] = panel["pct_chg"] / 100.0
    panel["mom_20d"] = g["close"].pct_change(20)
    panel["mom_60d"] = g["close"].pct_change(60)
    panel["ma20"] = g["close"].transform(lambda s: s.rolling(20, min_periods=10).mean())
    panel["above_ma20"] = (panel["close"] > panel["ma20"]).astype(float)
    panel["high_60d"] = g["high"].transform(lambda s: s.rolling(60, min_periods=20).max())
    panel["near_high_60d"] = (panel["close"] >= panel["high_60d"] * 0.98).astype(float)
    panel["amp_20d"] = g.apply(lambda x: ((x["high"] - x["low"]) / x["close"]).rolling(20, min_periods=10).mean()).reset_index(level=0, drop=True)
    panel["amount_ratio_20d"] = g["amount"].transform(lambda s: s / s.rolling(20, min_periods=10).mean() - 1)
    panel["volatility_60d"] = g["ret_1d"].transform(lambda s: s.rolling(60, min_periods=30).std(ddof=0))
    panel["amount_mean_60d"] = g["amount"].transform(lambda s: s.rolling(60, min_periods=30).mean())

    market_ret = stock.groupby("trade_date")["pct_chg"].mean().sort_index() / 100.0
    panel["market_ret_1d"] = panel["trade_date"].map(market_ret)
    panel["ret_mkt"] = panel["ret_1d"] * panel["market_ret_1d"]
    panel["mkt_sq"] = panel["market_ret_1d"] ** 2
    panel["cov_mkt_60d"] = g["ret_mkt"].transform(lambda s: s.rolling(60, min_periods=30).mean()) - (
        g["ret_1d"].transform(lambda s: s.rolling(60, min_periods=30).mean())
        * g["market_ret_1d"].transform(lambda s: s.rolling(60, min_periods=30).mean())
    )
    panel["var_mkt_60d"] = g["mkt_sq"].transform(lambda s: s.rolling(60, min_periods=30).mean()) - (
        g["market_ret_1d"].transform(lambda s: s.rolling(60, min_periods=30).mean()) ** 2
    )
    panel["beta_60d"] = panel["cov_mkt_60d"] / panel["var_mkt_60d"].replace(0, np.nan)

    def wavg(x: pd.DataFrame, col: str) -> float:
        valid = x[[col, "weight"]].dropna()
        if valid.empty:
            return np.nan
        return float((valid[col] * valid["weight"]).sum() / valid["weight"].sum())

    rows = []
    for d, x in panel.groupby("trade_date"):
        ret = x["ret_1d"]
        weights_d = x["weight"]
        crowding = {}
        for sort_col, prefix in [("mom_20d", "mom20"), ("amount_ratio_20d", "amount20")]:
            valid_sort = x.dropna(subset=[sort_col])
            if len(valid_sort) >= 30:
                low_q = valid_sort[sort_col].quantile(0.2)
                high_q = valid_sort[sort_col].quantile(0.8)
                top = valid_sort[valid_sort[sort_col] >= high_q]
                bottom = valid_sort[valid_sort[sort_col] <= low_q]
                for metric, suffix in [
                    ("amount_mean_60d", "amount_ratio"),
                    ("volatility_60d", "vol_ratio"),
                    ("beta_60d", "beta_ratio"),
                    ("amp_20d", "amp_ratio"),
                ]:
                    top_mean = top[metric].replace([np.inf, -np.inf], np.nan).mean()
                    bottom_mean = bottom[metric].replace([np.inf, -np.inf], np.nan).mean()
                    crowding[f"cf_crowding_{prefix}_{suffix}"] = top_mean / bottom_mean if bottom_mean and not np.isnan(bottom_mean) else np.nan
                crowding[f"cf_spread_{prefix}_ret1d"] = top["ret_1d"].mean() - bottom["ret_1d"].mean()
                crowding[f"cf_spread_{prefix}_next_concentration"] = top["amount"].sum() / x["amount"].sum()
        rows.append(
            {
                "trade_date": d,
                "cf_up_ratio_1d": (ret > 0).mean(),
                "cf_weighted_up_ratio_1d": weights_d[ret > 0].sum() / weights_d.sum(),
                "cf_limit_up_like_ratio": (x["pct_chg"] >= 9.5).mean(),
                "cf_big_down_ratio": (x["pct_chg"] <= -5).mean(),
                "cf_above_ma20_ratio": x["above_ma20"].mean(),
                "cf_weighted_above_ma20": wavg(x, "above_ma20"),
                "cf_near_high_60d_ratio": x["near_high_60d"].mean(),
                "cf_mom20_mean": x["mom_20d"].mean(),
                "cf_mom20_median": x["mom_20d"].median(),
                "cf_mom20_dispersion": x["mom_20d"].std(ddof=0),
                "cf_mom60_mean": x["mom_60d"].mean(),
                "cf_mom60_dispersion": x["mom_60d"].std(ddof=0),
                "cf_amount_ratio20_mean": x["amount_ratio_20d"].mean(),
                "cf_amount_ratio20_top20": x["amount_ratio_20d"].quantile(0.8),
                "cf_amp20_mean": x["amp_20d"].mean(),
                "cf_amount_concentration_top20": x.nlargest(max(1, len(x) // 5), "amount")["amount"].sum() / x["amount"].sum(),
                "cf_weight_concentration_top20": x.nlargest(max(1, len(x) // 5), "weight")["weight"].sum() / x["weight"].sum(),
                "cf_coverage": len(x),
                **crowding,
            }
        )
    features = pd.DataFrame(rows).set_index("trade_date").sort_index()
    for col in list(features.columns):
        if col.startswith("cf_") and col != "cf_coverage":
            features[f"{col}_z"] = zscore(features[col], 252)
            features[f"{col}_chg20"] = features[col].diff(20)
    out_path = DATA_DIR / f"constituent_features_{index_name}_{start_date}_{end_date}.csv"
    features.to_csv(out_path, index_label="trade_date")
    return features


def run(args: argparse.Namespace) -> None:
    token = args.token or os.environ.get("TUSHARE_TOKEN", "813912102bfd4aae584b4aafe45289757157dcd6a1ec4f7ae188da1c")
    if not token and not (DATA_DIR / f"stock_daily_all_{args.start_date}_{args.end_date}.parquet").exists():
        raise SystemExit("Missing token for stock-level download.")
    rows = []
    perf_rows = []
    OUT_DIR.mkdir(exist_ok=True)
    for index_name in args.indexes:
        code = INDEXES[index_name]
        px_path = DATA_DIR / f"{index_name}_{code}_20150101_20260902.csv"
        px = pd.read_csv(px_path, parse_dates=["trade_date"]).set_index("trade_date").sort_index()
        px = px[(px.index >= pd.to_datetime(args.start_date)) & (px.index <= pd.to_datetime(args.end_date))]
        features = build_constituent_features(index_name, code, args.start_date, args.end_date, token)
        for h in [5, 20]:
            future = px["close"].pct_change(h).shift(-h)
            ic = factor_ic(features, future)
            ic.insert(0, "horizon", h)
            ic.insert(0, "index", index_name)
            rows.append(ic)
        ic20 = factor_ic(features, px["close"].pct_change(20).shift(-20))
        selected = ic20.loc[ic20["spearman_ic"].abs() > args.min_abs_ic, "factor"].head(args.top_n).tolist()
        if selected:
            score = pd.concat([np.sign(ic20.set_index("factor").loc[c, "spearman_ic"]) * zscore(features[c], 252) for c in selected], axis=1).mean(axis=1)
            score = score.reindex(px.index)
            for mode in ["zero_threshold", "top_quantile", "weekly_hold", "monthly_hold"]:
                ret = timing_returns(px["close"], score, mode, args.cost_bps)
                st = perf_stats(ret)
                bench = benchmark_stats(index_name, ret)
                st.update(
                    {
                        "index": index_name,
                        "strategy": "constituent_selected_ic20",
                        "mode": mode,
                        "selected_factors": "|".join(selected),
                        "benchmark_ann_ret": bench.get("ann_ret"),
                        "benchmark_sharpe": bench.get("sharpe"),
                        "benchmark_max_drawdown": bench.get("max_drawdown"),
                    }
                )
                perf_rows.append(st)
    ic_out = pd.concat(rows, ignore_index=True).sort_values(["index", "horizon", "spearman_ic"], ascending=[True, True, False])
    perf_out = pd.DataFrame(perf_rows).sort_values("sharpe", ascending=False)
    ic_out.to_csv(OUT_DIR / "constituent_factor_ic.csv", index=False)
    perf_out.to_csv(OUT_DIR / "constituent_strategy_performance.csv", index=False)

    md = ["# 成分股穿透因子研究\n"]
    md.append(f"- 样本：{args.start_date} 至 {args.end_date}")
    md.append("- 成分股：使用 Tushare 月度 index_weight 权重快照，按目标指数交易日前向匹配")
    md.append("- 个股数据：日频行情，构造成分股广度、动量扩散、成交额集中度、均线覆盖率、振幅等穿透因子\n")
    md.append("## 20日 IC 前列")
    md.append(ic_out[ic_out["horizon"] == 20].groupby("index", group_keys=False).head(10).to_markdown(index=False, floatfmt=".5f"))
    md.append("\n## 穿透因子组合表现")
    md.append(perf_out.head(12).to_markdown(index=False, floatfmt=".4f"))
    (OUT_DIR / "constituent_summary.md").write_text("\n".join(md), encoding="utf-8")
    print((OUT_DIR / "constituent_summary.md").read_text(encoding="utf-8"))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-date", default="20200101")
    parser.add_argument("--end-date", default="20260902")
    parser.add_argument("--indexes", nargs="+", default=["CSI500", "CSI1000", "STAR50"])
    parser.add_argument("--token", default="")
    parser.add_argument("--min-abs-ic", type=float, default=0.04)
    parser.add_argument("--top-n", type=int, default=8)
    parser.add_argument("--cost-bps", type=float, default=2.0)
    return parser.parse_args()


if __name__ == "__main__":
    run(parse_args())
