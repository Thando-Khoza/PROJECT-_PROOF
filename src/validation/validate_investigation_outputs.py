
import csv
from pathlib import Path


# ============================================================
# PROJECT CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
REPORT_DIR = PROJECT_ROOT / "reports"

CASES_FILE = PROCESSED_DIR / "investigation_cases.csv"
EVIDENCE_FILE = PROCESSED_DIR / "investigation_evidence.csv"
QUEUE_FILE = PROCESSED_DIR / "investigation_priority_queue.csv"
MANAGEMENT_REPORT = REPORT_DIR / "investigation_management_report.txt"

VALIDATION_RESULTS_FILE = (
    PROCESSED_DIR / "investigation_validation_results.csv"
)


# ============================================================
# DATA LOADING
# ============================================================

def load_csv(file_path):
    """Load a CSV file and return its records."""

    if not file_path.exists():
        return None

    with open(file_path, "r", newline="", encoding="utf-8-sig") as file:
        return list(csv.DictReader(file))


def add_check(results, name, passed, details):
    """Record one validation result."""

    results.append({
        "check": name,
        "status": "PASS" if passed else "FAIL",
        "details": details
    })


# ============================================================
# VALIDATION
# ============================================================

def validate_outputs():

    results = []

    cases = load_csv(CASES_FILE)
    evidence = load_csv(EVIDENCE_FILE)
    queue = load_csv(QUEUE_FILE)

    # --------------------------------------------------------
    # 1. FILE EXISTENCE
    # --------------------------------------------------------

    required_files = [
        CASES_FILE,
        EVIDENCE_FILE,
        QUEUE_FILE,
        MANAGEMENT_REPORT
    ]

    missing_files = [
        str(path.relative_to(PROJECT_ROOT))
        for path in required_files
        if not path.exists()
    ]

    add_check(
        results,
        "Required output files",
        len(missing_files) == 0,
        (
            "All four output files exist."
            if not missing_files
            else f"Missing files: {missing_files}"
        )
    )

    # --------------------------------------------------------
    # 2. DATA AVAILABILITY
    # --------------------------------------------------------

    data_available = (
        cases is not None
        and evidence is not None
        and queue is not None
    )

    add_check(
        results,
        "CSV data availability",
        data_available,
        (
            "All three investigation CSV files were loaded."
            if data_available
            else "One or more CSV files could not be loaded."
        )
    )

    if not data_available:
        return results

    case_ids = {
        row.get("case_id", "").strip()
        for row in cases
    }

    evidence_case_ids = {
        row.get("case_id", "").strip()
        for row in evidence
    }

    queue_case_ids = {
        row.get("case_id", "").strip()
        for row in queue
    }

    # --------------------------------------------------------
    # 3. CASE ID UNIQUENESS
    # --------------------------------------------------------

    unique_case_ids = (
        len(case_ids) == len(cases)
        and "" not in case_ids
    )

    add_check(
        results,
        "Unique investigation case IDs",
        unique_case_ids,
        f"{len(cases)} cases; {len(case_ids)} unique IDs."
    )

    # --------------------------------------------------------
    # 4. EVIDENCE PRESERVATION
    # --------------------------------------------------------

    evidence_matches = (
        evidence_case_ids.issubset(case_ids)
        and len(evidence) > 0
    )

    add_check(
        results,
        "Evidence linked to valid cases",
        evidence_matches,
        (
            f"{len(evidence)} evidence records checked."
            if evidence_matches
            else "Evidence contains missing or invalid case references."
        )
    )

    evidence_counts = {}

    for row in evidence:
        case_id = row.get("case_id", "").strip()
        evidence_counts[case_id] = (
            evidence_counts.get(case_id, 0) + 1
        )

    finding_counts_match = True

    for case in cases:
        case_id = case.get("case_id", "").strip()

        try:
            expected_count = int(case.get("finding_count", ""))
        except (ValueError, TypeError):
            finding_counts_match = False
            break

        actual_count = evidence_counts.get(case_id, 0)

        if expected_count != actual_count:
            finding_counts_match = False
            break

    add_check(
        results,
        "Finding counts match preserved evidence",
        finding_counts_match,
        (
            "Every case's finding count matches its evidence records."
            if finding_counts_match
            else "At least one case has an incorrect evidence count."
        )
    )

    # --------------------------------------------------------
    # 5. RISK SCORE VALIDATION
    # --------------------------------------------------------

    valid_scores = True

    for case in cases:
        try:
            score = float(case.get("risk_score", ""))

            if not 0 <= score <= 100:
                valid_scores = False
                break

        except (ValueError, TypeError):
            valid_scores = False
            break

    add_check(
        results,
        "Risk scores within valid range",
        valid_scores,
        (
            "All risk scores are numeric and between 0 and 100."
            if valid_scores
            else "Invalid or out-of-range risk score detected."
        )
    )

    # --------------------------------------------------------
    # 6. RISK CLASSIFICATION VALIDATION
    # --------------------------------------------------------

    valid_classifications = True

    for case in cases:
        try:
            score = float(case.get("risk_score", ""))
            level = case.get("risk_level", "").strip().upper()

        except (ValueError, TypeError):
            valid_classifications = False
            break

        expected_level = (
            "HIGH" if score >= 70
            else "MEDIUM" if score >= 35
            else "LOW"
        )

        if level != expected_level:
            valid_classifications = False
            break

    add_check(
        results,
        "Risk classification consistency",
        valid_classifications,
        (
            "Risk levels match the configured scoring thresholds."
            if valid_classifications
            else "At least one risk level does not match its score."
        )
    )

    # --------------------------------------------------------
    # 7. PRIORITY QUEUE COMPLETENESS
    # --------------------------------------------------------

    queue_complete = (
        len(queue) == len(cases)
        and queue_case_ids == case_ids
        and "" not in queue_case_ids
    )

    add_check(
        results,
        "Priority queue completeness",
        queue_complete,
        (
            f"All {len(cases)} cases appear exactly once in the queue."
            if queue_complete
            else "Cases are missing, duplicated or incorrectly referenced."
        )
    )

    # --------------------------------------------------------
    # 8. PRIORITY RANK VALIDATION
    # --------------------------------------------------------

    rank_column = next(
        (
            column
            for column in ("priority_rank", "priority_order", "rank")
            if queue and column in queue[0]
        ),
        None
    )

    valid_ranks = False

    if rank_column:
        try:
            ranks = [
                int(row[rank_column])
                for row in queue
            ]

            valid_ranks = (
                len(ranks) == len(set(ranks))
                and sorted(ranks) == list(range(1, len(queue) + 1))
            )

        except (ValueError, TypeError):
            valid_ranks = False

    add_check(
        results,
        "Unique and complete priority ranks",
        valid_ranks,
        (
            f"Priority ranks run from 1 to {len(queue)}."
            if valid_ranks
            else "Priority ranks are missing, duplicated or invalid."
        )
    )

    # --------------------------------------------------------
    # 9. MANAGEMENT REPORT VALIDATION
    # --------------------------------------------------------

    report_valid = False

    if MANAGEMENT_REPORT.exists():
        report_text = MANAGEMENT_REPORT.read_text(
            encoding="utf-8-sig"
        ).upper()

        required_sections = [
            "EXECUTIVE SUMMARY",
            "FINANCIAL OVERVIEW",
            "RISK DISTRIBUTION",
            "HIGH-PRIORITY"
        ]

        report_valid = (
            len(report_text.strip()) > 0
            and all(section in report_text for section in required_sections)
        )

    add_check(
        results,
        "Management report completeness",
        report_valid,
        (
            "Report exists and contains the required sections."
            if report_valid
            else "Report is empty or one or more required sections are missing."
        )
    )

    return results


