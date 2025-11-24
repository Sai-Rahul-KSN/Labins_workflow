# BLMID Validator - Integration Guide

## Project Overview

This is a complete, production-ready Python application for validating BLMID entries from PDF survey forms. It includes:

✅ PDF extraction (text + OCR)
✅ Excel reference validation
✅ PostgreSQL database connectivity
✅ Comprehensive correction reporting
✅ Batch processing support
✅ Command-line interface
✅ Full logging system
✅ Unit tests
✅ Extensive documentation

---

## Quick Installation & Setup

### Step 1: Navigate to Project

```powershell
cd "C:\Users\sk23dg\Desktop\Labins_Workflow\BLMID_Validator"
```

### Step 2: Create Virtual Environment (Recommended)

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

### Step 3: Install Dependencies

```powershell
pip install -r requirements.txt
```

### Step 4: Configure Application

```powershell
# Generate config template
python -m blmid_validator.cli init-config --output config.yaml
```

Edit `config.yaml` and add your database connection:

```yaml
database:
  connection_uri: "postgresql://your_user:your_password@localhost:5432/your_database"
  table_name: "blmid_reference"
```

### Step 5: Create Sample Excel (For Testing)

```powershell
cd sample_data
python create_sample_excel.py
cd ..
```

---

## Usage Examples

### Example 1: Test with Mock Database (No PostgreSQL Required)

```powershell
# Uses built-in mock database with test data
python -m blmid_validator.cli process-batch ./sample_data `
  --excel ./sample_data/reference_data.xlsx `
  --output ./test_output `
  --mock-db
```

### Example 2: Process Single PDF

```powershell
python -m blmid_validator.cli process-single survey.pdf `
  --excel reference.xlsx `
  --output ./reports `
  --config config.yaml
```

### Example 3: Batch Process with Real Database

```powershell
python -m blmid_validator.cli process-batch ./pdf_folder `
  --excel reference.xlsx `
  --output ./reports `
  --config config.yaml
