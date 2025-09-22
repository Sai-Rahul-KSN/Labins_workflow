import os
import fitz  # PyMuPDF
from pathlib import Path
import logging

# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))

# Set up logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def convert_pdf_to_images(pdf_path, output_dir, zoom=2):
    """
    Convert a PDF file to images using PyMuPDF (no poppler required).
    
    Args:
        pdf_path (str): Path to the PDF file
        output_dir (str): Directory to save the output images
        zoom (int): Zoom factor for rendering (higher means better quality but larger files)
    
    Returns:
        list: List of paths to the generated images
    """
    try:
        # Create output directory if it doesn't exist
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Get the PDF filename without extension
        pdf_name = Path(pdf_path).stem
        
        # Open the PDF
        logger.info(f"Converting {pdf_path} to images...")
        pdf_document = fitz.open(pdf_path)
        
        # List to store image paths
        image_paths = []
        
        # Convert each page
        for page_number in range(pdf_document.page_count):
            # Get the page
            page = pdf_document[page_number]
            
            # Convert page to image
            # Higher zoom factors give better quality images
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)
            
            # Define output image path
            if pdf_document.page_count == 1:
                image_path = os.path.join(output_dir, f"{pdf_name}.png")
            else:
                image_path = os.path.join(output_dir, f"{pdf_name}_page_{page_number + 1}.png")
            
            # Save the image
            pix.save(image_path)
            image_paths.append(image_path)
            logger.info(f"Saved image: {image_path}")
        
        # Close the PDF
        pdf_document.close()
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
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Get all PDF files in the input directory
    pdf_files = list(Path(input_dir).glob("*.pdf"))
    
    if not pdf_files:
        logger.warning(f"No PDF files found in {input_dir}")
        return
    
    logger.info(f"Found {len(pdf_files)} PDF files to process")
    
    # Process each PDF file
    for pdf_path in pdf_files:
        convert_pdf_to_images(str(pdf_path), output_dir)

if __name__ == "__main__":
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Define input and output directories
    input_dir = script_dir  # Use the same directory as the script
    output_dir = os.path.join(script_dir, "extracted_images")
    
    # Process all PDFs in the directory
    process_directory(input_dir, output_dir)