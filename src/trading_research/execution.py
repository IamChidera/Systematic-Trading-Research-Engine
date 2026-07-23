"""Broker-neutral portfolio reconciliation and explainable order planning."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal, ROUND_DOWN
from typing import Mapping

from .contracts import PortfolioTarget


@dataclass(frozen=True)
class Position:
    symbol: str
    quantity: float
    price: float

    @property
    def notional(self) -> float:
        return self.quantity * self.price


@dataclass(frozen=True)
class MarketRule:
    min_quantity: float
    quantity_step: float


@dataclass(frozen=True)
class ExecutionPolicy:
    """Account-relative execution controls, without fixed GBP ceilings."""

    policy_id: str = "professional_spot_v1"
    no_trade_band_weight: float = 0.0025
    max_cycle_turnover_fraction: float = 1.0
    max_tickets_per_cycle: int = 8
    buy_cash_buffer_fraction: float = 0.01
    sell_before_buy: bool = True

    def validate(self) -> None:
        if not 0.0 <= self.no_trade_band_weight < 1.0:
            raise ValueError("no_trade_band_weight must be in [0, 1)")
        if not 0.0 < self.max_cycle_turnover_fraction <= 1.0:
            raise ValueError("max_cycle_turnover_fraction must be in (0, 1]")
        if self.max_tickets_per_cycle < 1:
            raise ValueError("max_tickets_per_cycle must be positive")
        if not 0.0 <= self.buy_cash_buffer_fraction < 1.0:
            raise ValueError("buy_cash_buffer_fraction must be in [0, 1)")


@dataclass(frozen=True)
class OrderTicket:
    symbol: str
    side: str
    quantity: float
    notional: float
    reference_price: float
    current_weight: float
    target_weight: float
    reason: str
    status: str = "planned"

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class ReconciliationResult:
    equity: float
    cash: float
    current_weights: Mapping[str, float]
    target_weights: Mapping[str, float]
    proposed_tickets: tuple[OrderTicket, ...]
    executable_tickets: tuple[OrderTicket, ...]
    deferred: tuple[dict, ...]
    execution_phase: str
    policy_id: str

    def as_dict(self) -> dict:
        payload = asdict(self)
        payload["proposed_tickets"] = [ticket.as_dict() for ticket in self.proposed_tickets]
        payload["executable_tickets"] = [ticket.as_dict() for ticket in self.executable_tickets]
        return payload


def _floor_to_step(quantity: float, step: float) -> float:
    if step <= 0:
        raise ValueError("quantity_step must be positive")
    units = (Decimal(str(quantity)) / Decimal(str(step))).to_integral_value(rounding=ROUND_DOWN)
    return float(units * Decimal(str(step)))


def reconcile_portfolio(
    *,
    cash: float,
    positions: Mapping[str, Position],
    target: PortfolioTarget,
    market_rules: Mapping[str, MarketRule],
    reference_prices: Mapping[str, float],
    policy: ExecutionPolicy | None = None,
) -> ReconciliationResult:
    """Create one safe execution phase from current holdings and target weights.

    If sells are required, only sells are executable in this cycle. Buys are
    regenerated after the broker balance is reconciled on the next cycle.
    """

    policy = policy or ExecutionPolicy()
    policy.validate()
    target.validate()
    if cash < 0:
        raise ValueError("cash cannot be negative for an unleveraged spot account")

    holdings_value = sum(position.notional for position in positions.values())
    equity = cash + holdings_value
    if equity <= 0:
        raise ValueError("account equity must be positive")

    symbols = sorted(set(positions) | set(target.asset_weights))
    current_weights = {
        symbol: positions.get(symbol, Position(symbol, 0.0, reference_prices[symbol])).notional / equity
        for symbol in symbols
    }
    proposed: list[OrderTicket] = []
    deferred: list[dict] = []

    for symbol in symbols:
        if symbol not in reference_prices:
            raise KeyError(f"missing reference price for {symbol}")
        if symbol not in market_rules:
            raise KeyError(f"missing market rule for {symbol}")
        price = float(reference_prices[symbol])
        if price <= 0:
            raise ValueError(f"reference price must be positive for {symbol}")

        current_notional = positions.get(symbol, Position(symbol, 0.0, price)).notional
        target_weight = float(target.asset_weights.get(symbol, 0.0))
        target_notional = equity * target_weight
        delta = target_notional - current_notional
        delta_weight = delta / equity
        if abs(delta_weight) < policy.no_trade_band_weight:
            deferred.append({"symbol": symbol, "reason": "inside_no_trade_band", "delta_weight": delta_weight})
            continue

        side = "buy" if delta > 0 else "sell"
        quantity = _floor_to_step(abs(delta) / price, market_rules[symbol].quantity_step)
        if quantity < market_rules[symbol].min_quantity:
            deferred.append(
                {
                    "symbol": symbol,
                    "reason": "below_market_minimum",
                    "quantity": quantity,
                    "minimum": market_rules[symbol].min_quantity,
                }
            )
            continue

        notional = quantity * price
        explanations = target.explanations.get(symbol, ())
        strategy_reason = " | ".join(explanations) if explanations else "target removed or reduced"
        proposed.append(
            OrderTicket(
                symbol=symbol,
                side=side,
                quantity=quantity,
                notional=notional,
                reference_price=price,
                current_weight=current_notional / equity,
                target_weight=target_weight,
                reason=(
                    f"{side.upper()} target difference from {current_notional / equity:.2%} "
                    f"to {target_weight:.2%}; {strategy_reason}"
                ),
            )
        )

    sells = sorted((ticket for ticket in proposed if ticket.side == "sell"), key=lambda item: -item.notional)
    buys = sorted((ticket for ticket in proposed if ticket.side == "buy"), key=lambda item: -item.notional)
    if sells and policy.sell_before_buy:
        phase = "sell"
        selected = sells
        deferred.extend(
            {"symbol": ticket.symbol, "reason": "buy_waits_for_post_sale_reconciliation"}
            for ticket in buys
        )
    else:
        phase = "buy" if buys else "none"
        available_cash = cash * (1.0 - policy.buy_cash_buffer_fraction)
        selected = []
        used_cash = 0.0
        for ticket in buys:
            if used_cash + ticket.notional <= available_cash + 1e-9:
                selected.append(ticket)
                used_cash += ticket.notional
            else:
                deferred.append({"symbol": ticket.symbol, "reason": "insufficient_reconciled_cash"})

    turnover_limit = equity * policy.max_cycle_turnover_fraction
    executable: list[OrderTicket] = []
    turnover = 0.0
    for ticket in selected:
        if len(executable) >= policy.max_tickets_per_cycle:
            deferred.append({"symbol": ticket.symbol, "reason": "cycle_ticket_limit"})
            continue
        if turnover + ticket.notional > turnover_limit + 1e-9:
            deferred.append({"symbol": ticket.symbol, "reason": "cycle_turnover_limit"})
            continue
        executable.append(ticket)
        turnover += ticket.notional

    return ReconciliationResult(
        equity=equity,
        cash=cash,
        current_weights=current_weights,
        target_weights=dict(target.asset_weights),
        proposed_tickets=tuple(proposed),
        executable_tickets=tuple(executable),
        deferred=tuple(deferred),
        execution_phase=phase,
        policy_id=policy.policy_id,
    )
