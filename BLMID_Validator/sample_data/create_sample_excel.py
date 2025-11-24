# Sample script to create test Excel reference file
# Run this to generate sample_data/reference_data.xlsx

import pandas as pd
from pathlib import Path

# Create sample data
data = {
    'BLMID': [
        'BLM12345',
        'BLM12346',
        'BLM12347',
        'BLM12348',
        'BLM12349',
    ],
    'Latitude': [
        40.7128,
        51.5074,
        48.8566,
        35.6762,
        -33.8688,
    ],
    'Longitude': [
        -74.0060,
        -0.1278,
        2.3522,
        139.6503,
        151.2093,
    ]
}

# Create DataFrame
df = pd.DataFrame(data)

# Create output directory if it doesn't exist
output_dir = Path(__file__).parent
output_file = output_dir / "reference_data.xlsx"

# Save to Excel
df.to_excel(output_file, sheet_name='BLMID Reference', index=False, engine='openpyxl')

print(f"Sample reference file created: {output_file}")
print(f"\nData preview:")
print(df)
