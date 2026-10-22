"""Generate deterministic, believable sample sales files using the standard library."""

import csv
import random
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "sample-data"
ROOT.mkdir(exist_ok=True)
HEADERS = [
    "Transaction Number",
    "Purchase Date",
    "Item Name",
    "Product Category",
    "Qty",
    "Selling Price",
    "Unit Cost",
    "Buyer",
]
PRODUCTS = [
    ("Basketball", "Equipment", 29.00, 14.00),
    ("Training Cones", "Training", 18.00, 7.00),
    ("Compression Sleeves", "Apparel", 24.00, 11.00),
    ("Basketball Shoes", "Footwear", 95.00, 53.00),
    ("Water Bottle", "Accessories", 14.00, 5.00),
    ("Shooting Sleeve", "Apparel", 22.00, 9.00),
    ("Ankle Support", "Accessories", 19.00, 8.00),
    ("Training Jersey", "Apparel", 36.00, 17.00),
    ("Ball Pump", "Equipment", 16.00, 6.00),
    ("Agility Ladder", "Training", 32.00, 13.00),
]
CUSTOMERS = [
    "Jordan Lee",
    "Amira Santos",
    "Noah Patel",
    "Sofia Chen",
    "Liam Rivera",
    "Maya Brooks",
    "Ethan Kim",
    "Ava Morgan",
    "Isabella Garcia",
    "Lucas Tan",
]


def make_rows(count: int, seed: int) -> list[list[str]]:
    rng = random.Random(seed)
    rows = []
    for order_index in range((count + 1) // 2):
        order = f"CS-{2025000 + order_index:06d}"
        when = date(2025, 1, 1) + timedelta(days=rng.randrange(240))
        buyer = rng.choice(CUSTOMERS)
        for product, category, price, cost in rng.sample(PRODUCTS, 2):
            rows.append(
                [
                    order,
                    when.isoformat(),
                    product,
                    category,
                    rng.choice([1, 1, 1, 2, 3]),
                    f"{price:.2f}",
                    f"{cost:.2f}",
                    buyer,
                ]
            )
            if len(rows) == count:
                return rows
    return rows


def write(name: str, headers: list[str], rows: list[list[str]]) -> None:
    with (ROOT / name).open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(headers)
        writer.writerows(rows)


small = make_rows(24, 17)
medium = make_rows(480, 19)
write("small_sales.csv", HEADERS, small)
write("medium_sales.csv", HEADERS, medium)
write(
    "sales_without_cost.csv",
    [header for header in HEADERS if header != "Unit Cost"],
    [row[:6] + row[7:] for row in small],
)
invalid = small[:4] + [
    [
        "CS-INVALID",
        "not-a-date",
        "Basketball",
        "Equipment",
        "-2",
        "oops",
        "-3",
        "Jordan Lee",
    ]
]
write("invalid_sales.csv", HEADERS, invalid)
