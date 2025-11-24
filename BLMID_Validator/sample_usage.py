#!/usr/bin/env python
"""
Sample usage script for BLMID Validator.
Demonstrates common workflows.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path so we can import blmid_validator
sys.path.insert(0, str(Path(__file__).parent))

from blmid_validator.config import Config
from blmid_validator.processor import BLMIDProcessor
from blmid_validator.excel_processor import DirectExcelProcessor
from blmid_validator.logger_setup import setup_logging


def example_1_single_pdf():
    """Example 1: Process a single PDF file."""
    print("\n" + "=" * 60)
    print("EXAMPLE 1: Process Single PDF")
    print("=" * 60)

    # Setup logging
    setup_logging(log_dir="./output/logs", level="INFO")

    # Load configuration (or use defaults)
    config = Config()

    # Create processor
    processor = BLMIDProcessor(config, use_mock_db=True)

    # Process single PDF
    # NOTE: Replace with your actual PDF path
    pdf_path = "./sample_data/survey_form_001.pdf"
    excel_path = "./sample_data/reference_data.xlsx"
    output_dir = "./output"

    try:
        result = processor.process_single_pdf(pdf_path, excel_path, output_dir)
        print(f"\nProcessing Result:")
        print(f"  Valid Entries: {result['valid_entries']}")
        print(f"  Corrected Entries: {result['corrected_entries']}")
        print(f"  Failed: {result['failed_extractions']}")
    except FileNotFoundError as e:
        print(f"Note: {e}")
        print("Please provide actual PDF and Excel files.")


def example_2_batch_processing():
    """Example 2: Process batch of PDF files from a directory."""
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Batch Process PDFs")
    print("=" * 60)

    # Setup logging
    setup_logging(log_dir="./output/logs", level="INFO")

    # Load configuration
    config = Config()

    # Create processor
    processor = BLMIDProcessor(config, use_mock_db=True)

    # Process batch
    pdf_dir = "./sample_data/pdfs"
    excel_path = "./sample_data/reference_data.xlsx"
    output_dir = "./output"

    try:
        result = processor.process_batch_pdfs(pdf_dir, excel_path, output_dir)
        print(f"\nBatch Processing Result:")
        print(f"  Total Processed: {result['total_processed']}")
        print(f"  Valid Entries: {result['valid_entries']}")
        print(f"  Corrected Entries: {result['corrected_entries']}")
        print(f"  Failed: {result['failed_extractions']}")
        if "output_files" in result:
            print(f"  Output Files: {result['output_files']}")
    except FileNotFoundError as e:
        print(f"Note: {e}")
        print("Please provide actual PDF directory and Excel file.")


def example_2b_direct_excel_processing():
    """Example 2b: Process BLMID data directly from extracted Excel (NO PDF NEEDED)."""
    print("\n" + "=" * 60)
    print("EXAMPLE 2b: Direct Excel Processing (No PDF)")
    print("=" * 60)

    # Setup logging
    setup_logging(log_dir="./output/logs", level="INFO")

    # Load configuration
    config = Config()

    # Create processor for direct Excel processing
    processor = DirectExcelProcessor(config, use_mock_db=True)

    # Process Excel directly
    extracted_excel = "./sample_data/extracted_blmid.xlsx"
    reference_excel = "./sample_data/reference_data.xlsx"
    output_dir = "./output"

    try:
        result = processor.process_excel_batch(
            extracted_excel=extracted_excel,
            reference_excel=reference_excel,
            output_dir=output_dir,
        )

        if result["success"]:
            print(f"\nDirect Excel Processing Result:")
            print(f"  Total Processed: {result['total_processed']}")
            print(f"  Valid Entries: {len(result['valid_entries'])}")
            print(f"  Corrected Entries: {len(result['corrected_entries'])}")
            print(f"  Failed: {len(result['failed_entries'])}")
            if "output_files" in result:
                print(f"\n  Output Files Generated:")
                for key, path in result["output_files"].items():
                    print(f"    - {key}: {path}")
        else:
            print(f"Processing failed: {result.get('error')}")

    except FileNotFoundError as e:
        print(f"Note: {e}")
        print("Please provide Excel files with BLMID, Latitude, Longitude columns.")


def example_3_custom_config():
    """Example 3: Use custom configuration."""
    print("\n" + "=" * 60)
    print("EXAMPLE 3: Custom Configuration")
    print("=" * 60)

    # Create custom configuration
    config = Config()

    # Customize settings
    config.set("database.connection_uri", "postgresql://user:password@localhost:5432/mydb")
    config.set("database.table_name", "blmid_references")
    config.set("validation.coordinate_tolerance", 0.0005)

    # Save config for later use
    config.save_to_file("./config_custom.yaml", format="yaml")
    print("Custom config saved to: ./config_custom.yaml")

    # Now processor will use custom settings
    processor = BLMIDProcessor(config, use_mock_db=True)
    print("Processor initialized with custom configuration")


def example_4_cli_commands():
    """Example 4: CLI command examples."""
    print("\n" + "=" * 60)
    print("EXAMPLE 4: CLI Commands")
    print("=" * 60)

    print("\nAvailable CLI commands:")
    print("\n1. Generate config template:")
    print("   python -m blmid_validator.cli init-config --output config.yaml")

    print("\n2. Process single PDF:")
    print("   python -m blmid_validator.cli process-single sample.pdf \\")
    print("     --excel reference.xlsx --output ./output --mock-db")

    print("\n3. Process batch of PDFs:")
    print("   python -m blmid_validator.cli process-batch ./pdf_dir \\")
    print("     --excel reference.xlsx --output ./output --mock-db")

    print("\n4. With custom config:")
    print("   python -m blmid_validator.cli process-batch ./pdf_dir \\")
    print("     --excel reference.xlsx --config config.yaml --output ./output")


if __name__ == "__main__":
    print("\nBLMID VALIDATOR - SAMPLE USAGE")
    print("=" * 60)

    # Run examples
    example_3_custom_config()
    example_4_cli_commands()
    
    # Show info about direct Excel processing
    print("\n" + "=" * 60)
    print("DIRECT EXCEL PROCESSING (New Feature)")
    print("=" * 60)
    print("\nIf you already have extracted BLMIDs in Excel:")
    print("  No need to process PDFs - use direct Excel mode!")
    print("\nCommand:")
    print("  python -m blmid_validator.cli process-excel \\")
    print("    extracted_data.xlsx reference_data.xlsx \\")
    print("    --output ./reports --mock-db")
    print("\nFor full example, run:")
    print("  python sample_usage.py --excel-example")

    # These require actual files
    # example_1_single_pdf()
    # example_2_batch_processing()
    # example_2b_direct_excel_processing()

    print("\n" + "=" * 60)
    print("For more information, see README.md")
    print("=" * 60 + "\n")
