# Testing

Backend API tests cover registration, duplicate email, login, invalid credentials, authentication, business editing and ownership, CSV and XLSX upload, malformed/unsupported files, mapping validation, import, analytics math, filters, missing-cost behavior, repeat import, and dataset ownership/deletion. They use FastAPI `TestClient` with a fresh SQLite in-memory database per test. This makes logic tests fast; it does not replace a PostgreSQL integration test for database-specific behavior.

Frontend tests use Vitest, jsdom, and React Testing Library for form validation and a key empty state. Manual browser review should cover upload/mapping and responsive layout. An end-to-end Playwright suite is not included because the MVP test environment does not bundle stable browser and PostgreSQL services together.

From `backend/`:

```sh
ruff check .
pytest
```

From `frontend/`:

```sh
pnpm lint
pnpm typecheck
pnpm test
pnpm build
```

CI runs the same checks. Coverage focuses on business behavior, financial formulas, access control, and import failure paths. It does not test third-party libraries or duplicate their internals. A production release should add PostgreSQL migration/integration tests and a browser flow test.
