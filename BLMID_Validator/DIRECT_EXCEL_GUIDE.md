# Direct Excel Processing - Getting Started Guide

## For Users with Extracted BLMID Data in Excel

If you already have BLMID and coordinates in Excel sheets (no PDF extraction needed), this guide is for you!

---

## 30-Second Quick Start

```bash
cd C:\Users\sk23dg\Desktop\Labins_Workflow\BLMID_Validator

# Install
pip install -r requirements.txt

# Run (with mock database - no PostgreSQL needed)
python -m blmid_validator.cli process-excel ^
  your_extracted.xlsx ^
  your_reference.xlsx ^
  --output ./reports ^
  --mock-db

# Check results in ./reports/
```

---

## What You Need

### Input Files

1. **Extracted Data Excel** (your data with BLMID)
   ```
   Column A: BLMID         (or any name containing "blmid")
   Column B: Latitude      (or any name containing "lat")
   Column C: Longitude     (or any name containing "lon")
   
   Example row:
   BLM001  40.7128  -74.0060
   BLM002  51.5074  -0.1278
   ```

2. **Reference Data Excel** (correct BLMID database)
   ```
   Column A: BLMID         (reference correct values)
   Column B: Latitude
   Column C: Longitude
   
   Example:
   BLM001  40.7128  -74.0060
   BLM999  51.5074  -0.1278
   ```

### Prerequisites

- Python 3.8+
- Dependencies: `pip install -r requirements.txt`
- That's it! No PostgreSQL, Tesseract, or external apps needed!

---

## How It Works

```
Your Extracted Excel
         ↓
[Load Data]
         ↓
For each row:
  ├─ Check Reference Excel
  ├─ Query Database (or mock data)
  └─ Validate/Correct BLMID
         ↓
Generate Reports:
  ├─ Updated Excel with corrections
  ├─ Corrections log
  └─ Failed entries (if any)
```

---

## Usage Examples

### Example 1: Basic Processing with Mock Database

```bash
python -m blmid_validator.cli process-excel ^
  extracted_blmid.xlsx ^
  reference_blmid.xlsx ^
  --output ./reports ^
  --mock-db
```

**Good for:** Testing, demo, proof-of-concept

### Example 2: With Real PostgreSQL Database

```bash
python -m blmid_validator.cli process-excel ^
  extracted_blmid.xlsx ^
  reference_blmid.xlsx ^
  --output ./reports ^
  --config config.yaml
```

**Requires:** PostgreSQL database configured in `config.yaml`

### Example 3: Custom Tolerance (Loose Matching)

```bash
python -m blmid_validator.cli process-excel ^
  extracted_blmid.xlsx ^
  reference_blmid.xlsx ^
  --output ./reports ^
  --tolerance 0.001 ^
  --mock-db
```

**Use:** If coordinates have slight variations (±0.001 degrees ≈ 111 meters)

### Example 4: Python Script

```python
from blmid_validator.config import Config
from blmid_validator.excel_processor import DirectExcelProcessor

# Setup
config = Config()  # Uses defaults
processor = DirectExcelProcessor(config, use_mock_db=True)

# Process
result = processor.process_excel_batch(
    extracted_excel="my_extracted.xlsx",
    reference_excel="my_reference.xlsx",
    output_dir="./my_output"
)

# Results
print(f"Valid:     {len(result['valid_entries'])}")
print(f"Corrected: {len(result['corrected_entries'])}")
print(f"Failed:    {len(result['failed_entries'])}")

# Output files
for name, path in result['output_files'].items():
    print(f"{name}: {path}")
```

---

## Understanding Results

### Output Files

1. **Updated_BLMID_[timestamp].xlsx**
   ```
   BLMID          Latitude    Longitude    Correction_Applied
   BLM001         40.7128     -74.0060     FALSE
   BLM999         51.5074     -0.1278      TRUE ← Corrected from BLM002
   ```

2. **Corrections_Log_[timestamp].xlsx**
   ```
   Original_BLMID  Corrected_BLMID  Latitude    Longitude
   BLM002          BLM999           51.5074     -0.1278
   ```

3. **Failed_Entries_[timestamp].xlsx** (if errors)
   ```
   Row  BLMID    Latitude    Longitude   Error
   2    BLM003   99.0        -74.0060    Latitude out of range [-90, 90]
   ```

### Logs

- **process.log** - All processing activities
- **error.log** - Errors and warnings only

---

## Validation Rules

The system validates each entry:

### ✅ VALID
- BLMID exactly matches reference Excel AND coordinates match
- OR BLMID exactly matches database AND coordinates match

### ⚠️ CORRECTED
- Coordinates exist in database but with different BLMID
- Correction applied from database

### ❌ FAILED
- Latitude/longitude out of valid ranges
- No matching entry in reference or database
- Invalid coordinate format

---

## Configuration (Optional)

If you want to customize behavior, create `config.yaml`:

```yaml
validation:
  # Coordinate matching tolerance (degrees)
  # 0.0001 = ±11.1 meters (tight)
  # 0.001  = ±111 meters (loose)
  coordinate_tolerance: 0.0001

database:
  # When NOT using --mock-db, configure database
  connection_uri: "postgresql://user:password@localhost:5432/db"
  table_name: "blmid_reference"

output:
  directory: "./output"

logging:
  level: "INFO"
```

---

## Troubleshooting

### Issue: "Column BLMID not found"

**Solution:** Ensure Excel has a column named BLMID (or BLMID*, BLM_ID, etc.)
The system auto-detects column names.

### Issue: "Latitude out of range"

