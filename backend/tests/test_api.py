from datetime import datetime
from io import BytesIO
from pathlib import Path

import pandas as pd
from conftest import business, register

MAPPING = {
    "order_id": "Transaction Number",
    "date": "Purchase Date",
    "product": "Item Name",
    "category": "Product Category",
    "quantity": "Qty",
    "unit_price": "Selling Price",
    "cost": "Unit Cost",
    "customer": "Buyer",
}
CSV = b"Transaction Number,Purchase Date,Item Name,Product Category,Qty,Selling Price,Unit Cost,Buyer\nA101,2025-01-01,Basketball,Equipment,2,20,10,Jordan Lee\nA101,2025-01-01,Pump,Equipment,1,10,4,Jordan Lee\nA102,2025-01-03,Basketball,Equipment,1,20,10,Sam Tan\n"


def upload(client, business_id, headers, data=CSV, filename="sales.csv"):
    return client.post(
        f"/api/businesses/{business_id}/datasets/upload", files={"file": (filename, data)}, headers=headers
    )


def test_auth_and_ownership(client):
    assert client.get("/api/businesses").status_code == 401
    owner = register(client)
    assert (
        client.post(
            "/api/auth/register", json={"name": "Again", "email": "OWNER@example.com", "password": "safe-password-123"}
        ).status_code
        == 409
    )
    assert client.post("/api/auth/login", json={"email": "owner@example.com", "password": "wrong"}).status_code == 401
    assert (
        client.post("/api/auth/login", json={"email": "owner@example.com", "password": "safe-password-123"}).status_code
        == 200
    )
    business_id = business(client, owner)
    assert client.get(f"/api/businesses/{business_id}", headers=owner).status_code == 200
    assert (
        client.patch(f"/api/businesses/{business_id}", json={"name": "Renamed"}, headers=owner).json()["name"]
        == "Renamed"
    )
    other = register(client, "other@example.com")
    assert client.get(f"/api/businesses/{business_id}", headers=other).status_code == 404
    assert client.get(f"/api/businesses/{business_id}/analytics/overview", headers=other).status_code == 404
    assert (
        client.post(
            f"/api/businesses/{business_id}/datasets/upload", files={"file": ("x.csv", CSV)}, headers=other
        ).status_code
        == 404
    )


def test_import_analytics_filters_and_delete(client):
    headers = register(client)
    business_id = business(client, headers)
    response = upload(client, business_id, headers)
    assert response.status_code == 201, response.text
    dataset_id = response.json()["id"]
    preview = client.get(f"/api/datasets/{dataset_id}/preview", headers=headers).json()
    assert preview["total_rows"] == 3
    assert preview["suggested_mapping"]["quantity"] == "Qty"
    assert client.post(f"/api/datasets/{dataset_id}/validate", json={"mapping": MAPPING}, headers=headers).json()[
        "valid"
    ]
    assert (
        client.post(f"/api/datasets/{dataset_id}/import", json={"mapping": MAPPING}, headers=headers).status_code == 200
    )
    assert (
        client.post(f"/api/datasets/{dataset_id}/import", json={"mapping": MAPPING}, headers=headers).status_code == 409
    )
    kpis = client.get(f"/api/businesses/{business_id}/analytics/overview", headers=headers).json()["kpis"]
    assert kpis == {
        "revenue": 70,
        "gross_profit": 36,
        "profit_margin": 51.43,
        "orders": 2,
        "units": 4,
        "average_order_value": 35,
        "cost_available": True,
    }
    filtered = client.get(
        f"/api/businesses/{business_id}/analytics/sales?start_date=2025-01-03&product=Basketball&category=Equipment&customer=Sam%20Tan",
        headers=headers,
    ).json()["kpis"]
    assert filtered["revenue"] == 20
    assert filtered["orders"] == 1
    options = client.get(f"/api/businesses/{business_id}/analytics/options", headers=headers)
    assert "Basketball" in options.json()["products"]
    assert client.delete(f"/api/datasets/{dataset_id}", headers=headers).status_code == 204
    assert (
        client.get(f"/api/businesses/{business_id}/analytics/overview", headers=headers).json()["kpis"]["revenue"] == 0
    )


def test_invalid_upload_mapping_and_missing_cost(client):
    headers = register(client)
    business_id = business(client, headers)
    assert upload(client, business_id, headers, b"bad", "sales.txt").status_code == 415
    assert upload(client, business_id, headers, b"", "sales.csv").status_code == 400
    assert upload(client, business_id, headers, b"\xff\xfe", "sales.csv").status_code == 400
    bad = upload(client, business_id, headers, CSV.replace(b"2,20,10", b"-2,20,10"))
    dataset_id = bad.json()["id"]
    result = client.post(f"/api/datasets/{dataset_id}/validate", json={"mapping": MAPPING}, headers=headers).json()
    assert result["valid"] is False and result["errors"][0]["row"] == 2
    assert (
        client.post(f"/api/datasets/{dataset_id}/import", json={"mapping": MAPPING}, headers=headers).status_code == 422
    )
    no_cost = CSV.replace(b",Unit Cost", b",Removed Cost").replace(b",10,Jordan", b",10,Jordan")
    response = upload(client, business_id, headers, no_cost, "no_cost.csv")
    assert response.status_code == 201
    mapping = {**MAPPING, "cost": ""}
    assert (
        client.post(
            f"/api/datasets/{response.json()['id']}/import", json={"mapping": mapping}, headers=headers
        ).status_code
        == 200
    )
    kpis = client.get(f"/api/businesses/{business_id}/analytics/overview", headers=headers).json()["kpis"]
    assert kpis["gross_profit"] is None and kpis["profit_margin"] is None


def test_xlsx_upload_and_cross_account_dataset_access(client):
    headers = register(client)
    business_id = business(client, headers)
    frame = pd.DataFrame(
        {
            "Transaction Number": ["X1"],
            "Purchase Date": [datetime(2025, 2, 1)],
            "Item Name": ["Training Cones"],
            "Qty": [2],
            "Selling Price": [15],
        }
    )
    stream = BytesIO()
    frame.to_excel(stream, index=False)
    response = upload(client, business_id, headers, stream.getvalue(), "sales.xlsx")
    assert response.status_code == 201, response.text
    dataset_id = response.json()["id"]
    mapping = {field: MAPPING[field] for field in ("order_id", "date", "product", "quantity", "unit_price")}
    assert (
        client.post(f"/api/datasets/{dataset_id}/import", json={"mapping": mapping}, headers=headers).status_code == 200
    )
    other = register(client, "other@example.com")
    assert client.get(f"/api/datasets/{dataset_id}/preview", headers=other).status_code == 404
    assert client.delete(f"/api/datasets/{dataset_id}", headers=other).status_code == 404


def test_medium_sample_can_be_imported(client):
    headers = register(client)
    business_id = business(client, headers)
    path = Path(__file__).resolve().parents[2] / "sample-data" / "medium_sales.csv"
    response = upload(client, business_id, headers, path.read_bytes())
    assert response.status_code == 201
    dataset_id = response.json()["id"]
    imported = client.post(f"/api/datasets/{dataset_id}/import", json={"mapping": MAPPING}, headers=headers)
    assert imported.status_code == 200, imported.text
    assert imported.json()["record_count"] == 480
