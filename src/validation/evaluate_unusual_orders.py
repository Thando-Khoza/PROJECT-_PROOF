
import csv
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

GROUND_TRUTH_FILE = (
    PROJECT_ROOT / "data" / "generated" / "ground_truth.csv"
)

DETECTION_FILE = (
    PROJECT_ROOT / "data" / "processed" / "unusual_order_findings.csv"
)

OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"

SUMMARY_FILE = OUTPUT_DIR / "unusual_order_evaluation_summary.csv"
DETAILS_FILE = OUTPUT_DIR / "unusual_order_evaluation_details.csv"


def load_csv(file_path):
    with open(file_path, "r", newline="", encoding="utf-8-sig") as file:
        return list(csv.DictReader(file))


def main():
    print("=" * 70)
    print("PROJECT PROOF | UNUSUAL ORDER DETECTION EVALUATION")
    print("=" * 70)

    ground_truth = load_csv(GROUND_TRUTH_FILE)
    detected_findings = load_csv(DETECTION_FILE)

    expected_ids = {
        row["record_id"]
        for row in ground_truth
        if row["issue_type"] == "HIGH_VALUE_ORDER"
    }

    detected_ids = {
        row["record_id"]
        for row in detected_findings
        if row["issue_type"] == "UNUSUAL_ORDER_VALUE"
    }

    true_positives = expected_ids & detected_ids
    false_positives = detected_ids - expected_ids
    false_negatives = expected_ids - detected_ids

    precision = (
        len(true_positives) / len(detected_ids) * 100
        if detected_ids else 0
    )

    recall = (
        len(true_positives) / len(expected_ids) * 100
        if expected_ids else 0
    )

    f1_score = (
        2 * precision * recall / (precision + recall)
        if precision + recall else 0
    )

    print("\nOVERALL EVALUATION")
    print("-" * 70)
    print(f"Expected findings: {len(expected_ids)}")
    print(f"Detected findings: {len(detected_ids)}")
    print(f"True positives: {len(true_positives)}")
    print(f"False positives: {len(false_positives)}")
    print(f"False negatives: {len(false_negatives)}")

    print("\nOVERALL PERFORMANCE")
    print("-" * 70)
    print(f"Precision: {precision:.2f}%")
    print(f"Recall: {recall:.2f}%")
    print(f"F1-score: {f1_score:.2f}%")

    details = []

    for order_id in sorted(true_positives):
        details.append({
            "purchase_order": order_id,
            "evaluation": "TRUE_POSITIVE"
        })

    for order_id in sorted(false_positives):
        details.append({
            "purchase_order": order_id,
            "evaluation": "FALSE_POSITIVE"
        })

    for order_id in sorted(false_negatives):
        details.append({
            "purchase_order": order_id,
            "evaluation": "FALSE_NEGATIVE"
        })

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(SUMMARY_FILE, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "expected_findings",
                "detected_findings",
                "true_positives",
                "false_positives",
                "false_negatives",
                "precision",
                "recall",
                "f1_score"
            ]
        )

        writer.writeheader()
        writer.writerow({
            "expected_findings": len(expected_ids),
            "detected_findings": len(detected_ids),
            "true_positives": len(true_positives),
            "false_positives": len(false_positives),
            "false_negatives": len(false_negatives),
            "precision": round(precision, 2),
            "recall": round(recall, 2),
            "f1_score": round(f1_score, 2)
        })

    with open(DETAILS_FILE, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["purchase_order", "evaluation"]
        )

        writer.writeheader()
        writer.writerows(details)

    print("\nEVALUATION DETAILS")
    print("-" * 70)

    for item in details:
        print(f"{item['purchase_order']} | {item['evaluation']}")

    print("\nEVALUATION FILES")
    print("-" * 70)
    print(SUMMARY_FILE.relative_to(PROJECT_ROOT))
    print(DETAILS_FILE.relative_to(PROJECT_ROOT))

    print("\nEVALUATION COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    main()
