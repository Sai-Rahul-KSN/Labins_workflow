# utils.py
from datetime import datetime
from typing import Tuple


def safe_strip(value):
    """Trim whitespace for strings; return original for non-strings."""
    if value is None:
        return value
    if isinstance(value, str):
        return value.strip()
    return value


def make_excel_row_number(df_index: int, header_rows: int = 1) -> int:
    """
    Compute Excel row number from pandas index (0-based).
    Default assumes header occupies 1 row so first data row is Excel row 2.
    """
    return df_index + 1 + header_rows


def is_valid_date_components(month: int, day: int, year: int) -> Tuple[bool, str]:
    """
    Validate that the three integers form a valid date.
    Returns (valid, error_message_if_any).
    """
    try:
        datetime(year=year, month=month, day=day)
        return True, ""
    except ValueError as e:
        return False, str(e)
