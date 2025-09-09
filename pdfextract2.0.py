import sys
import os
import pandas as pd
import glob
from datetime import datetime

# Path to the original script (adjust to your directory)
ORIGINAL_SCRIPT = r"C:\Users\sk23dg\Desktop\Content_extraction\pdf_form_extractor.py"

# Directory containing PDFs (from your earlier code)
PDF_DIR = r"C:\Users\sk23dg\Desktop\Content_extraction"
# Output Excel file
EXCEL_OUTPUT = r"C:\Users\sk23dg\Desktop\Content_extraction\output.xlsx"

# Add the script's directory to sys.path to allow importing
sys.path.append(os.path.dirname(ORIGINAL_SCRIPT))

try:
    # Import the original script as a module
    import pdf_form_extractor
except ImportError as e:
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ERROR: Failed to import pdf_form_extractor: {e}")
    sys.exit(1)

def process_pdf(pdf_path):
    # Temporarily override PDF_PATH in the original script
    pdf_form_extractor.PDF_PATH = pdf_path
    try:
        # Run the main function and capture results
        pdf_form_extractor.main()
        # Assume main() sets results dict (we'll access it directly or modify to return)
        # Since we can't modify, assume results is printed or accessible
        # For simplicity, we'll re-run logic to get results dict
        reader = pdf_form_extractor.load_reader(pdf_path)
        fields = pdf_form_extractor.get_fields_dict(reader)
        doc_num = pdf_form_extractor.get_value(fields, pdf_form_extractor.DOC_NUM_FIELD)
        corner_of_section = pdf_form_extractor.get_value(fields, pdf_form_extractor.CORNER_OF_SECTION_FIELD)
        township = pdf_form_extractor.get_value(fields, pdf_form_extractor.TOWNSHIP_FIELD)
        range_value = pdf_form_extractor.get_value(fields, pdf_form_extractor.RANGE_FIELD)
        county = pdf_form_extractor.get_value(fields, pdf_form_extractor.COUNTY_FIELD)
        image_present_bool = pdf_form_extractor.detect_image_in_button(reader, pdf_form_extractor.SURVEY_IMAGE_FIELD)
        image_present_flag = "Y" if image_present_bool else "N"
        township_options = pdf_form_extractor.get_choice_options(reader, pdf_form_extractor.TOWNSHIP_FIELD)
        range_options = pdf_form_extractor.get_choice_options(reader, pdf_form_extractor.RANGE_FIELD)
        county_options = pdf_form_extractor.get_choice_options(reader, pdf_form_extractor.COUNTY_FIELD)
        
        return {
            "doc_num": doc_num,
            "corner_of_section": corner_of_section,
            "township": township,
            "range": range_value,
            "county": county,
            "image_present_bool": image_present_bool,
            "image_present_flag": image_present_flag,
            "township_options": ",".join(township_options) if township_options else "",
            "range_options": ",".join(range_options) if range_options else "",
            "county_options": ",".join(county_options) if county_options else ""
        }
    except Exception as e:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ERROR processing {pdf_path}: {e}")
        return None

def main():
    # Collect results for all PDFs
    results_list = []
    pdf_files = glob.glob(os.path.join(PDF_DIR, "*.pdf"))
    
    if not pdf_files:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ERROR: No PDFs found in {PDF_DIR}")
        sys.exit(1)
    
    for pdf_path in pdf_files:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] INFO: Processing {pdf_path}")
        result = process_pdf(pdf_path)
        if result:
            results_list.append(result)
    
    # Create DataFrame
    df = pd.DataFrame(results_list)
    
    # Reorder columns to match desired output
    columns = [
        "doc_num", "corner_of_section", "township", "range", "county",
        "image_present_bool", "image_present_flag",
        "township_options", "range_options", "county_options"
    ]
    df = df[columns]
    
    # Write to Excel
    try:
        df.to_excel(EXCEL_OUTPUT, index=False, engine="openpyxl")
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] INFO: Excel saved to {EXCEL_OUTPUT}")
    except Exception as e:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ERROR: Failed to write Excel: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()