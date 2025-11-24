# BLMID Validator - README

## Overview

**BLMID Validator** is a Python application that automates the validation of BLMID (Bureau of Land Management ID) entries extracted from PDF survey forms. It compares extracted data against an Excel reference sheet and database records, generates correction reports, and produces updated files with validated BLMIDs.

### Key Features

- **PDF Processing**: Extract BLMID and coordinates from text-based and scanned PDFs
- **Multi-format Support**: Handle both fillable forms and scanned images with OCR
- **Direct Excel Processing**: Validate BLMID data directly from Excel (no PDF needed!) ⭐ **NEW**
- **Batch Processing**: Process multiple PDFs or Excel files simultaneously
- **Excel Validation**: Compare extracted data against reference sheets
- **Database Verification**: Query PostgreSQL for correct BLMID based on coordinates
- **Comprehensive Reports**: Generate updated Excel files and detailed correction logs
- **Configurable**: Customizable regex patterns, tolerances, and database connections
- **Logging**: Detailed process and error logs for troubleshooting
- **No External Apps Required**: Works with just Python (optional Tesseract for scanned PDFs)

## Installation

### Prerequisites

- Python 3.8 or higher
- PostgreSQL database (for production use)
- Tesseract OCR (optional, for scanned PDFs)

### Step 1: Install Python Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Install Tesseract OCR (Optional but Recommended)

**Windows:**
- Download installer from: https://github.com/UB-Mannheim/tesseract/wiki
- Install to default location or update `config.yaml` with the path

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
```

**macOS:**
```bash
brew install tesseract
```

### Step 3: Configure Application

1. Generate a configuration file:
```bash
python -m blmid_validator.cli init-config --output config.yaml
```

2. Edit `config.yaml` with your settings:
   - Database connection URI
   - Database table and column names
   - PDF extraction patterns
   - Coordinate tolerance
   - Output directories

## Configuration

### Database Connection

Edit the `database.connection_uri` in `config.yaml`:

```yaml
database:
  connection_uri: "postgresql://username:password@hostname:port/database_name"
  table_name: "blmid_reference"
  columns:
    blmid: "blmid"
    latitude: "latitude"
    longitude: "longitude"
```

**Connection URI Format:**
```
postgresql://[user[:password]@][host][:port][/database]
```

**Examples:**
- Local: `postgresql://user:password@localhost:5432/blmid_db`
- Remote: `postgresql://user@192.168.1.100:5432/survey_db`
- With special chars: `postgresql://user:pass%40word@host:5432/db` (@ encoded as %40)

### Excel Reference Sheet

Ensure your Excel file has:
- Headers in Row 1
- Column A: BLMID
- Column B: Latitude
- Column C: Longitude

You can customize column positions in `config.yaml`:
```yaml
excel:
  columns:
    blmid: "A"
    latitude: "B"
    longitude: "C"
```

### PDF Extraction Patterns

Customize regex patterns based on your PDF format in `config.yaml`:

```yaml
pdf:
  regex_patterns:
    blmid: "BLM[\\s-]*(?:ID)?[\\s-]*([A-Z0-9]+)"
    latitude: "(lat[a-z]*|latitude)[\\s:]*(-?\\d+\\.?\\d*)"
    longitude: "(lon[a-z]*|longitude)[\\s:]*(-?\\d+\\.?\\d*)"
```

### Coordinate Tolerance

Set the acceptable coordinate matching tolerance:

```yaml
validation:
  # 0.0001 degrees ≈ 11.1 meters at equator
  coordinate_tolerance: 0.0001
```

## Usage

### Option 1: Command-Line Interface (CLI)

#### Process a Single PDF

```bash
python -m blmid_validator.cli process-single survey_form.pdf \
  --excel reference_data.xlsx \
  --output ./reports \
  --config config.yaml
```

#### Process Batch of PDFs

```bash
python -m blmid_validator.cli process-batch ./pdf_directory \
  --excel reference_data.xlsx \
  --output ./reports \
  --config config.yaml
```

#### Process Extracted BLMID Data Directly from Excel (No PDF Needed!)

**If you already have BLMID and coordinates in Excel sheets, use direct Excel processing:**

```bash
python -m blmid_validator.cli process-excel \
  extracted_blmid_data.xlsx \
  reference_data.xlsx \
  --output ./reports \
  --config config.yaml
```

**Options:**
- `--tolerance 0.0005` - Override coordinate tolerance
- `--mock-db` - Use mock database for testing (no PostgreSQL needed)

#### Test with Mock Database (No DB Required)

```bash
python -m blmid_validator.cli process-batch ./pdf_directory \
  --excel reference_data.xlsx \
  --output ./reports \
  --mock-db
```

#### Generate Config Template

```bash
python -m blmid_validator.cli init-config --output my_config.yaml
```

### Option 2: Python Script

