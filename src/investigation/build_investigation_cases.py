
import csv
import json
from pathlib import Path
from collections import defaultdict


# ============================================================
# PROJECT PROOF | INVESTIGATION CASE BUILDER
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

INPUT_FILES = [
    "invoice_findings.csv",
    "payment_findings.csv",
    "high_value_order_findings.csv",
    "unusual_order_findings.csv",
]

OUTPUT_FILE = PROCESSED_DIR / "investigation_cases.csv"
EVIDENCE_FILE = PROCESSED_DIR / "investigation_evidence.csv"

RISK_WEIGHTS = {
    "OVERPAYMENT": 45,
    "SUPPLIER_MISMATCH": 45,
    "PRICE_DISCREPANCY": 40,
    "DUPLICATE_INVOICE": 40,
    "QUANTITY_DISCREPANCY": 35,
    "UNMATCHED_INVOICE": 30,
    "UNMATCHED_PAYMENT": 30,
    "UNUSUAL_ORDER_VALUE": 30,
    "HIGH_VALUE_ORDER": 35,
    "UNDERPAYMENT": 25,
}

HIGH_RISK_THRESHOLD = 70
MEDIUM_RISK_THRESHOLD = 35

DETECTOR_HIGH_RISK_FLOOR = 70


def load_findings():
    """Load findings from all four detection outputs."""

    all_findings = []

    for filename in INPUT_FILES:
        file_path = PROCESSED_DIR / filename

        if not file_path.exists():
            raise FileNotFoundError(
                f"Required findings file not found: {file_path}"
            )

        with open(
            file_path,
            "r",
            newline="",
            encoding="utf-8-sig"
        ) as file:

            reader = csv.DictReader(file)

            for row in reader:
                row["source_file"] = filename
                all_findings.append(row)

    return all_findings


def normalise_record_type(value):
    return str(value or "UNKNOWN").strip().upper()


def normalise_record_id(value):
    return str(value or "UNKNOWN").strip().upper()


def get_numeric_value(value):
    """Convert a value into a number safely."""

    try:
        return abs(float(value))
    except (TypeError, ValueError):
        return 0.0


def calculate_financial_difference(findings):
    """
    Find the largest recorded financial discrepancy
    within an investigation case.
    """

    differences = [
        get_numeric_value(item.get("difference"))
        for item in findings
    ]

    return max(differences, default=0.0)


def calculate_order_value(findings):
    """Retrieve the largest purchase order value in a case."""

    values = [
        get_numeric_value(item.get("order_value"))
        for item in findings
    ]

    return max(values, default=0.0)


def calculate_exposure_bonus(amount):
    """Assign additional points based on financial discrepancy."""

    if amount >= 100000:
        return 20
    elif amount >= 50000:
        return 15
    elif amount >= 10000:
        return 10
    elif amount >= 5000:
        return 5

    return 0


def calculate_order_value_bonus(amount):
    """Prioritise larger purchase order values for review."""

    if amount >= 1000000:
        return 20
    elif amount >= 500000:
        return 15
    elif amount >= 100000:
        return 10

    return 5


def calculate_risk_score(findings):
    """Calculate a transparent risk score for an investigation case."""

    issue_types = {
        str(item.get("issue_type", "UNKNOWN")).strip().upper()
        for item in findings
    }

    base_score = sum(
        RISK_WEIGHTS.get(issue, 20)
        for issue in issue_types
    )

    # Additional independent detection signals.
    corroboration_bonus = (
        5 if len(issue_types) >= 2 else 0
    )

    financial_difference = calculate_financial_difference(
        findings
    )

    order_value = calculate_order_value(findings)

    financial_exposure_bonus = calculate_exposure_bonus(
        financial_difference
    )

    order_value_bonus = (
        calculate_order_value_bonus(order_value)
        if order_value > 0
        else 0
    )

    # Carry forward an existing HIGH classification
    # from an upstream detection module.
    inherited_high_risk = any(
        str(item.get("risk_level", "")).strip().upper() == "HIGH"
        for item in findings
    )

    calculated_score = (
        base_score
        + corroboration_bonus
        + financial_exposure_bonus
        + order_value_bonus
    )

    if inherited_high_risk:
        calculated_score = max(
            calculated_score,
            DETECTOR_HIGH_RISK_FLOOR
        )

    final_score = min(100, calculated_score)

    return {
        "risk_score": final_score,
        "base_score": base_score,
        "corroboration_bonus": corroboration_bonus,
        "financial_exposure_bonus": financial_exposure_bonus,
        "order_value_bonus": order_value_bonus,
        "inherited_high_risk": inherited_high_risk,
        "financial_difference": financial_difference,
        "order_value_exposure": order_value,
    }


