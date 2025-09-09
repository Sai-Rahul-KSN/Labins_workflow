import sys
import os
import pandas as pd
import re
from datetime import datetime
import subprocess
import time
import argparse

# Directory containing PDFs (same as PDF_FOLDER in batch script)
PDF_DIR = r"C:\Users\sk23dg\Desktop\Content_extraction"
# Output Excel file
EXCEL_OUTPUT = r"C:\Users\sk23dg\Desktop\Content_extraction\output.xlsx"
# Path to the batch script
BATCH_SCRIPT = r"C:\Users\sk23dg\Desktop\Content_extraction\pdf_form_extractor3.0.py"

def ts():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

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
                            current_result[mapped_key] = value.replace(', ', ',')
                    else:
                        current_result[mapped_key] = value
        elif '---' in line and current_result:
            results.append(current_result)
            current_result = None

    if current_result:
        results.append(current_result)

    return results

def process_cycle(cycle_number, seen_identifiers):
    """
    Run the batch script for one cycle, parse output, and return unique results.
    """
    print(f"[{ts()}] INFO: Starting cycle {cycle_number}")
    
    try:
        batch_result = subprocess.run([sys.executable, BATCH_SCRIPT], capture_output=True, text=True, check=True)
        batch_output = batch_result.stdout
        print(f"[{ts()}] INFO: Batch script executed successfully for cycle {cycle_number}.")
    except subprocess.CalledProcessError as e:
        print(f"[{ts()}] ERROR: Failed to run batch script in cycle {cycle_number}: {e}")
        print(f"Batch stderr: {e.stderr}")
        return []

    # Parse the output
    results_list = parse_batch_output(batch_output)
    
    if not results_list:
        print(f"[{ts()}] WARN: No results parsed from batch output in cycle {cycle_number}.")
        return []

    # Filter out duplicates based on doc_num (or filename if doc_num is empty)
    unique_results = []
    for result in results_list:
        identifier = result.get('doc_num') or result.get('filename')
        if identifier and identifier not in seen_identifiers:
            seen_identifiers.add(identifier)
            unique_results.append(result)
    
    print(f"[{ts()}] INFO: Cycle {cycle_number} found {len(unique_results)} new unique PDFs.")
    return unique_results

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Recurring PDF form extraction with unique Excel output")
    parser.add_argument("--duration", type=int, default=60, help="Total duration for recurring runs in seconds (default: 86400)")
    parser.add_argument("--interval", type=int, default=6, help="Interval between runs in seconds (default: 600)")
    args = parser.parse_args()

    duration = args.duration
    interval = args.interval

    print(f"[{ts()}] INFO: Starting recurring PDF extraction for {duration} seconds, every {interval} seconds.")

    start_time = time.time()
    cycle_count = 0
    all_results = []
    seen_identifiers = set()

    while time.time() - start_time < duration:
        cycle_count += 1
        cycle_results = process_cycle(cycle_count, seen_identifiers)
        all_results.extend(cycle_results)
        
        # Wait for the next cycle, unless this was the last possible cycle
        if time.time() - start_time + interval <= duration:
            print(f"[{ts()}] INFO: Waiting {interval} seconds before next cycle.")
            time.sleep(interval)
        else:
            break

    # Create DataFrame from unique results
    if not all_results:
        print(f"[{ts()}] ERROR: No unique results collected across {cycle_count} cycles.")
        sys.exit(1)

    df = pd.DataFrame(all_results)
    
    # Reorder columns to match desired output
    columns = [
        "filename", "doc_num", "corner_of_section", "township", "range", "county",
        "image_present_bool", "image_present_flag",
        "township_options", "range_options", "county_options"
    ]
    df = df[columns]
    
    # Write to Excel
    try:
        df.to_excel(EXCEL_OUTPUT, index=False, engine="openpyxl")
        print(f"[{ts()}] INFO: Excel with {len(df)} unique records saved to {EXCEL_OUTPUT}")
    except Exception as e:
        print(f"[{ts()}] ERROR: Failed to write Excel: {e}")
        sys.exit(1)

    # Final summary
    print(f"[{ts()}] INFO: Completed {cycle_count} cycles in {int(time.time() - start_time)} seconds.")
    print(f"[{ts()}] INFO: Total unique PDFs extracted: {len(all_results)}")

if __name__ == "__main__":
    main()