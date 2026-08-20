"""Tests for the BMI / WHO weight band task."""

import pytest

from tasks.los247_bmi_band_v10 import task_fn


def test_normal_case():
    result = task_fn({"weight_kg": 70, "height_m": 1.75})
    assert result == {"bmi": 22.9, "band": "normal"}


def test_result_shape_and_types():
    result = task_fn({"weight_kg": 70.0, "height_m": 1.8})
    assert set(result) == {"bmi", "band"}
    assert isinstance(result["bmi"], float)
    assert isinstance(result["band"], str)


@pytest.mark.parametrize(
    ("weight_kg", "height_m", "bmi", "band"),
    [
        # 1 m tall makes BMI numerically equal to the weight, so these pin the
        # exact boundaries of each band.
        (18.4, 1.0, 18.4, "underweight"),
        (18.5, 1.0, 18.5, "normal"),
        (24.9, 1.0, 24.9, "normal"),
        (25.0, 1.0, 25.0, "overweight"),
        (29.9, 1.0, 29.9, "overweight"),
        (30.0, 1.0, 30.0, "obese"),
        (45.0, 1.0, 45.0, "obese"),
    ],
)
def test_band_boundaries(weight_kg, height_m, bmi, band):
    assert task_fn({"weight_kg": weight_kg, "height_m": height_m}) == {
        "bmi": bmi,
        "band": band,
    }


def test_rounds_to_one_decimal_place():
    # 95 / 1.82^2 = 28.6801... -> 28.7
    assert task_fn({"weight_kg": 95, "height_m": 1.82})["bmi"] == 28.7


def test_rounds_half_up():
    # 24.95 / 1.0^2 = 24.95 -> 25.0, which also moves the band to overweight.
    assert task_fn({"weight_kg": 24.95, "height_m": 1.0}) == {
        "bmi": 25.0,
        "band": "overweight",
    }


def test_zero_height_is_rejected_not_divided_by():
    with pytest.raises(ValueError, match="height_m"):
        task_fn({"weight_kg": 70, "height_m": 0})


def test_negative_height_is_rejected():
    with pytest.raises(ValueError, match="height_m"):
        task_fn({"weight_kg": 70, "height_m": -1.75})


def test_negative_weight_is_rejected():
    with pytest.raises(ValueError, match="weight_kg"):
        task_fn({"weight_kg": -70, "height_m": 1.75})


def test_non_numeric_input_is_rejected():
    with pytest.raises(TypeError, match="weight_kg"):
        task_fn({"weight_kg": "70", "height_m": 1.75})


def test_boolean_is_not_treated_as_a_number():
    with pytest.raises(TypeError, match="height_m"):
        task_fn({"weight_kg": 70, "height_m": True})


def test_missing_field_is_rejected():
    with pytest.raises(ValueError, match="height_m"):
        task_fn({"weight_kg": 70})


def test_dry_run_matches_real_run():
    payload = {"weight_kg": 82.5, "height_m": 1.68}
    assert task_fn(payload, dry_run=True) == task_fn(payload)


def test_dry_run_still_validates():
    with pytest.raises(ValueError, match="height_m"):
        task_fn({"weight_kg": 70, "height_m": 0}, dry_run=True)
