# `annotools.geometry`

Coordinates are normalized to 0.0–1.0 relative to the **uncropped** source everywhere in annotools.
This module holds the conversions in and out of that convention, including
[`normalize_coordinates`][annotools.geometry.normalize_coordinates], which maps a model's native
answer (pixels of the image it saw, a 0–1000 space, or 0–999) back to the source.

::: annotools.geometry
