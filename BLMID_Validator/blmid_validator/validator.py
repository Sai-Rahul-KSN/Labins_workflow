"""
Validation module for BLMID Validator.
Compares extracted data against Excel and database.
"""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of validation for a single PDF/record."""
    pdf_file: str
    blmid: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    excel_match: bool
    database_match: bool
    correct_blmid: Optional[str]
    correction_needed: bool
    errors: List[str]
    warnings: List[str]

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)


class Validator:
    """Validate BLMID entries against Excel and database."""

    def __init__(
        self,
        coordinate_tolerance: float = 0.0001,
        latitude_min: float = -90,
        latitude_max: float = 90,
        longitude_min: float = -180,
        longitude_max: float = 180,
        check_duplicates: bool = True,
    ):
        """
        Initialize validator.

        Args:
            coordinate_tolerance: Tolerance for coordinate matching (degrees)
            latitude_min: Minimum valid latitude
            latitude_max: Maximum valid latitude
            longitude_min: Minimum valid longitude
            longitude_max: Maximum valid longitude
            check_duplicates: Check for duplicate BLMIDs
        """
        self.coordinate_tolerance = coordinate_tolerance
        self.latitude_min = latitude_min
        self.latitude_max = latitude_max
        self.longitude_min = longitude_min
        self.longitude_max = longitude_max
        self.check_duplicates = check_duplicates

    def validate_coordinates(
        self, latitude: Optional[float], longitude: Optional[float]
    ) -> Tuple[bool, List[str]]:
        """
        Validate coordinate values.

        Args:
            latitude: Latitude value
            longitude: Longitude value

        Returns:
            Tuple of (is_valid, error_list)
        """
        errors = []

        if latitude is None:
            errors.append("Latitude is None")
        elif not isinstance(latitude, (int, float)):
            errors.append(f"Latitude must be numeric, got {type(latitude)}")
        elif latitude < self.latitude_min or latitude > self.latitude_max:
            errors.append(
                f"Latitude {latitude} out of range [{self.latitude_min}, {self.latitude_max}]"
            )

        if longitude is None:
            errors.append("Longitude is None")
        elif not isinstance(longitude, (int, float)):
            errors.append(f"Longitude must be numeric, got {type(longitude)}")
        elif longitude < self.longitude_min or longitude > self.longitude_max:
            errors.append(
                f"Longitude {longitude} out of range [{self.longitude_min}, {self.longitude_max}]"
            )

        return len(errors) == 0, errors

    def check_coordinates_match(
        self, lat1: float, lon1: float, lat2: float, lon2: float
    ) -> bool:
        """
        Check if two coordinate pairs match within tolerance.

        Args:
            lat1, lon1: First coordinate pair
            lat2, lon2: Second coordinate pair

        Returns:
            True if coordinates match within tolerance
        """
        return (
            abs(lat1 - lat2) <= self.coordinate_tolerance
            and abs(lon1 - lon2) <= self.coordinate_tolerance
        )

    def validate_entry(
        self,
        pdf_file: str,
        extracted_blmid: Optional[str],
        extracted_latitude: Optional[float],
        extracted_longitude: Optional[float],
        excel_lookup_result: Optional[Dict],
        database_lookup_result: Optional[Dict],
        pdf_extraction_errors: List[str],
    ) -> ValidationResult:
        """
        Validate a single extracted entry.

        Args:
            pdf_file: Source PDF filename
            extracted_blmid: BLMID extracted from PDF
            extracted_latitude: Latitude extracted from PDF
            extracted_longitude: Longitude extracted from PDF
            excel_lookup_result: Result from Excel lookup by BLMID
            database_lookup_result: Result from database lookup by coordinates
            pdf_extraction_errors: Errors from PDF extraction

        Returns:
            ValidationResult object
        """
        result = ValidationResult(
            pdf_file=pdf_file,
            blmid=extracted_blmid,
            latitude=extracted_latitude,
            longitude=extracted_longitude,
            excel_match=False,
            database_match=False,
            correct_blmid=extracted_blmid,
            correction_needed=False,
            errors=list(pdf_extraction_errors),
            warnings=[],
        )

        # Validate coordinates
        coords_valid, coord_errors = self.validate_coordinates(
            extracted_latitude, extracted_longitude
        )
        if not coords_valid:
            result.errors.extend(coord_errors)
            return result

        # Check if coordinates match Excel entry
        if excel_lookup_result:
            if self.check_coordinates_match(
                extracted_latitude,
                extracted_longitude,
                excel_lookup_result["latitude"],
                excel_lookup_result["longitude"],
            ):
                result.excel_match = True
                logger.info(
                    f"{pdf_file}: BLMID {extracted_blmid} coordinates match Excel"
                )
            else:
                result.warnings.append(
                    f"BLMID {extracted_blmid} in Excel but coordinates don't match"
                )

        # Query database for coordinates
        if database_lookup_result:
            result.database_match = True
            if extracted_blmid and database_lookup_result["blmid"].upper() != extracted_blmid.upper():
                result.correction_needed = True
                result.correct_blmid = database_lookup_result["blmid"]
                logger.warning(
                    f"{pdf_file}: BLMID correction needed: {extracted_blmid} -> {database_lookup_result['blmid']}"
                )
        else:
            result.errors.append("No matching BLMID found in database for these coordinates")

        return result

    def batch_validate(
        self,
        pdf_extractions: List[Dict],
        excel_handler,
        database_connector,
    ) -> Dict:
        """
        Validate batch of PDF extractions.

        Args:
            pdf_extractions: List of PDF extraction results
            excel_handler: ExcelHandler instance
            database_connector: DatabaseConnector or MockDatabase instance

        Returns:
            Dictionary with validation summary and results
        """
        results = []
        summary = {
            "total_processed": len(pdf_extractions),
            "valid_entries": 0,
            "corrected_entries": 0,
            "failed_extractions": 0,
            "corrections": [],
        }

        for extraction in pdf_extractions:
            pdf_file = extraction.get("pdf_file", "unknown")
            extracted_blmid = extraction.get("blmid")
            extracted_latitude = extraction.get("latitude")
            extracted_longitude = extraction.get("longitude")
            extraction_errors = extraction.get("errors", [])

            # Lookup in Excel
            excel_result = None
            if extracted_blmid:
                excel_result = excel_handler.find_by_blmid(extracted_blmid)

            # Lookup in database by coordinates
            database_result = None
            if extracted_latitude is not None and extracted_longitude is not None:
                database_result = database_connector.find_by_coordinates(
                    extracted_latitude, extracted_longitude, self.coordinate_tolerance
                )

            # Validate
            validation = self.validate_entry(
                pdf_file=pdf_file,
                extracted_blmid=extracted_blmid,
                extracted_latitude=extracted_latitude,
                extracted_longitude=extracted_longitude,
                excel_lookup_result=excel_result,
                database_lookup_result=database_result,
                pdf_extraction_errors=extraction_errors,
            )

            results.append(validation)

            # Update summary
            if validation.errors:
                summary["failed_extractions"] += 1
            elif validation.correction_needed:
                summary["corrected_entries"] += 1
                summary["corrections"].append({
                    "Original_Entry": validation.blmid,
                    "Corrected_BLMID": validation.correct_blmid,
                    "Latitude": validation.latitude,
                    "Longitude": validation.longitude,
                    "Source_PDF": validation.pdf_file,
                })
            else:
                summary["valid_entries"] += 1

        summary["results"] = results
        return summary
