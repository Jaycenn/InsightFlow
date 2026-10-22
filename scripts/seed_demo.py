"""Optional API-driven demo seed. Set INSIGHTFLOW_EMAIL and INSIGHTFLOW_PASSWORD."""

import json
import os
import urllib.error
import urllib.request
from pathlib import Path

BASE = os.getenv("INSIGHTFLOW_API_URL", "http://localhost:8000").rstrip("/")
EMAIL = os.environ["INSIGHTFLOW_EMAIL"]
PASSWORD = os.environ["INSIGHTFLOW_PASSWORD"]


def request(
    path: str, payload=None, token: str | None = None, content_type="application/json"
):
    data = json.dumps(payload).encode() if payload is not None else None
    headers = {"Content-Type": content_type}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(BASE + path, data=data, headers=headers)
    with urllib.request.urlopen(req) as response:
        return json.load(response)


try:
    auth = request(
        "/api/auth/register",
        {"name": "Demo Owner", "email": EMAIL, "password": PASSWORD},
    )
except urllib.error.HTTPError as exc:
    if exc.code != 409:
        raise
    auth = request("/api/auth/login", {"email": EMAIL, "password": PASSWORD})
token = auth["access_token"]
business = request("/api/businesses", {"name": "Courtside Supply Co."}, token)
path = Path(__file__).resolve().parents[1] / "sample-data" / "medium_sales.csv"
boundary = "InsightFlowDemoBoundary"
body = (
    f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="medium_sales.csv"\r\nContent-Type: text/csv\r\n\r\n'.encode()
    + path.read_bytes()
    + f"\r\n--{boundary}--\r\n".encode()
)
upload = urllib.request.Request(
    BASE + f"/api/businesses/{business['id']}/datasets/upload",
    data=body,
    headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": f"multipart/form-data; boundary={boundary}",
    },
)
with urllib.request.urlopen(upload) as response:
    dataset = json.load(response)
mapping = {
    "order_id": "Transaction Number",
    "date": "Purchase Date",
    "product": "Item Name",
    "category": "Product Category",
    "quantity": "Qty",
    "unit_price": "Selling Price",
    "cost": "Unit Cost",
    "customer": "Buyer",
}
result = request(f"/api/datasets/{dataset['id']}/import", {"mapping": mapping}, token)
print(f"Imported {result['record_count']} rows into {business['name']}.")
