"""
Healthcare Patient Data Cleansing, Normalization & Deduplication Web Application.
Interactive live dashboard for hospital data engineering teams.
"""
import streamlit as st
import pandas as pd
import json
import tempfile
from pathlib import Path

from src.pipeline import PatientDataPipeline
from src.generator import generate_dirty_patient_dataset
from src.cleaners import (
    clean_date_of_birth, clean_phone_number, clean_name_field,
    clean_gender, clean_zip_code, clean_mrn, clean_email
)

st.set_page_config(
    page_title="EHRClean | Patient Data Cleansing & Deduplication",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🏥 EHRClean: Patient Data Cleansing & Deduplication Hub")
st.caption("Standardize Fragmented EMR Demographics, Enforce Pydantic Schemas, Quarantine Defects & Deduplicate Patient Records")

# Sidebar Configuration
st.sidebar.header("📁 Ingestion Settings")
source_option = st.sidebar.radio(
    "Select Input Feed:",
    ["Generate Synthetic EMR Batch (Demo)", "Upload Raw Patient CSV"]
)

raw_df = None

if source_option == "Generate Synthetic EMR Batch (Demo)":
    count = st.sidebar.slider("Number of Patient Records", min_value=50, max_value=500, value=150, step=25)
    defect_rate = st.sidebar.slider("Simulated Defect Rate", min_value=0.10, max_value=0.50, value=0.30, step=0.05)
    if st.sidebar.button("⚡ Generate & Execute Pipeline", use_container_width=True):
        with st.spinner("Generating raw dirty EMR records..."):
            with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
                generate_dirty_patient_dataset(num_records=count, dirty_rate=defect_rate, output_file=Path(tmp.name))
                raw_df = pd.read_csv(tmp.name)
                st.session_state["raw_patients_df"] = raw_df
                st.session_state["patients_tmp_csv"] = tmp.name

else:
    uploaded = st.sidebar.file_uploader("Upload Patient EMR CSV", type=["csv"])
    if uploaded is not None:
        raw_df = pd.read_csv(uploaded)
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
            raw_df.to_csv(tmp.name, index=False)
            st.session_state["raw_patients_df"] = raw_df
            st.session_state["patients_tmp_csv"] = tmp.name

# Check session state
if "raw_patients_df" in st.session_state and "patients_tmp_csv" in st.session_state:
    raw_df = st.session_state["raw_patients_df"]
    tmp_path = st.session_state["patients_tmp_csv"]

    pipeline = PatientDataPipeline()
    with tempfile.TemporaryDirectory() as out_dir:
        results = pipeline.run(input_csv=Path(tmp_path), output_dir=Path(out_dir))
        metrics = results["metrics"]

        # Top KPI Scorecards
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            st.metric("Total Raw Ingested", f"{metrics['total_ingested']:,}")
        with c2:
            st.metric("Clean Golden Records", f"{metrics['clean_passed']:,}")
        with c3:
            st.metric("Duplicates Merged", f"{metrics['duplicates_merged']:,}")
        with c4:
            st.metric("Quarantined Corrupted", f"{metrics['quarantined']:,}", delta=f"{metrics['quarantined']} rejected", delta_color="inverse")
        with c5:
            st.metric("Data Quality Health", f"{metrics['avg_quality_score_improvement_pct']}%")

        st.markdown("---")

        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 Data Quality Audit",
            "👥 Clean Golden Records",
            "🚫 Quarantined Defects",
            "⚡ Live Cleanser Playground"
        ])

        with tab1:
            st.subheader("Data Quality Health & Error Taxonomy")
            col_a, col_b = st.columns([1, 1])
            with col_a:
                st.markdown("### Top Quarantine Failure Reasons")
                if metrics["error_distribution"]:
                    err_df = pd.DataFrame(
                        list(metrics["error_distribution"].items()),
                        columns=["Defect Code", "Records Affected"]
                    ).sort_values(by="Records Affected", ascending=False)
                    st.bar_chart(err_df.set_index("Defect Code"))
                else:
                    st.success("Zero defects! All records conformed to schema.")

            with col_b:
                st.markdown("### Pipeline Yield Summary")
                summary_data = {
                    "Stage": ["Total Ingested", "Clean Golden Profiles", "Duplicates Merged", "Quarantined Corrupt"],
                    "Count": [metrics["total_ingested"], metrics["clean_passed"], metrics["duplicates_merged"], metrics["quarantined"]]
                }
                st.dataframe(pd.DataFrame(summary_data), use_container_width=True)
                st.info(f"💡 **Quality Benchmark:** Clean data yield is **{metrics['clean_pass_rate_pct']}%** after applying automated normalization and hybrid deduplication.")

        with tab2:
            st.subheader("Clean Golden Patient Records (Enterprise Standardized)")
            if Path(results["clean_file"]).exists():
                clean_df = pd.read_csv(results["clean_file"])
                st.dataframe(clean_df, use_container_width=True)
                csv_bytes = clean_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download Clean Patients CSV",
                    data=csv_bytes,
                    file_name="clean_golden_patient_records.csv",
                    mime="text/csv",
                    type="primary"
                )

        with tab3:
            st.subheader("Quarantine Ledger (Audit & Remediation Queue)")
            if Path(results["quarantine_file"]).exists():
                with open(results["quarantine_file"], "r", encoding="utf-8") as f:
                    q_data = json.load(f)
                if q_data:
                    q_table = []
                    for item in q_data:
                        q_table.append({
                            "Raw ID": item.get("raw_id"),
                            "MRN": item.get("mrn"),
                            "Error Codes": ", ".join(item.get("error_codes", [])),
                            "Error Messages": " | ".join(item.get("error_messages", []))
                        })
                    st.dataframe(pd.DataFrame(q_table), use_container_width=True)
                    json_str = json.dumps(q_data, indent=2).encode('utf-8')
                    st.download_button(
                        label="📥 Download Quarantine Audit JSON",
                        data=json_str,
                        file_name="quarantined_patient_defects.json",
                        mime="application/json"
                    )

        with tab4:
            st.subheader("Interactive Normalization Playground")
            st.caption("Test individual field cleaners in real-time on dirty inputs.")
            p1, p2 = st.columns(2)
            with p1:
                test_name = st.text_input("Raw Name Field:", value="Dr. Robert Smith Jr., MD")
                test_dob = st.text_input("Raw Date of Birth:", value="10/24/1984")
                test_phone = st.text_input("Raw Phone Number:", value="(555) 349-1092")
            with p2:
                test_gender = st.text_input("Raw Gender:", value="Female / Woman")
                test_mrn = st.text_input("Raw MRN:", value="001928374")
                test_zip = st.text_input("Raw ZIP:", value="90210-4421")

            st.markdown("### Normalized Output:")
            st.json({
                "Clean Full Name": clean_name_field(test_name),
                "ISO 8601 DOB": clean_date_of_birth(test_dob),
                "E.164 Phone": clean_phone_number(test_phone),
                "HL7/FHIR Gender": clean_gender(test_gender),
                "Standard MRN": clean_mrn(test_mrn),
                "Standard ZIP": clean_zip_code(test_zip)
            })

else:
    st.info("👈 Choose **'Generate Synthetic EMR Batch'** or upload your patient CSV in the sidebar to run the cleaning pipeline!")
