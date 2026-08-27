# <project name>

<One paragraph: what this example project annotates, with which SDK, and where results go.>

## Map
- `spec/task.md` — the contract (read first); `spec/prompts/` — prompt templates
- `config/` — model, effort, budget; `src/` — pipeline and execution-agent tools
- `workspaces/<task>/` — data (`raw` read-only), `dataset.db`, `output/`
- `skills/` — skills the execution agent may load

## Rules
- Never modify `data/raw/`; the DB stores file pointers, never bytes.
- Execution agents are confined to `workspaces/<task>/` by the tool allowlist in `src/`.
- Changing `spec/` requires the user's confirmation; prompts and export follow the spec.

## Commands
- `just init` · `just trial` (1–3 items, shows previews) · `just run` · `just export` · `just check`

## Usage record
<model, items, tokens in/out, cost, wall time of the last full run>
