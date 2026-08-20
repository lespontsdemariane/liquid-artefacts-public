"""Tests for the BMI / WHO weight-band task."""

from __future__ import annotations

import pytest

from tasks.los247_bmi_band_v8 import task_fn


def test_normal_case_computes_bmi_and_band():
    result = task_fn({"weight_kg": 70, "height_m": 1.75})
    # 70 / 1.75^2 == 22.857... -> 22.9, comfortably inside the normal band.
    assert result == {"bmi": 22.9, "band": "normal"}


def test_returns_exactly_the_declared_shape_and_types():
    result = task_fn({"weight_kg": 80.0, "height_m": 1.8})
    assert set(result) == {"bmi", "band"}
    assert isinstance(result["bmi"], float)
    assert isinstance(result["band"], str)


@pytest.mark.parametrize(
    ("weight_kg", "height_m", "expected_bmi", "expected_band"),
    [
        # Band boundaries are inclusive at the bottom, exclusive at the top.
        (47.2, 1.6, 18.4, "underweight"),  # just below 18.5
        (47.4, 1.6, 18.5, "normal"),  # exactly 18.5 -> normal
        (63.9, 1.6, 25.0, "overweight"),  # exactly 25 -> overweight
        (63.7, 1.6, 24.9, "normal"),  # just below 25
        (76.7, 1.6, 30.0, "obese"),  # exactly 30 -> obese
        (76.5, 1.6, 29.9, "overweight"),  # just below 30
        (120.0, 1.6, 46.9, "obese"),
    ],
)
def test_who_band_boundaries(weight_kg, height_m, expected_bmi, expected_band):
    result = task_fn({"weight_kg": weight_kg, "height_m": height_m})
    assert result["bmi"] == pytest.approx(expected_bmi)
    assert result["band"] == expected_band


def test_bmi_is_rounded_to_one_decimal_place():
    result = task_fn({"weight_kg": 60, "height_m": 1.7})
    # 60 / 1.7^2 == 20.761245...
    assert result["bmi"] == pytest.approx(20.8)


def test_rounding_is_half_up_not_bankers():
    # 6.25 / 1.0^2 == 6.25 exactly; half-up gives 6.3, banker's would give 6.2.
    assert task_fn({"weight_kg": 6.25, "height_m": 1.0})["bmi"] == pytest.approx(6.3)


def test_band_agrees_with_the_rounded_bmi():
    # 63.98 / 1.6^2 == 24.99...; rounds to 25.0, so the band must say overweight
    # rather than contradicting the number that is returned alongside it.
    result = task_fn({"weight_kg": 63.98, "height_m": 1.6})
    assert result == {"bmi": 25.0, "band": "overweight"}


@pytest.mark.parametrize("height_m", [0, 0.0, -0.1, -2])
def test_zero_or_negative_height_is_rejected_without_dividing(height_m):
    with pytest.raises(ValueError, match="height_m"):
        task_fn({"weight_kg": 70, "height_m": height_m})


def test_negative_weight_is_rejected():
    with pytest.raises(ValueError, match="weight_kg"):
        task_fn({"weight_kg": -1, "height_m": 1.7})


def test_zero_weight_is_allowed_and_lands_in_underweight():
    assert task_fn({"weight_kg": 0, "height_m": 1.7}) == {
        "bmi": 0.0,
        "band": "underweight",
    }


def test_non_finite_values_are_rejected():
    with pytest.raises(ValueError):
        task_fn({"weight_kg": float("nan"), "height_m": 1.7})
    with pytest.raises(ValueError):
        task_fn({"weight_kg": 70, "height_m": float("inf")})


def test_missing_key_is_rejected():
    with pytest.raises(ValueError, match="height_m"):
        task_fn({"weight_kg": 70})


def test_non_numeric_value_is_rejected():
    with pytest.raises(TypeError):
        task_fn({"weight_kg": "70", "height_m": 1.75})
    with pytest.raises(TypeError):
        task_fn({"weight_kg": True, "height_m": 1.75})


def test_dry_run_matches_the_real_run_and_keeps_validating():
    payload = {"weight_kg": 95.0, "height_m": 1.7}
    assert task_fn(payload, dry_run=True) == task_fn(payload)
    assert task_fn(payload, dry_run=True)["band"] == "obese"
    with pytest.raises(ValueError, match="height_m"):
        task_fn({"weight_kg": 70, "height_m": 0}, dry_run=True)


def test_input_is_not_mutated():
    payload = {"weight_kg": 70, "height_m": 1.75}
    task_fn(payload)
    assert payload == {"weight_kg": 70, "height_m": 1.75}
