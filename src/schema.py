"""Pydantic schemas for patient records and data quality logging."""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator

class RawPatientInput(BaseModel):
    """Raw record as received from heterogeneous hospital EMR feeds."""
    raw_id: Optional[str] = None
    mrn: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    blood_group: Optional[str] = None
    systolic_bp: Optional[Any] = None
    diastolic_bp: Optional[Any] = None

class CleanPatientRecord(BaseModel):
    """Clean, standardized patient record ready for enterprise storage and analytics."""
    patient_id: str
    mrn: str
    first_name: str
    last_name: str
    full_name: str
    date_of_birth: str = Field(description="ISO format: YYYY-MM-DD")
    gender: str = Field(description="M, F, O, or U")
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    blood_group: Optional[str] = None
    systolic_bp: Optional[int] = None
    diastolic_bp: Optional[int] = None
    data_quality_score: float = Field(default=100.0)

class QuarantineRecord(BaseModel):
    """Corrupted or invalid record quarantined for audit and remediation."""
    raw_id: Optional[str]
    mrn: Optional[str]
    error_codes: List[str]
    error_messages: List[str]
    raw_payload: Dict[str, Any]
    quarantine_timestamp: str

class QualityMetricSummary(BaseModel):
    """Audit summary of data cleansing execution."""
    total_ingested: int
    clean_passed: int
    duplicates_merged: int
    quarantined: int
    clean_pass_rate_pct: float
    error_distribution: Dict[str, int]
    avg_quality_score_improvement_pct: float
