"""Command Line Interface for Healthcare Patient Data Pipeline."""
import argparse
from pathlib import Path
from src.config import RAW_DATA_DIR, PROCESSED_DATA_DIR
from src.generator import generate_dirty_patient_dataset
from src.pipeline import PatientDataPipeline

def main():
    parser = argparse.ArgumentParser(description="Healthcare Patient Data Cleansing & Normalization Pipeline")
    parser.add_argument("--generate-sample", type=int, default=500, help="Number of dirty sample records to generate")
    parser.add_argument("--input", type=str, default=None, help="Path to input raw CSV file")
    parser.add_argument("--output-dir", type=str, default=str(PROCESSED_DATA_DIR), help="Output directory for clean records")

    args = parser.parse_args()

    input_path = args.input
    if not input_path:
        sample_path = RAW_DATA_DIR / "raw_emr_patients.csv"
        print(f"[*] Generating {args.generate_sample} synthetic raw patient records with deliberate defects...")
        generate_dirty_patient_dataset(num_records=args.generate_sample, dirty_rate=0.35, output_file=sample_path)
        input_path = sample_path
    else:
        input_path = Path(input_path)

    pipeline = PatientDataPipeline()
    pipeline.run(input_csv=input_path, output_dir=Path(args.output_dir))

if __name__ == "__main__":
    main()
