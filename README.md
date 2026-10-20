# Compass Artifacts — Snapshot-First Reproducible Pipeline

This repository provides a **recipe-driven** pipeline that emits **auditable artifacts** (decision packets, manifests, briefs, and Overleaf-ready bundles) for contestable decision-system experiments.

## Governance and manuscript revision — 20 October 2026

The reference implementation now uses explicit binary entropy in **bits**, stable case-ID tie rules, feasible Pareto filtering, deterministic policy selection, persisted evidence verification, and an authorization gate for infeasible or unverifiable candidates. The implemented tasks predict interaction correctness or student success; early-warning intervention targeting remains a separate proposed use.

- [Implementation changes and scope](docs/REVISION_V2.md)
- [Revised article: PDF](paper/artigo_revisado.pdf), [editable Word](paper/artigo_acm_corrigido.docx), and [LaTeX source](paper/latex/main.tex)
- [Article files and typesetting limitations](paper/README.md)
- [Frozen reproduction package and checksums](reproduction/2026-10-20/README.md)
- [Publication inventory and verification](docs/PUBLICATION_2026-10-20.md)

The software tests cover policy semantics, deterministic selection, evidence tampering and authorization behavior. Historical model scores were not refit. Participant-level study responses are not distributed in this update; the included study results are aggregates. No connected human-review queue, medical-exception engine, prospective fairness guarantee or measured educational benefit is claimed.

Run application checks from the repository root:

```bash
PYTHONPATH=src python -m pytest
```

## Key idea: `data/` is a versioned snapshot artifact
To maximize reproducibility, this repo versions **processed dataset snapshots** under `data/` (with checksums and schema). This enables **fully offline reproduction** without requiring raw dataset downloads.

### Included snapshots
- `synthetic_v1` — deterministic synthetic snapshot (always included)
- `oulad_v1` — processed snapshot in `data/oulad_v1/processed/`
- `assistments_2009_2010_v1` — processed snapshot in `data/assistments_2009_2010_v1/processed/`

Each snapshot includes a `manifest.json` with checksums of processed files and provenance metadata.

> **Data licensing note.** Code is MIT-licensed. Datasets and derived snapshots remain subject to their original dataset licenses/terms. If redistribution is not permitted for a dataset, do not publish its snapshot. See `docs/REPRODUCIBILITY.md`.

---

## What you get (artifacts)
A typical run produces:
- `decision_packets*.jsonl` — per-case audit trail (packet + replay trace)
- `run_metadata.json` — run manifest (policy/config hashes, environment info, dataset manifest link)
- `metrics.json` — evaluation outputs
- `decision_brief.pdf` (or Markdown fallback)
- `bundle.zip` — Overleaf-ready paper bundle (template + generated tables/figures + manifests)

---

## Design constraints
1) **No network access during execution** (`compass run` never downloads anything).
2) **Snapshot-first reproduction**: experiments default to using versioned snapshots under `data/`.

If you need to regenerate snapshots locally (e.g., due to licensing constraints), see `scripts/` and `docs/SNAPSHOTS.md`.

---

## Quickstart (Synthetic)

### 1) Create a venv (Python 3.11+)
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install -U pip
```

### 2) Install
Minimum:
```bash
pip install -e ".[core]"
```

Recommended (PDF + pandas preprocessing):
```bash
pip install -e ".[full]"
```

### 3) Run (synthetic snapshot)
```bash
make fetch-synth
make run-synth
```

Outputs will be written to a timestamped run directory (see `run_metadata.json` for the exact paths).

---

## Reproducing from versioned snapshots (Tier A)
Example:
```bash
compass run configs/recipes/oulad.yaml
compass run configs/recipes/assistments_2009_2010.yaml
```

The recipes reference the snapshot ids under `data/`.

---

## Dependency pinning (recommended)
The project supports Python 3.11–3.13. For long-lived reproducibility, pin dependencies in your environment (lockfile / constraints).
At minimum, record:
- Python version
- dependency versions (`pip freeze`)
- recipe file used

---

## Documentation
- Reproducibility contract: `docs/REPRODUCIBILITY.md`
- Snapshot policy: `docs/SNAPSHOTS.md`
- Governance revision: `docs/REVISION_V2.md`
- Manuscript and public inventory: `docs/PUBLICATION_2026-10-20.md`

---

## License
MIT (see `LICENSE`).
