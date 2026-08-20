"""Compute body mass index and the matching WHO weight band.

Business rule
-------------
Given ``weight_kg`` (kilograms) and ``height_m`` (metres):

* ``bmi = weight_kg / height_m ** 2``, rounded half-up to one decimal place.
* The World Health Organisation weight band is derived from that rounded
  value, so the two returned fields can never disagree with each other:

  ==================  ==========================
  Band                Rounded BMI
  ==================  ==========================
  ``underweight``     below 18.5
  ``normal``          18.5 up to (excluding) 25
  ``overweight``      25 up to (excluding) 30
  ``obese``           30 and above
  ==================  ==========================

* A height of zero or below is rejected with :class:`ValueError` rather than
  being divided by.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from math import isfinite

__all__ = ["task_fn"]

UNDERWEIGHT_MAX = 18.5
NORMAL_MAX = 25.0
OVERWEIGHT_MAX = 30.0


def _as_number(value: object, field: str) -> float:
    """Return ``value`` as a finite float, or raise on anything unusable."""
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
        raise TypeError(f"{field} must be a number, got {type(value).__name__}")
    try:
        number = float(value)
    except (OverflowError, ValueError, InvalidOperation) as exc:  # pragma: no cover
        raise ValueError(f"{field} must be a finite number") from exc
    if not isfinite(number):
        raise ValueError(f"{field} must be a finite number, got {value!r}")
    return number


def _round_half_up(value: float) -> float:
    """Round to one decimal place, half away from zero (not banker's rounding)."""
    return float(Decimal(repr(value)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))


def _band(bmi: float) -> str:
    if bmi < UNDERWEIGHT_MAX:
        return "underweight"
    if bmi < NORMAL_MAX:
        return "normal"
    if bmi < OVERWEIGHT_MAX:
        return "overweight"
    return "obese"


def task_fn(input_data: dict, dry_run: bool = False) -> dict:
    """Compute BMI and the WHO weight band.

    Args:
        input_data: Mapping with ``weight_kg`` and ``height_m`` numbers.
        dry_run: Accepted for engine compatibility. The task is a pure
            calculation with no side effects, so inputs are validated and the
            real result is returned either way.

    Returns:
        ``{"bmi": <float>, "band": <str>}``.

    Raises:
        TypeError: If ``input_data`` or either field is of the wrong type.
        ValueError: If a required key is missing, a value is not finite, or
            the height is zero or negative.
    """
    del dry_run  # No side effects to skip; behaviour is identical.

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

    bmi = _round_half_up(weight_kg / (height_m * height_m))
    return {"bmi": bmi, "band": _band(bmi)}
