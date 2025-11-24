# BLMID Validator - Quick Start Guide

## 5-Minute Setup

### 1. Install Dependencies

```bash
cd c:\Users\sk23dg\Desktop\Labins_Workflow\BLMID_Validator

# Create virtual environment (optional but recommended)
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Generate Configuration

```bash
python -m blmid_validator.cli init-config --output config.yaml
```

### 3. Edit Configuration

Open `config.yaml` and update:

```yaml
database:
  connection_uri: "postgresql://your_username:your_password@pgAdmin_host:5432/your_database"
  table_name: "your_table_name"
```

### 4. Prepare Your Data

- Place PDF files in a directory (e.g., `./pdfs/`)
- Ensure Excel reference file has columns: BLMID, Latitude, Longitude
- Ensure database table has matching columns

### 5. Run Processing

**Option A: Single PDF**
```bash
python -m blmid_validator.cli process-single ./pdfs/survey_001.pdf \
  --excel reference.xlsx --output ./reports
```

**Option B: Batch of PDFs**
```bash
python -m blmid_validator.cli process-batch ./pdfs \
  --excel reference.xlsx --output ./reports
```

**Option C: Test Run with Mock Database (no DB needed)**
```bash
python -m blmid_validator.cli process-batch ./pdfs \
  --excel reference.xlsx --output ./reports --mock-db
```

### 6. Check Results

Output files will be in `./reports/`:
- `Updated_BLMID_[timestamp].xlsx` - Updated BLMID file
- `Corrections_Log_[timestamp].xlsx` - List of corrections made
- `logs/process.log` - Processing log
- `logs/error.log` - Errors and warnings

---

## Directory Structure

```
BLMID_Validator/
├── blmid_validator/              # Main package
│   ├── __init__.py
│   ├── config.py                 # Configuration management
│   ├── logger_setup.py           # Logging configuration
│   ├── pdf_extractor.py          # PDF extraction module
│   ├── excel_handler.py          # Excel operations
│   ├── database.py               # Database connectivity
│   ├── validator.py              # Validation logic
│   ├── processor.py              # Main processor
│   └── cli.py                    # Command-line interface
├── tests/
│   └── test_validator.py         # Unit tests
├── sample_data/                  # Sample files
│   ├── reference_data.xlsx       # Sample Excel reference
│   └── sample_survey.txt         # Sample PDF text
├── config.yaml                   # Configuration file (customize this)
├── requirements.txt              # Python dependencies
├── setup.py                      # Package installation script
├── __main__.py                   # Entry point
├── sample_usage.py               # Usage examples
└── README.md                     # Full documentation
```

---

## Database Connection Examples

### Local PostgreSQL (pgAdmin-3)

```yaml
database:
  connection_uri: "postgresql://postgres:password@localhost:5432/postgres"
  table_name: "blmid_reference"
```

### Remote PostgreSQL Server

```yaml
database:
  connection_uri: "postgresql://user:password@192.168.1.100:5432/blmid_db"
  table_name: "blmid_reference"
```

### With Special Characters in Password

Special characters must be URL-encoded:
- `@` → `%40`
- `#` → `%23`
- `:` → `%3A`

```yaml
database:
  connection_uri: "postgresql://user:pass%40word@host:5432/db"
```

---

## Common Issues & Solutions

### Issue: "No module named 'pdfplumber'"

**Solution:**
```bash
pip install pdfplumber PyPDF2 Pillow
```

### Issue: "psycopg2.OperationalError: could not connect to server"

**Solution:**
1. Verify PostgreSQL is running
2. Check connection string format
3. Test connection manually:
   ```bash
   psql -U username -d database_name
   ```

### Issue: "PDF contains no extractable text"

**Solution:**
1. Check if PDF is scanned (image-based)
2. Enable OCR and install Tesseract:
   ```bash
   pip install pytesseract pillow pymupdf
   # Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki
   # Linux: sudo apt-get install tesseract-ocr
   ```

### Issue: "No matching BLMID found in database"

**Solution:**
1. Verify coordinates are being extracted correctly
2. Check database has records for those coordinates
3. Increase `coordinate_tolerance` in `config.yaml`:
   ```yaml
   validation:
     coordinate_tolerance: 0.001  # Increase from 0.0001
   ```

---

## Configuration Customization

### Adjust PDF Extraction Patterns

