# REST API

Base URL: `/api`. JSON is used except multipart upload. Protected endpoints require `Authorization: Bearer <access_token>`. All errors use `{ "error": { "code": string, "message": string, "details": [] } }`. FastAPI's live OpenAPI explorer is at `/docs`.

| Method | Endpoint | Purpose | Auth | Success |
| --- | --- | --- | --- | --- |
| POST | `/auth/register` | Name, email, password → token and user | No | 201 |
| POST | `/auth/login` | Email, password → token and user | No | 200 |
| GET | `/auth/me` | Current user | Yes | 200 |
| GET | `/businesses` | Owned businesses | Yes | 200 |
| POST | `/businesses` | `{name}` creates business | Yes | 201 |
| GET | `/businesses/{id}` | Owned business | Yes | 200 |
| PATCH | `/businesses/{id}` | `{name}` renames business | Yes | 200 |
| GET | `/businesses/{id}/datasets` | Business dataset list | Yes | 200 |
| POST | `/businesses/{id}/datasets/upload` | Multipart `file` CSV/XLSX | Yes | 201 |
| GET | `/datasets/{id}` | Dataset metadata | Yes | 200 |
| GET | `/datasets/{id}/preview` | Columns, eight rows, suggestions | Yes | 200 |
| POST | `/datasets/{id}/validate` | `{mapping: {canonical: source}}` → validation | Yes | 200 |
| POST | `/datasets/{id}/import` | Same mapping → imported metadata | Yes | 200 |
| DELETE | `/datasets/{id}` | Remove dataset and its sales | Yes | 204 |
| GET | `/businesses/{id}/analytics/options` | Available product/category/customer filters | Yes | 200 |
| GET | `/businesses/{id}/analytics/{section}` | `overview`, `sales`, `products`, `customers` | Yes | 200 |
| GET | `/health` | Service status | No | 200 |

Analytics query parameters: optional ISO `start_date`, `end_date`, and exact-match `product`, `category`, `customer`. The response contains `kpis`, `trends`, `products`, `categories`, `customers`, and `recent_sales`; all fields honor the same filters. The sections currently share one response shape so the UI can reuse cards and tables.

Example import body:

```json
{"mapping":{"order_id":"Transaction Number","date":"Purchase Date","product":"Item Name","quantity":"Qty","unit_price":"Selling Price","category":"Product Category","cost":"Unit Cost","customer":"Buyer"}}
```

Typical errors: 400 invalid file/filter, 401 invalid credentials or missing/expired token, 404 inaccessible business/dataset, 409 duplicate email or repeat import, 413 file too large, 415 unsupported file, 422 invalid request or mapped rows, 500 import transaction failure. Inaccessible resources return 404 to avoid revealing another owner's IDs.
