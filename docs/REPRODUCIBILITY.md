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

## Current manuscript fixed-score reproduction

For the current manuscript, use [the 2026-10-21 runner](../reproduction/2026-10-21/README.md). It verifies the published source identity, reconstructs frozen selection/test outputs, checks all seven export vectors and 20 tests, and recomputes full-sample policy and uncertainty results. This fixed-score route is distinct from generating new predictor runs through the snapshot recipes above. Numerical matching does not establish temporal/student-disjoint generalization.

The article's local archive path `revisao_artigo/rodada4/pacote_avaliador.zip` maps to `reproduction/2026-10-21/pacote_avaliador.zip` here, with the identical SHA-256. The old 2026-10-20 archive is retained as immutable scientific provenance, not the current article.

Participant-level questionnaire data are excluded. Published case counts support regeneration of the aggregate plot, but not paired statistical tests or participant confidence intervals. The optional study reanalysis requires an authorized local ZIP and is explicitly separated from default public reproduction. No synthetic participants are substituted.
