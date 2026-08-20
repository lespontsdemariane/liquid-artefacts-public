"""Tests for the BMI / WHO weight-band task."""

import pytest

from tasks.los247_bmi_band_v7 import task_fn


def test_normal_case():
    # 70 / (1.75 ** 2) = 22.857... -> 22.9, comfortably in the normal band.
    result = task_fn({"weight_kg": 70, "height_m": 1.75})
    assert result == {"bmi": 22.9, "band": "normal"}


def test_return_shape_is_exact():
    result = task_fn({"weight_kg": 70, "height_m": 1.75})
    assert set(result) == {"bmi", "band"}
    assert isinstance(result["bmi"], float)
    assert isinstance(result["band"], str)


@pytest.mark.parametrize(
    ("weight_kg", "height_m", "expected_bmi", "expected_band"),
    [
        # Height of 1 m makes the BMI equal to the weight, so these pin the
        # exact WHO cut-offs and the values either side of them.
        (18.4, 1.0, 18.4, "underweight"),
        (18.5, 1.0, 18.5, "normal"),
        (24.9, 1.0, 24.9, "normal"),
        (25.0, 1.0, 25.0, "overweight"),
        (29.9, 1.0, 29.9, "overweight"),
        (30.0, 1.0, 30.0, "obese"),
        (45.0, 1.0, 45.0, "obese"),
        (0, 1.8, 0.0, "underweight"),
    ],
)
def test_band_boundaries(weight_kg, height_m, expected_bmi, expected_band):
    result = task_fn({"weight_kg": weight_kg, "height_m": height_m})
    assert result["bmi"] == pytest.approx(expected_bmi)
    assert result["band"] == expected_band


@pytest.mark.parametrize(
    ("weight_kg", "height_m", "expected_bmi"),
    [
        (70, 1.75, 22.9),  # 22.857... rounds up
        (95, 1.82, 28.7),  # 28.680... rounds up
        (50, 1.6, 19.5),  # 19.531... rounds down
        (60.5, 1.7, 20.9),  # 20.934... rounds down
        (74.5, 2.0, 18.6),  # exactly 18.625 -> half rounds up
    ],
)
def test_bmi_rounded_to_one_decimal_place(weight_kg, height_m, expected_bmi):
    result = task_fn({"weight_kg": weight_kg, "height_m": height_m})
    assert result["bmi"] == pytest.approx(expected_bmi)
    # One decimal place at most.
    assert round(result["bmi"], 1) == result["bmi"]


def test_band_agrees_with_the_reported_bmi_at_a_rounding_boundary():
    # 24.96 raw BMI reports as 25.0, so the band must be overweight too.
    result = task_fn({"weight_kg": 24.96, "height_m": 1.0})
    assert result == {"bmi": 25.0, "band": "overweight"}


@pytest.mark.parametrize("height_m", [0, 0.0, -0.1, -1.8])
def test_non_positive_height_is_rejected_without_dividing(height_m):
    with pytest.raises(ValueError, match="height_m"):
        task_fn({"weight_kg": 70, "height_m": height_m})


def test_negative_weight_is_rejected():
    with pytest.raises(ValueError, match="weight_kg"):
        task_fn({"weight_kg": -70, "height_m": 1.75})


@pytest.mark.parametrize(
    "input_data",
    [
        {"weight_kg": "70", "height_m": 1.75},
        {"weight_kg": 70, "height_m": None},
        {"weight_kg": True, "height_m": 1.75},
    ],
)
def test_non_numeric_inputs_are_rejected(input_data):
    with pytest.raises(TypeError):
        task_fn(input_data)


@pytest.mark.parametrize(
    "input_data",
    [
        {"weight_kg": float("nan"), "height_m": 1.75},
        {"weight_kg": 70, "height_m": float("inf")},
        {"weight_kg": 70},
        {"height_m": 1.75},
    ],
)
def test_invalid_numeric_inputs_are_rejected(input_data):
    with pytest.raises(ValueError):
        task_fn(input_data)


def test_dry_run_returns_the_same_result():
    payload = {"weight_kg": 82.3, "height_m": 1.68}
    assert task_fn(payload, dry_run=True) == task_fn(payload, dry_run=False)


def test_dry_run_still_rejects_a_non_positive_height():
    with pytest.raises(ValueError, match="height_m"):
        task_fn({"weight_kg": 70, "height_m": 0}, dry_run=True)


def test_input_is_not_mutated():
    payload = {"weight_kg": 70, "height_m": 1.75}
    task_fn(payload)
    assert payload == {"weight_kg": 70, "height_m": 1.75}