```python
from blmid_validator.config import Config
from blmid_validator.processor import BLMIDProcessor

# Load configuration
config = Config("config.yaml")

# Create processor
processor = BLMIDProcessor(config, use_mock_db=False)

# Process batch
result = processor.process_batch_pdfs(
    pdf_dir="./surveys",
    excel_path="./reference.xlsx",
    output_dir="./reports"
)

# Access results
print(f"Valid entries: {result['valid_entries']}")
print(f"Corrected entries: {result['corrected_entries']}")
print(f"Failed extractions: {result['failed_extractions']}")
print(f"Output files: {result['output_files']}")
```

### Option 3: Programmatic Usage

```python
from blmid_validator.pdf_extractor import PDFExtractor
from blmid_validator.excel_handler import ExcelHandler
from blmid_validator.database import DatabaseConnector
from blmid_validator.validator import Validator

# Extract from PDF
extractor = PDFExtractor()
extraction = extractor.extract_from_pdf("survey.pdf")

# Load Excel reference
excel = ExcelHandler()
excel.load("reference.xlsx")

# Query database
db = DatabaseConnector("postgresql://user:pass@host/db")
db_result = db.find_by_coordinates(extraction['latitude'], extraction['longitude'])

# Validate
validator = Validator()
validation = validator.validate_entry(
    pdf_file="survey.pdf",
    extracted_blmid=extraction['blmid'],
    extracted_latitude=extraction['latitude'],
    extracted_longitude=extraction['longitude'],
    excel_lookup_result=excel.find_by_blmid(extraction['blmid']),
    database_lookup_result=db_result,
    pdf_extraction_errors=extraction['errors']
)
```

## Output Files

### 1. Updated BLMID Excel File

**Filename:** `Updated_BLMID_[timestamp].xlsx`

Contains:
- BLMID (with corrections applied)
- Latitude
- Longitude
- Source_PDF (filename)
- Correction_Applied (true/false)

### 2. Corrections Log

**Filename:** `Corrections_Log_[timestamp].xlsx`

Contains:
- Original_Entry: BLMID extracted from PDF
- Corrected_BLMID: Correct BLMID from database
- Latitude: Coordinate for reference
- Longitude: Coordinate for reference
- Source_PDF: Source PDF filename

### 3. Process Logs

**Locations:** `./output/logs/`

- `process.log`: All processing activities
- `error.log`: Errors and warnings only

## Database Setup

### Creating the Reference Table (PostgreSQL)

```sql
CREATE TABLE blmid_reference (
    id SERIAL PRIMARY KEY,
    blmid VARCHAR(50) NOT NULL UNIQUE,
    latitude DECIMAL(10, 6) NOT NULL,
    longitude DECIMAL(10, 6) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for coordinate queries
CREATE INDEX idx_coordinates ON blmid_reference(latitude, longitude);

-- Create index for BLMID lookups
CREATE INDEX idx_blmid ON blmid_reference(blmid);
```

### Sample Data

```sql
INSERT INTO blmid_reference (blmid, latitude, longitude) VALUES
    ('BLM001', 40.7128, -74.0060),
    ('BLM002', 51.5074, -0.1278),
    ('BLM003', 48.8566, 2.3522);
```

## Troubleshooting

### Database Connection Fails

**Error:** `psycopg2.OperationalError: could not connect to server`

**Solutions:**
1. Check PostgreSQL is running: `psql -U username -d database_name`
2. Verify connection URI format in `config.yaml`
3. Check firewall rules for port 5432
4. Verify database credentials

### PDF Text Extraction Returns Empty

**Error:** PDF contains no extractable text

**Solutions:**
1. Check if PDF is scanned (image-based):
   - Enable OCR: `ocr_enabled: true`
   - Install Tesseract
2. Try different PDF library:
   - Uncomment PyPDF2 in `requirements.txt`
3. Verify PDF is not corrupted

### OCR Not Working

**Error:** `pytesseract.TesseractNotFoundError`

**Solutions:**
1. Install Tesseract from: https://github.com/UB-Mannheim/tesseract/wiki
2. Update `tesseract_path` in `config.yaml` if not in PATH
3. Verify installation: `tesseract --version`

### Coordinates Not Matching

**Solutions:**
1. Increase `coordinate_tolerance` in `config.yaml`:
   ```yaml
   validation:
     coordinate_tolerance: 0.001  # Increase from 0.0001
   ```
2. Verify PDF extraction patterns match your format
3. Check database coordinates are in correct format

### Memory Issues with Large Batches

**Solutions:**
1. Process PDFs in smaller batches
2. Reduce OCR resolution in PDF extraction
3. Increase system RAM

## API Reference

### Config Class

