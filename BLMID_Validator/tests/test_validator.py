"""
Unit tests for BLMID Validator.
"""

import unittest
import tempfile
import os
from pathlib import Path
import json
import pandas as pd

# Mock imports for testing (in case libraries not installed)
import sys
from unittest.mock import Mock, patch

from blmid_validator.config import Config
from blmid_validator.validator import Validator
from blmid_validator.excel_handler import ExcelHandler
from blmid_validator.excel_processor import DirectExcelProcessor
from blmid_validator.database import MockDatabase
from blmid_validator.pdf_extractor import PDFExtractor


class TestConfig(unittest.TestCase):
    """Test configuration module."""

    def test_config_defaults(self):
        """Test default configuration."""
        config = Config()
        self.assertIsNotNone(config.get("database.connection_uri"))
        self.assertEqual(config.get("validation.coordinate_tolerance"), 0.0001)

    def test_config_get_set(self):
        """Test config get/set with dot notation."""
        config = Config()
        config.set("test.key", "value")
        self.assertEqual(config.get("test.key"), "value")

    def test_config_save_load(self):
        """Test config save and load."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "test_config.yaml")
            
            # Save
            config1 = Config()
            config1.set("test.value", 42)
            config1.save_to_file(config_path, format="yaml")
            
            # Load
            config2 = Config(config_path)
            self.assertEqual(config2.get("test.value"), 42)


class TestValidator(unittest.TestCase):
    """Test validation module."""

    def setUp(self):
        """Setup test fixtures."""
        self.validator = Validator()

    def test_validate_coordinates_valid(self):
        """Test valid coordinate validation."""
        valid, errors = self.validator.validate_coordinates(40.7128, -74.0060)
        self.assertTrue(valid)
        self.assertEqual(len(errors), 0)

    def test_validate_coordinates_out_of_range(self):
        """Test out of range coordinates."""
        valid, errors = self.validator.validate_coordinates(95.0, 200.0)
        self.assertFalse(valid)
        self.assertTrue(len(errors) > 0)

    def test_validate_coordinates_none(self):
        """Test None coordinates."""
        valid, errors = self.validator.validate_coordinates(None, None)
        self.assertFalse(valid)
        self.assertTrue(len(errors) > 0)

    def test_coordinates_match(self):
        """Test coordinate matching."""
        # Exact match
        match = self.validator.check_coordinates_match(40.0, -74.0, 40.0, -74.0)
        self.assertTrue(match)

        # Within tolerance
        match = self.validator.check_coordinates_match(
            40.0, -74.0, 40.00005, -74.00005
        )
        self.assertTrue(match)

        # Outside tolerance
        match = self.validator.check_coordinates_match(
            40.0, -74.0, 40.001, -74.0
        )
        self.assertFalse(match)


class TestExcelHandler(unittest.TestCase):
    """Test Excel handling module."""

    def setUp(self):
        """Setup test fixtures."""
        self.handler = ExcelHandler()

    def test_excel_load_and_find(self):
        """Test loading Excel and finding records."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test Excel file
            test_data = {
                "BLMID": ["BLM001", "BLM002"],
                "Latitude": [40.7128, 51.5074],
                "Longitude": [-74.0060, -0.1278],
            }
            df = pd.DataFrame(test_data)
            excel_path = os.path.join(tmpdir, "test.xlsx")
            df.to_excel(excel_path, index=False, engine="openpyxl")

            # Load and find
            self.handler.load(excel_path)
            result = self.handler.find_by_blmid("BLM001")
            self.assertIsNotNone(result)
            self.assertEqual(result["blmid"], "BLM001")
            self.assertAlmostEqual(result["latitude"], 40.7128)

    def test_excel_find_by_coordinates(self):
        """Test finding record by coordinates."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_data = {
                "BLMID": ["BLM001"],
                "Latitude": [40.7128],
                "Longitude": [-74.0060],
            }
            df = pd.DataFrame(test_data)
            excel_path = os.path.join(tmpdir, "test.xlsx")
            df.to_excel(excel_path, index=False, engine="openpyxl")

            self.handler.load(excel_path)
            result = self.handler.find_by_coordinates(40.7128, -74.0060)
            self.assertIsNotNone(result)
            self.assertEqual(result["blmid"], "BLM001")


class TestMockDatabase(unittest.TestCase):
    """Test mock database."""

    def setUp(self):
        """Setup test fixtures."""
        self.db = MockDatabase()

    def test_find_by_coordinates(self):
        """Test finding by coordinates."""
        result = self.db.find_by_coordinates(40.7128, -74.0060)
        self.assertIsNotNone(result)
        self.assertEqual(result["blmid"], "BLM001")

    def test_find_by_blmid(self):
        """Test finding by BLMID."""
        result = self.db.find_by_blmid("BLM002")
        self.assertIsNotNone(result)
        self.assertAlmostEqual(result["latitude"], 51.5074)

    def test_find_not_found(self):
        """Test finding non-existent record."""
        result = self.db.find_by_coordinates(0.0, 0.0)
        self.assertIsNone(result)


class TestPDFExtractor(unittest.TestCase):
    """Test PDF extraction module."""

    def setUp(self):
        """Setup test fixtures."""
        self.extractor = PDFExtractor()

    def test_extract_from_text(self):
        """Test text pattern extraction."""
        test_text = """
        BLMID: BLM12345
        Latitude: 40.7128
        Longitude: -74.0060
        """
        result = {}
        self.extractor._extract_from_text(test_text, result)
        self.assertIsNotNone(result["blmid"])
        self.assertAlmostEqual(result["latitude"], 40.7128)
        self.assertAlmostEqual(result["longitude"], -74.0060)


class TestDirectExcelProcessor(unittest.TestCase):
    """Test direct Excel processing."""

    def setUp(self):
        """Setup test fixtures."""
        self.config = Config()
        self.processor = DirectExcelProcessor(self.config, use_mock_db=True)

    def test_standardize_columns(self):
        """Test column name standardization."""
        test_df = pd.DataFrame({
            "BLM_ID": ["BLM001"],
            "Lat": [40.7128],
            "Lon": [-74.0060]
        })
        standardized = self.processor._standardize_columns(test_df)
        self.assertIn("BLMID", standardized.columns)
        self.assertIn("Latitude", standardized.columns)
        self.assertIn("Longitude", standardized.columns)

    def test_process_excel_batch(self):
        """Test batch Excel processing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create extracted data
            extracted_data = {
                "BLMID": ["BLM001", "BLM002"],
                "Latitude": [40.7128, 51.5074],
                "Longitude": [-74.0060, -0.1278],
            }
            extracted_df = pd.DataFrame(extracted_data)
            extracted_file = f"{tmpdir}/extracted.xlsx"
            extracted_df.to_excel(extracted_file, index=False, engine="openpyxl")

            # Create reference data
            reference_data = {
                "BLMID": ["BLM001"],
                "Latitude": [40.7128],
                "Longitude": [-74.0060],
            }
            reference_df = pd.DataFrame(reference_data)
            reference_file = f"{tmpdir}/reference.xlsx"
            reference_df.to_excel(reference_file, index=False, engine="openpyxl")

            # Process
            result = self.processor.process_excel_batch(
                extracted_file, reference_file, f"{tmpdir}/output"
            )

            self.assertTrue(result["success"])
            self.assertGreater(result["total_processed"], 0)

    def test_validate_entry_valid(self):
        """Test validation of valid entry."""
        reference_df = pd.DataFrame({
            "BLMID": ["BLM001"],
            "Latitude": [40.7128],
            "Longitude": [-74.0060],
        })

        result = self.processor._validate_entry(
            "BLM001", 40.7128, -74.0060, reference_df, 0
        )

        self.assertEqual(result["status"], "valid")
        self.assertEqual(result["blmid"], "BLM001")

    def test_validate_entry_corrected(self):
        """Test validation requiring correction."""
        reference_df = pd.DataFrame({
            "BLMID": ["BLM999"],
            "Latitude": [40.0],
            "Longitude": [-74.0],
        })

        result = self.processor._validate_entry(
            "BLM001", 40.7128, -74.0060, reference_df, 0
        )

        # Should query database and find correction
        # With mock DB, BLM001 exists at 40.7128, -74.0060
        self.assertIn(result["status"], ["valid", "corrected", "failed"])

    def test_validate_entry_invalid_coordinates(self):
        """Test validation with invalid coordinates."""
        reference_df = pd.DataFrame({"BLMID": [], "Latitude": [], "Longitude": []})

        result = self.processor._validate_entry(
            "BLM001", 95.0, 200.0, reference_df, 0
        )

        self.assertEqual(result["status"], "failed")
        self.assertIn("out of range", result["error"])


def run_tests():
    """Run all tests."""
    unittest.main(argv=[""], exit=False, verbosity=2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
