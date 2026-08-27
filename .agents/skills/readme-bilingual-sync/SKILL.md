---
name: readme-bilingual-sync
description: >-
  Keeps README.md and README.zh.md as faithful mirrors. Use whenever either README is edited, when
  `just readme-check` or the CI lint job reports the READMEs out of sync, when a new MCP tool or install
  path must be documented, or when the user asks to "update the README". Not for other docs under docs/.
---

# README Bilingual Sync

`README.md` (English) is the source; `README.zh.md` mirrors it section for section.

## Workflow

1. Edit `README.md` first. Keep headings, tables, and code blocks in the same order in both files.
2. Mirror the change in `README.zh.md`: translate prose and table cells; keep commands, tool names,
   parameter names, URLs, and code identical. Comments inside code blocks may be translated.
3. Run `just readme-check` (`scripts/check_readme_sync.py`): it compares the heading depth sequence and
   every fenced code block (language + content with trailing `#` comments stripped). Fix until it prints
   "in sync".
4. Re-read the Chinese file once for meaning drift (the script does not compare prose).
   Done when: the check passes and no section exists in only one file.

## Gotchas

- Both files start with a language-switch line pointing at the other README; keep it.
- A new table row (e.g. a tool) is not caught by the script — step 4 is the only guard for tables.
- `ruff format` formats Python code blocks in both READMEs; run `just fix` before the check if a block
  contains Python.
