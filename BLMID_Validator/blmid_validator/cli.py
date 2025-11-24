"""
Command-line interface for BLMID Validator.
"""

import argparse
import sys
import logging
from pathlib import Path
from typing import Optional

from .config import Config
from .logger_setup import setup_logging
from .processor import BLMIDProcessor
from .excel_processor import DirectExcelProcessor

logger = logging.getLogger(__name__)


def print_summary(result: dict) -> None:
    """Print validation summary to console."""
    print("\n" + "=" * 60)
    print("BLMID VALIDATION SUMMARY")
    print("=" * 60)
    print(f"Total PDFs Processed:  {result['total_processed']}")
    print(f"Valid Entries:         {result['valid_entries']}")
    print(f"Corrected Entries:     {result['corrected_entries']}")
    print(f"Failed Extractions:    {result['failed_extractions']}")
    print("=" * 60)

    if result["corrections"]:
        print(f"\nCorrections Applied: {len(result['corrections'])}")
        for correction in result["corrections"][:5]:  # Show first 5
            print(f"  {correction['Original_Entry']} -> {correction['Corrected_BLMID']}")
        if len(result["corrections"]) > 5:
            print(f"  ... and {len(result['corrections']) - 5} more")

    if "output_files" in result:
        print("\nOutput Files Generated:")
        for key, path in result["output_files"].items():
            print(f"  {key}: {path}")

    print("=" * 60 + "\n")


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="BLMID Validator: Validate BLMID entries from PDF survey forms"
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Single PDF processing
    single_parser = subparsers.add_parser(
        "process-single", help="Process a single PDF file"
    )
    single_parser.add_argument("pdf", help="Path to PDF file")
    single_parser.add_argument(
        "--excel", required=True, help="Path to Excel reference file"
    )
    single_parser.add_argument(
        "--output", default="./output", help="Output directory"
    )
    single_parser.add_argument(
        "--config", help="Path to config file (yaml or json)"
    )
    single_parser.add_argument(
        "--mock-db", action="store_true", help="Use mock database for testing"
    )

    # Batch processing
    batch_parser = subparsers.add_parser("process-batch", help="Process batch of PDFs")
    batch_parser.add_argument("pdf_dir", help="Directory containing PDF files")
    batch_parser.add_argument(
        "--excel", required=True, help="Path to Excel reference file"
    )
    batch_parser.add_argument(
        "--output", default="./output", help="Output directory"
    )
    batch_parser.add_argument(
        "--config", help="Path to config file (yaml or json)"
    )
    batch_parser.add_argument(
        "--mock-db", action="store_true", help="Use mock database for testing"
    )

    # Generate config template
    config_parser = subparsers.add_parser(
        "init-config", help="Generate sample config file"
    )
    config_parser.add_argument(
        "--output", default="./config.yaml", help="Output config file path"
    )
    config_parser.add_argument(
        "--format", choices=["yaml", "json"], default="yaml",
        help="Config file format"
    )

    # Direct Excel processing (no PDF)
    excel_parser = subparsers.add_parser(
        "process-excel", help="Process extracted BLMID data from Excel (no PDF needed)"
    )
    excel_parser.add_argument(
        "extracted_excel", help="Excel file with extracted BLMID/Latitude/Longitude"
    )
    excel_parser.add_argument(
        "reference_excel", help="Excel file with reference BLMID/Latitude/Longitude"
    )
    excel_parser.add_argument(
        "--output", default="./output", help="Output directory"
    )
    excel_parser.add_argument(
        "--config", help="Path to config file (yaml or json)"
    )
    excel_parser.add_argument(
        "--mock-db", action="store_true", help="Use mock database for testing"
    )
    excel_parser.add_argument(
        "--tolerance", type=float, help="Coordinate tolerance override (degrees)"
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging()

    try:
        if args.command == "process-single":
            return cmd_process_single(args)
        elif args.command == "process-batch":
            return cmd_process_batch(args)
        elif args.command == "process-excel":
            return cmd_process_excel(args)
        elif args.command == "init-config":
            return cmd_init_config(args)
        else:
            parser.print_help()
            return 1

    except Exception as e:
        logger.error(f"Command failed: {e}", exc_info=True)
        return 1


def cmd_process_single(args) -> int:
    """Process single PDF command."""
    logger.info(f"Processing single PDF: {args.pdf}")

    # Load config
    config = Config(args.config) if args.config else Config()

    # Initialize processor
    processor = BLMIDProcessor(config, use_mock_db=args.mock_db)

    # Process
    result = processor.process_single_pdf(
        args.pdf, args.excel, args.output
    )

    print_summary(result)
    return 0


def cmd_process_batch(args) -> int:
    """Process batch PDFs command."""
    logger.info(f"Processing batch of PDFs from: {args.pdf_dir}")

    # Load config
    config = Config(args.config) if args.config else Config()

    # Initialize processor
    processor = BLMIDProcessor(config, use_mock_db=args.mock_db)

    # Process
    result = processor.process_batch_pdfs(
        args.pdf_dir, args.excel, args.output
    )

    print_summary(result)
    return 0


def cmd_init_config(args) -> int:
    """Generate config file command."""
    config = Config()
    config.save_to_file(args.output, format=args.format)
    print(f"Config file generated: {args.output}")
    return 0


def cmd_process_excel(args) -> int:
    """Process Excel directly (no PDF) command."""
    logger.info(
        f"Processing Excel files: {args.extracted_excel}, {args.reference_excel}"
    )

    # Load config
    config = Config(args.config) if args.config else Config()

    # Override tolerance if provided
    if args.tolerance:
        config.set("validation.coordinate_tolerance", args.tolerance)

    # Initialize processor
    processor = DirectExcelProcessor(config, use_mock_db=args.mock_db)

    # Process
    result = processor.process_excel_batch(
        extracted_excel=args.extracted_excel,
        reference_excel=args.reference_excel,
        output_dir=args.output,
    )

    if result.get("success"):
        print_summary(result)
        return 0
    else:
        logger.error(f"Processing failed: {result.get('error')}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
