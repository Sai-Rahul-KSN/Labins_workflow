"""
Direct Excel processor for BLMID Validator.
Processes BLMID data directly from extracted Excel sheets (no PDF needed).
"""

import logging
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class DirectExcelProcessor:
    """Process BLMID validation directly from extracted Excel data."""

    def __init__(self, config, use_mock_db: bool = False):
        """
        Initialize processor.

        Args:
            config: Config object
            use_mock_db: Use mock database if True
        """
        self.config = config
        self.use_mock_db = use_mock_db
        self.tolerance = config.get("validation.coordinate_tolerance", 0.0001)

        # Initialize database
        if use_mock_db:
            from .database import MockDatabase
            self.db = MockDatabase()
        else:
            from .database import DatabaseConnector
            uri = config.get("database.connection_uri")
            table_name = config.get("database.table_name", "blmid_reference")
            blmid_col = config.get("database.columns.blmid", "blmid")
            lat_col = config.get("database.columns.latitude", "latitude")
            lon_col = config.get("database.columns.longitude", "longitude")
            
            try:
                self.db = DatabaseConnector(
                    connection_uri=uri,
                    table_name=table_name,
                    blmid_column=blmid_col,
                    latitude_column=lat_col,
                    longitude_column=lon_col,
                )
            except Exception as e:
                logger.error(f"Failed to initialize database: {e}")
                raise

    def process_excel_batch(
        self,
        extracted_excel: str,
        reference_excel: str,
        output_dir: str = "./output",
    ) -> Dict:
        """
        Process extracted BLMID data from Excel.

        Args:
            extracted_excel: Path to Excel with extracted BLMID/coords
            reference_excel: Path to reference Excel
            output_dir: Output directory for reports

        Returns:
            Dict with processing summary
        """
        logger.info("=" * 60)
        logger.info("Starting Direct Excel Processing")
        logger.info("=" * 60)
        logger.info(f"Extracted data: {extracted_excel}")
        logger.info(f"Reference data: {reference_excel}")

        Path(output_dir).mkdir(parents=True, exist_ok=True)

        # Load data
        try:
            extracted_df = pd.read_excel(extracted_excel)
            reference_df = pd.read_excel(reference_excel)
            logger.info(f"Loaded {len(extracted_df)} extracted entries")
            logger.info(f"Loaded {len(reference_df)} reference entries")
        except Exception as e:
            logger.error(f"Failed to load Excel files: {e}")
            return {"success": False, "error": str(e), "results": []}

        # Normalize column names
        extracted_df = self._standardize_columns(extracted_df)
        reference_df = self._standardize_columns(reference_df)

        # Process each entry
        results = {
            "valid_entries": [],
            "corrected_entries": [],
            "failed_entries": [],
            "total_processed": 0,
            "results": [],
        }

        for idx, row in extracted_df.iterrows():
            try:
                blmid = str(row.get("BLMID", "")).strip()
                latitude = float(row.get("Latitude"))
                longitude = float(row.get("Longitude"))

                validation_result = self._validate_entry(
                    blmid, latitude, longitude, reference_df, idx
                )

                results["results"].append(validation_result)

                if validation_result["status"] == "valid":
                    results["valid_entries"].append(validation_result)
                elif validation_result["status"] == "corrected":
                    results["corrected_entries"].append(validation_result)
                else:
                    results["failed_entries"].append(validation_result)

                results["total_processed"] += 1

            except Exception as e:
                logger.error(f"Row {idx}: {e}")
                error_result = {
                    "status": "failed",
                    "row": idx,
                    "blmid": row.get("BLMID", "N/A"),
                    "error": str(e),
                    "latitude": None,
                    "longitude": None,
                }
                results["failed_entries"].append(error_result)
                results["results"].append(error_result)
                results["total_processed"] += 1

        # Generate reports
        output_files = self._generate_reports(extracted_df, results, output_dir)
        results["output_files"] = output_files
        results["success"] = True

        # Log summary
        logger.info("=" * 60)
        logger.info("Processing Complete")
        logger.info(f"Total processed:     {results['total_processed']}")
        logger.info(f"Valid entries:       {len(results['valid_entries'])}")
        logger.info(f"Corrected entries:   {len(results['corrected_entries'])}")
        logger.info(f"Failed entries:      {len(results['failed_entries'])}")
        logger.info("=" * 60)

        return results

    @staticmethod
    def _standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
        """Standardize column names to BLMID, Latitude, Longitude."""
        # Try to find columns by name (case-insensitive)
        col_mapping = {}
        for col in df.columns:
            col_lower = str(col).lower()
            if "blmid" in col_lower:
                col_mapping[col] = "BLMID"
            elif "latitude" in col_lower or "lat" in col_lower:
                col_mapping[col] = "Latitude"
            elif "longitude" in col_lower or "lon" in col_lower:
                col_mapping[col] = "Longitude"

        df = df.rename(columns=col_mapping)
        
        # Ensure required columns exist
        if "BLMID" not in df.columns:
            logger.warning("BLMID column not found")
        if "Latitude" not in df.columns:
            logger.warning("Latitude column not found")
        if "Longitude" not in df.columns:
            logger.warning("Longitude column not found")

        return df

    def _validate_entry(
        self,
        blmid: str,
        latitude: float,
        longitude: float,
        reference_df: pd.DataFrame,
        row_index: int,
    ) -> Dict:
        """
        Validate single entry against reference and database.

        Args:
            blmid: BLMID from extracted data
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            reference_df: Reference data DataFrame
            row_index: Row index for tracking

        Returns:
            Validation result dict
        """
        # Validate coordinate ranges
        if latitude < -90 or latitude > 90:
            return {
                "status": "failed",
                "row": row_index,
                "blmid": blmid,
                "latitude": latitude,
                "longitude": longitude,
                "error": f"Latitude {latitude} out of range [-90, 90]",
            }

        if longitude < -180 or longitude > 180:
            return {
                "status": "failed",
                "row": row_index,
                "blmid": blmid,
                "latitude": latitude,
                "longitude": longitude,
                "error": f"Longitude {longitude} out of range [-180, 180]",
            }

        # Check reference Excel first
        ref_match = self._find_in_reference(
            blmid, latitude, longitude, reference_df
        )

        if ref_match and ref_match["match_type"] == "exact":
            # Exact match in reference - entry is valid
            logger.info(
                f"Row {row_index}: BLMID {blmid} matches reference exactly"
            )
            return {
                "status": "valid",
                "row": row_index,
                "blmid": blmid,
                "latitude": latitude,
                "longitude": longitude,
                "source": "reference_exact",
            }

        # No exact match - query database
        db_match = self.db.find_by_coordinates(latitude, longitude, self.tolerance)

        if db_match:
            if db_match["blmid"].upper() != blmid.upper():
                # Database has different BLMID - correction needed
                logger.warning(
                    f"Row {row_index}: BLMID correction needed: {blmid} -> {db_match['blmid']}"
                )
                return {
                    "status": "corrected",
                    "row": row_index,
                    "original_blmid": blmid,
                    "corrected_blmid": db_match["blmid"],
                    "latitude": latitude,
                    "longitude": longitude,
                    "source": "database_correction",
                }
            else:
                # Database confirms BLMID - valid
                logger.info(
                    f"Row {row_index}: BLMID {blmid} confirmed by database"
                )
                return {
                    "status": "valid",
                    "row": row_index,
                    "blmid": blmid,
                    "latitude": latitude,
                    "longitude": longitude,
                    "source": "database_confirmed",
                }
        else:
            # No match found anywhere
            logger.error(
                f"Row {row_index}: No matching BLMID found in reference or database"
            )
            return {
                "status": "failed",
                "row": row_index,
                "blmid": blmid,
                "latitude": latitude,
                "longitude": longitude,
                "error": "No matching BLMID found in reference or database",
            }

    def _find_in_reference(
        self,
        blmid: str,
        latitude: float,
        longitude: float,
        reference_df: pd.DataFrame,
    ) -> Optional[Dict]:
        """Find entry in reference Excel."""
        if reference_df.empty:
            return None

        # Exact BLMID match
        if "BLMID" in reference_df.columns:
            blmid_matches = reference_df[
                reference_df["BLMID"].astype(str).str.upper() == blmid.upper()
            ]

            if not blmid_matches.empty:
                ref_row = blmid_matches.iloc[0]
                try:
                    ref_lat = float(ref_row["Latitude"])
                    ref_lon = float(ref_row["Longitude"])

                    if (
                        abs(ref_lat - latitude) <= self.tolerance
                        and abs(ref_lon - longitude) <= self.tolerance
                    ):
                        return {"match_type": "exact", "row": ref_row}
                except (ValueError, TypeError):
                    pass

        # Coordinate match in reference
        if "Latitude" in reference_df.columns and "Longitude" in reference_df.columns:
            try:
                coord_matches = reference_df[
                    (abs(reference_df["Latitude"] - latitude) <= self.tolerance)
                    & (abs(reference_df["Longitude"] - longitude) <= self.tolerance)
                ]

                if not coord_matches.empty:
                    return {
                        "match_type": "coordinate",
                        "row": coord_matches.iloc[0],
                        "blmid": coord_matches.iloc[0]["BLMID"],
                    }
            except (ValueError, TypeError):
                pass

        return None

    def _generate_reports(
        self, extracted_df: pd.DataFrame, results: Dict, output_dir: str
    ) -> Dict:
        """Generate output Excel reports."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_files = {}

        # 1. Updated BLMID file
        updated_data = extracted_df.copy()
        updated_data["Original_BLMID"] = updated_data.get("BLMID", "")
        updated_data["Correction_Applied"] = False

        for correction in results["corrected_entries"]:
            try:
                mask = (
                    (updated_data["BLMID"].astype(str) == str(correction["original_blmid"]))
                    & (updated_data["Latitude"] == correction["latitude"])
                    & (updated_data["Longitude"] == correction["longitude"])
                )
                updated_data.loc[mask, "BLMID"] = correction["corrected_blmid"]
                updated_data.loc[mask, "Correction_Applied"] = True
            except Exception as e:
                logger.warning(f"Could not apply correction: {e}")

        updated_file = f"{output_dir}/Updated_BLMID_{timestamp}.xlsx"
        try:
            updated_data.to_excel(updated_file, index=False, engine="openpyxl")
            output_files["updated_blmid"] = updated_file
            logger.info(f"Saved updated BLMID file: {updated_file}")
        except Exception as e:
            logger.error(f"Failed to save updated BLMID file: {e}")

        # 2. Corrections log file
        if results["corrected_entries"]:
            try:
                corrections_df = pd.DataFrame(
                    [
                        {
                            "Original_BLMID": c["original_blmid"],
                            "Corrected_BLMID": c["corrected_blmid"],
                            "Latitude": c["latitude"],
                            "Longitude": c["longitude"],
                        }
                        for c in results["corrected_entries"]
                    ]
                )

                corrections_file = f"{output_dir}/Corrections_Log_{timestamp}.xlsx"
                corrections_df.to_excel(corrections_file, index=False, engine="openpyxl")
                output_files["corrections_log"] = corrections_file
                logger.info(f"Saved corrections log: {corrections_file}")
            except Exception as e:
                logger.error(f"Failed to save corrections log: {e}")

        # 3. Failed entries file
        if results["failed_entries"]:
            try:
                failed_df = pd.DataFrame(
                    [
                        {
                            "Row": f.get("row", "N/A"),
                            "BLMID": f.get("blmid", "N/A"),
                            "Latitude": f.get("latitude", "N/A"),
                            "Longitude": f.get("longitude", "N/A"),
                            "Error": f.get("error", "Unknown error"),
                        }
                        for f in results["failed_entries"]
                    ]
                )

                failed_file = f"{output_dir}/Failed_Entries_{timestamp}.xlsx"
                failed_df.to_excel(failed_file, index=False, engine="openpyxl")
                output_files["failed_entries"] = failed_file
                logger.info(f"Saved failed entries: {failed_file}")
            except Exception as e:
                logger.error(f"Failed to save failed entries file: {e}")

        return output_files
