
import csv
import random
from datetime import date, timedelta
from pathlib import Path


# ============================================================
# PROJECT PROOF
# SUPPLIER FINANCIAL DATA GENERATOR
# ============================================================

random.seed(42)

PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_DIR = PROJECT_ROOT / "data" / "raw"
GENERATED_DIR = PROJECT_ROOT / "data" / "generated"

RAW_DIR.mkdir(parents=True, exist_ok=True)
GENERATED_DIR.mkdir(parents=True, exist_ok=True)

BASE_RECORDS = 100
START_DATE = date(2026, 1, 1)

SUPPLIERS = [
    ("SUP001", "Alpha Office Supplies"),
    ("SUP002", "Brightline Technologies"),
    ("SUP003", "Crestwood Logistics"),
    ("SUP004", "Delta Industrial"),
    ("SUP005", "Evergreen Packaging"),
    ("SUP006", "Frontier Equipment"),
    ("SUP007", "Global Stationery"),
    ("SUP008", "Horizon Electronics"),
    ("SUP009", "Insight Distribution"),
    ("SUP010", "Jupiter Manufacturing"),
]


# ============================================================
# CSV EXPORT FUNCTION
# ============================================================

def write_csv(directory, filename, records):

    if not records:
        raise ValueError(f"No records available for {filename}")

    file_path = directory / filename

    fieldnames = list(records[0].keys())

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
# DATE GENERATOR
# ============================================================

def random_date():

    return START_DATE + timedelta(
        days=random.randint(0, 300)
    )


# ============================================================
# GROUND-TRUTH RECORD FUNCTION
# ============================================================

def record_issue(
    ground_truth,
    record_type,
    record_id,
    issue_type,
    expected_reason
):

    ground_truth.append({

        "record_type": record_type,
        "record_id": record_id,
        "issue_type": issue_type,
        "expected_reason": expected_reason

    })


# ============================================================
# MAIN DATA GENERATOR
# ============================================================

