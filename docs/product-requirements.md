# Product requirements

## Problem and audience

Small-business owners often have CSV or Excel exports but no straightforward way to turn them into actionable sales insights. InsightFlow serves owners and managers of shops, online sellers, and local distributors who understand spreadsheets but do not need to know SQL or Python.

## User goals and MVP scope

Users can register, create isolated business workspaces, import sales files with flexible column names, find data errors before import, and inspect true sales analytics. The app includes Overview, Sales, Products, Customers, Datasets, and Business settings. It supports responsive desktop and mobile layouts and helpful empty/error/loading states.

## Functional requirements and acceptance criteria

| Requirement | Acceptance criterion |
| --- | --- |
| Authentication | Register with name, email, and password; sign in; protected API rejects missing/invalid/expired token. |
| Ownership | A different account cannot read, change, or import another owner's workspace or dataset by changing IDs. |
| Import | CSV/XLSX up to configured size is previewed, mapped to canonical fields, validated, and imported transactionally. |
| Analytics | Revenue is sum of quantity × unit price; orders are unique order IDs; profit is only shown when every matching sale has cost. |
| Filters | Date, product, category, and customer predicates apply to all metrics and charts returned by the analytics endpoint. |
| Dataset lifecycle | User can list, preview, and delete their datasets; deleting removes imported sales. |

## Business rules

Required fields: `order_id`, `date`, `product`, `quantity`, `unit_price`. Optional: `category`, `cost`, `customer`. Quantities must be positive; prices and costs non-negative. Dates use ISO `YYYY-MM-DD`. Identical rows within one file are rejected. A dataset can only be imported once. A missing cost makes profit unavailable for the filtered result. Empty analytics produce zero revenue/orders and no chart entries.

## Non-functional requirements

The API uses ownership checks, parameterized ORM queries, password hashing, expiring JWTs, bounded upload size, and consistent user-facing errors. The UI has semantic controls, keyboard access, visible focus styles, and responsive layouts. Tables show limited records where needed; charts receive aggregated data.

## Excluded scope and success

Multi-user business teams, currencies beyond USD, inventory, scheduled reports, forecasting, and AI advice are out of MVP scope. Success means a new user can import the provided sample file and inspect mathematically correct dashboards without editing its headers. Future releases may add comparison periods, inventory, exports, forecasting, and AI explanations.
