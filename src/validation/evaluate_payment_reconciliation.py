
import csv
from collections import Counter
from pathlib import Path


# ============================================================
# PROJECT PROOF | PAYMENT DETECTION ACCURACY EVALUATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
GENERATED_DIR = PROJECT_ROOT / "data" / "generated"

PAYMENT_ISSUE_TYPES = {
    "OVERPAYMENT",
    "UNDERPAYMENT",
    "UNMATCHED_PAYMENT"
}


# ============================================================
# CSV LOADING
# ============================================================

def load_csv(file_path):

    if not file_path.exists():
        raise FileNotFoundError(
            f"Required file not found: {file_path}"
        )

    with file_path.open(
        "r",
        newline="",
        encoding="utf-8"
    ) as file:

        return list(csv.DictReader(file))


# ============================================================
# EVALUATION METRICS
# ============================================================

def calculate_metrics(true_positives, false_positives, false_negatives):

    precision = (
        true_positives / (true_positives + false_positives)
        if true_positives + false_positives > 0
        else 0.0
    )

    recall = (
        true_positives / (true_positives + false_negatives)
        if true_positives + false_negatives > 0
        else 0.0
    )

    f1_score = (
        2 * precision * recall / (precision + recall)
        if precision + recall > 0
        else 0.0
    )

    return precision, recall, f1_score


# ============================================================
# PAYMENT RECONCILIATION EVALUATION
# ============================================================