# ============================================================
# VALIDATION REPORT
# ============================================================

def main():

    print("=" * 70)
    print("PROJECT PROOF | INVESTIGATION OUTPUT VALIDATION")
    print("=" * 70)

    results = validate_outputs()

    print("\nVALIDATION RESULTS")
    print("-" * 70)

    for result in results:
        print(
            f"{result['status']}: {result['check']}"
        )
        print(f"       {result['details']}")

    passed = sum(
        result["status"] == "PASS"
        for result in results
    )

    failed = sum(
        result["status"] == "FAIL"
        for result in results
    )

    # Save validation results
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    with open(
        VALIDATION_RESULTS_FILE,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=["check", "status", "details"]
        )

        writer.writeheader()
        writer.writerows(results)

    print("\nVALIDATION SUMMARY")
    print("-" * 70)
    print(f"Checks performed: {len(results)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")

    print(
        f"\nValidation results saved to:\n"
        f"{VALIDATION_RESULTS_FILE.relative_to(PROJECT_ROOT)}"
    )

    if failed:
        print("\nINVESTIGATION OUTPUT VALIDATION: FAILED")
        raise SystemExit(1)

    print("\nINVESTIGATION OUTPUT VALIDATION: ALL CHECKS PASSED")


if __name__ == "__main__":
    main()
