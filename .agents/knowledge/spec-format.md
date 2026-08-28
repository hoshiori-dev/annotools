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

## Snippet markers (docs site)

The docs site includes the user-facing part of every spec through `pymdownx.snippets` sections (see
`.agents/knowledge/docs-site.md`). Each tool spec carries four HTML comments on their own lines, each
followed by a blank line:

- `<!-- --8<-- [start:user] -->` before `## Goal` and `<!-- --8<-- [end:user] -->` before
  `## Acceptance criteria` — section `user` = Goal + Interface + Behavior;
- `<!-- --8<-- [start:user2] -->` before `## Out of scope` and `<!-- --8<-- [end:user2] -->` before
  `## References` — section `user2` = Out of scope.

Two sections are needed because Acceptance criteria sits between Behavior and Out of scope and a snippet
section must be contiguous. `mcp-overview.md` has a single `user` section from `## Goal` to before
`## References`. A new spec must carry both sections: `just docs-check` fails (`check_paths`) when a
section referenced from `docs/mcp/tools.md` is missing.

## Rules

- Write the spec before tests; tests are named after acceptance criteria (`test_ac3_upscale_disabled`).
- Defaults in the spec must match `annotools.config.Settings`; a changed default updates both in one PR.
- Coordinates are normalized 0.0–1.0 relative to the uncropped source unless the spec states otherwise.
