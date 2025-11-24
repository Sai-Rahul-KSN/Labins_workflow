"""
Setup script for BLMID Validator.
"""

from setuptools import setup, find_packages

setup(
    name="blmid-validator",
    version="1.0.0",
    description="Validate BLMID entries in PDF survey forms against Excel and database",
    author="BLMID Validation Team",
    packages=find_packages(),
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "blmid-validator=blmid_validator.cli:main",
        ],
    },
    install_requires=[],  # See requirements.txt for full list
)
