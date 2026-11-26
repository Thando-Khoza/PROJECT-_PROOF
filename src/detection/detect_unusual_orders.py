
import csv
from pathlib import Path
from statistics import median


PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = PROJECT_ROOT / "data" / "raw" / "purchase_orders.csv"
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_FILE = OUTPUT_DIR / "unusual_order_findings.csv"

MAD_MULTIPLIER = 3.5


def load_purchase_orders():
    with open(INPUT_FILE, "r", newline="", encoding="utf-8-sig") as file:
        return list(csv.DictReader(file))


def calculate_median_absolute_deviation(values):
    middle_value = median(values)

    deviations = [
        abs(value - middle_value)
        for value in values
    ]

    return median(deviations)


def calculate_modified_z_score(value, middle_value, mad):
    if mad == 0:
        return 0

    return 0.6745 * (value - middle_value) / mad


def detect_unusual_orders(orders):
    unit_prices = [
        float(order["unit_price"])
        for order in orders
    ]

    order_totals = [
        float(order["order_total"])
        for order in orders
    ]

    median_unit_price = median(unit_prices)
    median_order_total = median(order_totals)

    mad_unit_price = calculate_median_absolute_deviation(unit_prices)
    mad_order_total = calculate_median_absolute_deviation(order_totals)

    findings = []

    for order in orders:
        unit_price = float(order["unit_price"])
        order_total = float(order["order_total"])

        unit_price_score = calculate_modified_z_score(
            unit_price,
            median_unit_price,
            mad_unit_price
        )

        order_total_score = calculate_modified_z_score(
            order_total,
            median_order_total,
            mad_order_total
        )

        reasons = []

        if unit_price_score > MAD_MULTIPLIER:
            reasons.append("UNUSUALLY_HIGH_UNIT_PRICE")

        if order_total_score > MAD_MULTIPLIER:
            reasons.append("UNUSUALLY_HIGH_ORDER_TOTAL")

        if reasons:
            findings.append({
                "record_type": "purchase_order",
                "record_id": order["po_number"],
                "issue_type": "UNUSUAL_ORDER_VALUE",
                "supplier_id": order["supplier_id"],
                "unit_price": round(unit_price, 2),
                "order_total": round(order_total, 2),
                "unit_price_score": round(unit_price_score, 2),
                "order_total_score": round(order_total_score, 2),
                "risk_reason": "; ".join(reasons)
            })

    return (
        findings,
        median_unit_price,
        median_order_total,
        mad_unit_price,
        mad_order_total
    )


def main():
    print("=" * 70)
    print("PROJECT PROOF | UNUSUAL ORDER PATTERN DETECTION")
    print("=" * 70)

    orders = load_purchase_orders()

    (
        findings,
        median_unit_price,
        median_order_total,
        mad_unit_price,
        mad_order_total
    ) = detect_unusual_orders(orders)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "record_type",
        "record_id",
        "issue_type",
        "supplier_id",
        "unit_price",
        "order_total",
        "unit_price_score",
        "order_total_score",
        "risk_reason"
    ]

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(findings)

    print("\nDETECTION SUMMARY")
    print("-" * 70)
    print(f"Purchase orders investigated: {len(orders)}")
    print(f"Unusual orders detected: {len(findings)}")
    print(f"Median unit price: R{median_unit_price:,.2f}")
    print(f"Median order total: R{median_order_total:,.2f}")
    print(f"Unit price MAD: R{mad_unit_price:,.2f}")
    print(f"Order total MAD: R{mad_order_total:,.2f}")
    print(f"Modified Z-score threshold: {MAD_MULTIPLIER}")

    print("\nDETECTED ORDERS")
    print("-" * 70)

    for finding in findings:
        print(
            f"{finding['record_id']} | "
            f"Unit price: R{finding['unit_price']:,.2f} | "
            f"Order total: R{finding['order_total']:,.2f} | "
            f"Reason: {finding['risk_reason']}"
        )

    print("\nOUTPUT")
    print("-" * 70)
    print(f"Findings exported to: {OUTPUT_FILE.relative_to(PROJECT_ROOT)}")

    print("\nDETECTION COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    main()
