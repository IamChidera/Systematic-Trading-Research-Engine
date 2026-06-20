from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from trading_research.backtester import BacktestEngine
from trading_research.regimes import add_regime_columns, ema300_trend
from trading_research.strategies import prepare_strategy_frame, top_ranked_assets


def load_symbol(data_dir: Path, symbol: str) -> pd.DataFrame:
    path = data_dir / f"{symbol}.csv"
    frame = pd.read_csv(path)
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
    frame = frame.set_index("timestamp").sort_index()
    return prepare_strategy_frame(add_regime_columns(frame)).dropna()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--symbols", nargs="+", required=True)
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)
    parser.add_argument("--starting-cash", type=float, default=10_000.0)
    args = parser.parse_args()

    frames = {symbol: load_symbol(args.data_dir, symbol) for symbol in args.symbols}
    dates = sorted(set.intersection(*(set(frame.index) for frame in frames.values())))
    start = pd.Timestamp(args.start, tz="UTC")
    end = pd.Timestamp(args.end, tz="UTC")
    dates = [date for date in dates if start <= date <= end]
    engine = BacktestEngine(starting_cash=args.starting_cash)

    for date in dates:
        prices = {symbol: float(frame.loc[date, "close"]) for symbol, frame in frames.items()}
        market_ok = ema300_trend(frames[args.symbols[0]].loc[date])
        leaders = top_ranked_assets(frames, date, limit=2) if market_ok else []

        for symbol in list(engine.positions):
            if not market_ok or symbol not in leaders:
                engine.sell(symbol, prices[symbol], date, "regime_or_rank_exit")

        if market_ok:
            for symbol in leaders:
                if symbol not in engine.positions:
                    engine.buy(symbol, prices[symbol], engine.equity(prices) * 0.35, "initial")

        engine.record_equity(date, prices)

    summary = engine.summary()
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
