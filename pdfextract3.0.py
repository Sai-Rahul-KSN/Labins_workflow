import sys
import os
import pandas as pd
import re
from datetime import datetime
import subprocess

# Directory containing PDFs (same as PDF_FOLDER in batch script)
PDF_DIR = r"C:\Users\sk23dg\Desktop\Content_extraction"
# Output Excel file
EXCEL_OUTPUT = r"C:\Users\sk23dg\Desktop\Content_extraction\output.xlsx"

# Path to the batch script (adjust if needed)
BATCH_SCRIPT = r"C:\Users\sk23dg\Desktop\Content_extraction\pdf_form_extractor2.0.py"

def parse_batch_output(output):
    lines = output.strip().split('\n')
    results = []
    current_result = None
    key_map = {
        'Doc Num': 'doc_num',
        'Corner of Section': 'corner_of_section',
        'Township (value)': 'township',
        'Range (value)': 'range',
        'County (value)': 'county',
        'Image present (bool)': 'image_present_bool',
        'Image present (Y/N)': 'image_present_flag',
        'Township options': 'township_options',
        'Range options': 'range_options',
        'County options': 'county_options'
    }

    for line in lines:
        if 'Extraction results for' in line:
            filename_match = re.search(r'Extraction results for (.+):', line)
            if filename_match:
                if current_result:
                    results.append(current_result)
                current_result = {'filename': filename_match.group(1)}
        elif current_result and ':' in line:
            parts = line.split(':', 1)
            if len(parts) == 2:
                key = parts[0].strip()
                value = parts[1].strip()
                if key in key_map:
                    mapped_key = key_map[key]
                    if mapped_key == 'image_present_bool':
                        current_result[mapped_key] = True if value == 'True' else False
                    elif 'options' in mapped_key:
                        if value == 'None' or not value:
                            current_result[mapped_key] = ''
                        else:
                            current_result[mapped_key] = value.replace(', ', ',')  # Normalize to comma without space
                    else:
                        current_result[mapped_key] = value
        elif '---' in line and current_result:
            results.append(current_result)
            current_result = None

    if current_result:
        results.append(current_result)

    return results

def main():
    # Run the batch script and capture output
    try:
        batch_result = subprocess.run([sys.executable, BATCH_SCRIPT], capture_output=True, text=True, check=True)
        batch_output = batch_result.stdout
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] INFO: Batch script executed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ERROR: Failed to run batch script: {e}")
        print(f"Batch stderr: {e.stderr}")
        sys.exit(1)

    # Parse the output
    results_list = parse_batch_output(batch_output)
    
    if not results_list:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ERROR: No results parsed from batch output.")
        sys.exit(1)
    
    # Create DataFrame
    df = pd.DataFrame(results_list)
    
    # Reorder columns to include filename and match desired output
    columns = [
        "filename", "doc_num", "corner_of_section", "township", "range", "county",
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