def generate_data():

    purchase_orders = []
    invoices = []
    payments = []
    ground_truth = []

    positions = list(range(BASE_RECORDS))
    random.shuffle(positions)

    price_cases = set(positions[0:10])
    quantity_cases = set(positions[10:20])
    payment_cases = set(positions[20:30])
    supplier_cases = set(positions[30:35])
    suspicious_cases = set(positions[35:40])
    duplicate_cases = set(positions[40:50])

    overpayment_cases = set(positions[20:25])
    underpayment_cases = set(positions[25:30])

    # --------------------------------------------------------
    # 1. GENERATE PURCHASE ORDERS
    # --------------------------------------------------------

    for i in range(BASE_RECORDS):

        supplier_id, supplier_name = random.choice(SUPPLIERS)

        quantity = random.randint(5, 100)

        unit_price = round(
            random.uniform(100, 2500), 2
        )

        # Introduce unusually high-value orders.

        if i in suspicious_cases:

            unit_price = round(
                random.uniform(15000, 25000), 2
            )

        order_total = round(
            quantity * unit_price, 2
        )

        po_number = f"PO-{10001 + i}"

        # Generate the purchase order date first.
        # The invoice date will be based on this date.

        order_date = random_date()

        purchase_orders.append({

            "po_number": po_number,
            "supplier_id": supplier_id,
            "supplier_name": supplier_name,
            "order_date": order_date.isoformat(),
            "quantity": quantity,
            "unit_price": unit_price,
            "order_total": order_total,
            "currency": "ZAR"

        })

        # ----------------------------------------------------
        # 2. GENERATE SUPPLIER INVOICES
        # ----------------------------------------------------

        invoice_number = f"INV-{20001 + i}"

        invoice_quantity = quantity
        invoice_unit_price = unit_price

        # PRICE DISCREPANCY

        if i in price_cases:

            invoice_unit_price = round(
                unit_price * 1.15, 2
            )

            record_issue(
                ground_truth,
                "invoice",
                invoice_number,
                "PRICE_DISCREPANCY",
                "Invoice unit price exceeds purchase order price."
            )

        # QUANTITY DISCREPANCY

        if i in quantity_cases:

            invoice_quantity = (
                quantity + random.randint(2, 10)
            )

            record_issue(
                ground_truth,
                "invoice",
                invoice_number,
                "QUANTITY_DISCREPANCY",
                "Invoice quantity exceeds purchase order quantity."
            )

        invoice_amount = round(
            invoice_quantity * invoice_unit_price, 2
        )

        invoice_supplier_id = supplier_id

        # SUPPLIER MISMATCH

        if i in supplier_cases:

            alternatives = [
                supplier[0]
                for supplier in SUPPLIERS
                if supplier[0] != supplier_id
            ]

            invoice_supplier_id = random.choice(
                alternatives
            )

            record_issue(
                ground_truth,
                "invoice",
                invoice_number,
                "SUPPLIER_MISMATCH",
                "Invoice supplier differs from purchase order supplier."
            )

        # Invoice must occur after the purchase order.

        invoice_date = order_date + timedelta(
            days=random.randint(1, 30)
        )

        invoice_record = {

            "invoice_number": invoice_number,
            "po_number": po_number,
            "supplier_id": invoice_supplier_id,
            "invoice_date": invoice_date.isoformat(),
            "due_date": (
                invoice_date + timedelta(days=30)
            ).isoformat(),
            "quantity": invoice_quantity,
            "unit_price": invoice_unit_price,
            "invoice_amount": invoice_amount,
            "currency": "ZAR"

        }

        invoices.append(invoice_record)

        # ----------------------------------------------------
        # 3. GENERATE PAYMENT RECORDS
        # ----------------------------------------------------

        payment_amount = invoice_amount

        # OVERPAYMENT

        if i in overpayment_cases:

            payment_amount = round(
                invoice_amount * 1.20, 2
            )

            record_issue(
                ground_truth,
                "payment",
                f"PAY-{30001 + i}",
                "OVERPAYMENT",
                "Payment exceeds the invoice amount."
            )

        # UNDERPAYMENT

        elif i in underpayment_cases:

            payment_amount = round(
                invoice_amount * 0.80, 2
            )

            record_issue(
                ground_truth,
                "payment",
                f"PAY-{30001 + i}",
                "UNDERPAYMENT",
                "Payment is below the invoice amount."
            )

        # Payment must occur after the invoice.

        payment_date = invoice_date + timedelta(
            days=random.randint(5, 35)
        )

        payments.append({

            "payment_id": f"PAY-{30001 + i}",
            "invoice_number": invoice_number,
            "supplier_id": supplier_id,
            "payment_date": payment_date.isoformat(),
            "payment_amount": payment_amount,
            "currency": "ZAR"

        })

        # ----------------------------------------------------
        # 4. HIGH-VALUE TRANSACTION
        # ----------------------------------------------------

        if i in suspicious_cases:

            record_issue(
                ground_truth,
                "purchase_order",
                po_number,
                "HIGH_VALUE_ORDER",
                "Purchase order contains an unusually high unit price and requires review."
            )

    # --------------------------------------------------------
    # 5. DUPLICATE INVOICES
    # --------------------------------------------------------

    for i in sorted(duplicate_cases):

        original = invoices[i].copy()

        duplicate = original.copy()

        invoices.append(duplicate)

        record_issue(
            ground_truth,
            "invoice",
            original["invoice_number"],
            "DUPLICATE_INVOICE",
            "The same invoice appears more than once."
        )

    # --------------------------------------------------------
    # 6. UNMATCHED INVOICES
    # --------------------------------------------------------

    for i in range(5):

        supplier_id, _ = random.choice(SUPPLIERS)

        invoice_number = f"INV-UNMATCHED-{i + 1}"

        invoice_date = random_date()

        invoices.append({

            "invoice_number": invoice_number,
            "po_number": f"PO-MISSING-{i + 1}",
            "supplier_id": supplier_id,
            "invoice_date": invoice_date.isoformat(),
            "due_date": (
                invoice_date + timedelta(days=30)
            ).isoformat(),
            "quantity": 10,
            "unit_price": 500.00,
            "invoice_amount": 5000.00,
            "currency": "ZAR"

        })

        record_issue(
            ground_truth,
            "invoice",
            invoice_number,
            "UNMATCHED_INVOICE",
            "Invoice references a purchase order that does not exist."
        )

    # --------------------------------------------------------
    # 7. UNMATCHED PAYMENTS
    # --------------------------------------------------------

    for i in range(5):

        payment_id = f"PAY-UNMATCHED-{i + 1}"

        payments.append({

            "payment_id": payment_id,
            "invoice_number": f"INV-MISSING-{i + 1}",
            "supplier_id": random.choice(SUPPLIERS)[0],
            "payment_date": random_date().isoformat(),
            "payment_amount": round(
                random.uniform(1000, 10000), 2
            ),
            "currency": "ZAR"

        })

        record_issue(
            ground_truth,
            "payment",
            payment_id,
            "UNMATCHED_PAYMENT",
            "Payment references an invoice that does not exist."
        )

    # --------------------------------------------------------
    # 8. EXPORT OPERATIONAL DATASETS
    # --------------------------------------------------------

    write_csv(
        RAW_DIR,
        "purchase_orders.csv",
        purchase_orders
    )

    write_csv(
        RAW_DIR,
        "supplier_invoices.csv",
        invoices
    )

    write_csv(
        RAW_DIR,
        "payment_records.csv",
        payments
    )

    # Ground truth is stored separately.
    # It must not be used as an operational input.

    write_csv(
        GENERATED_DIR,
        "ground_truth.csv",
        ground_truth
    )

    # --------------------------------------------------------
    # 9. GENERATION SUMMARY
    # --------------------------------------------------------

    print("=" * 65)
    print("PROJECT PROOF | FINANCIAL DATA GENERATION")
    print("=" * 65)

    print("\nDATASET SUMMARY")
    print("-" * 65)

    print(f"Purchase orders: {len(purchase_orders)}")
    print(f"Supplier invoices: {len(invoices)}")
    print(f"Payment records: {len(payments)}")
    print(f"Ground-truth findings: {len(ground_truth)}")

    print("\nGROUND-TRUTH ISSUE BREAKDOWN")
    print("-" * 65)

    issue_counts = {}

    for issue in ground_truth:

        issue_type = issue["issue_type"]

        issue_counts[issue_type] = (
            issue_counts.get(issue_type, 0) + 1
        )

    for issue_type, count in sorted(issue_counts.items()):

        print(f"{issue_type}: {count}")

    print("\nGENERATED FILES")
    print("-" * 65)

    print("data/raw/purchase_orders.csv")
    print("data/raw/supplier_invoices.csv")
    print("data/raw/payment_records.csv")
    print("data/generated/ground_truth.csv")

    print("\nDATA GENERATION COMPLETED")
    print("=" * 65)


# ============================================================
# APPLICATION ENTRY POINT
# ============================================================

if __name__ == "__main__":

    generate_data()
