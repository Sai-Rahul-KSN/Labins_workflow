import os
from openpyxl import load_workbook
from openpyxl.drawing.image import Image
from openpyxl.utils import get_column_letter
from pdf2image import convert_from_path
import logging

# Set up logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def convert_pdf_to_images(pdf_path, output_dir, dpi=200):
    """
    Convert a PDF file to images without requiring poppler.
    
    Args:
        pdf_path (str): Path to the PDF file
        output_dir (str): Directory to save the output images
        dpi (int): DPI for the output images (default: 200)
    
    Returns:
        list: List of paths to the generated images
    """
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Get the PDF filename without extension
        pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
        
        # Convert PDF to images
        logger.info(f"Converting {pdf_path} to images...")
        images = convert_from_path(pdf_path, dpi=dpi)
        
        # Save images
        image_paths = []
        for i, image in enumerate(images):
            # If single page PDF, don't add page number to filename
            if len(images) == 1:
                image_path = os.path.join(output_dir, f"{pdf_name}.png")
            else:
                image_path = os.path.join(output_dir, f"{pdf_name}_page_{i+1}.png")
            
            image.save(image_path)
            image_paths.append(image_path)
            logger.info(f"Saved image: {image_path}")
        
        return image_paths
    
    except Exception as e:
        logger.error(f"Error converting {pdf_path}: {str(e)}")
        return []

def process_directory(input_dir, output_dir):
    """
    Process all PDFs in the input directory and convert them to images.
    
    Args:
        input_dir (str): Directory containing PDF files
        output_dir (str): Directory to save the output images
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Get all PDF files in the input directory
    pdf_files = [f for f in os.listdir(input_dir) if f.lower().endswith('.pdf')]
    
    if not pdf_files:
        logger.warning(f"No PDF files found in {input_dir}")
        return
    
    logger.info(f"Found {len(pdf_files)} PDF files to process")
    
    # Process each PDF file
    for pdf_file in pdf_files:
        pdf_path = os.path.join(input_dir, pdf_file)
        convert_pdf_to_images(pdf_path, output_dir)

if __name__ == "__main__":
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Define input and output directories
    input_dir = script_dir  # Use the same directory as the script
    output_dir = os.path.join(script_dir, "extracted_images")
    
    # Process all PDFs in the directory
    process_directory(input_dir, output_dir)