# main.py
import pandas as pd
from typing import List, Dict, Any
import validators as V
import config
from utils import make_excel_row_number, safe_strip
import argparse
import os


def validate_row(row: pd.Series, row_idx: int) -> List[Dict[str, Any]]:
    """
    Validate a single DataFrame row.
    Returns list of error dicts for that row (empty list if valid).
    Each error dict contains: row_idx, excel_row, column, value, expected, error_type
    """
    errors = []
    excel_row = make_excel_row_number(row_idx)

    def add_error(col, val, expected, err_type):
        errors.append({
            "row_index": row_idx,
            "excel_row": excel_row,
            "column": col,
            "invalid_value": val,
            "expected": expected,
            "error_type": err_type
        })

    # Example expected column names. Adjust to actual column names in your Excel.
    # We'll use typical names. If column missing, report as missing for entire row.
    # The script tolerates missing columns by reporting an error row-level.

    # Helper to pull column safely
    def g(c):
        return row.get(c, None)

    # 1. Corner of Section
    col = "Corner of Section"
    val = g(col)
    ok, cleaned, err = V.validate_categorical(val, config.CORNER_OF_SECTION, case_insensitive=True)
    if not ok:
        add_error(col, val, f"one of {config.CORNER_OF_SECTION}", err or "invalid")

    # 2. Sections
    col = "Section"
    val = g(col)
    ok, cleaned, err = V.validate_integer_range(val, config.SECTION_MIN, config.SECTION_MAX)
    if not ok:
        add_error(col, val, f"integer [{config.SECTION_MIN}-{config.SECTION_MAX}]", err or "invalid")

    # 3. Township
    col = "Township"
    val = g(col)
    ok, cleaned, err = V.validate_integer_range(val, config.TOWNSHIP_MIN, config.TOWNSHIP_MAX)
    if not ok:
        add_error(col, val, f"integer [{config.TOWNSHIP_MIN}-{config.TOWNSHIP_MAX}]", err or "invalid")

    # 4. Township Direction
    col = "Township Direction"
    val = g(col)
    ok, cleaned, err = V.validate_categorical(val, config.TOWNSHIP_DIR, case_insensitive=True)
    if not ok:
        add_error(col, val, f"one of {config.TOWNSHIP_DIR}", err or "invalid")

    # 5. Range
    col = "Range"
    val = g(col)
    ok, cleaned, err = V.validate_integer_range(val, config.RANGE_MIN, config.RANGE_MAX)
    if not ok:
        add_error(col, val, f"integer [{config.RANGE_MIN}-{config.RANGE_MAX}]", err or "invalid")

    # 6. Range Direction
    col = "Range Direction"
    val = g(col)
    ok, cleaned, err = V.validate_categorical(val, config.RANGE_DIR, case_insensitive=True)
    if not ok:
        add_error(col, val, f"one of {config.RANGE_DIR}", err or "invalid")

    # 7. County
    col = "County"
    val = g(col)
    ok, cleaned, err = V.validate_county(val)
    if not ok:
        add_error(col, val, "Florida county name", err or "invalid")

    # 8. Latitude
    col = "Latitude"
    val = g(col)
    ok, cleaned, err = V.validate_lat_lon(val, config.LAT_MIN, config.LAT_MAX)
    if not ok:
        add_error(col, val, f"float [{config.LAT_MIN}-{config.LAT_MAX}]", err or "invalid")

    # 9. Longitude
    col = "Longitude"
    val = g(col)
    ok, cleaned, err = V.validate_lat_lon(val, config.LON_MIN, config.LON_MAX)
    if not ok:
        add_error(col, val, f"float [{config.LON_MIN}-{config.LON_MAX}]", err or "invalid")

    # 10. Easting (optional)
    col = "Easting"
    val = g(col)
    ok, cleaned, err = V.validate_optional_coordinate(val, config.EASTING_MIN, config.EASTING_MAX)
    if not ok:
        add_error(col, val, f"float (optional) [{config.EASTING_MIN}-{config.EASTING_MAX}]", err or "invalid")

    # 11. Northing (optional)
    col = "Northing"
    val = g(col)
    ok, cleaned, err = V.validate_optional_coordinate(val, config.NORTHING_MIN, config.NORTHING_MAX)
    if not ok:
        add_error(col, val, f"float (optional) [{config.NORTHING_MIN}-{config.NORTHING_MAX}]", err or "invalid")

    # 12. Zone
    col = "Zone"
    val = g(col)
    ok, cleaned, err = V.validate_zone(val)
    if not ok:
        add_error(col, val, f"one of {config.ZONE_VALUES}", err or "invalid")

    # 13. Horizontal Datum
    col = "Horizontal Datum"
    val = g(col)
    ok, cleaned, err = V.validate_horizontal_datum(val)
    if not ok:
        add_error(col, val, f"one of {config.HORIZONTAL_DATUM}", err or "invalid")

    # 14. Source
    col = "Source"
    val = g(col)
    ok, cleaned, err = V.validate_string_field(val)
    if not ok:
        add_error(col, val, f"non-empty string up to {config.STRING_MAX_LEN} chars", err or "invalid")

    # 15. Determined By
    col = "Determined By"
    val = g(col)
    ok, cleaned, err = V.validate_string_field(val)
    if not ok:
        add_error(col, val, f"non-empty string up to {config.STRING_MAX_LEN} chars", err or "invalid")

    # 16. Certified Date (Month, Day, Year)
    col_m, col_d, col_y = "Certified Month", "Certified Day", "Certified Year"
    ok, dt, err = V.validate_date_components(g(col_m), g(col_d), g(col_y))
    if not ok:
        add_error("Certified Date", f"{g(col_m)}-{g(col_d)}-{g(col_y)}", "valid date", err or "invalid")

    # 17. File Date (Month, Day, Year)
    col_m, col_d, col_y = "File Month", "File Day", "File Year"
    ok, dt, err = V.validate_date_components(g(col_m), g(col_d), g(col_y))
    if not ok:
        add_error("File Date", f"{g(col_m)}-{g(col_d)}-{g(col_y)}", "valid date", err or "invalid")

    # 18. Surveyor Information: we will validate a few common subfields if present (Surveyor Name, Company)
    col = "Surveyor Name"
    val = g(col)
    if val is not None:
        ok, cleaned, err = V.validate_string_field(val, required=False)
        if not ok:
            add_error(col, val, "string", err or "invalid")

    col = "Surveyor Company"
    val = g(col)
    if val is not None:
        ok, cleaned, err = V.validate_string_field(val, required=False)
        if not ok:
            add_error(col, val, "string", err or "invalid")

    return errors


