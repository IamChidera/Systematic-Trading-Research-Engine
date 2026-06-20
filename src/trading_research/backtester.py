from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from .metrics import PerformanceSummary, summarize


@dataclass
class Position:
    symbol: str
    quantity: float
    entry_price: float
    cost: float
    peak_price: float
    layers: list[str] = field(default_factory=list)


@dataclass
class Trade:
    symbol: str
    entry_time: pd.Timestamp
    exit_time: pd.Timestamp
    entry_price: float
    exit_price: float
    pnl: float
    exit_reason: str


class BacktestEngine:
    def __init__(self, starting_cash: float = 10_000.0, fee_pct: float = 0.004) -> None:
        self.starting_cash = starting_cash
        self.cash = starting_cash
        self.fee_pct = fee_pct
        self.positions: dict[str, Position] = {}
        self.trades: list[Trade] = []
        self.equity_rows: list[dict] = []

    def equity(self, prices: dict[str, float]) -> float:
        position_value = sum(position.quantity * prices.get(symbol, 0.0) for symbol, position in self.positions.items())
        return self.cash + position_value

    def buy(self, symbol: str, price: float, value: float, layer: str) -> None:
        spend = min(self.cash, value)
        if spend <= 0:
            return
        quantity = spend * (1 - self.fee_pct) / price
        if symbol in self.positions:
            position = self.positions[symbol]
            old_value = position.quantity * position.entry_price
            position.quantity += quantity
            position.cost += spend
            position.entry_price = (old_value + spend) / position.quantity
            position.layers.append(layer)
        else:
            self.positions[symbol] = Position(
                symbol=symbol,
                quantity=quantity,
                entry_price=price,
                cost=spend,
                peak_price=price,
                layers=[layer],
            )
        self.cash -= spend

    def sell(self, symbol: str, price: float, timestamp: pd.Timestamp, reason: str) -> None:
        position = self.positions.pop(symbol, None)
        if position is None:
            return
        proceeds = position.quantity * price * (1 - self.fee_pct)
        pnl = proceeds - position.cost
        self.cash += proceeds
        self.trades.append(
            Trade(
                symbol=symbol,
                entry_time=timestamp,
                exit_time=timestamp,
                entry_price=position.entry_price,
                exit_price=price,
                pnl=pnl,
                exit_reason=reason,
            )
        )

    def record_equity(self, timestamp: pd.Timestamp, prices: dict[str, float]) -> None:
        self.equity_rows.append({"timestamp": timestamp, "equity": self.equity(prices)})

    def summary(self) -> PerformanceSummary:
        equity_curve = pd.DataFrame(self.equity_rows)
        trade_pnls = [trade.pnl for trade in self.trades]
        return summarize(equity_curve, trade_pnls, self.starting_cash)
