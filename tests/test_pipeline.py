"""End-to-end integration tests for patient data pipeline."""
from pathlib import Path
from src.pipeline import PatientDataPipeline
from src.generator import generate_dirty_patient_dataset

def test_pipeline_execution(tmp_path):
    # Generate small dirty dataset
    raw_file = tmp_path / "raw_test_patients.csv"
    generate_dirty_patient_dataset(num_records=50, dirty_rate=0.3, output_file=raw_file)

    pipeline = PatientDataPipeline()
    results = pipeline.run(input_csv=raw_file, output_dir=tmp_path)

    assert "metrics" in results
    assert results["metrics"]["total_ingested"] >= 50
    assert results["metrics"]["clean_passed"] > 0
    assert Path(results["clean_file"]).exists()
    assert Path(results["quarantine_file"]).exists()