def evaluate_payment_reconciliation():

    detected_findings = load_csv(
        PROCESSED_DIR / "payment_findings.csv"
    )

    ground_truth = load_csv(
        GENERATED_DIR / "ground_truth.csv"
    )

    # --------------------------------------------------------
    # 1. FILTER PAYMENT-RELATED GROUND TRUTH
    # --------------------------------------------------------

    expected_findings = [
        row for row in ground_truth
        if row["issue_type"] in PAYMENT_ISSUE_TYPES
    ]

    # --------------------------------------------------------
    # 2. CREATE COMPARISON KEYS
    # --------------------------------------------------------

    expected_keys = Counter(
        (
            row["record_type"],
            row["record_id"],
            row["issue_type"]
        )
        for row in expected_findings
    )

    detected_keys = Counter(
        (
            row["record_type"],
            row["record_id"],
            row["issue_type"]
        )
        for row in detected_findings
        if row["issue_type"] in PAYMENT_ISSUE_TYPES
    )

    # --------------------------------------------------------
    # 3. IDENTIFY TRUE AND FALSE FINDINGS
    # --------------------------------------------------------

    true_positive_keys = expected_keys & detected_keys

    false_positive_keys = detected_keys - expected_keys

    false_negative_keys = expected_keys - detected_keys

    true_positives = sum(true_positive_keys.values())
    false_positives = sum(false_positive_keys.values())
    false_negatives = sum(false_negative_keys.values())

    # --------------------------------------------------------
    # 4. CALCULATE OVERALL METRICS
    # --------------------------------------------------------

    precision, recall, f1_score = calculate_metrics(
        true_positives,
        false_positives,
        false_negatives
    )

    # --------------------------------------------------------
    # 5. CALCULATE CATEGORY METRICS
    # --------------------------------------------------------

    category_results = []

    for issue_type in sorted(PAYMENT_ISSUE_TYPES):

        expected_category = Counter({
            key: count
            for key, count in expected_keys.items()
            if key[2] == issue_type
        })

        detected_category = Counter({
            key: count
            for key, count in detected_keys.items()
            if key[2] == issue_type
        })

        category_tp = sum(
            (expected_category & detected_category).values()
        )

        category_fp = sum(
            (detected_category - expected_category).values()
        )

        category_fn = sum(
            (expected_category - detected_category).values()
        )

        category_precision, category_recall, category_f1 = (
            calculate_metrics(
                category_tp,
                category_fp,
                category_fn
            )
        )

        category_results.append({

            "issue_type": issue_type,
            "expected": sum(expected_category.values()),
            "detected": sum(detected_category.values()),
            "true_positives": category_tp,
            "false_positives": category_fp,
            "false_negatives": category_fn,
            "precision": round(category_precision, 4),
            "recall": round(category_recall, 4),
            "f1_score": round(category_f1, 4)

        })

    # --------------------------------------------------------
    # 6. RECORD INCORRECT FINDINGS
    # --------------------------------------------------------

    evaluation_details = []

    for key, count in false_positive_keys.items():

        evaluation_details.append({

            "record_type": key[0],
            "record_id": key[1],
            "issue_type": key[2],
            "evaluation_result": "FALSE_POSITIVE",
            "occurrences": count

        })

    for key, count in false_negative_keys.items():

        evaluation_details.append({

            "record_type": key[0],
            "record_id": key[1],
            "issue_type": key[2],
            "evaluation_result": "FALSE_NEGATIVE",
            "occurrences": count

        })

    # --------------------------------------------------------
    # 7. EXPORT EVALUATION RESULTS
    # --------------------------------------------------------

    summary_fields = [
        "issue_type",
        "expected",
        "detected",
        "true_positives",
        "false_positives",
        "false_negatives",
        "precision",
        "recall",
        "f1_score"
    ]

    detail_fields = [
        "record_type",
        "record_id",
        "issue_type",
        "evaluation_result",
        "occurrences"
    ]

    with (
        PROCESSED_DIR / "payment_evaluation_summary.csv"
    ).open("w", newline="", encoding="utf-8") as file:

        writer = csv.DictWriter(
            file,
            fieldnames=summary_fields
        )

        writer.writeheader()
        writer.writerows(category_results)

    with (
        PROCESSED_DIR / "payment_evaluation_details.csv"
    ).open("w", newline="", encoding="utf-8") as file:

        writer = csv.DictWriter(
            file,
            fieldnames=detail_fields
        )

        writer.writeheader()
        writer.writerows(evaluation_details)

    # --------------------------------------------------------
    # 8. DISPLAY RESULTS
    # --------------------------------------------------------

    print("=" * 70)
    print("PROJECT PROOF | PAYMENT DETECTION ACCURACY")
    print("=" * 70)

    print("\nOVERALL EVALUATION")
    print("-" * 70)

    print(f"Expected findings: {sum(expected_keys.values())}")
    print(f"Detected findings: {sum(detected_keys.values())}")
    print(f"True positives: {true_positives}")
    print(f"False positives: {false_positives}")
    print(f"False negatives: {false_negatives}")

    print("\nOVERALL PERFORMANCE")
    print("-" * 70)

    print(f"Precision: {precision * 100:.2f}%")
    print(f"Recall: {recall * 100:.2f}%")
    print(f"F1-score: {f1_score * 100:.2f}%")

    print("\nPER-CATEGORY EVALUATION")
    print("-" * 70)

    for result in category_results:

        print(f"\n{result['issue_type']}")

        print(f"Expected: {result['expected']}")
        print(f"Detected: {result['detected']}")
        print(f"True positives: {result['true_positives']}")
        print(f"False positives: {result['false_positives']}")
        print(f"False negatives: {result['false_negatives']}")

        print(
            f"Precision: {result['precision'] * 100:.2f}%"
        )

        print(
            f"Recall: {result['recall'] * 100:.2f}%"
        )

        print(
            f"F1-score: {result['f1_score'] * 100:.2f}%"
        )

    print("\nEVALUATION FILES")
    print("-" * 70)

    print("data/processed/payment_evaluation_summary.csv")
    print("data/processed/payment_evaluation_details.csv")

    if false_positives == 0 and false_negatives == 0:

        print("\nEVALUATION RESULT: ALL EXPECTED FINDINGS MATCHED")

    else:

        print("\nEVALUATION RESULT: INVESTIGATION REQUIRED")

    print("=" * 70)


# ============================================================
# APPLICATION ENTRY POINT
# ============================================================

if __name__ == "__main__":

    evaluate_payment_reconciliation()
