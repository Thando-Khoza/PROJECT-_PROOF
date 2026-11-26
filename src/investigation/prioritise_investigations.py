
import csv
from pathlib import Path


# ============================================================
# PROJECT PROOF | INVESTIGATION PRIORITISATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

INPUT_FILE = PROCESSED_DIR / "investigation_cases.csv"
OUTPUT_FILE = PROCESSED_DIR / "investigation_priority_queue.csv"


RISK_PRIORITY = {
    "HIGH": 1,
    "MEDIUM": 2,
    "LOW": 3,
}


RECOMMENDED_ACTIONS = {
    "OVERPAYMENT":
        "Review payment records and verify the excess amount.",

    "SUPPLIER_MISMATCH":
        "Verify supplier identity across purchase orders and invoices.",

    "PRICE_DISCREPANCY":
        "Compare invoice prices against authorised purchase order prices.",

    "QUANTITY_DISCREPANCY":
        "Verify invoiced quantities against authorised order quantities.",

    "DUPLICATE_INVOICE":
        "Investigate repeated invoice numbers and confirm whether duplicate billing occurred.",

    "UNMATCHED_INVOICE":
        "Locate supporting purchase order documentation for the invoice.",

    "UNMATCHED_PAYMENT":
        "Identify the invoice or supporting document associated with the payment.",

    "UNDERPAYMENT":
        "Compare the payment amount with the invoice amount and investigate the difference.",

    "HIGH_VALUE_ORDER":
        "Review purchase order approval and supporting procurement documentation.",

    "UNUSUAL_ORDER_VALUE":
        "Review the unusual order value against supplier history and supporting documentation.",
}


def load_cases():
    """Load consolidated investigation cases."""

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Investigation cases not found: {INPUT_FILE}"
        )

    with open(
        INPUT_FILE,
        "r",
        newline="",
        encoding="utf-8-sig"
    ) as file:

        return list(csv.DictReader(file))


def determine_recommended_action(issue_types):
    """Generate investigation actions from detected issue types."""

    issues = [
        issue.strip()
        for issue in issue_types.split("|")
        if issue.strip()
    ]

    actions = []

    for issue in issues:
        action = RECOMMENDED_ACTIONS.get(issue)

        if action and action not in actions:
            actions.append(action)

    if not actions:
        return "Review the available evidence and determine the next investigation step."

    return " | ".join(actions)


def determine_priority_reason(case):
    """Explain why a case has its position in the queue."""

    risk_level = case["risk_level"]
    score = float(case["risk_score"])
    financial_difference = float(
        case.get("financial_difference") or 0
    )
    order_value = float(
        case.get("order_value_exposure") or 0
    )

    reasons = [
        f"{risk_level} risk classification",
        f"Risk score: {score:.0f}/100",
    ]

    if financial_difference > 0:
        reasons.append(
            f"Financial discrepancy: R{financial_difference:,.2f}"
        )

    if order_value > 0:
        reasons.append(
            f"Purchase order value: R{order_value:,.2f}"
        )

    return " | ".join(reasons)


def build_priority_queue(cases):
    """Rank investigation cases by risk and financial exposure."""

    prioritised = []

    for case in cases:

        case_copy = dict(case)

        case_copy["risk_score"] = float(
            case["risk_score"]
        )

        case_copy["financial_difference"] = float(
            case.get("financial_difference") or 0
        )

        case_copy["order_value_exposure"] = float(
            case.get("order_value_exposure") or 0
        )

        case_copy["risk_priority"] = RISK_PRIORITY.get(
            case["risk_level"],
            4
        )

        prioritised.append(case_copy)

    # Risk classification comes first.
    # Risk score breaks ties.
    # Financial exposure breaks remaining ties.
    prioritised.sort(
        key=lambda case: (
            case["risk_priority"],
            -case["risk_score"],
            -max(
                case["financial_difference"],
                case["order_value_exposure"]
            ),
        )
    )

    priority_queue = []

    for rank, case in enumerate(prioritised, start=1):

        priority_queue.append({
            "priority_rank": rank,
            "case_id": case["case_id"],
            "record_type": case["record_type"],
            "record_id": case["record_id"],
            "supplier_ids": case["supplier_ids"],
            "issue_types": case["issue_types"],
            "risk_level": case["risk_level"],
            "risk_score": case["risk_score"],
            "financial_difference": case["financial_difference"],
            "order_value_exposure": case["order_value_exposure"],
            "finding_count": case["finding_count"],
            "priority_reason": determine_priority_reason(case),
            "recommended_action": determine_recommended_action(
                case["issue_types"]
            ),
            "investigation_status": "OPEN",
        })

    return priority_queue


def export_priority_queue(records):
    """Save the prioritised investigation queue."""

    if not records:
        raise ValueError(
            "No investigation cases available for prioritisation."
        )

    with open(
        OUTPUT_FILE,
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=list(records[0].keys())
        )

        writer.writeheader()
        writer.writerows(records)


def main():

    print("=" * 70)
    print("PROJECT PROOF | INVESTIGATION PRIORITY QUEUE")
    print("=" * 70)

    cases = load_cases()

    priority_queue = build_priority_queue(cases)

    export_priority_queue(priority_queue)

    print("\nPRIORITISATION SUMMARY")
    print("-" * 70)

    print(f"Cases prioritised: {len(priority_queue)}")

    for level in ["HIGH", "MEDIUM", "LOW"]:

        count = sum(
            1 for case in priority_queue
            if case["risk_level"] == level
        )

        print(f"{level} risk cases: {count}")

    print("\nTOP 10 INVESTIGATION PRIORITIES")
    print("-" * 70)

    for case in priority_queue[:10]:

        print(
            f"#{case['priority_rank']} | "
            f"{case['case_id']} | "
            f"{case['record_id']} | "
            f"{case['risk_level']} | "
            f"Score: {case['risk_score']:.0f}"
        )

    print("\nOUTPUT FILE")
    print("-" * 70)

    print(OUTPUT_FILE.relative_to(PROJECT_ROOT))

    print("\nINVESTIGATION PRIORITISATION: COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    main()