```python
from blmid_validator.config import Config

# Load config
config = Config("config.yaml")

# Get values with dot notation
uri = config.get("database.connection_uri")
tolerance = config.get("validation.coordinate_tolerance")

# Set values
config.set("validation.coordinate_tolerance", 0.0005)

# Save config
config.save_to_file("new_config.yaml", format="yaml")
```

### PDFExtractor Class

```python
from blmid_validator.pdf_extractor import PDFExtractor

extractor = PDFExtractor(
    blmid_pattern=r"BLM[\s-]*([A-Z0-9]+)",
    latitude_pattern=r"latitude[\s:]*(-?\d+\.?\d*)",
    longitude_pattern=r"longitude[\s:]*(-?\d+\.?\d*)",
    ocr_enabled=True,
    ocr_fallback=True
)

# Extract from single PDF
result = extractor.extract_from_pdf("survey.pdf")

# Batch extract
results = extractor.batch_extract("./pdf_dir")
```

### ExcelHandler Class

```python
from blmid_validator.excel_handler import ExcelHandler

handler = ExcelHandler()
df = handler.load("reference.xlsx")

# Find by BLMID
record = handler.find_by_blmid("BLM001")

# Find by coordinates
record = handler.find_by_coordinates(40.7128, -74.0060, tolerance=0.0001)

# Save updated data
handler.save_updated(updated_df, "./output")
handler.save_corrections_log(corrections, "./output")
```

### DatabaseConnector Class

```python
from blmid_validator.database import DatabaseConnector

db = DatabaseConnector(
    connection_uri="postgresql://user:pass@localhost:5432/db",
    table_name="blmid_reference"
)

# Find by coordinates
record = db.find_by_coordinates(40.7128, -74.0060, tolerance=0.0001)

# Find by BLMID
record = db.find_by_blmid("BLM001")

# Get all records
records = db.get_all_records()
```

### Validator Class

```python
from blmid_validator.validator import Validator

validator = Validator(coordinate_tolerance=0.0001)

# Validate coordinates
valid, errors = validator.validate_coordinates(40.7128, -74.0060)

# Check coordinate match
match = validator.check_coordinates_match(40.0, -74.0, 40.00005, -74.00005)

# Validate entry
result = validator.validate_entry(...)

# Batch validate
summary = validator.batch_validate(extractions, excel_handler, db)
```

### DirectExcelProcessor Class (NEW)

```python
from blmid_validator.excel_processor import DirectExcelProcessor
from blmid_validator.config import Config

config = Config("config.yaml")

# Create processor for direct Excel processing
processor = DirectExcelProcessor(config, use_mock_db=False)

# Process Excel files directly (no PDF extraction)
result = processor.process_excel_batch(
    extracted_excel="extracted_blmid_data.xlsx",
    reference_excel="reference_data.xlsx",
    output_dir="./output"
)

# Access results
print(f"Valid entries: {len(result['valid_entries'])}")
print(f"Corrected entries: {len(result['corrected_entries'])}")
print(f"Failed entries: {len(result['failed_entries'])}")
print(f"Output files: {result['output_files']}")
```

**Use this when:**
- You already have extracted BLMID and coordinates in Excel
- You don't have PDFs or have already processed them
- You want to skip PDF processing entirely
- You need to validate/correct existing data

## Testing

Run unit tests:

```bash
python -m pytest tests/ -v

# With coverage
python -m pytest tests/ --cov=blmid_validator
```

Run sample usage:

```bash
python sample_usage.py
```

## Performance Tips

1. **Batch Processing**: Process multiple PDFs at once rather than individually
2. **Database Indexes**: Ensure database has indexes on coordinate and BLMID columns
3. **OCR Optimization**: 
   - Use `ocr_fallback: true` to avoid OCR on text PDFs
   - Reduce PDF resolution if OCR is slow
4. **Excel Files**: Keep reference sheets under 100,000 rows for best performance
5. **Connection Pooling**: Database connections are reused automatically

## Security Considerations

1. **Database Credentials**: 
   - Never commit `config.yaml` with real credentials to version control
   - Use environment variables for sensitive data
   - Restrict file permissions: `chmod 600 config.yaml`

2. **PDF Security**: 
   - Verify PDFs from trusted sources only
   - Be cautious with OCR on sensitive documents

3. **Data Privacy**: 
   - Store coordinates securely
   - Limit log file access
   - Comply with data protection regulations

## Contributing

To extend or modify the application:

1. Add new modules in `blmid_validator/`
2. Update configuration in `Config` class
3. Add tests in `tests/`
4. Update documentation in `README.md`

## License

[Add your license information here]

## Support

For issues or questions:
1. Check `output/logs/error.log` for error messages
2. Review configuration settings in `config.yaml`
3. Test database connection separately
4. Run with `--debug` flag for verbose logging

## Version History

### v1.0.0 (2025-11-24)
- Initial release
- PDF text and OCR extraction
- Excel and database validation
- Batch processing support
- Comprehensive reporting
- Full CLI interface
