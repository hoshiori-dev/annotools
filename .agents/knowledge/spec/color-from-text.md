# color_from_text

<!-- --8<-- [start:user] -->

## Goal

Give agents (and the segmentation tool) a stable colour for any label or ID without maintaining a
palette: the same text always maps to the same colour, and slightly different text maps to an unrelated
one.

## Interface

Tool: `color_from_text` (MCP) / `annotools.color.color_from_text` (library)

| Parameter | Type | Default | Constraints |
|---|---|---|---|
| `text` | str | — | any string, including empty |

Returns (structured): `{"hex": "#rrggbb", "rgb": [r, g, b]}` with `hex` lowercase.

## Behavior

1. `digest = sha256(text.encode("utf-8"))`.
2. Hue = `digest[0:2]` as a big-endian integer / 65536 (a 0–1 hue as `colorsys` expects; × 360 for
   degrees); saturation = 0.75; lightness = 0.5. Two bytes give 65 536 hues, which already exceeds what
   8-bit RGB can distinguish on one HSL ring, so the "first 3 bytes" sketch in issue #24 was reduced to 2.
3. Convert HSL → RGB (0–255, rounded) and format `hex`.

No error conditions.

<!-- --8<-- [end:user] -->

## Acceptance criteria

1. `test_ac1_deterministic`: two calls with the same text return identical values.
2. `test_ac2_small_change_differs`: `"cat"` and `"cat "` differ.
3. `test_ac3_saturation_and_lightness`: for 100 varied strings the HSL saturation is ≥ 0.7 and the
   lightness within [0.45, 0.55].
4. `test_ac4_tool`: `Client(mcp).call_tool("color_from_text", {"text": "cat"})` returns structured
   content with `hex` matching `^#[0-9a-f]{6}$` and `rgb` of three ints in 0–255.

<!-- --8<-- [start:user2] -->

## Out of scope

Palette optimisation for contrast between arbitrary label sets.

<!-- --8<-- [end:user2] -->

## References

issue #24.