**Solution:** Check Excel data - latitude must be between -90 and 90

### Issue: "No matching BLMID found"

**Possible causes:**
1. Coordinates don't match reference or database
2. Database not configured (use `--mock-db` for testing)
3. Tolerance too strict - try `--tolerance 0.001`

### Issue: Too many "Failed" entries

**Solutions:**
1. Verify Excel coordinate format (should be decimal numbers)
2. Increase tolerance: `--tolerance 0.001`
3. Check reference data has matching coordinates
4. Use `--mock-db` to test without database

---

## Performance

Processing speed with mock database:
- 1,000 entries: ~10 seconds
- 10,000 entries: ~100 seconds
- 100,000 entries: ~1,000 seconds (16 minutes)

**Tips to speed up:**
- Use smaller batches (< 10,000 entries)
- Run multiple batches in parallel
- Use PostgreSQL database (faster than mock)

---

## Database Setup (Optional)

If you want to use real PostgreSQL instead of `--mock-db`:

### 1. Create Database Table

```sql
CREATE TABLE blmid_reference (
    id SERIAL PRIMARY KEY,
    blmid VARCHAR(50) NOT NULL UNIQUE,
    latitude DECIMAL(10, 6) NOT NULL,
    longitude DECIMAL(10, 6) NOT NULL
);

CREATE INDEX idx_blmid ON blmid_reference(blmid);
CREATE INDEX idx_coordinates ON blmid_reference(latitude, longitude);
```

### 2. Load Data

```sql
INSERT INTO blmid_reference (blmid, latitude, longitude) VALUES
    ('BLM001', 40.7128, -74.0060),
    ('BLM002', 51.5074, -0.1278);
```

### 3. Configure config.yaml

```yaml
database:
  connection_uri: "postgresql://user:password@localhost:5432/blmid_db"
  table_name: "blmid_reference"
```

### 4. Run Without --mock-db

```bash
python -m blmid_validator.cli process-excel ^
  extracted.xlsx ^
  reference.xlsx ^
  --output ./reports
```

---

## Workflow Examples

### Workflow 1: Validate Extracted Data (No Correction)

```bash
# Just verify extracted BLMIDs are correct
python -m blmid_validator.cli process-excel ^
  extracted.xlsx ^
  reference.xlsx ^
  --output ./reports ^
  --mock-db
```

### Workflow 2: Find & Fix Incorrect BLMIDs

```bash
# Validate and auto-correct using database
python -m blmid_validator.cli process-excel ^
  extracted.xlsx ^
  reference.xlsx ^
  --output ./reports

# Updated_BLMID_*.xlsx will have corrections applied
```

### Workflow 3: Audit Trail

```bash
# Generate audit log of all corrections
python -m blmid_validator.cli process-excel ^
  extracted.xlsx ^
  reference.xlsx ^
  --output ./audit_results

# Corrections_Log_*.xlsx shows what changed
```

---

## Python API

### Simple Usage

```python
from blmid_validator.excel_processor import DirectExcelProcessor
from blmid_validator.config import Config

processor = DirectExcelProcessor(Config(), use_mock_db=True)

result = processor.process_excel_batch(
    extracted_excel="data.xlsx",
    reference_excel="ref.xlsx",
    output_dir="./output"
)

print(f"Results: {result['total_processed']} rows processed")
```

### Advanced Usage

```python
# Access individual results
for validation in result['results']:
    if validation['status'] == 'corrected':
        print(f"Row {validation['row']}: {validation['original_blmid']} → {validation['corrected_blmid']}")
    elif validation['status'] == 'failed':
        print(f"Row {validation['row']}: ERROR - {validation['error']}")
```

---

## FAQ

**Q: Do I need PostgreSQL?**
A: No! Use `--mock-db` flag for testing without any database.

**Q: Can I use my own regex patterns for column detection?**
A: Yes, column names are auto-detected case-insensitively. If auto-detection fails, edit Excel to use standard names (BLMID, Latitude, Longitude).

**Q: How accurate is the coordinate matching?**
A: Default is ±0.0001 degrees (≈11 meters). Use `--tolerance` to adjust.

**Q: Can I process huge Excel files (1M+ rows)?**
A: Yes, but split into chunks (100k rows each) for better performance.

**Q: What if coordinate formats are different (DMS vs decimal)?**
A: Convert to decimal format before processing (use Excel formulas).

**Q: Can I schedule this to run daily?**
A: Yes! Use Windows Task Scheduler or cron on Linux/Mac.

---

## Quick Reference

```bash
# Help
python -m blmid_validator.cli process-excel --help

# Generate config
python -m blmid_validator.cli init-config --output config.yaml

# Process with defaults
python -m blmid_validator.cli process-excel data.xlsx ref.xlsx --mock-db

# Process with custom tolerance
python -m blmid_validator.cli process-excel data.xlsx ref.xlsx --tolerance 0.001 --mock-db

# Process with database
python -m blmid_validator.cli process-excel data.xlsx ref.xlsx --config config.yaml
```

---

## Next Steps

1. ✅ Install: `pip install -r requirements.txt`
2. ✅ Prepare Excel files with BLMID, Latitude, Longitude
3. ✅ Run: `python -m blmid_validator.cli process-excel extracted.xlsx reference.xlsx --mock-db`
4. ✅ Check results in `./reports/`
5. ✅ Configure database when ready (optional)
6. ✅ Set up automated processing (optional)

---

**Ready to validate BLMIDs from Excel!** 🚀

For more details, see: README.md, QUICKSTART.md, INTEGRATION.md
