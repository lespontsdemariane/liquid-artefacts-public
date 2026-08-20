"""Tests for the BMI / WHO weight band task."""

from __future__ import annotations

import pytest

from tasks.los247_bmi_band_v9 import task_fn


def test_normal_case():
    result = task_fn({"weight_kg": 70, "height_m": 1.75})
    assert result == {"bmi": 22.9, "band": "normal"}


def test_result_shape_and_types():
    result = task_fn({"weight_kg": 70.0, "height_m": 1.8})
    assert set(result) == {"bmi", "band"}
    assert isinstance(result["bmi"], float)
    assert isinstance(result["band"], str)


@pytest.mark.parametrize(
    ("weight_kg", "height_m", "expected_bmi", "expected_band"),
    [
        # Well inside each band.
        (40.0, 1.70, 13.8, "underweight"),
        (70.0, 1.75, 22.9, "normal"),
        (80.0, 1.70, 27.7, "overweight"),
        (110.0, 1.70, 38.1, "obese"),
        # Exact boundaries: lower bound is inclusive, upper bound exclusive.
        (18.5, 1.0, 18.5, "normal"),
        (25.0, 1.0, 25.0, "overweight"),
        (30.0, 1.0, 30.0, "obese"),
        # Just below each boundary.
        (18.4, 1.0, 18.4, "underweight"),
        (24.9, 1.0, 24.9, "normal"),
        (29.9, 1.0, 29.9, "overweight"),
    ],
)
def test_bands(weight_kg, height_m, expected_bmi, expected_band):
    assert task_fn({"weight_kg": weight_kg, "height_m": height_m}) == {
        "bmi": expected_bmi,
        "band": expected_band,
    }


def test_bmi_is_rounded_to_one_decimal_place():
    # 95 / 1.82^2 = 28.68011... -> 28.7
    assert task_fn({"weight_kg": 95, "height_m": 1.82})["bmi"] == 28.7


def test_banding_uses_the_rounded_bmi():
    # 24.96 / 1.0^2 rounds to 25.0, which is the 'overweight' threshold.
    assert task_fn({"weight_kg": 24.96, "height_m": 1.0}) == {
        "bmi": 25.0,
        "band": "overweight",
    }


@pytest.mark.parametrize("height_m", [0, 0.0, -1.75])
def test_non_positive_height_is_rejected(height_m):
    with pytest.raises(ValueError, match="height_m"):
        task_fn({"weight_kg": 70.0, "height_m": height_m})


def test_zero_weight_is_underweight():
    assert task_fn({"weight_kg": 0, "height_m": 1.75}) == {
        "bmi": 0.0,
        "band": "underweight",
    }


def test_negative_weight_is_rejected():
    with pytest.raises(ValueError, match="weight_kg"):
        task_fn({"weight_kg": -5.0, "height_m": 1.75})


@pytest.mark.parametrize(
    "payload",
    [
        {"weight_kg": 70.0},
        {"height_m": 1.75},
        {},
    ],
)
def test_missing_keys_are_rejected(payload):
    with pytest.raises(ValueError, match="missing required key"):
        task_fn(payload)


@pytest.mark.parametrize("bad", ["70", None, True])
def test_non_numeric_values_are_rejected(bad):
    with pytest.raises(TypeError, match="weight_kg"):
        task_fn({"weight_kg": bad, "height_m": 1.75})


@pytest.mark.parametrize("bad", [float("nan"), float("inf")])
def test_non_finite_values_are_rejected(bad):
    with pytest.raises(ValueError, match="height_m"):
        task_fn({"weight_kg": 70.0, "height_m": bad})


def test_dry_run_returns_the_same_result_without_error():
    payload = {"weight_kg": 70.0, "height_m": 1.75}
    assert task_fn(payload, dry_run=True) == task_fn(payload)


def test_dry_run_still_validates_height():
    with pytest.raises(ValueError, match="height_m"):
        task_fn({"weight_kg": 70.0, "height_m": 0.0}, dry_run=True)
