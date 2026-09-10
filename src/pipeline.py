"""Core ETL Pipeline Orchestrator."""
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Tuple

from src.config import RAW_DATA_DIR, PROCESSED_DATA_DIR, QUARANTINE_DATA_DIR, REPORTS_DIR
from src.cleaners import (
    clean_date_of_birth, clean_phone_number, clean_name_field,
    clean_gender, clean_zip_code, clean_mrn, clean_email
)
from src.schema import CleanPatientRecord, QuarantineRecord, RawPatientInput
from src.deduplicator import PatientDeduplicator
from src.metrics import DataQualityAuditor

class PatientDataPipeline:
    """
    Enterprise healthcare data cleansing and normalization pipeline.
    Executes:
      1. Ingest raw EMR records
      2. Cleanse and standardize fields
      3. Validate integrity and route failures to quarantine
      4. Deduplicate patient identities
      5. Output clean analytics-ready datasets and audit logs
    """

    def __init__(self):
        self.deduplicator = PatientDeduplicator()

    def process_record(self, raw: Dict[str, Any]) -> Tuple[CleanPatientRecord, QuarantineRecord]:
        """
        Validate, normalize and route an individual record to either Clean or Quarantine.
        """
        raw_id = raw.get("raw_id", "UNKNOWN")
        raw_mrn = raw.get("mrn")
        first_raw = raw.get("first_name", "")
        last_raw = raw.get("last_name", "")
        dob_raw = raw.get("date_of_birth")

        error_codes = []
        error_msgs = []

        # 1. Clean MRN
        mrn_clean = clean_mrn(raw_mrn)
        if not mrn_clean:
            error_codes.append("ERR_INVALID_MRN")
            error_msgs.append(f"Missing or invalid Medical Record Number: '{raw_mrn}'")

        # 2. Clean Names
        first_clean = clean_name_field(first_raw)
        last_clean = clean_name_field(last_raw)
        if not first_clean or not last_clean:
            error_codes.append("ERR_MISSING_NAME")
            error_msgs.append("Patient first name or last name is missing or invalid.")

        # 3. Clean Date of Birth
        dob_clean = clean_date_of_birth(dob_raw)
        if not dob_clean:
            error_codes.append("ERR_INVALID_DOB")
            error_msgs.append(f"Unparseable or out-of-range date of birth: '{dob_raw}'")

        # If any mandatory identity attribute failed -> Quarantine
        if error_codes:
            q_record = QuarantineRecord(
                raw_id=raw_id,
                mrn=raw_mrn,
                error_codes=error_codes,
                error_messages=error_msgs,
                raw_payload=raw,
                quarantine_timestamp=datetime.utcnow().isoformat()
            )
            return None, q_record

        # Clean optional / non-blocking fields
        gender_clean = clean_gender(raw.get("gender"))
        phone_clean = clean_phone_number(raw.get("phone"))
        email_clean = clean_email(raw.get("email"))
        zip_clean = clean_zip_code(raw.get("zip_code"))

        systolic = None
        diastolic = None
        try:
            if raw.get("systolic_bp") is not None and str(raw.get("systolic_bp")).strip():
                val = int(raw.get("systolic_bp"))
                if 50 <= val <= 260:
                    systolic = val
        except (ValueError, TypeError):
            pass

        try:
            if raw.get("diastolic_bp") is not None and str(raw.get("diastolic_bp")).strip():
                val = int(raw.get("diastolic_bp"))
                if 30 <= val <= 160:
                    diastolic = val
        except (ValueError, TypeError):
            pass

        clean_rec = CleanPatientRecord(
            patient_id=f"PAT-{mrn_clean.replace('MRN-', '')}",
            mrn=mrn_clean,
            first_name=first_clean,
            last_name=last_clean,
            full_name=f"{first_clean} {last_clean}",
            date_of_birth=dob_clean,
            gender=gender_clean,
            phone=phone_clean,
            email=email_clean,
            address=str(raw.get("address", "")).strip() or None,
            city=str(raw.get("city", "")).strip() or None,
            state=str(raw.get("state", "")).strip().upper() or None,
            zip_code=zip_clean,
            blood_group=str(raw.get("blood_group", "")).strip() or None,
            systolic_bp=systolic,
            diastolic_bp=diastolic,
            data_quality_score=100.0
        )
        return clean_rec, None

    def run(self, input_csv: Path, output_dir: Path = PROCESSED_DATA_DIR) -> Dict[str, Any]:
        """Execute end-to-end pipeline."""
        print(f"[+] Ingesting data from: {input_csv}")

        raw_records = []
        with open(input_csv, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            raw_records = list(reader)

        total_ingested = len(raw_records)
        candidate_clean: List[CleanPatientRecord] = []
        quarantined: List[QuarantineRecord] = []

        for row in raw_records:
            clean, q = self.process_record(row)
            if clean:
                candidate_clean.append(clean)
            else:
                quarantined.append(q)

        # Apply deduplication on candidate clean records
        print(f"[+] Running demographic & MRN deduplication engine...")
        unique_clean, duplicates_merged = self.deduplicator.deduplicate(candidate_clean)

        # Write clean output
        clean_file = output_dir / "patients_cleaned.csv"
        if unique_clean:
            fieldnames = list(unique_clean[0].model_dump().keys())
            with open(clean_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for rec in unique_clean:
                    writer.writerow(rec.model_dump())
            print(f"[+] Clean dataset saved: {clean_file} ({len(unique_clean)} records)")

        # Write quarantine output
        quarantine_file = QUARANTINE_DATA_DIR / "patients_quarantined.json"
        with open(quarantine_file, "w", encoding="utf-8") as f:
            json.dump([q.model_dump() for q in quarantined], f, indent=2)
        print(f"[+] Quarantined dataset saved: {quarantine_file} ({len(quarantined)} records)")

        # Generate metrics & audit report
        metrics = DataQualityAuditor.calculate_metrics(
            total_ingested=total_ingested,
            clean_records=unique_clean,
            quarantined_records=quarantined,
            duplicates_merged=duplicates_merged
        )

        terminal_report = DataQualityAuditor.format_terminal_report(metrics)
        print(terminal_report)

        report_file = REPORTS_DIR / "quality_audit_summary.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(metrics.model_dump(), f, indent=2)

        return {
            "metrics": metrics.model_dump(),
            "clean_file": str(clean_file),
            "quarantine_file": str(quarantine_file),
            "report_file": str(report_file)
        }
