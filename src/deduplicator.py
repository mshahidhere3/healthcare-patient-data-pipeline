"""Patient deduplication engine supporting deterministic and fuzzy matching."""
from typing import List, Tuple, Dict
from rapidfuzz import fuzz
from src.schema import CleanPatientRecord
from src.config import FUZZY_NAME_SIMILARITY_THRESHOLD, COMPOSITE_MATCH_THRESHOLD

class PatientDeduplicator:
    """
    Detects duplicate patient profiles across multiple hospital feeds.
    Combines exact MRN matching with fuzzy demographic scoring (Name, DOB, Phone, Address).
    """

    def __init__(self, fuzzy_threshold: float = COMPOSITE_MATCH_THRESHOLD):
        self.fuzzy_threshold = fuzzy_threshold

    def calculate_demographic_similarity(self, rec1: CleanPatientRecord, rec2: CleanPatientRecord) -> float:
        """
        Calculate a composite similarity score between two patient records (0.0 to 100.0).
        Weights:
          - First Name: 25%
          - Last Name: 30%
          - Date of Birth: 25%
          - Phone/Zip: 20%
        """
        first_score = fuzz.token_sort_ratio(rec1.first_name.lower(), rec2.first_name.lower())
        last_score = fuzz.token_sort_ratio(rec1.last_name.lower(), rec2.last_name.lower())

        dob_score = 100.0 if rec1.date_of_birth == rec2.date_of_birth else 0.0

        contact_score = 0.0
        contact_points = 0
        if rec1.phone and rec2.phone:
            contact_points += 1
            if rec1.phone == rec2.phone:
                contact_score += 100.0
        if rec1.zip_code and rec2.zip_code:
            contact_points += 1
            if rec1.zip_code == rec2.zip_code:
                contact_score += 100.0

        contact_final = (contact_score / contact_points) if contact_points > 0 else 50.0

        composite = (first_score * 0.25) + (last_score * 0.30) + (dob_score * 0.25) + (contact_final * 0.20)
        return round(composite, 2)

    def deduplicate(self, records: List[CleanPatientRecord]) -> Tuple[List[CleanPatientRecord], int]:
        """
        Deduplicates a list of CleanPatientRecord.
        Returns (unique_records, duplicate_count).
        """
        if not records:
            return [], 0

        unique_records: List[CleanPatientRecord] = []
        mrn_map: Dict[str, CleanPatientRecord] = {}
        duplicate_count = 0

        for record in records:
            # Deterministic Match 1: Exact MRN
            if record.mrn in mrn_map:
                existing = mrn_map[record.mrn]
                # Merge more complete contact info into existing if missing
                self._merge_records(existing, record)
                duplicate_count += 1
                continue

            # Deterministic/Fuzzy Match 2: Compare against unique list
            is_dup = False
            for existing in unique_records:
                sim = self.calculate_demographic_similarity(existing, record)
                if sim >= self.fuzzy_threshold:
                    self._merge_records(existing, record)
                    duplicate_count += 1
                    is_dup = True
                    break

            if not is_dup:
                mrn_map[record.mrn] = record
                unique_records.append(record)

        return unique_records, duplicate_count

    def _merge_records(self, target: CleanPatientRecord, incoming: CleanPatientRecord) -> None:
        """Merge missing fields from incoming duplicate record into primary record."""
        if not target.phone and incoming.phone:
            target.phone = incoming.phone
        if not target.email and incoming.email:
            target.email = incoming.email
        if not target.address and incoming.address:
            target.address = incoming.address
        if not target.blood_group and incoming.blood_group:
            target.blood_group = incoming.blood_group
