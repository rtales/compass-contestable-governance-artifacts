# Reproducibility

This repository is designed to make **offline reproduction** straightforward and verifiable.

## What is versioned
- `data/` — **processed dataset snapshots** used in the experiments (the primary reproduction tier)
- `snapshots/` — snapshot catalog and manifests
- `configs/recipes/` — executable experiment recipes
- `paper_template/` — Overleaf-ready template used to generate paper bundles
- `src/` — pipeline implementation

## Reproduction tiers
### Tier A (recommended): reproduce from versioned snapshots
Use the processed snapshot under `data/<dataset_id>/processed/` and run:
- `compass run <recipe.yaml>`

This avoids any dependency on downloading raw datasets and enables fully offline reproduction.

### Tier B: regenerate a snapshot locally (when required)
If you cannot use the versioned snapshot (e.g., licensing constraints), you can regenerate it locally and then verify it by comparing:
- the `manifest.json` checksums for processed files, and
- key run artifacts (`metrics.json`, `decision_packets*.jsonl`) produced by the recipe.

## Determinism
Recipes set explicit seeds. For comparable results across machines, also pin dependencies (see README).

## Data licensing
The code is MIT-licensed, but **datasets and derived snapshots remain subject to their original dataset licenses/terms**.
If redistribution is not permitted for a dataset, do not publish its snapshot.
