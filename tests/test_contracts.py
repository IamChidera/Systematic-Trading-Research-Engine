import pytest

from trading_research.contracts import SleeveTarget, combine_sleeve_targets


def test_combine_sleeves_preserves_unused_capital_as_cash():
    target = combine_sleeve_targets(
        [
            SleeveTarget("core", 0.60, {"BTCUSDT": 1.0}, "core regime active"),
            SleeveTarget("growth", 0.30, {"SOLUSDT": 0.50}, "SOL ranks first"),
        ]
    )

    assert target.asset_weights == {"BTCUSDT": 0.60, "SOLUSDT": 0.15}
    assert target.cash_weight == pytest.approx(0.25)
    assert target.weight_sum == pytest.approx(1.0)
    assert target.explanations["SOLUSDT"] == ("growth: SOL ranks first",)


def test_combine_sleeves_rejects_excess_account_budget():
    with pytest.raises(ValueError, match="budgets"):
        combine_sleeve_targets(
            [
                SleeveTarget("a", 0.70, {}, "waiting"),
                SleeveTarget("b", 0.40, {}, "waiting"),
            ]
        )
