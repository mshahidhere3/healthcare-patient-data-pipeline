"""Unit tests for patient deduplication and merging."""
import pytest
from src.schema import CleanPatientRecord
from src.deduplicator import PatientDeduplicator

def test_deduplication_exact_mrn():
    dedup = PatientDeduplicator()
    rec1 = CleanPatientRecord(
        patient_id="PAT-1001",
        mrn="MRN-1001",
        first_name="Alice",
        last_name="Smith",
        full_name="Alice Smith",
        date_of_birth="1980-05-15",
        gender="F",
        phone=None
    )
    rec2 = CleanPatientRecord(
        patient_id="PAT-1001",
        mrn="MRN-1001",
        first_name="Alice",
        last_name="Smith",
        full_name="Alice Smith",
        date_of_birth="1980-05-15",
        gender="F",
        phone="+1-555-111-2222"
    )

    clean_records, dup_count = dedup.deduplicate([rec1, rec2])
    assert len(clean_records) == 1
    assert dup_count == 1
    assert clean_records[0].phone == "+1-555-111-2222"  # Merged missing phone

def test_deduplication_fuzzy_demographics():
    dedup = PatientDeduplicator()
    rec1 = CleanPatientRecord(
        patient_id="PAT-1002",
        mrn="MRN-1002",
        first_name="Robert",
        last_name="Johnson",
        full_name="Robert Johnson",
        date_of_birth="1975-10-20",
        gender="M",
        zip_code="10001"
    )
    rec2 = CleanPatientRecord(
        patient_id="PAT-9999",
        mrn="MRN-9999",  # Slightly different temporary MRN but identical person
        first_name="Rob",
        last_name="Johnson",
        full_name="Rob Johnson",
        date_of_birth="1975-10-20",
        gender="M",
        zip_code="10001"
    )

    clean_records, dup_count = dedup.deduplicate([rec1, rec2])
    assert len(clean_records) == 1
    assert dup_count == 1
