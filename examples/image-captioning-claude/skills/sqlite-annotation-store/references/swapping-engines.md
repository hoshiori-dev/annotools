# Swapping the engine

The schema is plain SQL with JSON text columns; PostgreSQL and DuckDB run it with minor edits
(`strftime` defaults → `now()`, `PRAGMA`s removed, JSON columns → `jsonb`/`JSON`). Keep the same
tables, the `(item_id, run_id, kind, key)` uniqueness, and the `final_annotations` view semantics so
the tool contract and export script stay valid. Do not move to a document store: the export relies on
joins between items, runs, and annotations.
