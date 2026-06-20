from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .indicators import momentum, rsi
from .regimes import ema300_trend, momentum_damage_gate, ret60_damage_gate, volume_damage_gate


@dataclass(frozen=True)
class Signal:
    symbol: str
    should_enter: bool
    should_exit: bool
    score: float
    reason: str


def prepare_strategy_frame(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    result["rsi14"] = rsi(result["close"], 14)
    result["mom7"] = momentum(result["close"], 7)
    result["mom30"] = momentum(result["close"], 30)
    result["mom90"] = momentum(result["close"], 90)
    result["ranking_score"] = result["mom90"] + result["mom30"] + 0.25 * result["mom7"]
    return result


def mean_reversion_signal(symbol: str, row: pd.Series, regime_ok: bool) -> Signal:
    enter = bool(regime_ok and row["rsi14"] < 20)
    return Signal(
        symbol=symbol,
        should_enter=enter,
        should_exit=not regime_ok,
        score=float(row.get("rsi14", 0.0)),
        reason="rsi_pullback" if enter else "no_signal",
    )


def trend_pyramid_signal(symbol: str, row: pd.Series, market_row: pd.Series, gate: str = "ema300") -> Signal:
    gate_functions = {
        "ema300": ema300_trend,
        "momentum_damage": momentum_damage_gate,
        "volume_damage": volume_damage_gate,
        "ret60_damage": ret60_damage_gate,
    }
    regime_ok = gate_functions[gate](market_row)
    score = float(row["ranking_score"])
    enter = bool(regime_ok and score > 0.75)
    return Signal(
        symbol=symbol,
        should_enter=enter,
        should_exit=not regime_ok,
        score=score,
        reason=f"{gate}_score" if enter else "no_signal",
    )


def top_ranked_assets(frames: dict[str, pd.DataFrame], timestamp: pd.Timestamp, limit: int = 2) -> list[str]:
    ranked = []
    for symbol, frame in frames.items():
        if timestamp not in frame.index:
            continue
        row = frame.loc[timestamp]
        score = float(row.get("ranking_score", 0.0))
        if score > 0.75:
            ranked.append((score, symbol))
    ranked.sort(reverse=True)
    return [symbol for _, symbol in ranked[:limit]]
