"""
Excel handling module for BLMID Validator.
Loads, validates, and updates Excel reference sheets.
"""

import logging
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import pandas as pd
from datetime import datetime

logger = logging.getLogger(__name__)


class ExcelHandler:
    """Load and manage Excel reference sheets."""

    def __init__(
        self,
        sheet_name: Optional[str] = None,
        blmid_column: str = "A",
        latitude_column: str = "B",
        longitude_column: str = "C",
        header_row: int = 1,
    ):
        """
        Initialize Excel handler.

        Args:
            sheet_name: Sheet name in Excel (None = first sheet)
            blmid_column: Column letter for BLMID
            latitude_column: Column letter for Latitude
            longitude_column: Column letter for Longitude
            header_row: Header row number (1-indexed)
        """
        self.sheet_name = sheet_name
        self.blmid_column = blmid_column
        self.latitude_column = latitude_column
        self.longitude_column = longitude_column
        self.header_row = header_row - 1  # Convert to 0-indexed
        self.df: Optional[pd.DataFrame] = None
        self.file_path: Optional[str] = None

    def load(self, excel_path: str) -> pd.DataFrame:
        """
        Load Excel reference sheet.

        Args:
            excel_path: Path to Excel file

        Returns:
            DataFrame with columns: BLMID, Latitude, Longitude
        """
        excel_path = Path(excel_path)
        if not excel_path.exists():
            logger.error(f"Excel file not found: {excel_path}")
            raise FileNotFoundError(f"Excel file not found: {excel_path}")

        try:
            # Read Excel file
            if self.sheet_name:
                df = pd.read_excel(excel_path, sheet_name=self.sheet_name, header=self.header_row)
            else:
                df = pd.read_excel(excel_path, sheet_name=0, header=self.header_row)

            logger.info(f"Loaded Excel file: {excel_path} with {len(df)} rows")

            # Standardize column names
            df = self._standardize_columns(df)
            self.df = df
            self.file_path = str(excel_path)
            return df

        except Exception as e:
            logger.error(f"Failed to load Excel file {excel_path}: {e}")
            raise

    def _standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Standardize column names to BLMID, Latitude, Longitude.
        Accepts columns by position (A, B, C) or by name.
        """
        # Try to get columns by position (column letters)
        col_mapping = {}
        try:
            # Map Excel column letters to pandas column indices
            col_list = df.columns.tolist()
            
            # Get column indices for specified letters (A=0, B=1, C=2)
            blmid_idx = ord(self.blmid_column.upper()) - ord('A')
            lat_idx = ord(self.latitude_column.upper()) - ord('A')
            lon_idx = ord(self.longitude_column.upper()) - ord('A')

            if blmid_idx < len(col_list):
                col_mapping[col_list[blmid_idx]] = "BLMID"
            if lat_idx < len(col_list):
                col_mapping[col_list[lat_idx]] = "Latitude"
            if lon_idx < len(col_list):
                col_mapping[col_list[lon_idx]] = "Longitude"

            df = df.rename(columns=col_mapping)
        except Exception as e:
            logger.warning(f"Column position mapping failed: {e}. Trying name-based mapping...")
            # Fallback: try to find by name (case-insensitive)
            for col in df.columns:
                col_lower = str(col).lower()
                if "blmid" in col_lower:
                    df = df.rename(columns={col: "BLMID"})
                elif "latitude" in col_lower or "lat" in col_lower:
                    df = df.rename(columns={col: "Latitude"})
                elif "longitude" in col_lower or "lon" in col_lower:
                    df = df.rename(columns={col: "Longitude"})

        # Ensure required columns exist
        required_cols = ["BLMID", "Latitude", "Longitude"]
        missing = [col for col in required_cols if col not in df.columns]
        if missing:
            logger.warning(f"Missing columns in Excel: {missing}")

        return df

    def get_reference_data(self) -> pd.DataFrame:
        """Get loaded reference DataFrame."""
        if self.df is None:
            raise ValueError("No Excel file loaded. Call load() first.")
        return self.df

    def find_by_blmid(self, blmid: str) -> Optional[Dict]:
        """
        Find reference record by BLMID.

        Args:
            blmid: BLMID to search for

        Returns:
            Dict with record or None if not found
        """
        if self.df is None:
            return None

        matches = self.df[self.df["BLMID"].astype(str).str.upper() == str(blmid).upper()]
        if len(matches) > 0:
            row = matches.iloc[0]
            return {
                "blmid": row["BLMID"],
                "latitude": float(row["Latitude"]),
                "longitude": float(row["Longitude"]),
            }
        return None

    def find_by_coordinates(
        self, latitude: float, longitude: float, tolerance: float = 0.0001
    ) -> Optional[Dict]:
        """
        Find reference record by coordinates within tolerance.

        Args:
            latitude: Target latitude
            longitude: Target longitude
            tolerance: Tolerance in degrees

        Returns:
            Dict with record or None if not found
        """
        if self.df is None:
            return None

        # Filter by coordinate tolerance
        matches = self.df[
            (abs(self.df["Latitude"] - latitude) <= tolerance)
            & (abs(self.df["Longitude"] - longitude) <= tolerance)
        ]

        if len(matches) > 0:
            row = matches.iloc[0]
            return {
                "blmid": row["BLMID"],
                "latitude": float(row["Latitude"]),
                "longitude": float(row["Longitude"]),
            }
        return None

    def save_updated(
        self, updated_data: pd.DataFrame, output_dir: str = "./output"
    ) -> str:
        """
        Save updated Excel with corrections.

        Args:
            updated_data: DataFrame with updated BLMIDs
            output_dir: Output directory

        Returns:
            Path to saved file
        """
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = Path(output_dir) / f"Updated_BLMID_{timestamp}.xlsx"

        try:
            updated_data.to_excel(output_file, index=False, engine="openpyxl")
            logger.info(f"Updated Excel saved to {output_file}")
            return str(output_file)
        except Exception as e:
            logger.error(f"Failed to save updated Excel: {e}")
            raise

    def save_corrections_log(
        self, corrections: List[Dict], output_dir: str = "./output"
    ) -> str:
        """
        Save corrections log Excel.

        Args:
            corrections: List of correction records
            output_dir: Output directory

        Returns:
            Path to saved file
        """
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = Path(output_dir) / f"Corrections_Log_{timestamp}.xlsx"

        try:
            df = pd.DataFrame(corrections)
            df = df[
                [
                    "Original_Entry",
                    "Corrected_BLMID",
                    "Latitude",
                    "Longitude",
                    "Source_PDF",
                ]
            ]
            df.to_excel(output_file, index=False, engine="openpyxl")
            logger.info(f"Corrections log saved to {output_file}")
            return str(output_file)
        except Exception as e:
            logger.error(f"Failed to save corrections log: {e}")
            raise
