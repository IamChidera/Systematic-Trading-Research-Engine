from __future__ import annotations

import pandas as pd

from .indicators import drawdown_from_rolling_high, ema, momentum, volume_ratio


def add_regime_columns(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    close = result["close"]
    result["ema200"] = ema(close, 200)
    result["ema300"] = ema(close, 300)
    result["ema300_lag30"] = result["ema300"].shift(30)
    result["ret30"] = momentum(close, 30)
    result["ret60"] = momentum(close, 60)
    result["ret90"] = momentum(close, 90)
    result["ret180"] = momentum(close, 180)
    result["dd180"] = drawdown_from_rolling_high(close, 180)
    result["volume_ratio30"] = volume_ratio(result["volume"], 30)
    return result


def ema300_trend(row: pd.Series) -> bool:
    return bool(row["close"] > row["ema300"] and row["ema300"] > row["ema300_lag30"])


def momentum_damage_gate(row: pd.Series) -> bool:
    return bool(row["ret30"] > 0 and row["dd180"] > -0.25)


def volume_damage_gate(row: pd.Series) -> bool:
    return bool(row["dd180"] > -0.25 and row["volume_ratio30"] > 1.0)


def ret60_damage_gate(row: pd.Series) -> bool:
    return bool(row["ret60"] > 0 and row["dd180"] > -0.25)


def score(row: pd.Series) -> float:
    return float(row["ret90"] + row["ret30"] + 0.25 * (row["close"] / row["close_7d"] - 1))
