
import csv
from collections import defaultdict, Counter
from decimal import Decimal
from pathlib import Path


# ============================================================
# PROJECT PROOF | PAYMENT RECONCILIATION ENGINE
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_DIR = PROJECT_ROOT / "data" / "raw"
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# CSV LOADING
# ============================================================

def load_csv(filename):

    file_path = RAW_DIR / filename

    if not file_path.exists():
        raise FileNotFoundError(
            f"Required input file not found: {file_path}"
        )

    with file_path.open(
        "r",
        newline="",
        encoding="utf-8"
    ) as file:

        return list(csv.DictReader(file))


# ============================================================
# CSV EXPORT
# ============================================================

def export_csv(filename, records, fieldnames):

    file_path = OUTPUT_DIR / filename

    with file_path.open(
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )

        writer.writeheader()
        writer.writerows(records)


# ============================================================
# FINANCIAL VALUE CONVERSION
# ============================================================

def money(value):

    return Decimal(str(value))


# ============================================================
# PAYMENT RECONCILIATION
# ============================================================

def reconcile_payments():

    invoices = load_csv("supplier_invoices.csv")
    payments = load_csv("payment_records.csv")

    # --------------------------------------------------------
    # 1. CREATE INVOICE LOOKUP
    # --------------------------------------------------------

    invoice_lookup = {}

    for invoice in invoices:

        invoice_number = invoice["invoice_number"]

        if invoice_number not in invoice_lookup:
            invoice_lookup[invoice_number] = invoice

    # --------------------------------------------------------
    # 2. GROUP PAYMENTS BY INVOICE
    # --------------------------------------------------------

    payment_groups = defaultdict(list)

    for payment in payments:

        payment_groups[
            payment["invoice_number"]
        ].append(payment)

    reconciliation_results = []
    findings = []

    # --------------------------------------------------------
    # 3. INVESTIGATE EACH PAYMENT
    # --------------------------------------------------------

    for invoice_number, invoice_payments in payment_groups.items():

        invoice = invoice_lookup.get(invoice_number)

        payment_ids = [
            payment["payment_id"]
            for payment in invoice_payments
        ]

        payment_count = len(invoice_payments)

        total_paid = sum(
            (
                money(payment["payment_amount"])
                for payment in invoice_payments
            ),
            Decimal("0")
        )

        payment_suppliers = {
            payment["supplier_id"]
            for payment in invoice_payments
        }

        issues = []

        # ----------------------------------------------------
        # 4. UNMATCHED PAYMENT CHECK
        # ----------------------------------------------------

        if invoice is None:

            issues.append("UNMATCHED_PAYMENT")

            for payment in invoice_payments:

                findings.append({

                    "issue_type": "UNMATCHED_PAYMENT",
                    "record_type": "payment",
                    "record_id": payment["payment_id"],
                    "related_record_id": invoice_number,
                    "expected_value": "Existing supplier invoice",
                    "observed_value": "Invoice not found",
                    "difference": "",
                    "explanation": (
                        "Payment references an invoice "
                        "that does not exist."
                    )

                })

            expected_amount = ""
            difference = ""

        else:

            # ------------------------------------------------
            # 5. SUPPLIER VERIFICATION
            # ------------------------------------------------

            invoice_supplier = invoice["supplier_id"]

            mismatched_suppliers = (
                payment_suppliers - {invoice_supplier}
            )

            if mismatched_suppliers:

                issues.append("SUPPLIER_MISMATCH")

                findings.append({

                    "issue_type": "SUPPLIER_MISMATCH",
                    "record_type": "invoice",
                    "record_id": invoice_number,
                    "related_record_id": " | ".join(payment_ids),
                    "expected_value": invoice_supplier,
                    "observed_value": " | ".join(
                        sorted(payment_suppliers)
                    ),
                    "difference": "",
                    "explanation": (
                        "Payment supplier does not match "
                        "the supplier recorded on the invoice."
                    )

                })

            # ------------------------------------------------
            # 6. PAYMENT AMOUNT VERIFICATION
            # ------------------------------------------------

            expected_amount = money(
                invoice["invoice_amount"]
            )

            difference = total_paid - expected_amount

            if difference > 0:

                issues.append("OVERPAYMENT")

                findings.append({

                    "issue_type": "OVERPAYMENT",
                    "record_type": "payment",
                    "record_id": payment_ids[0],
                    "related_record_id": invoice_number,
                    "expected_value": str(expected_amount),
                    "observed_value": str(total_paid),
                    "difference": str(difference),
                    "explanation": (
                        "Total payments exceed the invoice amount."
                    )

                })

            elif difference < 0:

                issues.append("UNDERPAYMENT")

                findings.append({

                    "issue_type": "UNDERPAYMENT",
                    "record_type": "payment",
                    "record_id": payment_ids[0],
                    "related_record_id": invoice_number,
                    "expected_value": str(expected_amount),
                    "observed_value": str(total_paid),
                    "difference": str(difference),
                    "explanation": (
                        "Total payments are below the invoice amount."
                    )

                })

        # ----------------------------------------------------
        # 7. RECONCILIATION STATUS
        # ----------------------------------------------------

        if payment_count > 1:
            issues.append("MULTIPLE_PAYMENTS")

        if issues:

            status = "REQUIRES INVESTIGATION"

        else:

            status = "MATCHED"

        for payment in invoice_payments:

            reconciliation_results.append({

                "payment_id": payment["payment_id"],
                "invoice_number": invoice_number,
                "supplier_id": payment["supplier_id"],
                "payment_amount": payment["payment_amount"],
                "invoice_amount": (
                    str(expected_amount)
                    if expected_amount != ""
                    else ""
                ),
                "payment_count": payment_count,
                "total_paid": str(total_paid),
                "difference": (
                    str(difference)
                    if difference != ""
                    else ""
                ),
                "issues": " | ".join(issues),
                "status": status

            })

    # --------------------------------------------------------
    # 8. INVESTIGATION SUMMARY
    # --------------------------------------------------------

    issue_counts = Counter(
        finding["issue_type"]
        for finding in findings
    )

    flagged_payments = sum(
        1
        for result in reconciliation_results
        if result["status"] == "REQUIRES INVESTIGATION"
    )

    matched_payments = (
        len(reconciliation_results) - flagged_payments
    )

    # --------------------------------------------------------
    # 9. EXPORT RESULTS
    # --------------------------------------------------------

    reconciliation_fields = [
        "payment_id",
        "invoice_number",
        "supplier_id",
        "payment_amount",
        "invoice_amount",
        "payment_count",
        "total_paid",
        "difference",
        "issues",
        "status"
    ]

    finding_fields = [
        "issue_type",
        "record_type",
        "record_id",
        "related_record_id",
        "expected_value",
        "observed_value",
        "difference",
        "explanation"
    ]

    export_csv(
        "payment_reconciliation.csv",
        reconciliation_results,
        reconciliation_fields
    )

    export_csv(
        "payment_findings.csv",
        findings,
        finding_fields
    )

    # --------------------------------------------------------
    # 10. DISPLAY RESULTS
    # --------------------------------------------------------

    print("=" * 70)
    print("PROJECT PROOF | PAYMENT RECONCILIATION")
    print("=" * 70)

    print("\nRECONCILIATION SUMMARY")
    print("-" * 70)

    print(f"Payments investigated: {len(payments)}")
    print(f"Unique invoices referenced: {len(payment_groups)}")
    print(f"Flagged payment records: {flagged_payments}")
    print(f"Matched payment records: {matched_payments}")
    print(f"Total findings: {len(findings)}")

    print("\nFINDINGS BREAKDOWN")
    print("-" * 70)

    for issue_type, count in sorted(issue_counts.items()):

        print(f"{issue_type}: {count}")

    print("\nOUTPUT FILES")
    print("-" * 70)

    print("data/processed/payment_reconciliation.csv")
    print("data/processed/payment_findings.csv")

    print("\nPAYMENT RECONCILIATION COMPLETED")
    print("=" * 70)


# ============================================================
# APPLICATION ENTRY POINT
# ============================================================

if __name__ == "__main__":

    reconcile_payments()
