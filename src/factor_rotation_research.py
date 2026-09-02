import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from enhanced_timing_strategies import benchmark_stats, timing_returns
from index_timing_research import INDEXES, factor_ic, perf_stats, zscore


PROJECT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_DIR / "data"
OUT_DIR = PROJECT_DIR / "outputs"


def load_price(index_name: str, start_date: str, end_date: str) -> pd.DataFrame:
    code = INDEXES[index_name]
    path = DATA_DIR / f"{index_name}_{code}_20150101_20260902.csv"
    df = pd.read_csv(path, parse_dates=["trade_date"]).set_index("trade_date").sort_index()
    return df[(df.index >= pd.to_datetime(start_date)) & (df.index <= pd.to_datetime(end_date))]


def load_constituent_features(index_name: str, start_date: str, end_date: str) -> pd.DataFrame:
    path = DATA_DIR / f"constituent_features_{index_name}_{start_date}_{end_date}.csv"
    if not path.exists():
        raise FileNotFoundError(f"Missing {path}. Run constituent_factor_research.py first.")
    return pd.read_csv(path, parse_dates=["trade_date"]).set_index("trade_date").sort_index()


def rolling_factor_quality(features: pd.DataFrame, close: pd.Series, horizon: int, window: int) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    realized = close.pct_change(horizon)
    ic = {}
    win = {}
    payoff = {}
    for col in features:
        x = features[col].shift(horizon)
        ic[col] = x.rolling(window, min_periods=max(120, window // 2)).corr(realized)
        signal = np.sign(x)
        hit = (signal == np.sign(realized)).astype(float)
        hit[(signal == 0) | realized.isna()] = np.nan
        win[col] = hit.rolling(window, min_periods=max(120, window // 2)).mean()
        payoff[col] = (np.sign(x) * realized).rolling(window, min_periods=max(120, window // 2)).mean()
    ic = pd.DataFrame(ic)
    win = pd.DataFrame(win)
    payoff = pd.DataFrame(payoff)
    icir = ic.rolling(window, min_periods=max(120, window // 2)).mean() / ic.rolling(window, min_periods=max(120, window // 2)).std(ddof=0).replace(0, np.nan)
    quality = icir.abs().rank(axis=1, pct=True) + win.rank(axis=1, pct=True) + payoff.abs().rank(axis=1, pct=True)
    return ic, win, quality


def rotation_score(
    features: pd.DataFrame,
    close: pd.Series,
    horizon: int = 20,
    window: int = 252,
    top_n: int = 6,
    min_win_rate: float = 0.50,
) -> tuple[pd.Series, pd.DataFrame]:
    ic, win, quality = rolling_factor_quality(features, close, horizon, window)
    selected = (quality.rank(axis=1, ascending=False) <= top_n) & (win >= min_win_rate)
    oriented_parts = {}
    for col in features:
        direction = np.sign(ic[col].rolling(window, min_periods=max(120, window // 2)).mean())
        oriented_parts[col] = zscore(features[col], 252) * direction
    oriented = pd.DataFrame(oriented_parts)
    weights = quality.where(selected)
    weights = weights.div(weights.sum(axis=1), axis=0)
    score = (oriented * weights).sum(axis=1)
    return score, weights


def run(args: argparse.Namespace) -> None:
    rows = []
    top_factor_rows = []
    data_start_date = args.data_start_date or args.start_date
    for index_name in args.indexes:
        px = load_price(index_name, data_start_date, args.end_date)
        features = load_constituent_features(index_name, data_start_date, args.end_date).reindex(px.index)
        for window in args.windows:
            for top_n in args.top_ns:
                score, weights = rotation_score(
                    features,
                    px["close"],
                    horizon=args.horizon,
                    window=window,
                    top_n=top_n,
                    min_win_rate=args.min_win_rate,
                )
                for mode in args.modes:
                    ret = timing_returns(px["close"], score.reindex(px.index), mode, args.cost_bps)
                    ret = ret.loc[ret.index >= pd.to_datetime(args.start_date)]
                    st = perf_stats(ret)
                    bench = benchmark_stats(index_name, ret)
                    st.update(
                        {
                            "index": index_name,
                            "strategy": f"factor_rotation_h{args.horizon}_w{window}_top{top_n}",
                            "mode": mode,
                            "window": window,
                            "top_n": top_n,
                            "benchmark_ann_ret": bench.get("ann_ret"),
                            "benchmark_sharpe": bench.get("sharpe"),
                            "benchmark_max_drawdown": bench.get("max_drawdown"),
                        }
                    )
                    rows.append(st)

                avg_w = weights.tail(252).mean().sort_values(ascending=False).head(12)
                for factor, weight in avg_w.items():
                    if pd.notna(weight) and weight > 0:
                        top_factor_rows.append(
                            {
                                "index": index_name,
                                "window": window,
                                "top_n": top_n,
                                "factor": factor,
                                "recent_avg_weight": weight,
                            }
                        )

    OUT_DIR.mkdir(exist_ok=True)
    perf = pd.DataFrame(rows).sort_values("sharpe", ascending=False)
    factors = pd.DataFrame(top_factor_rows)
    suffix = f"{data_start_date}_data_{args.start_date}_bt_{args.end_date}"
    perf.to_csv(OUT_DIR / f"factor_rotation_performance_{suffix}.csv", index=False)
    factors.to_csv(OUT_DIR / f"factor_rotation_recent_weights_{suffix}.csv", index=False)

    md = ["# 成分股穿透因子轮动结果\n"]
    md.append(f"- 数据：{data_start_date} 至 {args.end_date}")
    md.append(f"- 绩效统计：{args.start_date} 至 {args.end_date}")
    md.append(f"- 目标：未来 {args.horizon} 日收益")
    md.append(f"- 规则：滚动窗口内按 ICIR、方向胜率、收益贡献筛选因子；仅保留胜率不低于 {args.min_win_rate:.0%} 的因子；按质量分数加权。\n")
    md.append("## 策略表现前二十")
    md.append(perf.head(20).to_markdown(index=False, floatfmt=".4f"))
    md.append("\n## 最近一年平均入选权重")
    md.append(factors.sort_values(["index", "recent_avg_weight"], ascending=[True, False]).groupby("index", group_keys=False).head(12).to_markdown(index=False, floatfmt=".4f"))
    (OUT_DIR / f"factor_rotation_summary_{suffix}.md").write_text("\n".join(md), encoding="utf-8")
    print((OUT_DIR / f"factor_rotation_summary_{suffix}.md").read_text(encoding="utf-8"))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-date", default="20160101")
    parser.add_argument("--data-start-date", default="")
    parser.add_argument("--end-date", default="20260902")
    parser.add_argument("--indexes", nargs="+", default=["CSI500", "CSI1000", "STAR50"])
    parser.add_argument("--horizon", type=int, default=20)
    parser.add_argument("--windows", nargs="+", type=int, default=[126, 252, 504])
    parser.add_argument("--top-ns", nargs="+", type=int, default=[4, 6, 8])
    parser.add_argument("--min-win-rate", type=float, default=0.50)
    parser.add_argument("--modes", nargs="+", default=["weekly_hold", "monthly_hold", "top_quantile"])
    parser.add_argument("--cost-bps", type=float, default=2.0)
    return parser.parse_args()


if __name__ == "__main__":
    run(parse_args())
