# ADR 001 — PostgreSQL as primary database

**Status:** Accepted

**Context:** Workspace ownership, normalized sales relationships, transactions, and aggregate reporting need reliable relational behavior.

**Decision:** Use PostgreSQL in application and Docker environments. SQLAlchemy models and Alembic migrations define the schema.

**Alternatives:** SQLite is simple but less representative of concurrent SaaS use; document stores add complexity for joins and totals.

**Consequences:** Strong constraints and transactions support reliable imports. Local setup requires a database; isolated API tests use SQLite for speed and need a future PostgreSQL integration layer.
