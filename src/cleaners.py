"""Data cleaning, normalization, and standardization functions."""
import re
from datetime import datetime
from typing import Optional, Tuple
from src.config import SUPPORTED_DATE_FORMATS, VALID_GENDERS

def clean_date_of_birth(val: Optional[str]) -> Optional[str]:
    """
    Standardize diverse date representations to ISO 8601 YYYY-MM-DD.
    Handles Unix timestamps, slashes, dashes, and text representations.
    Returns None if date is unparseable or outside human boundaries (1900 to current date).
    """
    if not val or str(val).strip().lower() in ["", "nan", "none", "null", "n/a", "unknown"]:
        return None

    val_str = str(val).strip()

    # Numeric timestamp (seconds or milliseconds)
    if val_str.isdigit() and len(val_str) in [10, 13]:
        try:
            ts = int(val_str)
            if len(val_str) == 13:
                ts = ts / 1000.0
            dt = datetime.fromtimestamp(ts)
            if 1900 <= dt.year <= datetime.now().year:
                return dt.strftime("%Y-%m-%d")
        except (ValueError, OSError):
            pass

    for fmt in SUPPORTED_DATE_FORMATS:
        try:
            dt = datetime.strptime(val_str, fmt)
            if 1900 <= dt.year <= datetime.now().year:
                return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue

    return None

def clean_phone_number(val: Optional[str]) -> Optional[str]:
    """
    Normalize phone numbers to standard E.164-compatible US/Canada format (+1-XXX-XXX-XXXX).
    Strips noise words (e.g. 'call', 'cell', 'home', dashes, parentheses).
    """
    if not val or str(val).strip().lower() in ["", "nan", "none", "null", "n/a"]:
        return None

    digits = re.sub(r"\D", "", str(val))

    # Strip US country code if provided
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]

    if len(digits) == 10:
        return f"+1-{digits[0:3]}-{digits[3:6]}-{digits[6:10]}"

    return None

def clean_name_field(val: Optional[str]) -> str:
    """
    Clean patient name fields:
    - Strips titles/salutations (Mr., Dr., Mrs., Ms., MD, PhD)
    - Removes trailing special characters and numbers
    - Normalizes to Proper Title Case
    """
    if not val or str(val).strip().lower() in ["", "nan", "none", "null", "n/a"]:
        return ""

    s = str(val).strip()
    # Remove common prefixes/suffixes
    s = re.sub(r"^(dr\.?|mr\.?|mrs\.?|ms\.?|prof\.?)\s+", "", s, flags=re.IGNORECASE)
    s = re.sub(r"\s+(md|phd|rn|jr\.?|sr\.?|iii|iv|ii)$", "", s, flags=re.IGNORECASE)
    # Remove numeric artifacts
    s = re.sub(r"[^A-Za-z\s\-']", "", s)
    # Collapse whitespace
    s = re.sub(r"\s+", " ", s).strip()
    return s.title()

def clean_gender(val: Optional[str]) -> str:
    """
    Standardize gender codes into standard HL7/FHIR categories:
    M (Male), F (Female), O (Other), U (Unknown).
    """
    if not val or str(val).strip().lower() in ["", "nan", "none", "null", "n/a"]:
        return "U"

    norm = str(val).strip().upper()
    if norm in ["M", "MALE", "MAN", "BOY"]:
        return "M"
    elif norm in ["F", "FEMALE", "WOMAN", "GIRL"]:
        return "F"
    elif norm in ["O", "OTHER", "NON-BINARY", "NB", "TRANSGENDER"]:
        return "O"
    return "U"

def clean_zip_code(val: Optional[str]) -> Optional[str]:
    """Standardize US ZIP code to 5-digit format or ZIP+4."""
    if not val or str(val).strip().lower() in ["", "nan", "none", "null", "n/a"]:
        return None

    raw = str(val).strip()
    digits = re.sub(r"\D", "", raw)
    if len(digits) == 5:
        return digits
    elif len(digits) == 9:
        return f"{digits[:5]}-{digits[5:]}"
    elif len(digits) > 5:
        return digits[:5]
    return None

def clean_mrn(val: Optional[str]) -> Optional[str]:
    """
    Standardize Medical Record Number into format MRN-XXXXXXX.
    Rejects completely empty or dummy values (e.g. 0000000, 9999999).
    """
    if not val or str(val).strip().lower() in ["", "nan", "none", "null", "n/a"]:
        return None

    raw = str(val).strip().upper()
    # Strip prefix MRN if already there
    digits = re.sub(r"\D", "", raw)
    if len(digits) >= 6 and not re.match(r"^0+$", digits):
        return f"MRN-{digits[-7:].zfill(7)}"
    return None

def clean_email(val: Optional[str]) -> Optional[str]:
    """Validate and lower-case email addresses."""
    if not val or str(val).strip().lower() in ["", "nan", "none", "null", "n/a"]:
        return None

    email = str(val).strip().lower()
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    if re.match(pattern, email):
        return email
    return None
