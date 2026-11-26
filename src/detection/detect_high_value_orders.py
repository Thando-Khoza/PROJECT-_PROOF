
import csv
from decimal import Decimal, InvalidOperation
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = PROJECT_ROOT / "data" / "raw" / "purchase_orders.csv"
OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "high_value_order_findings.csv"
)

UNIT_PRICE_THRESHOLD = Decimal("10000.00")


def load_purchase_orders():
    with open(INPUT_FILE, "r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        required_columns = {
            "po_number",
            "supplier_id",
            "quantity",
            "unit_price",
        }

        if not required_columns.issubset(reader.fieldnames or []):
            raise ValueError(
                f"Missing required columns: "
                f"{required_columns - set(reader.fieldnames or [])}"
            )

        return list(reader)


def detect_high_value_orders(purchase_orders):
    findings = []

    for order in purchase_orders:
        try:
            quantity = Decimal(order["quantity"])
            unit_price = Decimal(order["unit_price"])
        except InvalidOperation:
            raise ValueError(
                f"Invalid numeric data in PO {order['po_number']}"
            )

        if quantity <= 0 or unit_price < 0:
            raise ValueError(
                f"Invalid quantity or unit price in PO {order['po_number']}"
            )

        order_value = quantity * unit_price

        if unit_price >= UNIT_PRICE_THRESHOLD:
            findings.append({
                "record_type": "purchase_order",
                "record_id": order["po_number"],
                "issue_type": "HIGH_VALUE_ORDER",
                "supplier_id": order["supplier_id"],
                "quantity": str(quantity),
                "unit_price": f"{unit_price:.2f}",
                "order_value": f"{order_value:.2f}",
                "threshold": f"{UNIT_PRICE_THRESHOLD:.2f}",
                "risk_level": "HIGH",
                "description": (
                    "Purchase order has a unit price above "
                    "the high-value review threshold."
                ),
            })

    return findings


def export_findings(findings):
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "record_type",
        "record_id",
        "issue_type",
        "supplier_id",
        "quantity",
        "unit_price",
        "order_value",
        "threshold",
        "risk_level",
        "description",
    ]

    with open(
        OUTPUT_FILE,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(findings)


def main():
    print("=" * 70)
    print("PROJECT PROOF | HIGH-VALUE ORDER DETECTION")
    print("=" * 70)

    purchase_orders = load_purchase_orders()

    findings = detect_high_value_orders(purchase_orders)

    export_findings(findings)

    print("\nDETECTION SUMMARY")
    print("-" * 70)
    print(f"Purchase orders investigated: {len(purchase_orders)}")
    print(f"High-value orders detected: {len(findings)}")
    print(f"Unit price threshold: R{UNIT_PRICE_THRESHOLD:,.2f}")

    print("\nDETECTED ORDERS")
    print("-" * 70)

    for finding in findings:
        print(
            f"{finding['record_id']} | "
            f"Unit price: R{Decimal(finding['unit_price']):,.2f} | "
            f"Order value: R{Decimal(finding['order_value']):,.2f}"
        )

    print("\nOUTPUT")
    print("-" * 70)
    print(f"Findings exported to: {OUTPUT_FILE.relative_to(PROJECT_ROOT)}")

    print("\nDETECTION COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    main()
