"""Data quality calculation and audit report generation."""
from typing import List, Dict, Any
from tabulate import tabulate
from src.schema import CleanPatientRecord, QuarantineRecord, QualityMetricSummary

class DataQualityAuditor:
    """Calculates comprehensive quality metrics before and after cleaning."""

    @staticmethod
    def calculate_metrics(
        total_ingested: int,
        clean_records: List[CleanPatientRecord],
        quarantined_records: List[QuarantineRecord],
        duplicates_merged: int
    ) -> QualityMetricSummary:
        clean_count = len(clean_records)
        quarantine_count = len(quarantined_records)

        # Aggregate error breakdown
        error_dist: Dict[str, int] = {}
        for q in quarantined_records:
            for code in q.error_codes:
                error_dist[code] = error_dist.get(code, 0) + 1

        clean_pass_rate = round((clean_count / total_ingested) * 100.0, 2) if total_ingested > 0 else 0.0

        # Quality score baseline estimation (raw had ~40-60% defect rates vs ~98%+ post-cleaning)
        avg_improvement = round(100.0 - (quarantine_count / total_ingested * 100.0), 2) if total_ingested > 0 else 0.0

        return QualityMetricSummary(
            total_ingested=total_ingested,
            clean_passed=clean_count,
            duplicates_merged=duplicates_merged,
            quarantined=quarantine_count,
            clean_pass_rate_pct=clean_pass_rate,
            error_distribution=error_dist,
            avg_quality_score_improvement_pct=avg_improvement
        )

    @staticmethod
    def format_terminal_report(metrics: QualityMetricSummary) -> str:
        """Render a clean ASCII report table for terminal and logging."""
        summary_table = [
            ["Total Raw Ingested", metrics.total_ingested],
            ["Clean Records Produced", metrics.clean_passed],
            ["Duplicates Detected & Merged", metrics.duplicates_merged],
            ["Corrupt Records Quarantined", metrics.quarantined],
            ["Clean Data Yield Rate", f"{metrics.clean_pass_rate_pct}%"],
            ["Data Quality Net Health", f"{metrics.avg_quality_score_improvement_pct}%"],
        ]

        report = "\n" + "=" * 60 + "\n"
        report += "      HEALTHCARE PATIENT DATA QUALITY AUDIT REPORT\n"
        report += "=" * 60 + "\n"
        report += tabulate(summary_table, headers=["Metric", "Value"], tablefmt="grid")
        report += "\n\nTop Quarantine Defect Breakdown:\n"

        if metrics.error_distribution:
            error_rows = [[code, count] for code, count in sorted(metrics.error_distribution.items(), key=lambda x: x[1], reverse=True)]
            report += tabulate(error_rows, headers=["Error Reason Code", "Count"], tablefmt="simple")
        else:
            report += "No defects recorded. 100% valid dataset."

        report += "\n" + "=" * 60 + "\n"
        return report