```

### Example 4: Python Script

```powershell
python sample_usage.py
```

---

## Database Setup (PostgreSQL with pgAdmin-3)

### 1. Create Table

In pgAdmin-3, run:

```sql
-- Create table
CREATE TABLE blmid_reference (
    id SERIAL PRIMARY KEY,
    blmid VARCHAR(50) NOT NULL UNIQUE,
    latitude DECIMAL(10, 6) NOT NULL,
    longitude DECIMAL(10, 6) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX idx_blmid ON blmid_reference(blmid);
CREATE INDEX idx_coordinates ON blmid_reference(latitude, longitude);
```

### 2. Add Sample Data

```sql
INSERT INTO blmid_reference (blmid, latitude, longitude) VALUES
    ('BLM12345', 40.7128, -74.0060),
    ('BLM12346', 51.5074, -0.1278),
    ('BLM12347', 48.8566, 2.3522),
    ('BLM12348', 35.6762, 139.6503),
    ('BLM12349', -33.8688, 151.2093);
```

### 3. Update config.yaml

```yaml
database:
  connection_uri: "postgresql://postgres:your_password@localhost:5432/postgres"
  table_name: "blmid_reference"
  columns:
    blmid: "blmid"
    latitude: "latitude"
    longitude: "longitude"
```

### 4. Test Connection

```powershell
python -c "from blmid_validator.database import DatabaseConnector; db = DatabaseConnector('postgresql://postgres:password@localhost:5432/postgres'); print('Connected!')"
```

---

## Project Structure

```
BLMID_Validator/
│
├── blmid_validator/                 # Main package
│   ├── __init__.py
│   ├── config.py                    # Configuration manager
│   ├── logger_setup.py              # Logging configuration
│   ├── pdf_extractor.py             # PDF text + OCR extraction
│   ├── excel_handler.py             # Excel file operations
│   ├── database.py                  # PostgreSQL connector + Mock DB
│   ├── validator.py                 # Validation logic
│   ├── processor.py                 # Main orchestration
│   └── cli.py                       # Command-line interface
│
├── tests/
│   └── test_validator.py            # Unit tests
│
├── sample_data/
│   ├── sample_survey.txt            # Sample PDF text
│   ├── reference_data.xlsx          # Sample Excel (create via script)
│   └── create_sample_excel.py       # Script to create sample Excel
│
├── config.yaml                      # Configuration (CUSTOMIZE THIS)
├── requirements.txt                 # Python dependencies
├── setup.py                         # Package installation
├── __main__.py                      # Entry point
├── sample_usage.py                  # Usage examples
├── QUICKSTART.md                    # Quick start guide
├── INTEGRATION.md                   # This file
└── README.md                        # Full documentation
```

---

## File Descriptions

### Core Modules

| File | Purpose |
|------|---------|
| `config.py` | Loads/manages configuration from YAML/JSON files |
| `pdf_extractor.py` | Extracts BLMID and coordinates from PDFs (text + OCR) |
| `excel_handler.py` | Loads Excel, finds/saves records |
| `database.py` | PostgreSQL connector and mock database for testing |
| `validator.py` | Validates extracted data and compares against sources |
| `processor.py` | Orchestrates the entire workflow |
| `cli.py` | Command-line interface with subcommands |
| `logger_setup.py` | Configures logging to files and console |

### Configuration

- `config.yaml` - Main configuration file (edit with your settings)
  - Database connection URI
  - Excel column mappings
  - PDF regex patterns
  - Coordinate tolerance
  - Log settings

### Documentation

- `README.md` - Complete API and usage documentation
- `QUICKSTART.md` - 5-minute quick start guide
- `INTEGRATION.md` - This integration guide

### Testing & Samples

- `tests/test_validator.py` - Unit tests
- `sample_data/` - Sample files for testing
- `sample_usage.py` - Example usage patterns

---

## Key Features Explained

### 1. PDF Extraction

Automatically extracts:
- BLMID (using regex pattern)
- Latitude and Longitude coordinates
- Supports both text PDFs and scanned PDFs (with OCR)

Configurable patterns in `config.yaml`:
```yaml
pdf:
  regex_patterns:
    blmid: "BLM[\\s-]*([A-Z0-9]+)"
    latitude: "(lat[a-z]*|latitude)[\\s:]*(-?\\d+\\.?\\d*)"
    longitude: "(lon[a-z]*|longitude)[\\s:]*(-?\\d+\\.?\\d*)"
```

### 2. Excel Validation

- Loads reference data from Excel
- Finds records by BLMID or coordinates
- Compares coordinates with configurable tolerance
- Supports custom column positions (A, B, C, etc.)

### 3. Database Verification

- Queries PostgreSQL for correct BLMID
- Searches by coordinates (with tolerance)
- Returns matching records
- Includes mock database for testing (no DB needed)

### 4. Validation Logic

- Validates coordinate ranges (±90° lat, ±180° lon)
- Checks tolerance-based matching
- Flags mismatches for correction
- Logs all errors and warnings

### 5. Report Generation

**Output 1: Updated BLMID Excel**
- Same structure as input
- Corrected BLMIDs applied
- Filename: `Updated_BLMID_[timestamp].xlsx`

**Output 2: Corrections Log**
- Original BLMID from PDF
- Corrected BLMID from database
- Latitude/Longitude references
- Source PDF filename

**Output 3: Process Logs**
- `output/logs/process.log` - All activities
- `output/logs/error.log` - Errors only

---

## Workflow Example

```
Survey PDF (with BLMID & coordinates)
    ↓
PDF Extraction Module
    ├─ Extract BLMID (regex)
    ├─ Extract Latitude (regex)
    ├─ Extract Longitude (regex)
    └─ Handle OCR if needed
    ↓
Extracted Data
    ↓
Validator Module
    ├─ Validate coordinate formats
    ├─ Check Excel for BLMID
    └─ Query Database for coordinates
    ↓
Database Query Results
    ↓
Correction Logic
    ├─ If BLMID matches → Mark as valid
    ├─ If coordinates mismatch → Flag correction
    └─ If no match → Log error
    ↓
Generate Reports
    ├─ Updated Excel with corrections
    ├─ Corrections log
    └─ Process logs
    ↓
Output Files
```

---

## Configuration Reference

### Database Connection

Format: `postgresql://[user[:password]@][host][:port][/database]`

Examples:
- Local: `postgresql://postgres:password@localhost:5432/blmid_db`
- Remote: `postgresql://user@192.168.1.100:5432/survey_db`
- With special chars: `postgresql://user:pass%40word@host/db` (@ → %40)

### Excel Column Mapping

Default: Column A=BLMID, B=Latitude, C=Longitude

Custom example:
```yaml
excel:
  columns:
    blmid: "B"        # BLMID in column B
    latitude: "C"     # Latitude in column C
    longitude: "D"    # Longitude in column D
```

### Coordinate Tolerance

- `0.0001` degrees ≈ 11.1 meters (default, tight match)
- `0.001` degrees ≈ 111 meters (loose match)
- Adjust based on your GPS accuracy requirements

### Regex Patterns

All patterns are case-insensitive by default. Examples:

```yaml
pdf:
  regex_patterns:
    # Matches: BLMID-001, BLM 001, BLMID: 001
    blmid: "BLM[ID\\s-]*([A-Z0-9]+)"
    
    # Matches: Lat: 40.7, Latitude=40.7, lat 40.7
    latitude: "(lat[a-z]*|latitude)[\\s:=]*(-?\\d+\\.?\\d*)"
    
    # Matches: Lon: -74.0, Longitude=-74.0
    longitude: "(lon[a-z]*|longitude)[\\s:=]*(-?\\d+\\.?\\d*)"
```

---

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'pdfplumber'"

```powershell
pip install -r requirements.txt
```

### Issue: Database Connection Failed

1. Verify PostgreSQL running
2. Check connection string
3. Test: `psql -U postgres -d postgres`

### Issue: PDF Text Not Extracted

1. Check if PDF is scanned (image-based)
2. Enable OCR and install Tesseract
3. Check regex patterns in config.yaml

### Issue: Coordinates Not Matching

1. Increase `coordinate_tolerance`
2. Verify PDF extraction patterns
3. Check database has matching records

---

## Performance Optimization

1. **Batch Size**: Process 10+ PDFs at once
2. **Database Indexes**: Essential for large datasets
3. **OCR**: Only enable when needed (`ocr_fallback: true`)
4. **Excel Size**: Keep under 100,000 rows

---

## API Usage

### Quick Examples

```python
# Load configuration
from blmid_validator.config import Config
config = Config("config.yaml")

# Extract from PDF
from blmid_validator.pdf_extractor import PDFExtractor
extractor = PDFExtractor()
result = extractor.extract_from_pdf("survey.pdf")
print(result['blmid'], result['latitude'], result['longitude'])

# Query database
from blmid_validator.database import DatabaseConnector
db = DatabaseConnector(config.get("database.connection_uri"))
record = db.find_by_coordinates(40.7128, -74.0060)

# Load Excel
from blmid_validator.excel_handler import ExcelHandler
excel = ExcelHandler()
excel.load("reference.xlsx")
record = excel.find_by_blmid("BLM12345")

# Full processing
from blmid_validator.processor import BLMIDProcessor
processor = BLMIDProcessor(config)
result = processor.process_batch_pdfs("./pdfs", "reference.xlsx", "./output")
```

---

## Running Tests

```powershell
# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=blmid_validator

# Run specific test
python -m pytest tests/test_validator.py::TestValidator::test_validate_coordinates_valid -v
```

---

## Deployment Checklist

- [ ] Database created and populated with reference data
- [ ] `config.yaml` customized with correct connection URI
- [ ] Database table has indexes on BLMID and coordinates
- [ ] All dependencies installed: `pip install -r requirements.txt`
- [ ] Test run successful with mock database: `--mock-db`
- [ ] Connection to real database verified
- [ ] PDF sample tested and extraction patterns validated
- [ ] Excel reference file format verified
- [ ] Output directory created and has write permissions
- [ ] Logging configuration reviewed
- [ ] Error handling tested

---

## Support & Debugging

### Enable Debug Logging

In `config.yaml`:
```yaml
logging:
  level: "DEBUG"
```

### Check Logs

```powershell
# View process log
Get-Content output\logs\process.log -Tail 50

# View error log
Get-Content output\logs\error.log
```

### Test Individual Components

```python
# Test PDF extraction
from blmid_validator.pdf_extractor import PDFExtractor
extractor = PDFExtractor()
result = extractor.extract_from_pdf("test.pdf")
print("BLMID:", result['blmid'])
print("Errors:", result['errors'])

# Test database
from blmid_validator.database import MockDatabase
db = MockDatabase()
print(db.find_by_blmid("BLM001"))

# Test configuration
from blmid_validator.config import Config
config = Config("config.yaml")
print(config.to_json())
```

---

## Next Steps

1. ✅ Review this guide
2. ✅ Install dependencies
3. ✅ Configure `config.yaml` with your database
4. ✅ Create sample Excel reference file
5. ✅ Run test with mock database
6. ✅ Prepare production PDFs and reference data
7. ✅ Run full batch processing
8. ✅ Review output reports
9. ✅ Deploy to production

---

**Questions?** Refer to README.md for detailed API documentation or QUICKSTART.md for quick examples.
