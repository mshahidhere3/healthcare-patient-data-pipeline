"""Pipeline configuration settings and constants."""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
QUARANTINE_DATA_DIR = DATA_DIR / "quarantine"
REPORTS_DIR = BASE_DIR / "reports"

for path in [RAW_DATA_DIR, PROCESSED_DATA_DIR, QUARANTINE_DATA_DIR, REPORTS_DIR]:
    path.mkdir(parents=True, exist_ok=True)

# Demographics standards
VALID_GENDERS = {
    "M": "Male",
    "F": "Female",
    "O": "Other",
    "U": "Unknown"
}

# Matching and deduplication threshold
FUZZY_NAME_SIMILARITY_THRESHOLD = 85.0
COMPOSITE_MATCH_THRESHOLD = 88.0

# Supported Date Formats
SUPPORTED_DATE_FORMATS = [
    "%Y-%m-%d",
    "%m/%d/%Y",
    "%d/%m/%Y",
    "%Y/%m/%d",
    "%d-%m-%Y",
    "%m-%d-%Y",
    "%B %d, %Y",
    "%b %d, %Y",
    "%Y%m%d"
]
