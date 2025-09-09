#!/usr/bin/env python3
"""
PDF form reader for Adobe-named fields with batch processing and recurring execution.
- Extracts values from text and choice fields for multiple PDFs in a hardcoded folder
- Detects whether a "Survey Image" button field contains an image/icon
- Emits both a boolean and "Y/N" image-present flag
- Outputs results for all PDFs to stdout
- Runs repeatedly within a specified time frame (default 10 minutes) with a configurable interval
"""

import sys
import os
import glob
import datetime
import traceback
import argparse
import time

def ts() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

try:
    from PyPDF2 import PdfReader
    from PyPDF2.generic import IndirectObject, DecodedStreamObject
except Exception as e:
    print(f"[{ts()}] ERROR: PyPDF2 is required. Install with: pip install PyPDF2")
    print(f"[{ts()}] ERROR detail: {e}")
    sys.exit(1)

# --- CONFIG: Hardcoded folder path containing PDFs ---
PDF_FOLDER = r"C:\Users\sk23dg\Desktop\Content_extraction\test_pdfs"

# --- Field name constants (hard-coded to match the Adobe field names) ---
DOC_NUM_FIELD             = "Doc Num"
CORNER_OF_SECTION_FIELD   = "Corner of Section"
TOWNSHIP_FIELD            = "Township"
RANGE_FIELD               = "Range"
COUNTY_FIELD              = "County"
SURVEY_IMAGE_FIELD        = "Survey Image"  # button field intended for an image/icon

def load_reader(pdf_path: str) -> PdfReader:
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF not found: {pdf_path}")
    return PdfReader(pdf_path)

def get_fields_dict(reader: PdfReader):
    """
    Returns a dict keyed by field name, where each value is a dict-like object
    containing PDF keys (e.g., /FT, /V, /Opt, etc.).
    """
    try:
        return reader.get_fields()
    except Exception:
        # Fallback to AcroForm if needed
        root = reader.trailer.get("/Root")
        acro = root.get("/AcroForm") if root else None
        fields = {}
        if acro and "/Fields" in acro.get_object():
            for f in acro.get_object()["/Fields"]:
                obj = f.get_object()
                name = obj.get("/T")
                if name:
                    fields[name] = obj
        return fields

def find_field_obj(reader: PdfReader, field_name: str):
    """
    Locate the raw field object by name from the AcroForm /Fields array.
    """
    root = reader.trailer.get("/Root")
    acro = root.get("/AcroForm") if root else None
    if not acro:
        return None
    for f in acro.get_object().get("/Fields", []):
        obj = f.get_object()
        if obj.get("/T") == field_name:
            return obj
    return None

def get_value(fields_dict, field_name: str) -> str:
    """
    Get the current value (/V) for the given field name as a string ('' if missing).
    Works for both text (/Tx) and choice (/Ch) fields.
    """
    try:
        entry = fields_dict.get(field_name)
        if entry is None:
            return ""
        val = entry.get("/V")
        return "" if val is None else str(val)
    except Exception as e:
        print(f"[{ts()}] WARN: Could not read value for '{field_name}': {e}")
        return ""

def get_choice_options(reader: PdfReader, field_name: str):
    """
    Return the list of available options for a /Ch (choice) field, normalized to strings.
    In Adobe, /Opt can store either strings or [export, display] pairs.
    """
    options = []
    try:
        obj = find_field_obj(reader, field_name)
        if not obj:
            return options
        opt = obj.get("/Opt")
        if not opt:
            return options
        for item in opt:
            if isinstance(item, list) and len(item) >= 1:
                options.append(str(item[0]))
            else:
                options.append(str(item))
    except Exception as e:
        print(f"[{ts()}] WARN: Could not read options for '{field_name}': {e}")
    return options

def detect_image_in_button(reader: PdfReader, field_name: str) -> bool:
    """
    Heuristics to determine whether a button field (e.g., 'Survey Image') has an image:
    1) Check the field is /Btn.
    2) Inspect the normal appearance stream (/AP /N) and see if it references any XObject images.
    3) Check for an icon in /MK (/I).
    4) As a bonus, check for embedded file attachments in the document.
    """
    try:
        obj = find_field_obj(reader, field_name)
        if not obj:
            return False
        if obj.get("/FT") != "/Btn":
            return False
        mk = obj.get("/MK")
        if mk and mk.get("/I") is not None:
            return True
        ap = obj.get("/AP")
        if ap and "/N" in ap:
            apn = ap["/N"]
            try:
                apn_obj = apn.get_object()
            except Exception:
                apn_obj = apn
            if isinstance(apn_obj, DecodedStreamObject):
                resources = apn_obj.get("/Resources")
                if resources:
                    xo = resources.get("/XObject")
                    if isinstance(xo, IndirectObject):
                        xo = xo.get_object()
                    if xo and hasattr(xo, "items"):
                        for _name, xobj in xo.items():
                            try:
                                xobj_obj = xobj.get_object()
                                if xobj_obj.get("/Subtype") == "/Image":
                                    return True
                            except Exception:
                                continue
        root = reader.trailer.get("/Root")
        names = root.get("/Names") if root else None
        if names and names.get("/EmbeddedFiles"):
            pass
        return False
    except Exception as e:
        print(f"[{ts()}] WARN: Image detection error for '{field_name}': {e}")
        return False

