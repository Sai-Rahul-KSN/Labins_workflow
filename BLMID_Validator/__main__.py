"""
Generate main entry point for BLMID Validator package.
"""

import sys
from pathlib import Path

# Add package to path
package_dir = Path(__file__).parent

if __name__ == "__main__":
    from blmid_validator.cli import main
    sys.exit(main())
