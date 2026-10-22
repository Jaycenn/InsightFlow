# ADR 002 — FastAPI backend

**Status:** Accepted

**Context:** The service needs typed request validation, clear API documentation, and Python data processing.

**Decision:** Use FastAPI with Pydantic schemas and SQLAlchemy.

**Alternatives:** Django offers more batteries but adds framework surface for this focused API; Flask needs more manual schema and documentation work.

**Consequences:** OpenAPI documentation and typing are straightforward. Import and analytics logic remain in services to avoid bloated route functions.
