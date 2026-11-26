
import csv
from pathlib import Path
from collections import defaultdict

# ============================================================
# PROJECT PROOF | INVESTIGATION CASE SUMMARY GENERATOR
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

CASES_FILE = (
    PROJECT_ROOT / "data" / "processed" / "investigation_cases.csv"
)

EVIDENCE_FILE = (
    PROJECT_ROOT / "data" / "processed" / "investigation_evidence.csv"
)

PRIORITY_FILE = (
    PROJECT_ROOT / "data" / "processed" / "investigation_priority_queue.csv"
)

OUTPUT_DIR = PROJECT_ROOT / "reports"
OUTPUT_FILE = OUTPUT_DIR / "investigation_case_summaries.txt"


def load_csv(file_path):
    """Load a CSV file and return its records."""

    if not file_path.exists():
        raise FileNotFoundError(
            f"Required file not found: {file_path}"
        )

    with file_path.open(
        "r",
        newline="",
        encoding="utf-8-sig"
    ) as file:
        return list(csv.DictReader(file))


def format_currency(value):
    """Format a numeric value as South African rand."""

    try:
        return f"R{float(value):,.2f}"
    except (ValueError, TypeError):
        return "Not available"


def build_evidence_lookup(evidence_records):
    """Group evidence records by investigation case."""

    evidence_lookup = defaultdict(list)

    for record in evidence_records:
        case_id = record.get("case_id", "").strip()
        evidence_lookup[case_id].append(record)

    return evidence_lookup


def build_priority_lookup(priority_records):
    """Match each investigation case to its priority information."""

    priority_lookup = {}

    for record in priority_records:
        case_id = record.get("case_id", "").strip()
        priority_lookup[case_id] = record

    return priority_lookup


def generate_case_summary(case, evidence_records, priority):
    """Create a readable summary for one investigation case."""

    case_id = case.get("case_id", "UNKNOWN")
    record_id = case.get("record_id", "Not available")
    record_type = case.get("record_type", "Not available")
    supplier_id = case.get("supplier_id", "Not available")
    supplier_name = case.get("supplier_name", "Not available")

    risk_level = case.get("risk_level", "Not classified")
    risk_score = case.get("risk_score", "Not available")

    financial_difference = format_currency(
        case.get("financial_difference", "")
    )

    order_value_exposure = format_currency(
        case.get("order_value_exposure", "")
    )

    recommended_action = priority.get(
        "recommended_action",
        "Manual review required."
    )

    priority_rank = priority.get(
        "priority_rank",
        "Not ranked"
    )

    lines = [
        "=" * 75,
        f"INVESTIGATION CASE: {case_id}",
        "=" * 75,
        "",
        "CASE INFORMATION",
        "-" * 75,
        f"Record ID: {record_id}",
        f"Record Type: {record_type}",
        f"Supplier ID: {supplier_id}",
        f"Supplier Name: {supplier_name}",
        "",
        "RISK ASSESSMENT",
        "-" * 75,
        f"Risk Level: {risk_level}",
        f"Risk Score: {risk_score}/100",
        f"Priority Rank: {priority_rank}",
        "",
        "FINANCIAL INFORMATION",
        "-" * 75,
        f"Financial Difference: {financial_difference}",
        f"Order Value Exposure: {order_value_exposure}",
        "",
        "DETECTED FINDINGS",
        "-" * 75,
    ]

    if evidence_records:
        for index, evidence in enumerate(evidence_records, start=1):
            issue_type = evidence.get(
                "issue_type",
                "Unspecified finding"
            )

            lines.append(f"{index}. {issue_type}")

            risk_reason = evidence.get("risk_reason", "").strip()

            if risk_reason:
                lines.append(f"   Evidence: {risk_reason}")

    else:
        lines.append("No evidence records were linked to this case.")

    lines.extend([
        "",
        "RECOMMENDED INVESTIGATION ACTION",
        "-" * 75,
        recommended_action,
        "",
        "INVESTIGATION NOTE",
        "-" * 75,
        (
            "This case contains automated findings that require "
            "appropriate human review. An identified discrepancy "
            "or unusual pattern does not, by itself, establish "
            "fraud or confirm a financial loss."
        ),
        "",
    ])

    return "\n".join(lines)


def main():
    print("=" * 75)
    print("PROJECT PROOF | INVESTIGATION CASE SUMMARY GENERATOR")
    print("=" * 75)

    cases = load_csv(CASES_FILE)
    evidence = load_csv(EVIDENCE_FILE)
    priorities = load_csv(PRIORITY_FILE)

    evidence_lookup = build_evidence_lookup(evidence)
    priority_lookup = build_priority_lookup(priorities)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    summaries = []

    for case in cases:
        case_id = case.get("case_id", "").strip()

        case_evidence = evidence_lookup.get(case_id, [])

        priority = priority_lookup.get(case_id, {})

        summary = generate_case_summary(
            case,
            case_evidence,
            priority
        )

        summaries.append(summary)

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8"
    ) as file:
        file.write(
            "PROJECT PROOF | INVESTIGATION CASE SUMMARIES\n"
        )
        file.write("=" * 75 + "\n\n")

        file.write(
            f"Total investigation cases: {len(summaries)}\n"
        )

        file.write(
            f"Total evidence records: {len(evidence)}\n\n"
        )

        file.write(
            "These summaries support investigation and management review.\n\n"
        )

        for summary in summaries:
            file.write(summary)
            file.write("\n")

    print("\nGENERATION SUMMARY")
    print("-" * 75)
    print(f"Investigation cases processed: {len(cases)}")
    print(f"Evidence records loaded: {len(evidence)}")
    print(f"Priority records loaded: {len(priorities)}")
    print(f"Case summaries generated: {len(summaries)}")

    print("\nREPORT GENERATED")
    print("-" * 75)
    print(OUTPUT_FILE.relative_to(PROJECT_ROOT))

    print("\nINVESTIGATION CASE SUMMARY GENERATION: COMPLETED")
    print("=" * 75)


if __name__ == "__main__":
    main()
