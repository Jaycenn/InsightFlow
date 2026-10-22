# InsightFlow

**Smart Business Analytics Platform** · Portfolio MVP 0.1.0

InsightFlow helps a small-business owner turn CSV or Excel sales exports into understandable revenue, product, customer, and order insights. The application follows a complete workflow: create an account, create a business workspace, upload a dataset, preview and map columns, validate it, import it, and explore the resulting dashboards.

## What it does

- Email/password registration and sign-in; JWT protected API routes.
- Owner-isolated business workspaces with rename and selection.
- CSV and XLSX upload, preview, suggested column mapping, row-level validation, transactional import, dataset list and deletion.
- Revenue, gross profit, profit margin, orders, units, and average order value calculated from imported sales. Profit is explicitly unavailable if any matching sale has no cost.
- Daily revenue and order trends, categories, top and lower-performing products, customer spending, and recent transactions.
- Shared date, product, category, and customer filters across each analytics view.
- Responsive Overview, Sales, Products, Customers, Datasets, and Business settings screens.

The sample data describes **Courtside Supply Co.**, a sports equipment retailer. Production analytics never use sample or hard-coded values.

## Architecture

React 19 + TypeScript + Vite + TanStack Query + Recharts → FastAPI → services → SQLAlchemy → PostgreSQL. Pandas parses CSV/XLSX for preview and normalization. Alembic owns schema migrations. See [architecture](docs/architecture.md), [database](docs/database.md), and [API](docs/api.md).

```
frontend/       React application and UI tests
backend/        FastAPI application, Alembic migration, API tests
sample-data/    Small, medium, invalid, and missing-cost examples
scripts/        Sample generator and optional API seed
docs/           Requirements, decisions, architecture, API, operations
compose.yaml    PostgreSQL, API, and static frontend
```

## Quick start with Docker

Requires Docker Compose. Copy `.env.example` to `.env`, replace `POSTGRES_PASSWORD` and `JWT_SECRET` with strong local values, then run:

```sh
docker compose up --build
```

Open `http://localhost:5173`; API documentation is at `http://localhost:8000/docs`. Compose waits for PostgreSQL and runs `alembic upgrade head` before serving the API. No demo account is created automatically.

## Local development

Requires Python 3.11+, Node 22+, pnpm 11+, and PostgreSQL 16+. Create a PostgreSQL database and user, copy `.env.example` to `.env`, and set `DATABASE_URL`, `JWT_SECRET`, and `CORS_ORIGINS`. The provided `pnpm-workspace.yaml` locates the package store and cache on D: for this workspace; change those machine-specific paths if using this project elsewhere.

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e '.[dev]'
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

On macOS/Linux use `.venv/bin/python` in place of `.\.venv\Scripts\python.exe`. In another terminal:

```sh
cd frontend
pnpm install
pnpm dev
```

The Vite development server proxies `/api` to `http://localhost:8000`. For separate hosting, set `VITE_API_URL` at build time and configure `CORS_ORIGINS` on the backend.

### Data and demo

Upload `sample-data/small_sales.csv` from Datasets. Suggested mappings match its headers. `medium_sales.csv` contains 480 rows; `invalid_sales.csv` demonstrates validation; `sales_without_cost.csv` demonstrates unavailable profit metrics. Regenerate examples with `python scripts/generate_samples.py`.

Optional API seed, after starting the application:

```powershell
$env:INSIGHTFLOW_EMAIL='you@example.com'
$env:INSIGHTFLOW_PASSWORD='your-own-long-password'
python scripts/seed_demo.py
```

On macOS/Linux use `export` for those environment variables. The script registers or signs in, creates Courtside Supply Co., and imports `medium_sales.csv`. Never use a shared demo password in a public deployment.

### Quality checks

```powershell
cd backend
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\pytest.exe
cd ../frontend
pnpm lint
pnpm typecheck
pnpm test
pnpm build
```

API tests use isolated SQLite for speed, while the application and migrations target PostgreSQL. CI configuration is provided in `.github/workflows/ci.yml`. See [testing](docs/testing.md).

### Migrations

From `backend/`, run `alembic upgrade head`. For a schema change, edit models then run `alembic revision --autogenerate -m "description"`, review the generated SQL, and run `alembic upgrade head`. To reset *local development data*, stop the app and recreate the local database with your PostgreSQL tooling, then rerun migrations. Do not reset a production database.

## Security and deployment

Passwords use Argon2 through `pwdlib`; JWTs expire after eight hours. Every business and dataset route checks ownership. Uploads are size limited and parsed before storage. SQLAlchemy uses bound parameters. See [security](docs/security.md) and [deployment](docs/deployment.md).

## Known limitations and roadmap

This MVP stores uploaded file bytes in PostgreSQL (5 MB default) and imports synchronously, so large files need a background worker and object storage. Authentication uses a browser-stored access token; production deployment should add refresh/session handling and stronger browser token protection. Orders are counted by unique `order_id` within a business. Currency is displayed as USD, with no conversion. Rows are validated for ISO dates (`YYYY-MM-DD`). Dataset deletion removes its sales but may leave unused product/customer labels in the database; analytics ignore those labels.

Planned: comparison periods and richer filters (1.1), inventory and low-stock warnings (1.2), PDF/Excel reports (1.3), forecasting (2), and an explainable AI analyst only after the core analytics matures (3).

## License

MIT. See [LICENSE](LICENSE).
