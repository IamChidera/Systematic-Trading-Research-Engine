"""Operational helpers for paper-live trading monitors.

The functions in this module are intentionally exchange-agnostic. They work
with plain report dictionaries so the public research package can demonstrate
the monitoring pattern without exposing local bot scripts, API keys, or broker
adapters.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class ExecutionAssumptions:
    """Simple cost assumptions for simulated order tickets."""

    fee_pct: float = 0.001
    slippage_pct: float = 0.0002
    spread_pct: float = 0.0004


@dataclass(frozen=True)
class RiskLimits:
    """Portfolio-level paper-live risk limits."""

    max_bot_exposure_pct: float = 0.80
    max_symbol_exposure_pct: float = 0.35
    max_btc_beta_exposure_pct: float = 0.85
    max_open_bots: int = 8


def parse_timestamp(value: str | None) -> datetime | None:
    """Parse ISO timestamps from bot reports."""

    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def age_minutes(value: str | None, now: datetime | None = None) -> float | None:
    """Return report age in minutes."""

    parsed = parse_timestamp(value)
    if parsed is None:
        return None
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    return (current.astimezone(timezone.utc) - parsed).total_seconds() / 60


def detect_orders(bot_reports: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    """Collect order records from a mapping of bot reports."""

    orders: list[dict[str, Any]] = []
    for bot_name, report in bot_reports.items():
        for order in report.get("orders", []) or []:
            if not isinstance(order, dict):
                continue
            enriched = {"bot": bot_name}
            enriched.update(order)
            orders.append(enriched)
    return orders


def simulate_execution(
    orders: list[dict[str, Any]],
    assumptions: ExecutionAssumptions | None = None,
) -> list[dict[str, Any]]:
    """Estimate fill cost for generated paper orders.

    This is not an execution engine. It creates dry-run tickets that make the
    cost assumptions visible for review.
    """

    assumptions = assumptions or ExecutionAssumptions()
    tickets = []
    for order in orders:
        side = str(order.get("side", "buy")).lower()
        price = float(order.get("price", order.get("limit_price", 0.0)) or 0.0)
        quantity = float(order.get("quantity", order.get("qty", 0.0)) or 0.0)
        notional = float(order.get("notional", price * quantity) or 0.0)
        direction = 1.0 if side == "buy" else -1.0
        spread_adjustment = direction * assumptions.spread_pct / 2.0
        slippage_adjustment = direction * assumptions.slippage_pct
        estimated_fill = price * (1.0 + spread_adjustment + slippage_adjustment)
        fee = abs(notional) * assumptions.fee_pct
        tickets.append(
            {
                "bot": order.get("bot"),
                "symbol": order.get("symbol"),
                "side": side,
                "quantity": quantity,
                "notional": notional,
                "reference_price": price,
                "estimated_fill_price": estimated_fill,
                "estimated_fee": fee,
                "status": "dry_run_only",
            }
        )
    return tickets


def position_notional(position: Any) -> float:
    """Extract absolute notional from common position record shapes."""

    if isinstance(position, dict):
        if "notional" in position:
            return abs(float(position.get("notional") or 0.0))
        price = float(position.get("price", position.get("mark_price", 0.0)) or 0.0)
        quantity = float(position.get("quantity", position.get("qty", 0.0)) or 0.0)
        return abs(price * quantity)
    return 0.0


def build_risk_snapshot(
    bot_reports: dict[str, dict[str, Any]],
    limits: RiskLimits | None = None,
) -> dict[str, Any]:
    """Aggregate exposure and warnings from paper-live bot reports."""

    limits = limits or RiskLimits()
    total_equity = sum(float(report.get("equity", 0.0) or 0.0) for report in bot_reports.values())
    bot_exposure: dict[str, float] = {}
    symbol_exposure: dict[str, float] = {}

    for bot_name, report in bot_reports.items():
        positions = report.get("positions", {}) or {}
        if not isinstance(positions, dict):
            continue
        for symbol, position in positions.items():
            notional = position_notional(position)
            if notional <= 0:
                continue
            bot_exposure[bot_name] = bot_exposure.get(bot_name, 0.0) + notional
            symbol_exposure[symbol] = symbol_exposure.get(symbol, 0.0) + notional

    total_open_notional = sum(bot_exposure.values())
    warnings = []
    if total_equity > 0:
        for bot_name, notional in bot_exposure.items():
            if notional / total_equity > limits.max_bot_exposure_pct:
                warnings.append(f"BOT_EXPOSURE_LIMIT:{bot_name}")
        for symbol, notional in symbol_exposure.items():
            if notional / total_equity > limits.max_symbol_exposure_pct:
                warnings.append(f"SYMBOL_EXPOSURE_LIMIT:{symbol}")

    if len(bot_exposure) > limits.max_open_bots:
        warnings.append("OPEN_BOT_COUNT_LIMIT")

    gross_exposure_pct = total_open_notional / total_equity if total_equity > 0 else 0.0
    return {
        "total_equity_observed": total_equity,
        "total_open_notional": total_open_notional,
        "gross_exposure_pct": gross_exposure_pct,
        "open_bots": len(bot_exposure),
        "open_symbols": len(symbol_exposure),
        "bot_exposure": bot_exposure,
        "symbol_exposure": symbol_exposure,
        "warnings": warnings,
    }


def readiness_check(
    heartbeat: dict[str, Any],
    execution_report: dict[str, Any],
    risk_report: dict[str, Any],
    manual_confirmations: dict[str, bool] | None = None,
    max_heartbeat_age_minutes: float = 30.0,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Summarise whether paper ops and tiny-live prerequisites are satisfied."""

    blockers = []
    warnings = []
    heartbeat_age = age_minutes(heartbeat.get("last_cycle_finished_at"), now=now)
    if heartbeat.get("status") not in {"running", "completed_once"}:
        blockers.append("SUPERVISOR_NOT_RUNNING")
    if heartbeat_age is None or heartbeat_age > max_heartbeat_age_minutes:
        blockers.append("STALE_HEARTBEAT")
    if heartbeat.get("alerts"):
        blockers.append("SUPERVISOR_ALERTS_PRESENT")
    if risk_report.get("warnings"):
        blockers.append("RISK_WARNINGS_PRESENT")

    paper_ops_ready = not blockers
    manual_confirmations = manual_confirmations or {}
    missing_manual = [key for key, value in manual_confirmations.items() if not value]
    if missing_manual:
        warnings.append("MANUAL_CONFIRMATIONS_INCOMPLETE")

    tiny_live_ready = paper_ops_ready and not missing_manual
    return {
        "paper_ops_ready": paper_ops_ready,
        "tiny_live_ready": tiny_live_ready,
        "heartbeat_age_minutes": heartbeat_age,
        "orders_detected": execution_report.get("orders_detected", 0),
        "blockers": blockers,
        "warnings": warnings,
    }
