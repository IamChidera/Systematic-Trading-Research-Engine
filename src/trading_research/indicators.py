from __future__ import annotations

import numpy as np
import pandas as pd


def ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False).mean()


def sma(series: pd.Series, window: int) -> pd.Series:
    return series.rolling(window).mean()


def rsi(series: pd.Series, window: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / window, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / window, adjust=False).mean()
    relative_strength = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + relative_strength))


def annualized_volatility(returns: pd.Series, window: int, periods_per_year: int = 365) -> pd.Series:
    return returns.rolling(window).std() * np.sqrt(periods_per_year)


def drawdown_from_rolling_high(series: pd.Series, window: int) -> pd.Series:
    rolling_high = series.rolling(window).max()
    return series / rolling_high - 1


def momentum(series: pd.Series, window: int) -> pd.Series:
    return series / series.shift(window) - 1


def volume_ratio(volume: pd.Series, window: int = 30) -> pd.Series:
    return volume / volume.rolling(window).mean()
