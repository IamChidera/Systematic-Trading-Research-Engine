"""Typed contracts between strategies, portfolio construction, and execution."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Mapping


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class SleeveTarget:
    """A strategy sleeve's desired internal allocation.

    ``budget_weight`` is the sleeve's share of the account. ``asset_weights``
    are weights inside that budget and may sum to less than one; unused sleeve
    capital remains cash.
    """

    sleeve_id: str
    budget_weight: float
    asset_weights: Mapping[str, float]
    reason: str
    observed_at: str = field(default_factory=_utc_now)

    def validate(self) -> None:
        if not self.sleeve_id.strip():
            raise ValueError("sleeve_id is required")
        if not 0.0 <= self.budget_weight <= 1.0:
            raise ValueError("budget_weight must be between 0 and 1")
        if any(weight < 0.0 or weight > 1.0 for weight in self.asset_weights.values()):
            raise ValueError("asset weights must be between 0 and 1")
        if sum(self.asset_weights.values()) > 1.0 + 1e-9:
            raise ValueError("asset weights inside a sleeve cannot exceed 1")
        if not self.reason.strip():
            raise ValueError("every sleeve target requires a reason")


@dataclass(frozen=True)
class PortfolioTarget:
    """A complete account-level target produced from strategy sleeves."""

    asset_weights: Mapping[str, float]
    cash_weight: float
    sleeve_contributions: Mapping[str, Mapping[str, float]]
    explanations: Mapping[str, tuple[str, ...]]
    created_at: str = field(default_factory=_utc_now)

    @property
    def weight_sum(self) -> float:
        return float(sum(self.asset_weights.values()) + self.cash_weight)

    def validate(self) -> None:
        if any(weight < 0.0 or weight > 1.0 for weight in self.asset_weights.values()):
            raise ValueError("portfolio asset weights must be between 0 and 1")
        if not 0.0 <= self.cash_weight <= 1.0:
            raise ValueError("cash_weight must be between 0 and 1")
        if abs(self.weight_sum - 1.0) > 1e-8:
            raise ValueError(f"portfolio weights must sum to 1, got {self.weight_sum:.10f}")


def combine_sleeve_targets(sleeves: list[SleeveTarget]) -> PortfolioTarget:
    """Combine independent sleeve targets without hiding unused capital."""

    if not sleeves:
        return PortfolioTarget(
            asset_weights={},
            cash_weight=1.0,
            sleeve_contributions={},
            explanations={},
        )

    budget_sum = sum(sleeve.budget_weight for sleeve in sleeves)
    if budget_sum > 1.0 + 1e-9:
        raise ValueError("sleeve budgets cannot exceed 100% of account equity")

    assets: dict[str, float] = {}
    contributions: dict[str, dict[str, float]] = {}
    explanations: dict[str, list[str]] = {}
    deployed = 0.0

    for sleeve in sleeves:
        sleeve.validate()
        contribution: dict[str, float] = {}
        for symbol, internal_weight in sleeve.asset_weights.items():
            account_weight = sleeve.budget_weight * internal_weight
            if account_weight <= 0:
                continue
            assets[symbol] = assets.get(symbol, 0.0) + account_weight
            contribution[symbol] = account_weight
            explanations.setdefault(symbol, []).append(f"{sleeve.sleeve_id}: {sleeve.reason}")
            deployed += account_weight
        contributions[sleeve.sleeve_id] = contribution

    target = PortfolioTarget(
        asset_weights=assets,
        cash_weight=max(0.0, 1.0 - deployed),
        sleeve_contributions=contributions,
        explanations={symbol: tuple(reasons) for symbol, reasons in explanations.items()},
    )
    target.validate()
    return target
