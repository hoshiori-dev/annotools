Copy this directory to `workspaces/<name>/`, then `just init-db` and place or download raw data under `data/raw/<source>/`.
`data/raw` is read-only for pipelines; `data/interim` holds previews and caches; `output/` holds exports.
