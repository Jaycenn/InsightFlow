# Architecture

```mermaid
flowchart LR
  UI[React / TypeScript] --> API[FastAPI REST API]
  API --> Services[Import and analytics services]
  Services --> ORM[SQLAlchemy]
  ORM --> PG[(PostgreSQL)]
```

The React UI manages navigation, forms, states, and charts. TanStack Query caches server results and invalidates them after imports/deletions. FastAPI handles request validation and auth. Import and analytics logic live in `backend/app/services`; SQLAlchemy models represent the normalized database. Alembic handles schema changes.

```mermaid
flowchart LR
  File[CSV / XLSX] --> Bound[Size and extension checks]
  Bound --> Parse[Pandas parsing]
  Parse --> Preview[Preview and suggested mapping]
  Preview --> Validate[Row validation]
  Validate --> Tx[Transactional import]
  Tx --> DB[(PostgreSQL)]
  DB --> Agg[SQL aggregation]
  Agg --> Charts[Dashboard API and charts]
```

Uploaded bytes are stored in `datasets.file_data` so preview and validation reuse the same exact source. `import_rows` creates/reuses business-scoped products and customers, writes sales, and commits once. If it fails, the request rolls back. Analytics use SQL aggregations and grouped queries; the frontend never downloads all sales rows. Every analytics section uses the same filter predicates.

The backend routes are kept in `api.py` for the compact MVP; data parsing and analytics are separate service modules. A larger codebase could split the router further by domain. The frontend separates auth, datasets, analytics, shared UI, and API transport.
