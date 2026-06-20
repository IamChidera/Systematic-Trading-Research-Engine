from __future__ import annotations

import math

import pandas as pd


def normalize_curve(curve: pd.Series, starting_value: float = 10_000.0) -> pd.Series:
    first = float(curve.iloc[0])
    if first <= 0:
        raise ValueError("Cannot normalize an equity curve with a non-positive starting value.")
    return starting_value * curve / first


def blend_curves(curves: dict[str, pd.Series], weights: dict[str, float]) -> pd.Series:
    if set(weights) - set(curves):
        missing = sorted(set(weights) - set(curves))
        raise KeyError(f"Missing curves for: {missing}")
    common_index = None
    for name in weights:
        common_index = curves[name].index if common_index is None else common_index.intersection(curves[name].index)
    if common_index is None or common_index.empty:
        raise ValueError("No overlapping dates between equity curves.")
    blended = pd.Series(0.0, index=common_index)
    for name, weight in weights.items():
        blended = blended + normalize_curve(curves[name].reindex(common_index)) * weight
    return blended


def correlation_matrix(curves: dict[str, pd.Series]) -> pd.DataFrame:
    returns = pd.DataFrame({name: curve.pct_change() for name, curve in curves.items()})
    return returns.corr()


def annualized_sharpe(curve: pd.Series, periods_per_year: int = 365) -> float | None:
    returns = curve.pct_change().dropna()
    if len(returns) < 2 or returns.std() == 0:
        return None
    return float(returns.mean() / returns.std() * math.sqrt(periods_per_year))
