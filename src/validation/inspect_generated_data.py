
import csv
from collections import Counter
from datetime import date
from pathlib import Path


# ============================================================
# PROJECT PROOF | DATASET QUALITY INSPECTION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_DIR = PROJECT_ROOT / "data" / "raw"
GENERATED_DIR = PROJECT_ROOT / "data" / "generated"


EXPECTED_COUNTS = {
    "purchase_orders.csv": 100,
    "supplier_invoices.csv": 115,
    "payment_records.csv": 105,
    "ground_truth.csv": 60
}


EXPECTED_ISSUES = {
    "DUPLICATE_INVOICE": 10,
    "HIGH_VALUE_ORDER": 5,
    "OVERPAYMENT": 5,
    "PRICE_DISCREPANCY": 10,
    "QUANTITY_DISCREPANCY": 10,
    "SUPPLIER_MISMATCH": 5,
    "UNDERPAYMENT": 5,
    "UNMATCHED_INVOICE": 5,
    "UNMATCHED_PAYMENT": 5
}


EXPECTED_COLUMNS = {
    "purchase_orders.csv": [
        "po_number",
        "supplier_id",
        "supplier_name",
        "order_date",
        "quantity",
        "unit_price",
        "order_total",
        "currency"
    ],
    "supplier_invoices.csv": [
        "invoice_number",
        "po_number",
        "supplier_id",
        "invoice_date",
        "due_date",
        "quantity",
        "unit_price",
        "invoice_amount",
        "currency"
    ],
    "payment_records.csv": [
        "payment_id",
        "invoice_number",
        "supplier_id",
        "payment_date",
        "payment_amount",
        "currency"
    ],
    "ground_truth.csv": [
        "record_type",
        "record_id",
        "issue_type",
        "expected_reason"
    ]
}


# ============================================================
# CSV LOADING
# ============================================================

def load_csv(directory, filename):

    file_path = directory / filename

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
# INSPECTION
# ============================================================

