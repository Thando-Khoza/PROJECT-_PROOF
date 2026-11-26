
import csv
from pathlib import Path
from datetime import datetime
from collections import defaultdict


# ============================================================
# PROJECT PROOF | MANAGEMENT INVESTIGATION REPORT
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
REPORT_DIR = PROJECT_ROOT / "reports"

CASES_FILE = PROCESSED_DIR / "investigation_cases.csv"
QUEUE_FILE = PROCESSED_DIR / "investigation_priority_queue.csv"

REPORT_FILE = REPORT_DIR / "investigation_management_report.txt"


def load_csv(file_path):
    """Load records from a CSV file."""

    if not file_path.exists():
        raise FileNotFoundError(
            f"Required input file not found: {file_path}"
        )

    with open(
        file_path,
        "r",
        newline="",
        encoding="utf-8-sig"
    ) as file:

        return list(csv.DictReader(file))


def calculate_risk_distribution(cases):
    """Count cases by risk classification."""

    distribution = defaultdict(int)

    for case in cases:
        distribution[case["risk_level"]] += 1

    return distribution


def calculate_issue_distribution(cases):
    """Count unique investigation cases by issue type."""

    distribution = defaultdict(int)

    for case in cases:
        issue_types = [
            issue.strip()
            for issue in case["issue_types"].split("|")
            if issue.strip()
        ]

        for issue in issue_types:
            distribution[issue] += 1

    return distribution


def calculate_financial_summary(cases):
    """Calculate recorded discrepancies and order values."""

    financial_differences = [
        float(case.get("financial_difference") or 0)
        for case in cases
    ]

    order_values = [
        float(case.get("order_value_exposure") or 0)
        for case in cases
    ]

    return {
        "total_discrepancies": sum(financial_differences),
        "largest_discrepancy": max(
            financial_differences,
            default=0
        ),
        "total_order_value": sum(order_values),
        "largest_order_value": max(
            order_values,
            default=0
        ),
    }


def format_currency(amount):
    """Format a financial amount in South African rand."""

    return f"R{amount:,.2f}"


def build_report(cases, priority_queue):
    """Build the complete management report."""

    risk_distribution = calculate_risk_distribution(cases)
    issue_distribution = calculate_issue_distribution(cases)
    financial_summary = calculate_financial_summary(cases)

    high_risk_cases = [
        case for case in priority_queue
        if case["risk_level"] == "HIGH"
    ]

    lines = []

    lines.append("=" * 75)
    lines.append("PROJECT PROOF")
    lines.append("FINANCIAL VERIFICATION | INVESTIGATION MANAGEMENT REPORT")
    lines.append("=" * 75)

    lines.append(
        f"Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )

    lines.append("\n1. EXECUTIVE SUMMARY")
    lines.append("-" * 75)

    lines.append(f"Investigation cases: {len(cases)}")
    lines.append(f"High-risk cases: {risk_distribution['HIGH']}")
    lines.append(f"Medium-risk cases: {risk_distribution['MEDIUM']}")
    lines.append(f"Low-risk cases: {risk_distribution['LOW']}")

    lines.append("\n2. FINANCIAL OVERVIEW")
    lines.append("-" * 75)

    lines.append(
        "Recorded financial discrepancies: "
        + format_currency(
            financial_summary["total_discrepancies"]
        )
    )

    lines.append(
        "Largest individual discrepancy: "
        + format_currency(
            financial_summary["largest_discrepancy"]
        )
    )

    lines.append(
        "Combined value of flagged purchase orders: "
        + format_currency(
            financial_summary["total_order_value"]
        )
    )

    lines.append(
        "Largest flagged purchase order: "
        + format_currency(
            financial_summary["largest_order_value"]
        )
    )

    lines.append("\n3. RISK DISTRIBUTION")
    lines.append("-" * 75)

    for level in ["HIGH", "MEDIUM", "LOW"]:
        count = risk_distribution[level]

        percentage = (
            count / len(cases) * 100
            if cases else 0
        )

        lines.append(
            f"{level}: {count} cases ({percentage:.1f}%)"
        )

    lines.append("\n4. FINDINGS BY ISSUE TYPE")
    lines.append("-" * 75)

    for issue, count in sorted(
        issue_distribution.items(),
        key=lambda item: item[1],
        reverse=True
    ):

        lines.append(f"{issue}: {count} cases")

    lines.append("\n5. HIGH-PRIORITY INVESTIGATIONS")
    lines.append("-" * 75)

    for case in high_risk_cases:

        lines.append(
            f"\nPriority #{case['priority_rank']} | "
            f"{case['case_id']}"
        )

        lines.append(
            f"Record: {case['record_id']}"
        )

        lines.append(
            f"Risk score: {float(case['risk_score']):.0f}/100"
        )

        lines.append(
            f"Issues: {case['issue_types']}"
        )

        lines.append(
            f"Recommended action: {case['recommended_action']}"
        )

    lines.append("\n6. MANAGEMENT OBSERVATIONS")
    lines.append("-" * 75)

    lines.append(
        f"{risk_distribution['HIGH']} cases require priority review "
        "under the current risk classification model."
    )

    lines.append(
        "Investigation cases consolidate related detection alerts "
        "to reduce duplicate case handling."
    )

    lines.append(
        "Original finding records are retained separately as "
        "supporting investigation evidence."
    )

    lines.append(
        "Automated findings indicate potential issues requiring "
        "human review; they do not establish fraud or misconduct."
    )

    lines.append("\n7. REPORTING NOTES")
    lines.append("-" * 75)

    lines.append(
        "Financial discrepancies and purchase order values are "
        "reported as separate measures."
    )

    lines.append(
        "The combined flagged purchase order value is not a "
        "confirmed financial loss."
    )

    lines.append(
        "Risk scores are based on the project's configured "
        "prioritisation rules."
    )

    lines.append(
        "This report reflects the current generated dataset "
        "and available investigation outputs."
    )

    lines.append("\n" + "=" * 75)
    lines.append("END OF REPORT")
    lines.append("=" * 75)

    return "\n".join(lines)


def main():

    print("=" * 75)
    print("PROJECT PROOF | MANAGEMENT REPORT GENERATOR")
    print("=" * 75)

    REPORT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    cases = load_csv(CASES_FILE)
    priority_queue = load_csv(QUEUE_FILE)

    report = build_report(
        cases,
        priority_queue
    )

    with open(
        REPORT_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(report)

    print("\nREPORT SUMMARY")
    print("-" * 75)

    print(f"Investigation cases: {len(cases)}")
    print(f"Priority records: {len(priority_queue)}")

    print("\nREPORT GENERATED")
    print("-" * 75)

    print(REPORT_FILE.relative_to(PROJECT_ROOT))

    print("\nMANAGEMENT REPORT GENERATION: COMPLETED")
    print("=" * 75)


if __name__ == "__main__":
    main()
