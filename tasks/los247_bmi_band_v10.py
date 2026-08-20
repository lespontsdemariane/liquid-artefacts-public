"""Body mass index and WHO weight band.

Business rule
-------------
Given a patient's weight in kilograms and height in metres, compute the body
mass index (BMI = weight / height^2) rounded to one decimal place and return
the World Health Organisation weight band:

    underweight   BMI < 18.5
    normal        18.5 <= BMI < 25
    overweight    25 <= BMI < 30
    obese         BMI >= 30

A height of zero or below is rejected rather than divided by.
"""

from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

__all__ = ["task_fn"]

# Lower bound (inclusive) of each band, ordered from heaviest to lightest.
_BANDS = (
    (Decimal(30), "obese"),
    (Decimal(25), "overweight"),
    (Decimal("18.5"), "normal"),
)
_LIGHTEST_BAND = "underweight"


def _to_decimal(value, field):
    """Coerce a JSON-ish number to Decimal, rejecting anything that is not one."""
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
        raise TypeError(f"{field} must be a number, got {type(value).__name__}")
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:  # pragma: no cover - defensive
        raise ValueError(f"{field} must be a finite number") from exc
    if not number.is_finite():
        raise ValueError(f"{field} must be a finite number")
    return number


def _band_for(bmi):
    for lower_bound, name in _BANDS:
        if bmi >= lower_bound:
            return name
    return _LIGHTEST_BAND


def task_fn(input_data: dict, dry_run: bool = False) -> dict:
    """Return the rounded BMI and its WHO weight band.

    Parameters
    ----------
    input_data:
        Mapping with ``weight_kg`` and ``height_m``, both numbers.
    dry_run:
        The calculation is pure and has no side effects, so a dry run still
        validates the input and returns the real result.

    Returns
    -------
    dict
        ``{"bmi": <float rounded to 1dp>, "band": <str>}``

    Raises
    ------
    TypeError
        If ``input_data`` is not a dict or a field is not a number.
    ValueError
        If a field is missing or not finite, if ``height_m`` is zero or below,
        or if ``weight_kg`` is negative.
    """
    if not isinstance(input_data, dict):
        raise TypeError("input_data must be a dict")

    for field in ("weight_kg", "height_m"):
        if field not in input_data:
            raise ValueError(f"missing required field: {field}")

    weight_kg = _to_decimal(input_data["weight_kg"], "weight_kg")
    height_m = _to_decimal(input_data["height_m"], "height_m")

    if height_m <= 0:
        raise ValueError("height_m must be greater than zero")
    if weight_kg < 0:
        raise ValueError("weight_kg must not be negative")

    # Round half up so that, e.g., 24.95 reports as 25.0 rather than 24.9.
    bmi = (weight_kg / (height_m * height_m)).quantize(
        Decimal("0.1"), rounding=ROUND_HALF_UP
    )

    # Band the value we report, so the band never contradicts the printed BMI.
    # ``dry_run`` needs no special handling: there is nothing to withhold.
    return {"bmi": float(bmi), "band": _band_for(bmi)}
