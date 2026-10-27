
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

def read_csv(filename):
    with (DATA / filename).open(
        encoding="utf-8-sig", newline=""
    ) as f:
        return list(csv.DictReader(f))

orders = read_csv("orders.csv")
customers = read_csv("customers.csv")

customer_map = {
    row["customer_id"]: row for row in customers
}

# Pick orders with different statuses
selected = []
seen_statuses = set()

for order in orders:
    status = order.get("status", "").strip()

    if status and status not in seen_statuses:
        selected.append(order)
        seen_statuses.add(status)

    if len(selected) == 15:
        break

# Fill remaining slots if fewer than 15 statuses exist
selected_ids = {o["order_id"] for o in selected}

for order in orders:
    if len(selected) >= 15:
        break
    if order["order_id"] not in selected_ids:
        selected.append(order)
        selected_ids.add(order["order_id"])

print("\n" + "=" * 75)
print("          ZENTROMART — TEST ORDER CHEAT SHEET")
print("=" * 75)

for order in selected:
    customer = customer_map.get(order["customer_id"], {})
    phone = customer.get("phone", "")

    print(f"\nOrder ID       : {order.get('order_id', 'N/A')}")
    print(f"Status         : {order.get('status', 'N/A')}")
    print(f"Delivery PIN   : {order.get('delivery_pincode', 'N/A')}")
    print(f"Phone last 4   : {phone[-4:] if phone else 'N/A'}")
    print(f"Payment        : {order.get('payment', 'N/A')}")
    print(f"Promised date  : {order.get('promised_date', 'N/A')}")
    print("-" * 75)

print(f"\nTotal orders displayed: {len(selected)}")
print("Use these synthetic records for testing only.")
