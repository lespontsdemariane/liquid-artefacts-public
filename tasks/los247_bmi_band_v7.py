"""Compute body mass index and the WHO weight band for a patient.

Business rule
-------------
Given a patient's weight in kilograms and height in metres, compute the body
mass index (BMI) rounded to one decimal place and return the World Health
Organisation weight band:

    band          BMI range
    ------------  ---------------------
    underweight   below 18.5
    normal        18.5 up to (not incl.) 25
    overweight    25 up to (not incl.) 30
    obese         30 and above

A height of zero or below is rejected rather than divided by.
"""

from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from math import isfinite

__all__ = ["task_fn"]

# Lower bounds of each band, highest first, so the first match wins.
_BANDS = (
    (Decimal(30), "obese"),
    (Decimal(25), "overweight"),
    (Decimal("18.5"), "normal"),
)
_LOWEST_BAND = "underweight"


def _as_number(value: object, field: str) -> Decimal:
    """Coerce an input field to a finite Decimal.

    Raises TypeError if the field is not a number and ValueError if it is a
    number that cannot be used (NaN or infinity).
    """
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
        raise TypeError(f"{field} must be a number, got {type(value).__name__}")
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:  # pragma: no cover - defensive
        raise ValueError(f"{field} must be a number, got {value!r}") from exc
    if not number.is_finite() or (isinstance(value, float) and not isfinite(value)):
        raise ValueError(f"{field} must be a finite number, got {value!r}")
    return number


def task_fn(input_data: dict, dry_run: bool = False) -> dict:
    """Return the BMI (1 decimal place) and WHO weight band for a patient.

    Parameters
    ----------
    input_data:
        Mapping with ``weight_kg`` (number) and ``height_m`` (number).
    dry_run:
        Accepted for interface compatibility. This task is a pure
        calculation with no side effects, so the same validation and the
        same result are produced whether or not it is set.

    Returns
    -------
    dict
        ``{"bmi": float, "band": str}``.

    Raises
    ------
    TypeError
        If ``input_data`` is not a dict or a field is not a number.
    ValueError
        If a required field is missing or is not finite, if the height is
        zero or negative, or if the weight is negative.
    """
    if not isinstance(input_data, dict):
        raise TypeError(f"input_data must be a dict, got {type(input_data).__name__}")

    for field in ("weight_kg", "height_m"):
        if field not in input_data:
            raise ValueError(f"missing required field: {field}")

    weight_kg = _as_number(input_data["weight_kg"], "weight_kg")
    height_m = _as_number(input_data["height_m"], "height_m")

    # Reject a non-positive height instead of dividing by it.
    if height_m <= 0:
        raise ValueError(f"height_m must be greater than zero, got {height_m}")
    if weight_kg < 0:
        raise ValueError(f"weight_kg must not be negative, got {weight_kg}")

    bmi = (weight_kg / (height_m * height_m)).quantize(
        Decimal("0.1"), rounding=ROUND_HALF_UP
    )

    # Band the reported (rounded) BMI so that the two returned values can
    # never disagree with each other.
    band = _LOWEST_BAND
    for lower_bound, name in _BANDS:
        if bmi >= lower_bound:
            band = name
            break

    del dry_run  # No side effects to skip.
    return {"bmi": float(bmi), "band": band}