If PDFs have different formats, customize regex patterns:

```yaml
pdf:
  regex_patterns:
    # Match "BLM-001", "BLMID: 001", "BLM 001"
    blmid: "BLM[ID]*[\\s-]*([A-Z0-9]+)"
    
    # Match "Lat: 40.7128", "Latitude=40.7128"
    latitude: "(lat[a-z]*|latitude)[\\s:=]*(-?\\d+\\.?\\d*)"
    
    # Match "Lon: -74.0060", "Longitude=-74.0060"
    longitude: "(lon[a-z]*|longitude)[\\s:=]*(-?\\d+\\.?\\d*)"
```

### Change Coordinate Tolerance

For tighter matching (±0.0001 degrees ≈ 11 meters):
```yaml
validation:
  coordinate_tolerance: 0.0001
```

For looser matching (±0.001 degrees ≈ 111 meters):
```yaml
validation:
  coordinate_tolerance: 0.001
```

### Change Excel Sheet Name

If your Excel file has a specific sheet name:
```yaml
excel:
  sheet_name: "Survey Data"  # or null for first sheet
```

---

## Python Scripting

### Example: Process PDFs Programmatically

```python
from blmid_validator.config import Config
from blmid_validator.processor import BLMIDProcessor
from blmid_validator.logger_setup import setup_logging

# Setup
setup_logging()
config = Config("config.yaml")
processor = BLMIDProcessor(config)

# Process
result = processor.process_batch_pdfs(
    pdf_dir="./my_surveys",
    excel_path="./reference_data.xlsx",
    output_dir="./my_output"
)

# Results
print(f"Processed: {result['total_processed']}")
print(f"Valid: {result['valid_entries']}")
print(f"Corrected: {result['corrected_entries']}")
print(f"Failed: {result['failed_extractions']}")

for output_name, output_path in result.get('output_files', {}).items():
    print(f"{output_name}: {output_path}")
```

### Example: Extract from Single PDF

```python
from blmid_validator.pdf_extractor import PDFExtractor

extractor = PDFExtractor()
result = extractor.extract_from_pdf("survey.pdf")

print(f"BLMID: {result['blmid']}")
print(f"Latitude: {result['latitude']}")
print(f"Longitude: {result['longitude']}")
if result['errors']:
    print(f"Errors: {result['errors']}")
```

### Example: Query Database

```python
from blmid_validator.database import DatabaseConnector

db = DatabaseConnector("postgresql://user:pass@host:5432/db")

# Find by coordinates
record = db.find_by_coordinates(40.7128, -74.0060, tolerance=0.0001)
if record:
    print(f"Found: {record['blmid']}")
else:
    print("No match found")

# Find by BLMID
record = db.find_by_blmid("BLM001")
```

---

## Running Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_validator.py -v

# Run with coverage
python -m pytest tests/ --cov=blmid_validator --cov-report=html
```

---

## Logging

### View Logs

```bash
# Process log (all messages)
type output\logs\process.log

# Error log (errors only)
type output\logs\error.log
```

### Change Log Level

In `config.yaml`:
```yaml
logging:
  level: "DEBUG"  # or INFO, WARNING, ERROR, CRITICAL
```

---

## Performance Tips

1. **Batch Processing**: Process 10+ PDFs together (faster than one-by-one)
2. **Database**: Add indexes to coordinates and BLMID columns:
   ```sql
   CREATE INDEX idx_coordinates ON blmid_reference(latitude, longitude);
   CREATE INDEX idx_blmid ON blmid_reference(blmid);
   ```
3. **OCR**: Only enable when needed (use `ocr_fallback: true`)
4. **Excel**: Keep reference sheets under 100,000 rows

---

## Next Steps

1. Customize `config.yaml` with your database and PDF details
2. Prepare sample PDFs and Excel reference file
3. Run: `python -m blmid_validator.cli process-batch ./pdfs --excel reference.xlsx --mock-db`
4. Review output in `./output/` directory
5. Connect to real database when ready
6. Schedule batch processing as needed

---

## Support Resources

- Full documentation: `README.md`
- Example usage: `sample_usage.py`
- Configuration template: `config.yaml`
- Unit tests: `tests/test_validator.py`
- Error logs: `output/logs/error.log`

---

**Ready to validate BLMIDs!** 🚀
