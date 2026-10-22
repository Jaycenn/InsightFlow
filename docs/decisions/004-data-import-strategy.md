# ADR 004 — Preview, map, validate, import

**Status:** Accepted

**Context:** Spreadsheet headers vary widely, and users need row-level feedback before data enters reporting.

**Decision:** Store bounded source bytes in the dataset row. Parse with Pandas for preview and validation. Let users map headers to canonical fields. Commit normalized sales in one transaction after all rows pass validation.

**Alternatives:** Requiring a fixed template blocks common exports; row-by-row commits can leave partial imports; background jobs add operational complexity for 5 MB files.

**Consequences:** Imports are understandable and atomic for small files. Database storage and synchronous processing limit scale; object storage and workers are logical next steps.