def classify_risk(score):
    """Assign a risk category based on the final score."""

    if score >= HIGH_RISK_THRESHOLD:
        return "HIGH"

    if score >= MEDIUM_RISK_THRESHOLD:
        return "MEDIUM"

    return "LOW"


def build_risk_explanation(issue_types, scoring):
    """Explain the components of the risk score."""

    explanation = [
        f"Base issue score: {scoring['base_score']}",
        f"Corroboration bonus: {scoring['corroboration_bonus']}",
        f"Financial exposure bonus: {scoring['financial_exposure_bonus']}",
        f"Order value bonus: {scoring['order_value_bonus']}",
    ]

    if scoring["inherited_high_risk"]:
        explanation.append(
            "Inherited HIGH classification from detection module"
        )

    explanation.append(
        f"Final risk score: {scoring['risk_score']}"
    )

    return " | ".join(explanation)


def build_cases(findings):
    """Group findings into investigation cases."""

    grouped = defaultdict(list)

    for finding in findings:
        record_type = normalise_record_type(
            finding.get("record_type")
        )

        record_id = normalise_record_id(
            finding.get("record_id")
        )

        key = (record_type, record_id)
        grouped[key].append(finding)

    cases = []
    evidence_records = []

    for case_number, (key, case_findings) in enumerate(
        sorted(grouped.items()),
        start=1
    ):

        record_type, record_id = key

        issue_types = sorted({
            str(item.get("issue_type", "UNKNOWN")).strip().upper()
            for item in case_findings
        })

        sources = sorted({
            item["source_file"]
            for item in case_findings
        })

        supplier_ids = sorted({
            str(item.get("supplier_id", "")).strip()
            for item in case_findings
            if item.get("supplier_id")
        })

        source_risk_levels = sorted({
            str(item.get("risk_level", "")).strip().upper()
            for item in case_findings
            if item.get("risk_level")
        })

        scoring = calculate_risk_score(case_findings)

        risk_level = classify_risk(
            scoring["risk_score"]
        )

        case_id = f"CASE-{case_number:04d}"

        case = {
            "case_id": case_id,
            "record_type": record_type,
            "record_id": record_id,
            "supplier_ids": " | ".join(supplier_ids),
            "issue_types": " | ".join(issue_types),
            "detection_sources": " | ".join(sources),
            "source_risk_levels": " | ".join(source_risk_levels),
            "finding_count": len(case_findings),
            "financial_difference": round(
                scoring["financial_difference"], 2
            ),
            "order_value_exposure": round(
                scoring["order_value_exposure"], 2
            ),
            "base_score": scoring["base_score"],
            "corroboration_bonus": scoring["corroboration_bonus"],
            "financial_exposure_bonus": scoring["financial_exposure_bonus"],
            "order_value_bonus": scoring["order_value_bonus"],
            "inherited_high_risk": scoring["inherited_high_risk"],
            "risk_score": scoring["risk_score"],
            "risk_level": risk_level,
            "risk_explanation": build_risk_explanation(
                issue_types,
                scoring
            ),
        }

        cases.append(case)

        # Preserve every original finding as evidence.
        for finding in case_findings:
            evidence_records.append({
                "case_id": case_id,
                "source_file": finding["source_file"],
                "issue_type": finding.get("issue_type", ""),
                "record_type": finding.get("record_type", ""),
                "record_id": finding.get("record_id", ""),
                "related_record_id": finding.get(
                    "related_record_id", ""
                ),
                "evidence_details": json.dumps(
                    finding,
                    ensure_ascii=False
                ),
            })

    return cases, evidence_records


def export_csv(file_path, records):
    """Export investigation results to CSV."""

    if not records:
        print(f"No records to export: {file_path.name}")
        return

    with open(
        file_path,
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
    print("PROJECT PROOF | INVESTIGATION CASE BUILDER")
    print("=" * 70)

    findings = load_findings()

    cases, evidence = build_cases(findings)

    export_csv(OUTPUT_FILE, cases)
    export_csv(EVIDENCE_FILE, evidence)

    risk_counts = defaultdict(int)

    for case in cases:
        risk_counts[case["risk_level"]] += 1

    print("\nINVESTIGATION SUMMARY")
    print("-" * 70)

    print(f"Findings investigated: {len(findings)}")
    print(f"Investigation cases created: {len(cases)}")
    print(f"Evidence records preserved: {len(evidence)}")

    print("\nRISK CLASSIFICATION")
    print("-" * 70)

    for level in ["HIGH", "MEDIUM", "LOW"]:
        print(f"{level} risk cases: {risk_counts[level]}")

    print("\nOUTPUT FILES")
    print("-" * 70)

    print(OUTPUT_FILE.relative_to(PROJECT_ROOT))
    print(EVIDENCE_FILE.relative_to(PROJECT_ROOT))

    print("\nINVESTIGATION CASE BUILD: COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    main()
