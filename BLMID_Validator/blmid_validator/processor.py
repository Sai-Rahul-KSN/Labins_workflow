"""
Main processor for BLMID Validator.
Orchestrates PDF extraction, validation, and report generation.
"""

import logging
from pathlib import Path
from typing import Optional, Dict
import pandas as pd

from .pdf_extractor import PDFExtractor
from .excel_handler import ExcelHandler
from .database import DatabaseConnector, MockDatabase
from .validator import Validator
from .config import Config

logger = logging.getLogger(__name__)


class BLMIDProcessor:
    """Main processor for BLMID validation workflow."""

    def __init__(self, config: Config, use_mock_db: bool = False):
        """
        Initialize processor.

        Args:
            config: Config object
            use_mock_db: Use mock database instead of real PostgreSQL (for testing)
        """
        self.config = config
        self.use_mock_db = use_mock_db

        # Initialize components
        self.pdf_extractor = PDFExtractor(
            blmid_pattern=config.get("pdf.regex_patterns.blmid"),
            latitude_pattern=config.get("pdf.regex_patterns.latitude"),
            longitude_pattern=config.get("pdf.regex_patterns.longitude"),
            ocr_enabled=config.get("pdf.ocr_enabled", True),
            ocr_fallback=config.get("pdf.ocr_fallback", True),
            tesseract_path=config.get("pdf.tesseract_path"),
        )

        self.excel_handler = ExcelHandler(
            sheet_name=config.get("excel.sheet_name"),
            blmid_column=config.get("excel.columns.blmid", "A"),
            latitude_column=config.get("excel.columns.latitude", "B"),
            longitude_column=config.get("excel.columns.longitude", "C"),
            header_row=config.get("excel.header_row", 1),
        )

        # Initialize database (will be set in process methods)
        self.database_connector: Optional[DatabaseConnector] = None
        self.use_mock_db = use_mock_db

        self.validator = Validator(
            coordinate_tolerance=config.get("validation.coordinate_tolerance", 0.0001),
            latitude_min=config.get("validation.latitude_min", -90),
            latitude_max=config.get("validation.latitude_max", 90),
            longitude_min=config.get("validation.longitude_min", -180),
            longitude_max=config.get("validation.longitude_max", 180),
            check_duplicates=config.get("validation.check_duplicates", True),
        )

    def initialize_database(self) -> None:
        """Initialize database connector."""
        if self.use_mock_db:
            logger.info("Using mock database for testing")
            self.database_connector = MockDatabase()
        else:
            connection_uri = self.config.get("database.connection_uri")
            table_name = self.config.get("database.table_name", "blmid_reference")
            blmid_col = self.config.get("database.columns.blmid", "blmid")
            lat_col = self.config.get("database.columns.latitude", "latitude")
            lon_col = self.config.get("database.columns.longitude", "longitude")

            try:
                self.database_connector = DatabaseConnector(
                    connection_uri=connection_uri,
                    table_name=table_name,
                    blmid_column=blmid_col,
                    latitude_column=lat_col,
                    longitude_column=lon_col,
                )
                logger.info("Database connector initialized")
            except Exception as e:
                logger.error(f"Failed to initialize database: {e}")
                raise

    def process_single_pdf(
        self, pdf_path: str, excel_path: str, output_dir: str = "./output"
    ) -> Dict:
        """
        Process a single PDF file.

        Args:
            pdf_path: Path to PDF file
            excel_path: Path to Excel reference file
            output_dir: Output directory for reports

        Returns:
            Processing result dictionary
        """
        logger.info(f"Processing single PDF: {pdf_path}")

        # Initialize database if not done
        if not self.database_connector:
            self.initialize_database()

        # Load Excel reference
        self.excel_handler.load(excel_path)

        # Extract from PDF
        extraction = self.pdf_extractor.extract_from_pdf(pdf_path)
        extraction["pdf_file"] = Path(pdf_path).name

        # Validate
        validation_result = self.validator.batch_validate(
            [extraction], self.excel_handler, self.database_connector
        )

        # Generate reports
        if validation_result["corrections"]:
            self._save_corrections_log(validation_result["corrections"], output_dir)

        logger.info(f"Single PDF processing complete: {Path(pdf_path).name}")
        return validation_result

    def process_batch_pdfs(
        self, pdf_dir: str, excel_path: str, output_dir: str = "./output"
    ) -> Dict:
        """
        Process all PDFs in a directory.

        Args:
            pdf_dir: Directory containing PDF files
            excel_path: Path to Excel reference file
            output_dir: Output directory for reports

        Returns:
            Processing result dictionary with summary
        """
        logger.info(f"Processing batch of PDFs from: {pdf_dir}")

        # Initialize database if not done
        if not self.database_connector:
            self.initialize_database()

        # Load Excel reference
        self.excel_handler.load(excel_path)

        # Extract from all PDFs
        extractions = self.pdf_extractor.batch_extract(pdf_dir)
        logger.info(f"Extracted data from {len(extractions)} PDFs")

        # Validate
        validation_result = self.validator.batch_validate(
            extractions, self.excel_handler, self.database_connector
        )

        # Generate reports
        output_files = {}
        if validation_result["corrections"]:
            output_files["corrections_log"] = self._save_corrections_log(
                validation_result["corrections"], output_dir
            )

        output_files["updated_excel"] = self._save_updated_excel(
            extractions, validation_result, output_dir
        )

        validation_result["output_files"] = output_files
        logger.info(f"Batch processing complete. Results saved to {output_dir}")
        return validation_result

    def _save_corrections_log(
        self, corrections: list, output_dir: str = "./output"
    ) -> str:
        """Save corrections log."""
        return self.excel_handler.save_corrections_log(corrections, output_dir)

    def _save_updated_excel(
        self, extractions: list, validation_result: dict, output_dir: str = "./output"
    ) -> str:
        """
        Save updated Excel with corrections applied.

        Args:
            extractions: Original extractions
            validation_result: Validation results
            output_dir: Output directory

        Returns:
            Path to saved file
        """
        # Build updated data from extractions and corrections
        data = []
        for extraction, validation in zip(
            extractions, validation_result.get("results", [])
        ):
            data.append({
                "BLMID": validation.correct_blmid,
                "Latitude": validation.latitude,
                "Longitude": validation.longitude,
                "Source_PDF": validation.pdf_file,
                "Correction_Applied": validation.correction_needed,
            })

        df_updated = pd.DataFrame(data)
        return self.excel_handler.save_updated(df_updated, output_dir)
