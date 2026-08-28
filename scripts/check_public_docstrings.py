#!/usr/bin/env python3
"""Check that every public annotools name (``annotools.__all__``) carries a complete Google docstring.

Rules (see .agents/knowledge/conventions.md, "Docstrings"):
- functions: ``Args`` iff the signature has parameters, ``Returns`` iff the annotation is not ``None``,
  ``Raises`` iff the body contains ``raise`` (errors that propagate from helpers must be documented by
  hand — the checker cannot see them), and an ``Examples`` block that is a doctest, always;
- classes: a summary, an ``Examples`` block, and ``Attributes`` (or pydantic ``Field`` descriptions on every field);
- ``References`` for names whose contract comes from a spec or vendor document (REFERENCED below).
Constants and type aliases have no docstring object and are skipped.

Usage: check_public_docstrings.py            exit 0 when complete, 1 with ``ERROR:`` lines otherwise.
"""

import ast
import inspect
import re
import sys

import annotools

REFERENCED = {
    "preview",
    "encode",
    "fit_size",
    "normalize_coordinates",
    "denormalize_coordinates",
    "rotated_box_to_corners",
    "is_rectangle",
    "draw_grid",
    "overlay_mask",
    "load_mask",
    "sample_frames",
    "clip_audio",
    "color_from_text",
    "Settings",
    "GridOptions",
    "draw_bboxes",
    "draw_keypoints",
    "draw_polygons",
}
SECTION = re.compile(r"^\s*(Args|Returns|Raises|Examples?|References|Attributes):\s*$", re.MULTILINE)


def sections(doc: str) -> set[str]:
    found = {m.group(1) for m in SECTION.finditer(doc)}
    return {"Examples" if s.startswith("Example") else s for s in found}


def body_raises(obj) -> bool:
    try:
        tree = ast.parse(inspect.getsource(obj))
    except (OSError, TypeError):
        return False
    return any(isinstance(node, ast.Raise) for node in ast.walk(tree))


def check_function(name: str, fn) -> list[str]:
    errors = []
    doc = inspect.getdoc(fn) or ""
    have = sections(doc)
    if not doc:
        return [f"ERROR: annotools.{name}: missing docstring"]
    params = [p for p in inspect.signature(fn).parameters.values() if p.name not in ("self", "cls")]
    want = set()
    if params:
        want.add("Args")
    if inspect.signature(fn).return_annotation not in (None, "None", inspect.Signature.empty):
        want.add("Returns")
    if body_raises(fn):
        want.add("Raises")
    want.add("Examples")
    if name in REFERENCED:
        want.add("References")
    for section in sorted(want - have):
        errors.append(f"ERROR: annotools.{name}: missing section {section}")
    if "Examples" in have and ">>>" not in doc:
        errors.append(f"ERROR: annotools.{name}: Examples is not a doctest (no >>>)")
    if "Args" in have:
        for p in params:
            if not re.search(rf"^\s+{re.escape(p.name)}( \(.*\))?:", doc, re.MULTILINE):
                errors.append(f"ERROR: annotools.{name}: Args does not describe `{p.name}`")
    return errors


def check_class(name: str, cls) -> list[str]:
    errors = []
    doc = inspect.getdoc(cls) or ""
    if not doc:
        return [f"ERROR: annotools.{name}: missing docstring"]
    have = sections(doc)
    fields = getattr(cls, "model_fields", None)
    described = fields is not None and all(f.description for f in fields.values())
    if "Attributes" not in have and not described:
        errors.append(f"ERROR: annotools.{name}: missing section Attributes (or Field descriptions)")
    if "Examples" not in have:
        errors.append(f"ERROR: annotools.{name}: missing section Examples")
    elif ">>>" not in doc:
        errors.append(f"ERROR: annotools.{name}: Examples is not a doctest (no >>>)")
    if name in REFERENCED and "References" not in have:
        errors.append(f"ERROR: annotools.{name}: missing section References")
    return errors


def main() -> int:
    errors: list[str] = []
    for name in annotools.__all__:
        obj = getattr(annotools, name)
        if inspect.isfunction(obj):
            errors += check_function(name, obj)
        elif inspect.isclass(obj):
            errors += check_class(name, obj)
    for line in errors:
        print(line)
    print(f"{len(annotools.__all__)} public names checked, {len(errors)} problem(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
