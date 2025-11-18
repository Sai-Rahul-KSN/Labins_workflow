# validators.py
from typing import Any, Tuple, Optional, List
import re
from datetime import datetime

import config
from utils import is_valid_date_components, safe_strip

# Each validator returns (is_valid: bool, cleaned_value, error_message: Optional[str])


def validate_categorical(value: Any, allowed: List[str], case_insensitive: bool = True) -> Tuple[bool, Any, Optional[str]]:
    if value is None or (isinstance(value, float) and (value != value)):  # NaN
        return False, value, "missing"
    raw = safe_strip(value)
    if case_insensitive:
        normalized = str(raw).upper()
        allowed_upper = [a.upper() for a in allowed]
        if normalized in allowed_upper:
            # return canonical form from allowed (preserve original allowed casing)
            idx = allowed_upper.index(normalized)
            return True, allowed[idx], None
        return False, raw, f"invalid categorical value, expected one of {allowed}"
    else:
        if raw in allowed:
            return True, raw, None
        return False, raw, f"invalid categorical value, expected one of {allowed}"


def validate_integer_range(value: Any, min_v: int, max_v: int) -> Tuple[bool, Optional[int], Optional[str]]:
    if value is None or value == "" or (isinstance(value, float) and (value != value)):
        return False, None, "missing"
    try:
        # Allow floats that are whole numbers
        if isinstance(value, float):
            if value.is_integer():
                value_int = int(value)
            else:
                return False, value, "not an integer"
        else:
            value_int = int(str(value).strip())
    except Exception:
        return False, value, "not an integer"

    if value_int < min_v or value_int > max_v:
        return False, value_int, f"out of range [{min_v}-{max_v}]"
    return True, value_int, None


def validate_float_range(value: Any, min_v: float, max_v: float, nullable: bool = False) -> Tuple[bool, Optional[float], Optional[str]]:
    if value is None or value == "" or (isinstance(value, float) and (value != value)):
        if nullable:
            return True, None, None
        return False, None, "missing"
    try:
        valf = float(str(value).strip())
    except Exception:
        return False, value, "not a float"
    if valf < min_v or valf > max_v:
        return False, valf, f"out of range [{min_v} - {max_v}]"
    return True, valf, None


def validate_county(value: Any) -> Tuple[bool, Optional[str], Optional[str]]:
    if value is None or value == "" or (isinstance(value, float) and (value != value)):
        return False, None, "missing"
    raw = safe_strip(value)
    # normalize spacing and casing
    cand = re.sub(r"\s+", " ", raw).strip()
    # check case-insensitively across FL_COUNTIES
    for c in config.FL_COUNTIES:
        if cand.lower() == c.lower():
            return True, c, None
    return False, raw, f"invalid county; expected one of Florida counties"


def validate_lat_lon(value: Any, min_v: float, max_v: float) -> Tuple[bool, Optional[float], Optional[str]]:
    # Accept decimal degrees; value must be float in range
    return validate_float_range(value, min_v, max_v, nullable=False)


def validate_optional_coordinate(value: Any, min_v: float, max_v: float) -> Tuple[bool, Optional[float], Optional[str]]:
    # Easting/Northing are optional — null allowed
    return validate_float_range(value, min_v, max_v, nullable=True)


def validate_zone(value: Any) -> Tuple[bool, Optional[str], Optional[str]]:
    return validate_categorical(value, config.ZONE_VALUES, case_insensitive=True)


def validate_horizontal_datum(value: Any) -> Tuple[bool, Optional[str], Optional[str]]:
    return validate_categorical(value, config.HORIZONTAL_DATUM, case_insensitive=False)


def validate_string_field(value: Any, min_len: int = config.STRING_MIN_LEN, max_len: int = config.STRING_MAX_LEN, required: bool = True) -> Tuple[bool, Optional[str], Optional[str]]:
    if value is None or (isinstance(value, float) and (value != value)) or (isinstance(value, str) and value.strip() == ""):
        if required:
            return False, None, "missing"
        else:
            return True, None, None
    s = safe_strip(value)
    if not (min_len <= len(s) <= max_len):
        return False, s, f"string length out of range [{min_len}-{max_len}]"
    return True, s, None


def validate_date_components(month: Any, day: Any, year: Any) -> Tuple[bool, Optional[datetime], Optional[str]]:
    # Validate integer ranges and logical date
    ok_m, m_val, err_m = validate_integer_range(month, 1, 12)
    if not ok_m:
        return False, None, f"month: {err_m}"
    ok_d, d_val, err_d = validate_integer_range(day, 1, 31)
    if not ok_d:
        return False, None, f"day: {err_d}"
    ok_y, y_val, err_y = validate_integer_range(year, config.YEAR_MIN, config.YEAR_MAX)
    if not ok_y:
        return False, None, f"year: {err_y}"
    valid_date, date_err = is_valid_date_components(m_val, d_val, y_val)
    if not valid_date:
        return False, None, f"invalid date: {date_err}"
    return True, datetime(year=y_val, month=m_val, day=d_val), None
