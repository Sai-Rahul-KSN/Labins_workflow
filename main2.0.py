import os
import argparse
import subprocess
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_command(command, cwd=None):
    """Run a shell command and handle errors."""
    try:
        result = subprocess.run(command, cwd=cwd, check=True, capture_output=True, text=True)
        logger.info(f"Command succeeded: {' '.join(command)}")
        logger.debug(f"Output: {result.stdout}")
        return result.stdout
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed: {' '.join(command)}\nError: {e.stderr}")
        raise

def pipeline(pdf_folder: str, images_folder: str, output_excel: str, temp_excel: str, duration: int, interval: int, dpi: int):
    """
    Run the full PDF extraction pipeline:
    1. Extract images/screenshots from PDFs.
    2. Extract form data and save to temporary Excel.
    3. Embed images into the Excel to produce final output.
    """
    pdf_folder = Path(pdf_folder).resolve()
    images_folder = Path(images_folder).resolve()
    output_excel = Path(output_excel).resolve()
    temp_excel = Path(temp_excel).resolve()

    # Ensure directories exist
    images_folder.mkdir(parents=True, exist_ok=True)

    # Step 1: Extract images and screenshots using extract_images4.0.py
    logger.info("Step 1: Extracting images and screenshots from PDFs...")
    extract_script = Path(__file__).parent / "extract_images4.0.py"
    if not extract_script.exists():
        raise FileNotFoundError(f"extract_images4.0.py not found at {extract_script}")
    
    run_command([
        "python", str(extract_script),
        "--input", str(pdf_folder),
        "--outdir", str(images_folder),
        "--rasterize", "auto",
        "--dpi", str(dpi),
        "--fields", "Survey Image",
        "--include-page-images"
    ])

    # Step 2: Extract form data using pdfextract4.0.py (which runs pdf_form_extractor3.0.py)
    logger.info("Step 2: Extracting form data to temporary Excel...")
    pdfextract_script = Path(__file__).parent / "pdfextract4.0.py"
    if not pdfextract_script.exists():
        raise FileNotFoundError(f"pdfextract4.0.py not found at {pdfextract_script}")
    
    # Temporarily override the EXCEL_OUTPUT in pdfextract4.0.py via environment or args if possible
    # Note: Since pdfextract4.0.py has hardcoded EXCEL_OUTPUT, we assume it's modified or use env vars if added.
    # For simplicity, run it and then rename the output to temp_excel.
    run_command([
        "python", str(pdfextract_script),
        "--duration", str(duration),
        "--interval", str(interval)
    ])
    default_temp = Path(r"C:\Users\sk23dg\Desktop\Content_extraction\output.xlsx")
    if default_temp.exists():
        default_temp.rename(temp_excel)
        logger.info(f"Renamed default output to {temp_excel}")
    else:
        raise FileNotFoundError("Temporary Excel from pdfextract4.0.py not found.")

    # Step 3: Embed images into Excel using excel_image_embedder5.0.py
    logger.info("Step 3: Embedding images into Excel...")
    embedder_script = Path(__file__).parent / "excel_image_embedder5.0.py"
    if not embedder_script.exists():
        raise FileNotFoundError(f"excel_image_embedder5.0.py not found at {embedder_script}")
    
    run_command([
    "python", "extract_images4.0.py",
    "--input", input_path,
    "--outdir", output_path,
    "--rasterize",   # ✅ just a flag, no "auto"
    "--dpi", "300"
])


    logger.info(f"Pipeline completed successfully. Final output: {output_excel}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PDF Extraction Pipeline: Extract data, images, screenshots, and embed in Excel.")
    parser.add_argument("--pdf_folder", default=r"C:\Users\sk23dg\Desktop\Labins_Workflow\PDF_Extractor\test_pdfs",
                        help="Folder containing PDF files")
    parser.add_argument("--images_folder", default=r"C:\Users\sk23dg\Desktop\Labins_Workflow\PDF_Extractor\test_pdfs\extracted_images",
                        help="Folder to store extracted images/screenshots")
    parser.add_argument("--output_excel", default="final_excel_with_data_and_images.xlsx",
                        help="Path for final Excel output")
    parser.add_argument("--temp_excel", default="temp_data_output.xlsx",
                        help="Path for temporary Excel from data extraction")
    parser.add_argument("--duration", type=int, default=60,
                        help="Duration for recurring data extraction in seconds")
    parser.add_argument("--interval", type=int, default=6,
                        help="Interval for recurring data extraction in seconds")
    parser.add_argument("--dpi", type=int, default=300,
                        help="DPI for image extraction and rasterization")
    args = parser.parse_args()

    try:
        pipeline(
            args.pdf_folder,
            args.images_folder,
            args.output_excel,
            args.temp_excel,
            args.duration,
            args.interval,
            args.dpi
        )
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        raise