def process_pdf(pdf_path: str):
    """
    Process a single PDF and return its extracted data as a dictionary.
    """
    print(f"[{ts()}] INFO: Processing {pdf_path}")
    try:
        reader = load_reader(pdf_path)
        fields = get_fields_dict(reader)

        # Read field values
        doc_num = get_value(fields, DOC_NUM_FIELD)
        corner_of_section = get_value(fields, CORNER_OF_SECTION_FIELD)
        township = get_value(fields, TOWNSHIP_FIELD)
        range_value = get_value(fields, RANGE_FIELD)
        county = get_value(fields, COUNTY_FIELD)

        # Read dropdown options
        township_options = get_choice_options(reader, TOWNSHIP_FIELD)
        range_options = get_choice_options(reader, RANGE_FIELD)
        county_options = get_choice_options(reader, COUNTY_FIELD)

        # Detect image presence
        image_present_bool = detect_image_in_button(reader, SURVEY_IMAGE_FIELD)
        image_present_flag = "Y" if image_present_bool else "N"

        # Display results for this PDF
        print(f"[{ts()}] INFO: Extraction results for {os.path.basename(pdf_path)}:")
        print(f"Doc Num: {doc_num}")
        print(f"Corner of Section: {corner_of_section}")
        print(f"Township (value): {township}")
        print(f"Range (value): {range_value}")
        print(f"County (value): {county}")
        print(f"Image present (bool): {image_present_bool}")
        print(f"Image present (Y/N): {image_present_flag}")
        print(f"Township options: {', '.join(township_options) if township_options else 'None'}")
        print(f"Range options: {', '.join(range_options) if range_options else 'None'}")
        print(f"County options: {', '.join(county_options) if county_options else 'None'}")
        print("-" * 50)

        return {
            "filename": os.path.basename(pdf_path),
            "doc_num": doc_num,
            "corner_of_section": corner_of_section,
            "township": township,
            "range": range_value,
            "county": county,
            "image_present_bool": image_present_bool,
            "image_present_flag": image_present_flag,
            "township_options": township_options,
            "range_options": range_options,
            "county_options": county_options
        }
    except Exception as e:
        print(f"[{ts()}] ERROR during extraction of {pdf_path}: {e}")
        traceback.print_exc()
        return None

def process_batch(folder_path: str, cycle_number: int):
    """
    Process all PDFs in the folder for a single cycle.
    """
    print(f"[{ts()}] INFO: Starting cycle {cycle_number}")
    
    # Check if folder exists
    if not os.path.isdir(folder_path):
        print(f"[{ts()}] ERROR: Directory not found: {folder_path}")
        return 0, 0

    # Find all PDFs in the folder
    pdf_files = glob.glob(os.path.join(folder_path, "*.pdf"))
    if not pdf_files:
        print(f"[{ts()}] ERROR: No PDFs found in {folder_path}")
        return 0, 0

    print(f"[{ts()}] INFO: Found {len(pdf_files)} PDFs in cycle {cycle_number}.")
    
    # Process each PDF
    results = []
    for pdf_path in pdf_files:
        result = process_pdf(pdf_path)
        if result:
            results.append(result)

    # Summary for this cycle
    print(f"[{ts()}] INFO: Cycle {cycle_number} processed {len(results)}/{len(pdf_files)} PDFs successfully.")
    if len(results) < len(pdf_files):
        print(f"[{ts()}] WARN: Cycle {cycle_number} failed to process {len(pdf_files) - len(results)} PDFs.")
    
    return len(pdf_files), len(results)

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Extract form fields from all PDFs in a hardcoded folder with recurring execution")
    parser.add_argument("--duration", type=int, default=600, help="Total duration for recurring runs in seconds (default: 600)")
    parser.add_argument("--interval", type=int, default=5, help="Interval between runs in seconds (default: 30)")
    args = parser.parse_args()

    duration = args.duration
    interval = args.interval

    print(f"[{ts()}] INFO: Starting recurring PDF field extraction for {duration} seconds, every {interval} seconds in folder {PDF_FOLDER}.")

    start_time = time.time()
    cycle_count = 0
    total_processed = 0
    total_success = 0

    while time.time() - start_time < duration:
        cycle_count += 1
        pdf_count, success_count = process_batch(PDF_FOLDER, cycle_count)
        total_processed += pdf_count
        total_success += success_count
        
        # Wait for the next cycle, unless this was the last possible cycle
        if time.time() - start_time + interval <= duration:
            print(f"[{ts()}] INFO: Waiting {interval} seconds before next cycle.")
            time.sleep(interval)
        else:
            break

    # Final summary
    print(f"[{ts()}] INFO: Completed {cycle_count} cycles in {int(time.time() - start_time)} seconds.")
    print(f"[{ts()}] INFO: Total PDFs processed: {total_processed}, successfully extracted: {total_success}")
    if total_processed > total_success:
        print(f"[{ts()}] WARN: {total_processed - total_success} PDFs failed to process across all cycles.")

if __name__ == "__main__":
    main()