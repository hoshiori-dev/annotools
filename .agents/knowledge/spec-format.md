# Specification Format

Load this when writing or reviewing a spec for an MCP tool, a library function that agents will build on,
or an example pipeline's output contract.

## Source Of Truth

`.agents/knowledge/spec/` holds the specs; the implementing issue quotes the goal and acceptance criteria. When they
disagree, the spec file wins and the issue is updated.

## File

`.agents/knowledge/spec/<tool-or-feature>.md`, English, one feature per file, sections in this order:

1. **Goal** — one paragraph: what the agent gains, which token or precision problem it solves.
2. **Interface** — tool name, parameter table (name, type, default, constraints), return shape including
   the metadata JSON keys. Reuse shared parameter groups by name (`PreviewOptions`, `GridOptions`).
3. **Behavior** — ordered processing steps, edge cases, and every error condition with its message.
4. **Acceptance criteria** — numbered, executable statements: a test name or a command plus the observable
   result. No "works correctly"; write "output long side ≤ 384 px for a 4000×3000 input".
5. **Out of scope** — what the feature deliberately does not do.
6. **References** — related issues, `ARCHITECTURE.md` decisions, upstream docs used to verify facts.

## Rules

- Write the spec before tests; tests are named after acceptance criteria (`test_ac3_upscale_disabled`).
- Defaults in the spec must match `annotools.config.Settings`; a changed default updates both in one PR.
- Coordinates are normalized 0.0–1.0 relative to the uncropped source unless the spec states otherwise.
