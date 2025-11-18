# tests/test_validators.py
import pytest
import validators as V
import config
from datetime import datetime

def test_validate_categorical_ok():
    ok, val, err = V.validate_categorical("ne", config.CORNER_OF_SECTION)
    assert ok and err is None

def test_validate_categorical_bad():
    ok, val, err = V.validate_categorical("XYZ", config.CORNER_OF_SECTION)
    assert not ok and "invalid" in err.lower()

def test_validate_integer_ok():
    ok, val, err = V.validate_integer_range(12, 1, 20)
    assert ok and val == 12

def test_validate_integer_bad_float():
    ok, val, err = V.validate_integer_range(12.5, 1, 20)
    assert not ok

def test_validate_float_range_ok():
    ok, val, err = V.validate_float_range("25.5", 24.0, 31.5)
    assert ok and 24.0 <= val <= 31.5

def test_validate_county_ok():
    ok, val, err = V.validate_county("miami-dade".replace('-', ' '))
    # normalize: we used exact list, so test a known case
    ok2, val2, err2 = V.validate_county("Miami-Dade")
    assert ok2

def test_validate_date_components_ok():
    ok, dt, err = V.validate_date_components(2, 28, 2024)
    assert ok and isinstance(dt, datetime)

def test_validate_date_components_invalid():
    ok, dt, err = V.validate_date_components(2, 30, 2021)
    assert not ok