def validate_dataframe(df: pd.DataFrame) -> Dict[str, Any]:
    all_errors = []
    valid_rows_indices = []
    invalid_rows_indices = []

    for i, row in df.iterrows():
        errs = validate_row(row, i)
        if errs:
            all_errors.extend(errs)
            invalid_rows_indices.append(i)
        else:
            valid_rows_indices.append(i)

    # Build DataFrames for output
    report_df = pd.DataFrame(all_errors)
    return {
        "report_df": report_df,
        "valid_idx": valid_rows_indices,
        "invalid_idx": invalid_rows_indices
    }


def write_results(original_df: pd.DataFrame, results: Dict[str, Any], out_path: str):
    report_df = results["report_df"]
    valid_idx = results["valid_idx"]
    invalid_idx = results["invalid_idx"]

    # Summary
    total_rows = len(original_df)
    total_valid = len(valid_idx)
    total_invalid = len(invalid_idx)
    error_count_by_column = report_df['column'].value_counts().to_dict() if not report_df.empty else {}

    summary = {
        "total_rows": total_rows,
        "valid_rows": total_valid,
        "invalid_rows": total_invalid,
        "errors_by_column": error_count_by_column
    }

    # Flagged original
    flagged = original_df.copy()
    flagged["has_errors"] = False
    flagged["validation_errors"] = ""
    if not report_df.empty:
        grouped = report_df.groupby("row_index")['error_type'].apply(lambda errs: "; ".join(errs)).to_dict()
        for idx, err_str in grouped.items():
            if idx in flagged.index:
                flagged.at[idx, "has_errors"] = True
                flagged.at[idx, "validation_errors"] = err_str

    # Valid and invalid slices
    valid_rows = original_df.loc[valid_idx].copy() if valid_idx else original_df.iloc[0:0].copy()
    invalid_rows = original_df.loc[invalid_idx].copy() if invalid_idx else original_df.iloc[0:0].copy()

    # Write to Excel with multiple sheets
    with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
        summary_df = pd.DataFrame([summary])
        summary_df.to_excel(writer, sheet_name="summary", index=False)
        report_df.to_excel(writer, sheet_name="validation_report", index=False)
        valid_rows.to_excel(writer, sheet_name="valid_rows", index=False)
        invalid_rows.to_excel(writer, sheet_name="invalid_rows", index=False)
        flagged.to_excel(writer, sheet_name="flagged_original", index=False)

    print(f"Wrote results to {out_path}")


def main():
    parser = argparse.ArgumentParser(description="Validate CCR form Excel file.")
    parser.add_argument("input_excel", help="Path to input Excel file")
    parser.add_argument("--sheet", default=None, help="Sheet name (default: first sheet)")
    parser.add_argument("--output", default="validation_results.xlsx", help="Path to output Excel report")
    args = parser.parse_args()

    if not os.path.exists(args.input_excel):
        raise FileNotFoundError(f"Input file not found: {args.input_excel}")

    df = pd.read_excel(args.input_excel, sheet_name=args.sheet, engine="openpyxl", dtype=object)
    # Trim whitespace in all string columns
    df = df.applymap(lambda v: safe_strip(v) if isinstance(v, str) else v)

    results = validate_dataframe(df)
    write_results(df, results, args.output)


if __name__ == "__main__":
    main()
