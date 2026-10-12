from decimal import Decimal


FRACTIONAL_UNITS = {"kg", "sq. feet"}


def quantity_validation_error(
    quantity: Decimal,
    unit: str,
) -> str | None:
    if not quantity.is_finite():
        return "Quantity must be a finite number."

    normalized_unit = unit.strip().lower()

    if normalized_unit in FRACTIONAL_UNITS:
        if quantity.as_tuple().exponent < -3:
            return f"Quantity for {unit} must have no more than 3 decimal places."
        return None

    if quantity != quantity.to_integral_value():
        return f"Quantity for {unit} must be a whole number. Received: {quantity}"

    return None