def inspect_data():

    failures = []

    def check(condition, success_message, failure_message):

        if condition:
            print(f"PASS: {success_message}")
        else:
            print(f"FAIL: {failure_message}")
            failures.append(failure_message)

    print("=" * 70)
    print("PROJECT PROOF | DATASET QUALITY INSPECTION")
    print("=" * 70)

    # --------------------------------------------------------
    # 1. FILE AND COLUMN VALIDATION
    # --------------------------------------------------------

    print("\n1. FILE AND COLUMN VALIDATION")
    print("-" * 70)

    locations = {
        "purchase_orders.csv": RAW_DIR,
        "supplier_invoices.csv": RAW_DIR,
        "payment_records.csv": RAW_DIR,
        "ground_truth.csv": GENERATED_DIR
    }

    datasets = {}

    for filename, directory in locations.items():

        try:

            records = load_csv(directory, filename)
            datasets[filename] = records

            actual_columns = (
                list(records[0].keys()) if records else []
            )

            expected_columns = EXPECTED_COLUMNS[filename]

            missing_columns = [
                column
                for column in expected_columns
                if column not in actual_columns
            ]

            check(
                len(records) > 0 and not missing_columns,
                (
                    f"{filename} | {len(records)} records | "
                    f"{len(actual_columns)} columns"
                ),
                (
                    f"{filename} is empty or missing columns: "
                    f"{missing_columns}"
                )
            )

        except (FileNotFoundError, OSError) as error:

            failures.append(str(error))
            print(f"FAIL: {error}")

    if len(datasets) != 4:

        print("\nInspection stopped because required files are missing.")
        raise SystemExit(1)

    # --------------------------------------------------------
    # 2. RECORD COUNT VALIDATION
    # --------------------------------------------------------

    print("\n2. RECORD COUNT VALIDATION")
    print("-" * 70)

    for filename, expected_count in EXPECTED_COUNTS.items():

        actual_count = len(datasets[filename])

        check(
            actual_count == expected_count,
            f"{filename} = {actual_count}",
            (
                f"{filename}: expected {expected_count}, "
                f"found {actual_count}"
            )
        )

    purchase_orders = datasets["purchase_orders.csv"]
    invoices = datasets["supplier_invoices.csv"]
    payments = datasets["payment_records.csv"]
    ground_truth = datasets["ground_truth.csv"]

    # --------------------------------------------------------
    # 3. DUPLICATE INVOICE INVESTIGATION
    # --------------------------------------------------------

    print("\n3. DUPLICATE INVOICE INVESTIGATION")
    print("-" * 70)

    invoice_counts = Counter(
        row["invoice_number"]
        for row in invoices
    )

    duplicate_groups = sum(
        1 for count in invoice_counts.values()
        if count > 1
    )

    duplicate_extra_rows = sum(
        count - 1
        for count in invoice_counts.values()
        if count > 1
    )

    print(f"Duplicate invoice groups: {duplicate_groups}")
    print(f"Additional duplicate rows: {duplicate_extra_rows}")

    check(
        duplicate_groups == 10 and duplicate_extra_rows == 10,
        "Expected duplicate invoices identified.",
        "Duplicate invoice counts do not match expectations."
    )

    # --------------------------------------------------------
    # 4. UNMATCHED INVOICE INVESTIGATION
    # --------------------------------------------------------

    print("\n4. UNMATCHED PURCHASE ORDER INVESTIGATION")
    print("-" * 70)

    po_numbers = {
        row["po_number"]
        for row in purchase_orders
    }

    unmatched_invoices = [
        row for row in invoices
        if row["po_number"] not in po_numbers
    ]

    print(f"Unmatched invoices: {len(unmatched_invoices)}")

    check(
        len(unmatched_invoices) == 5,
        "Expected unmatched invoices identified.",
        f"Expected 5 unmatched invoices, found {len(unmatched_invoices)}."
    )

    # --------------------------------------------------------
    # 5. UNMATCHED PAYMENT INVESTIGATION
    # --------------------------------------------------------

    print("\n5. UNMATCHED PAYMENT INVESTIGATION")
    print("-" * 70)

    invoice_numbers = {
        row["invoice_number"]
        for row in invoices
    }

    unmatched_payments = [
        row for row in payments
        if row["invoice_number"] not in invoice_numbers
    ]

    print(f"Unmatched payments: {len(unmatched_payments)}")

    check(
        len(unmatched_payments) == 5,
        "Expected unmatched payments identified.",
        f"Expected 5 unmatched payments, found {len(unmatched_payments)}."
    )

    # --------------------------------------------------------
    # 6. TRANSACTION DATE VALIDATION
    # --------------------------------------------------------

    print("\n6. TRANSACTION DATE VALIDATION")
    print("-" * 70)

    po_lookup = {
        row["po_number"]: row
        for row in purchase_orders
    }

    invoice_lookup = {
        row["invoice_number"]: row
        for row in invoices
    }

    invalid_invoice_dates = []

    for invoice in invoices:

        purchase_order = po_lookup.get(invoice["po_number"])

        if purchase_order is None:
            continue

        order_date = date.fromisoformat(
            purchase_order["order_date"]
        )

        invoice_date = date.fromisoformat(
            invoice["invoice_date"]
        )

        if invoice_date < order_date:

            invalid_invoice_dates.append(
                invoice["invoice_number"]
            )

    print(
        "Invoices dated before purchase orders: "
        f"{len(invalid_invoice_dates)}"
    )

    check(
        len(invalid_invoice_dates) == 0,
        "All matched invoices follow their purchase order dates.",
        "One or more invoices predate their purchase orders."
    )

    invalid_payment_dates = []

    for payment in payments:

        invoice = invoice_lookup.get(
            payment["invoice_number"]
        )

        if invoice is None:
            continue

        invoice_date = date.fromisoformat(
            invoice["invoice_date"]
        )

        payment_date = date.fromisoformat(
            payment["payment_date"]
        )

        if payment_date < invoice_date:

            invalid_payment_dates.append(
                payment["payment_id"]
            )

    print(
        "Payments dated before invoices: "
        f"{len(invalid_payment_dates)}"
    )

    check(
        len(invalid_payment_dates) == 0,
        "All matched payments follow their invoice dates.",
        "One or more payments predate their invoices."
    )

    # --------------------------------------------------------
    # 7. GROUND-TRUTH INVESTIGATION
    # --------------------------------------------------------

    print("\n7. GROUND-TRUTH INVESTIGATION")
    print("-" * 70)

    issue_counts = Counter(
        row["issue_type"]
        for row in ground_truth
    )

    for issue_type, expected_count in sorted(
        EXPECTED_ISSUES.items()
    ):

        actual_count = issue_counts.get(issue_type, 0)

        print(f"{issue_type}: {actual_count}")

        check(
            actual_count == expected_count,
            f"{issue_type} count verified.",
            (
                f"{issue_type}: expected {expected_count}, "
                f"found {actual_count}"
            )
        )

    print(f"\nTotal ground-truth findings: {len(ground_truth)}")

    check(
        len(ground_truth) == 60,
        "All 60 ground-truth findings recorded.",
        f"Expected 60 findings, found {len(ground_truth)}."
    )

    check(
        set(issue_counts.keys()) == set(EXPECTED_ISSUES.keys()),
        "All nine expected issue categories recorded.",
        "Ground-truth issue categories do not match expectations."
    )

    # --------------------------------------------------------
    # 8. FINAL RESULT
    # --------------------------------------------------------

    print("\n" + "=" * 70)

    if failures:

        print("DATASET INSPECTION: FAILED")
        print(f"Failed checks: {len(failures)}")

        for failure in failures:
            print(f"- {failure}")

        print("=" * 70)
        raise SystemExit(1)

    print("DATASET INSPECTION: ALL CHECKS PASSED")
    print("=" * 70)


# ============================================================
# APPLICATION ENTRY POINT
# ============================================================

if __name__ == "__main__":

    inspect_data()
