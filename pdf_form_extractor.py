#!/usr/bin/env python3
"""
PDF form reader for Adobe-named fields.
- Extracts values from text and choice fields
- Detects whether a "Survey Image" button field actually contains an image/icon
- Emits both a boolean and "Y/N" image-present flag
"""

import sys, os, datetime, traceback

def ts() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

try:
    from PyPDF2 import PdfReader
    from PyPDF2.generic import IndirectObject, DecodedStreamObject
except Exception as e:
    print(f"[{ts()}] ERROR: PyPDF2 is required. Install with: pip install PyPDF2")
    print(f"[{ts()}] ERROR detail: {e}")
    sys.exit(1)

# --- CONFIG: set to your PDF path ---
PDF_PATH = r"C:/Users/sk23dg/Desktop/Content_extraction/pdftest.pdf"  # e.g., r"C:\work\Untitled 2.pdf"

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
            # No such field; no image present.
            return False

        if obj.get("/FT") != "/Btn":
            # Not a button; treat as no image
            return False

        # Check for icon in /MK
        mk = obj.get("/MK")
        if mk and mk.get("/I") is not None:
            return True  # An icon stream is present

        # Inspect appearance stream resources for images
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
                    # Look for XObject image resources
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
                # If no image XObjects, appearance may be vector-only (no image)
            # If appearance is a name (static), treat as no image
        # Check for document-level embedded files as a fallback signal
        root = reader.trailer.get("/Root")
        names = root.get("/Names") if root else None
        if names and names.get("/EmbeddedFiles"):
            # If there are any embedded files, caller can decide how to interpret.
            # We don't automatically mark this True unless you specifically want that.
            pass

        return False
    except Exception as e:
        print(f"[{ts()}] WARN: Image detection error for '{field_name}': {e}")
        return False

def main():
    print(f"[{ts()}] INFO: Starting PDF field extraction.")
    try:
        reader = load_reader(PDF_PATH)
    except Exception as e:
        print(f"[{ts()}] ERROR: {e}")
        sys.exit(2)

    try:
        fields = get_fields_dict(reader)

        # --- Read field values ---
        doc_num                = get_value(fields, DOC_NUM_FIELD)
        corner_of_section      = get_value(fields, CORNER_OF_SECTION_FIELD)
        township               = get_value(fields, TOWNSHIP_FIELD)
        range_value            = get_value(fields, RANGE_FIELD)   # avoid Python keyword
        county                 = get_value(fields, COUNTY_FIELD)

        # --- (Optional) Read dropdown options, if you need them ---
        township_options = get_choice_options(reader, TOWNSHIP_FIELD)
        range_options    = get_choice_options(reader, RANGE_FIELD)
        county_options   = get_choice_options(reader, COUNTY_FIELD)

        # --- Detect image presence in the button field ---
        image_present_bool = detect_image_in_button(reader, SURVEY_IMAGE_FIELD)
        image_present_flag = "Y" if image_present_bool else "N"

        # --- Results ---
        print(f"[{ts()}] INFO: Extraction complete.")
        print(f"Doc Num: {doc_num}")
        print(f"Corner of Section: {corner_of_section}")
        print(f"Township (value): {township}")
        print(f"Range (value): {range_value}")
        print(f"County (value): {county}")
        print(f"Image present (bool): {image_present_bool}")
        print(f"Image present (Y/N): {image_present_flag}")

        # If you want to use these programmatically:
        results = {
            "doc_num": doc_num,
            "corner_of_section": corner_of_section,
            "township": township,
            "range": range_value,
            "county": county,
            "image_present_bool": image_present_bool,
            "image_present_flag": image_present_flag,
            "choices": {
                "township": township_options,
                "range": range_options,
                "county": county_options,
            },
        }

        # Example: return nonzero exit code if a critical field is missing
        if not doc_num:
            print(f"[{ts()}] WARN: '{DOC_NUM_FIELD}' is empty.")
        # You can write `results` to JSON here if needed.

    except Exception as e:
        print(f"[{ts()}] ERROR during extraction: {e}")
        traceback.print_exc()
        sys.exit(3)

if __name__ == "__main__":
    main()
