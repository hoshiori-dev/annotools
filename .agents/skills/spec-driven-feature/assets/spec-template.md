# <tool_or_feature_name>

## Goal

<One paragraph: what the agent gains; which token or precision problem this solves.>

## Interface

Tool: `<tool_name>` (MCP) / `annotools.<module>.<function>` (library)

| Parameter | Type | Default | Constraints |
|---|---|---|---|
| `source` | str | — | local path or fsspec URL |

Returns: `[Image, metadata]` where metadata is one JSON line with keys `<...>`.

## Behavior

1. <Ordered processing step.>
2. <Edge case handling.>
- Error: `<condition>` → `ValueError("<message>")`

## Acceptance criteria

1. `test_ac1_<slug>`: <input> → <observable result>.
2. `test_ac2_<slug>`: ...

## Out of scope

- <What this feature deliberately does not do.>

## References

- issue #<n>; <vendor doc URL used to verify a fact>.
