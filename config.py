# config.py
from typing import List, Dict, Any

# Valid closed lists and ranges for CCR form fields.
# Use this dictionary to change rules without changing code.

FL_COUNTIES: List[str] = [
    "Alachua", "Baker", "Bay", "Bradford", "Brevard", "Broward", "Calhoun",
    "Charlotte", "Citrus", "Clay", "Collier", "Columbia", "DeSoto", "Dixie",
    "Duval", "Escambia", "Flagler", "Franklin", "Gadsden", "Gilchrist", "Glades",
    "Gulf", "Hamilton", "Hardee", "Hendry", "Hernando", "Highlands",
    "Hillsborough", "Holmes", "Indian River", "Jackson", "Jefferson", "Lafayette",
    "Lake", "Lee", "Leon", "Levy", "Liberty", "Madison", "Manatee", "Marion",
    "Martin", "Miami-Dade", "Monroe", "Nassau", "Okaloosa", "Okeechobee", "Orange",
    "Osceola", "Palm Beach", "Pasco", "Pinellas", "Polk", "Putnam", "St. Johns",
    "St. Lucie", "Santa Rosa", "Sarasota", "Seminole", "Sumter", "Suwannee",
    "Taylor", "Union", "Volusia", "Wakulla", "Walton", "Washington"
]

# Corner of Section closed list (from your spec). Case-insensitive allowed.
CORNER_OF_SECTION: List[str] = [
    "NE", "NW", "SE", "SW",
    "S 1/4", "W 1/4", "E 1/4", "N 1/4",
    "NE 1/4", "NW 1/4", "SE 1/4", "SW 1/4"
]

HORIZONTAL_DATUM: List[str] = ["NAD27", "NAD83(1990)", "NAD83(2011)", "OTHER"]

ZONE_VALUES: List[str] = ["SPW", "SPE", "SPN"]

TOWNSHIP_DIR: List[str] = ["N", "S"]
RANGE_DIR: List[str] = ["E", "W"]

# numeric ranges
SECTION_MIN = 1
SECTION_MAX = 8030  # includes standard 1-36 and 37-8030 unusual as requested

TOWNSHIP_MIN = 1
TOWNSHIP_MAX = 70

RANGE_MIN = 1
RANGE_MAX = 43

# lat/lon expected for Florida (approx)
LAT_MIN = 24.0
LAT_MAX = 31.5

LON_MIN = -87.5
LON_MAX = -80.0

# Easting / Northing typical ranges for FL (open but validated if present)
EASTING_MIN = 200_000.0
EASTING_MAX = 900_000.0

NORTHING_MIN = 0.0
NORTHING_MAX = 3_000_000.0

# date year range
YEAR_MIN = 1900
YEAR_MAX = 2100

# Simple lengths for open string fields
STRING_MIN_LEN = 1
STRING_MAX_LEN = 200
