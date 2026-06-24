import pandas as pd
import pytest

from trading_research.portfolio import annualized_sharpe, blend_curves, correlation_matrix, normalize_curve


def test_normalize_curve_scales_to_starting_value():
    curve = pd.Series([50.0, 75.0, 100.0])

    normalized = normalize_curve(curve, starting_value=10_000.0)

    assert normalized.tolist() == [10_000.0, 15_000.0, 20_000.0]


def test_normalize_curve_rejects_non_positive_start():
    with pytest.raises(ValueError):
        normalize_curve(pd.Series([0.0, 1.0]))


def test_blend_curves_uses_common_dates_and_weights():
    dates = pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"])
    curves = {
        "core": pd.Series([100.0, 110.0, 120.0], index=dates),
        "growth": pd.Series([220.0, 260.0], index=dates[1:]),
    }

    blended = blend_curves(curves, {"core": 0.7, "growth": 0.3})

    assert blended.index.tolist() == dates[1:].tolist()
    assert round(float(blended.iloc[0]), 2) == 10_000.0
    assert round(float(blended.iloc[1]), 2) == 11_181.82


def test_blend_curves_requires_present_curve_names():
    with pytest.raises(KeyError):
        blend_curves({"core": pd.Series([1.0, 2.0])}, {"missing": 1.0})


def test_correlation_matrix_uses_return_correlation():
    curves = {
        "a": pd.Series([100.0, 110.0, 132.0]),
        "b": pd.Series([200.0, 210.0, 231.0]),
    }

    matrix = correlation_matrix(curves)

    assert matrix.loc["a", "b"] == pytest.approx(1.0)


def test_annualized_sharpe_returns_none_for_flat_curve():
    assert annualized_sharpe(pd.Series([100.0, 100.0, 100.0])) is None
