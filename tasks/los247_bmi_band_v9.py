"""Compute body mass index and the WHO weight band for a patient.

Business rule
-------------
Given a weight in kilograms and a height in metres, compute the body mass
index (``weight_kg / height_m ** 2``) rounded to one decimal place and return
the World Health Organisation weight band:

* ``underweight`` -- below 18.5
* ``normal``      -- from 18.5 up to but excluding 25
* ``overweight``  -- from 25 up to but excluding 30
* ``obese``       -- 30 and above

A height of zero or below is rejected rather than divided by.
"""

from __future__ import annotations

import math

__all__ = ["task_fn"]

# (exclusive upper bound, band name) in ascending order; the final band is open
# ended and is applied to anything at or above the last threshold.
_BANDS: tuple[tuple[float, str], ...] = (
    (18.5, "underweight"),
    (25.0, "normal"),
    (30.0, "overweight"),
)
_TOP_BAND = "obese"


def _as_number(value: object, field: str) -> float:
    """Return ``value`` as a finite float or raise."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{field} must be a number, got {type(value).__name__}")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{field} must be a finite number, got {value!r}")
    return number


def _band_for(bmi: float) -> str:
    """Return the WHO weight band for an already-rounded BMI value."""
    for upper, name in _BANDS:
        if bmi < upper:
            return name
    return _TOP_BAND


def task_fn(input_data: dict, dry_run: bool = False) -> dict:
    """Compute the BMI and WHO weight band for ``input_data``.

    Parameters
    ----------
    input_data:
        Mapping with ``weight_kg`` and ``height_m`` numeric keys.
    dry_run:
        When true, validate the input and return a representative result
        without asserting it as a real measurement. The computation here is
        pure, so the same values are returned either way.

    Returns
    -------
    dict
        ``{"bmi": <float>, "band": <str>}``.

    Raises
    ------
    TypeError
        If ``input_data`` is not a dict or a value is not a number.
    ValueError
        If a required key is missing, a value is not finite, the weight is
        negative, or the height is zero or below.
    """
    if not isinstance(input_data, dict):
        raise TypeError(f"input_data must be a dict, got {type(input_data).__name__}")

    missing = [key for key in ("weight_kg", "height_m") if key not in input_data]
    if missing:
        raise ValueError(f"input_data is missing required key(s): {', '.join(missing)}")

    weight_kg = _as_number(input_data["weight_kg"], "weight_kg")
    height_m = _as_number(input_data["height_m"], "height_m")

    if height_m <= 0:
        raise ValueError(f"height_m must be greater than zero, got {height_m}")
    if weight_kg < 0:
        raise ValueError(f"weight_kg must not be negative, got {weight_kg}")

    # The computation is pure and side-effect free, so a dry run produces
    # exactly the same result as a real run; `dry_run` is accepted for
    # interface compatibility with the workflow engine.
    del dry_run

    bmi = round(weight_kg / (height_m * height_m), 1)
    return {"bmi": bmi, "band": _band_for(bmi)}
