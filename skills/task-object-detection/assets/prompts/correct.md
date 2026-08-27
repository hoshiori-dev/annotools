<!-- Same system part as propose.md (cached). Item part: -->
Your boxes are drawn on the image with their index labels. For each box say "ok" or give the
corrected coordinates (same convention as before); add missing boxes with new indices; mark boxes
to delete. If everything is right, reply {"done": true}.
Return JSON only: {"done": bool, "edits": [{"index": n, "box": [..] | null, "label": "...", "confidence": 0-1}], "add": [...]}
[image with grid and indexed boxes]
