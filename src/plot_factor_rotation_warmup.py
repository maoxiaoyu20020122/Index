import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from enhanced_timing_strategies import timing_returns
from factor_rotation_research import load_constituent_features, load_price, rotation_score
from index_timing_research import perf_stats


PROJECT_DIR = Path(__file__).resolve().parents[1]
OUT_DIR = PROJECT_DIR / "outputs"
PLOT_DIR = OUT_DIR / "plots"


BEST_CONFIGS = {
    "CSI500": {"window": 504, "top_n": 8, "mode": "weekly_hold"},
    "CSI1000": {"window": 504, "top_n": 4, "mode": "weekly_hold"},
    "STAR50": {"window": 504, "top_n": 8, "mode": "monthly_hold"},
}

EARLY_SIGNAL_CONFIGS = {
    "CSI500": {"window": 126, "top_n": 6, "mode": "monthly_hold"},
    "CSI1000": {"window": 126, "top_n": 4, "mode": "monthly_hold"},
    "STAR50": {"window": 126, "top_n": 6, "mode": "monthly_hold"},
}


def nav_from_returns(ret: pd.Series) -> pd.Series:
    ret = ret.dropna()
    return (1.0 + ret).cumprod()


def plot_one(index_name: str, args: argparse.Namespace) -> dict:
    configs = EARLY_SIGNAL_CONFIGS if args.profile == "early_signal" else BEST_CONFIGS
    cfg = configs[index_name]
    px = load_price(index_name, args.data_start_date, args.end_date)
    features = load_constituent_features(index_name, args.data_start_date, args.end_date).reindex(px.index)
    score, _ = rotation_score(
        features,
        px["close"],
        horizon=args.horizon,
        window=cfg["window"],
        top_n=cfg["top_n"],
        min_win_rate=args.min_win_rate,
    )
    ret = timing_returns(px["close"], score.reindex(px.index), cfg["mode"], args.cost_bps)
    ret = ret.loc[ret.index >= pd.to_datetime(args.start_date)]
    bench_ret = px["close"].pct_change().loc[ret.index].fillna(0.0)

    nav = nav_from_returns(ret)
    bench_nav = nav_from_returns(bench_ret)
    common = nav.index.intersection(bench_nav.index)
    nav = nav.loc[common]
    bench_nav = bench_nav.loc[common]
    if not nav.empty:
        nav = nav / nav.iloc[0]
        bench_nav = bench_nav / bench_nav.iloc[0]

    stats = perf_stats(ret)
    bench_stats = perf_stats(bench_ret)
    title = (
        f"{index_name} factor rotation vs benchmark\n"
        f"{args.data_start_date} warmup, {args.start_date}-{args.end_date} backtest, {args.profile}"
    )
    subtitle = (
        f"Strategy ann {stats['ann_ret']:.2%}, Sharpe {stats['sharpe']:.2f}, "
        f"MDD {stats['max_drawdown']:.2%} | "
        f"Benchmark ann {bench_stats['ann_ret']:.2%}, Sharpe {bench_stats['sharpe']:.2f}, "
        f"MDD {bench_stats['max_drawdown']:.2%}"
    )

    PLOT_DIR.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(12, 6.8))
    ax.plot(nav.index, nav, label="Factor rotation", linewidth=2.2, color="#1f77b4")
    ax.plot(bench_nav.index, bench_nav, label="Benchmark", linewidth=1.8, color="#4d4d4d", alpha=0.8)
    ax.set_title(title, fontsize=15, pad=16)
    ax.text(0.0, 1.01, subtitle, transform=ax.transAxes, fontsize=10.5, color="#333333")
    ax.set_ylabel("Net value")
    ax.grid(True, color="#d9d9d9", linewidth=0.8, alpha=0.7)
    ax.legend(loc="upper left")
    fig.autofmt_xdate()
    fig.tight_layout()

    out = PLOT_DIR / f"{index_name}_factor_rotation_{args.profile}_warmup_2014_bt_2016_2026.png"
    fig.savefig(out, dpi=160)
    plt.close(fig)

    return {
        "index": index_name,
        "plot": str(out),
        "mode": cfg["mode"],
        "window": cfg["window"],
        "top_n": cfg["top_n"],
        "ann_ret": stats["ann_ret"],
        "sharpe": stats["sharpe"],
        "max_drawdown": stats["max_drawdown"],
        "benchmark_ann_ret": bench_stats["ann_ret"],
        "benchmark_sharpe": bench_stats["sharpe"],
        "benchmark_max_drawdown": bench_stats["max_drawdown"],
    }


def run(args: argparse.Namespace) -> None:
    rows = [plot_one(index_name, args) for index_name in args.indexes]
    summary = pd.DataFrame(rows)
    summary.to_csv(OUT_DIR / "factor_rotation_warmup_plot_stats.csv", index=False)
    print(summary.to_markdown(index=False, floatfmt=".4f"))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-start-date", default="20140101")
    parser.add_argument("--start-date", default="20160101")
    parser.add_argument("--end-date", default="20260902")
    parser.add_argument("--indexes", nargs="+", default=["CSI500", "CSI1000", "STAR50"])
    parser.add_argument("--horizon", type=int, default=20)
    parser.add_argument("--min-win-rate", type=float, default=0.50)
    parser.add_argument("--cost-bps", type=float, default=2.0)
    parser.add_argument("--profile", choices=["best_sharpe", "early_signal"], default="best_sharpe")
    return parser.parse_args()


if __name__ == "__main__":
    run(parse_args())
