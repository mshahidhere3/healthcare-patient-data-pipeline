"""Realistic dirty synthetic healthcare EHR dataset generator."""
import random
import csv
from pathlib import Path
from typing import List, Dict, Any

FIRST_NAMES = ["James", "Mary", "Robert", "Patricia", "John", "Jennifer", "Michael", "Linda", "David", "Elizabeth", "William", "Barbara", "Richard", "Susan", "Joseph", "Jessica", "Thomas", "Sarah", "Charles", "Karen"]
LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin"]
CITIES = ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia", "San Antonio", "San Diego", "Dallas", "San Jose"]
STATES = ["NY", "CA", "IL", "TX", "AZ", "PA", "TX", "CA", "TX", "CA"]
BLOOD_GROUPS = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]

def generate_dirty_patient_dataset(num_records: int = 500, dirty_rate: float = 0.35, output_file: Path = None) -> List[Dict[str, Any]]:
    """
    Generates synthetic patient EHR data simulating real-world messiness:
    - Inconsistent date formats (MM/DD/YYYY, YYYY-MM-DD, epoch, invalid dates)
    - Formatting noise in phone numbers ('(555) 000-1111', '555.000.1111', 'call: 5550001111')
    - Name salutations & suffixes ('Dr. John Smith MD', 'MR. ROBERT WILLIAMS JR')
    - Non-standard gender representations ('male', 'FEMALE', 'M', 'woman', 'unknown', 'N/A')
    - Corrupted MRNs and missing required fields
    - Intentional duplicate patients with slight variations
    """
    records = []
    base_mrn = 1000000

    for i in range(1, num_records + 1):
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        city_idx = random.randint(0, len(CITIES) - 1)
        city = CITIES[city_idx]
        state = STATES[city_idx]
        mrn = f"MRN-{base_mrn + i}"

        # Natural birthdate
        year = random.randint(1950, 2015)
        month = random.randint(1, 12)
        day = random.randint(1, 28)
        dob = f"{year:04d}-{month:02d}-{day:02d}"

        gender = random.choice(["Male", "Female"])
        phone = f"555{random.randint(1000000, 9999999)}"
        email = f"{first.lower()}.{last.lower()}{random.randint(10, 99)}@example.com"
        address = f"{random.randint(100, 9999)} Main St"
        zip_code = f"{random.randint(10000, 99999)}"
        blood = random.choice(BLOOD_GROUPS)
        systolic = random.randint(100, 160)
        diastolic = random.randint(60, 100)

        # Inject realistic dirtiness
        is_dirty = random.random() < dirty_rate

        if is_dirty:
            defect_type = random.choice(["date", "phone", "name", "gender", "zip", "mrn", "missing_required"])

            if defect_type == "date":
                style = random.choice(["slash_us", "slash_eu", "text", "epoch", "invalid"])
                if style == "slash_us":
                    dob = f"{month:02d}/{day:02d}/{year}"
                elif style == "slash_eu":
                    dob = f"{day:02d}/{month:02d}/{year}"
                elif style == "text":
                    dob = f"Oct {day}, {year}"
                elif style == "epoch":
                    dob = str(int(random.uniform(0, 1600000000)))
                elif style == "invalid":
                    dob = "1990-13-45"  # Impossible date -> quarantined

            elif defect_type == "phone":
                noise = random.choice(["(555) {}-{}", "555.{}.{}", "Call: 555{}", "INVALID_PHONE", ""])
                if "{}" in noise:
                    phone = noise.format(phone[3:6], phone[6:])
                else:
                    phone = noise

            elif defect_type == "name":
                prefix = random.choice(["Dr. ", "Mr. ", "Mrs. ", "MS. "])
                suffix = random.choice([" MD", " PhD", " Jr.", ""])
                first = f"{prefix}{first}"
                last = f"{last}{suffix}"

            elif defect_type == "gender":
                gender = random.choice(["man", "woman", "MALE", "FEMALE", "N/A", "Transgender", "Unknown"])

            elif defect_type == "zip":
                zip_code = random.choice(["0", "999", "12345-6789", "INVALID"])

            elif defect_type == "mrn":
                mrn = random.choice(["", "0000000", "CORRUPT", "None"])  # Invalid MRN -> quarantined

            elif defect_type == "missing_required":
                first = ""  # Missing required name -> quarantined

        records.append({
            "raw_id": f"RAW_{i:06d}",
            "mrn": mrn,
            "first_name": first,
            "last_name": last,
            "date_of_birth": dob,
            "gender": gender,
            "phone": phone,
            "email": email,
            "address": address,
            "city": city,
            "state": state,
            "zip_code": zip_code,
            "blood_group": blood,
            "systolic_bp": systolic,
            "diastolic_bp": diastolic
        })

    # Inject 5% duplicate records with slight modifications
    num_dups = max(3, int(num_records * 0.05))
    for _ in range(num_dups):
        donor = random.choice(records)
        dup = donor.copy()
        dup["raw_id"] = f"RAW_DUP_{random.randint(1000, 9999)}"
        # Add slight typo or different phone
        dup["phone"] = f"+1-555-{random.randint(100,999)}-{random.randint(1000,9999)}"
        records.append(dup)

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        keys = records[0].keys()
        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(records)

    return records
