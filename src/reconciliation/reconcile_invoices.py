
import csv
from collections import Counter
from decimal import Decimal
from pathlib import Path


# ============================================================
# PROJECT PROOF | INVOICE RECONCILIATION ENGINE
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
# INVOICE RECONCILIATION
# ============================================================

def reconcile_invoices():

    purchase_orders = load_csv("purchase_orders.csv")
    invoices = load_csv("supplier_invoices.csv")

    # Create a purchase order lookup for matching.

    po_lookup = {
        row["po_number"]: row
        for row in purchase_orders
    }

    # Count how often each invoice number appears.

    invoice_counts = Counter(
        row["invoice_number"]
        for row in invoices
    )

    reconciliation_results = []
    findings = []

    # ========================================================
    # 1. INVESTIGATE EACH INVOICE
    # ========================================================

    for invoice in invoices:

        invoice_number = invoice["invoice_number"]
        po_number = invoice["po_number"]

        invoice_issues = []

        purchase_order = po_lookup.get(po_number)

        # ----------------------------------------------------
        # 2. DUPLICATE INVOICE CHECK
        # ----------------------------------------------------

        if invoice_counts[invoice_number] > 1:

            invoice_issues.append("DUPLICATE_INVOICE")

        # ----------------------------------------------------
        # 3. PURCHASE ORDER MATCHING
        # ----------------------------------------------------

        if purchase_order is None:

            invoice_issues.append("UNMATCHED_INVOICE")

            findings.append({

                "issue_type": "UNMATCHED_INVOICE",
                "record_type": "invoice",
                "record_id": invoice_number,
                "related_record_id": po_number,
                "expected_value": "Existing purchase order",
                "observed_value": "Purchase order not found",
                "difference": "",
                "explanation": (
                    "Invoice references a purchase order "
                    "that does not exist."
                )

            })

        else:

            # ------------------------------------------------
            # 4. SUPPLIER VERIFICATION
            # ------------------------------------------------

            if invoice["supplier_id"] != purchase_order["supplier_id"]:

                invoice_issues.append("SUPPLIER_MISMATCH")

                findings.append({

                    "issue_type": "SUPPLIER_MISMATCH",
                    "record_type": "invoice",
                    "record_id": invoice_number,
                    "related_record_id": po_number,
                    "expected_value": purchase_order["supplier_id"],
                    "observed_value": invoice["supplier_id"],
                    "difference": "",
                    "explanation": (
                        "Invoice supplier does not match "
                        "the purchase order supplier."
                    )

                })

            # ------------------------------------------------
            # 5. QUANTITY VERIFICATION
            # ------------------------------------------------

            ordered_quantity = int(
                purchase_order["quantity"]
            )

            invoiced_quantity = int(
                invoice["quantity"]
            )

            if invoiced_quantity != ordered_quantity:

                difference = (
                    invoiced_quantity - ordered_quantity
                )

                invoice_issues.append(
                    "QUANTITY_DISCREPANCY"
                )

                findings.append({

                    "issue_type": "QUANTITY_DISCREPANCY",
                    "record_type": "invoice",
                    "record_id": invoice_number,
                    "related_record_id": po_number,
                    "expected_value": ordered_quantity,
                    "observed_value": invoiced_quantity,
                    "difference": difference,
                    "explanation": (
                        "Invoiced quantity differs from "
                        "the purchase order quantity."
                    )

                })

            # ------------------------------------------------
            # 6. UNIT PRICE VERIFICATION
            # ------------------------------------------------

            ordered_price = money(
                purchase_order["unit_price"]
            )

            invoiced_price = money(
                invoice["unit_price"]
            )

            if invoiced_price != ordered_price:

                price_difference = (
                    invoiced_price - ordered_price
                )

                invoice_issues.append(
                    "PRICE_DISCREPANCY"
                )

                findings.append({

                    "issue_type": "PRICE_DISCREPANCY",
                    "record_type": "invoice",
                    "record_id": invoice_number,
                    "related_record_id": po_number,
                    "expected_value": str(ordered_price),
                    "observed_value": str(invoiced_price),
                    "difference": str(price_difference),
                    "explanation": (
                        "Invoice unit price differs from "
                        "the approved purchase order price."
                    )

                })

        # ----------------------------------------------------
        # 7. RECONCILIATION RESULT
        # ----------------------------------------------------

        reconciliation_results.append({

            "invoice_number": invoice_number,
            "po_number": po_number,
            "supplier_id": invoice["supplier_id"],
            "invoice_amount": invoice["invoice_amount"],
            "duplicate_occurrences": invoice_counts[invoice_number],
            "issue_count": len(invoice_issues),
            "issues": " | ".join(invoice_issues),
            "status": (
                "REQUIRES INVESTIGATION"
                if invoice_issues
                else "MATCHED"
            )

        })

    # ========================================================
    # 8. CREATE ONE FINDING PER DUPLICATE INVOICE GROUP
    # ========================================================

    duplicate_numbers = {
        number
        for number, count in invoice_counts.items()
        if count > 1
    }

    for invoice_number in sorted(duplicate_numbers):

        findings.append({

            "issue_type": "DUPLICATE_INVOICE",
            "record_type": "invoice",
            "record_id": invoice_number,
            "related_record_id": invoice_number,
            "expected_value": "One occurrence",
            "observed_value": invoice_counts[invoice_number],
            "difference": invoice_counts[invoice_number] - 1,
            "explanation": (
                "The same invoice number appears "
                "multiple times in the invoice dataset."
            )

        })

    # ========================================================
    # 9. EXPORT RECONCILIATION RESULTS
    # ========================================================

    reconciliation_fields = [
        "invoice_number",
        "po_number",
        "supplier_id",
        "invoice_amount",
        "duplicate_occurrences",
        "issue_count",
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
        "invoice_reconciliation.csv",
        reconciliation_results,
        reconciliation_fields
    )

    export_csv(
        "invoice_findings.csv",
        findings,
        finding_fields
    )

    # ========================================================
    # 10. INVESTIGATION SUMMARY
    # ========================================================

    issue_counts = Counter(
        finding["issue_type"]
        for finding in findings
    )

    flagged_invoice_records = sum(
        1
        for result in reconciliation_results
        if result["issue_count"] > 0
    )

    matched_invoice_records = (
        len(reconciliation_results) - flagged_invoice_records
    )

    print("=" * 70)
    print("PROJECT PROOF | INVOICE RECONCILIATION")
    print("=" * 70)

    print("\nRECONCILIATION SUMMARY")
    print("-" * 70)

    print(f"Invoices investigated: {len(invoices)}")
    print(f"Unique invoice numbers: {len(invoice_counts)}")
    print(f"Flagged invoice records: {flagged_invoice_records}")
    print(f"Matched invoice records: {matched_invoice_records}")
    print(f"Total findings: {len(findings)}")

    print("\nFINDINGS BREAKDOWN")
    print("-" * 70)

    for issue_type, count in sorted(issue_counts.items()):

        print(f"{issue_type}: {count}")

    print("\nOUTPUT FILES")
    print("-" * 70)

    print("data/processed/invoice_reconciliation.csv")
    print("data/processed/invoice_findings.csv")

    print("\nINVOICE RECONCILIATION COMPLETED")
    print("=" * 70)


# ============================================================
# APPLICATION ENTRY POINT
# ============================================================

if __name__ == "__main__":

    reconcile_invoices()
