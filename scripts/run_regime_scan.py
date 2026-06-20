from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from trading_research.regimes import add_regime_columns


def load_symbol(data_dir: Path, symbol: str) -> pd.DataFrame:
    path = data_dir / f"{symbol}.csv"
    frame = pd.read_csv(path)
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
    return frame.set_index("timestamp").sort_index()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--symbols", nargs="+", required=True)
    args = parser.parse_args()

    rows = []
    for symbol in args.symbols:
        frame = add_regime_columns(load_symbol(args.data_dir, symbol))
        rows.append(
            {
                "symbol": symbol,
                "latest_close": round(float(frame["close"].iloc[-1]), 4),
                "ret30_pct": round(float(frame["ret30"].iloc[-1]) * 100, 2),
                "ret60_pct": round(float(frame["ret60"].iloc[-1]) * 100, 2),
                "drawdown_180d_pct": round(float(frame["dd180"].iloc[-1]) * 100, 2),
                "volume_ratio30": round(float(frame["volume_ratio30"].iloc[-1]), 2),
                "ema300_trend": bool(
                    frame["close"].iloc[-1] > frame["ema300"].iloc[-1]
                    and frame["ema300"].iloc[-1] > frame["ema300_lag30"].iloc[-1]
                ),
            }
        )
    print(pd.DataFrame(rows).to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
