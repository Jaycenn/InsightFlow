# ADR 003 — REST API

**Status:** Accepted

**Context:** React needs resource-based account, workspace, dataset, and analytics operations.

**Decision:** Expose JSON REST endpoints with conventional HTTP methods and status codes; multipart is reserved for file upload.

**Alternatives:** GraphQL adds schema and query complexity without a clear MVP need; server-rendered pages reduce independent UI flexibility.

**Consequences:** Resource ownership and error handling are explicit. Analytics sections currently return one common response model, which may be narrowed if client needs diverge.
