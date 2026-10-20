# Publication update — 20 October 2026

The original reference application did not persist sufficient evidence to substantiate every replay claim and did not explicitly implement the stated feasible-Pareto selection procedure. This revision records policy and fitted-model hashes separately, validates persisted packets, uses stable case identifiers for score ties, implements feasible Pareto filtering with documented tolerances, and prevents an authorized-decision export when the gate fails. Binary entropy is explicitly measured in bits. OULAD positive labels are Pass/Distinction: these experiments predict reported success, rather than implement an early-warning intervention.

## Published inventory

- `src/compass/`, recipe configurations and `tests/test_governance_v2.py`: current reference implementation and regression checks.
- `paper/latex/`: 32 transitive manuscript build inputs, including bibliography and figure.
- `paper/artigo_revisado.pdf`: reviewed scientific PDF, 10 pages.
- `paper/artigo_acm_corrigido.docx`: editable two-column Word export, 12 pages in the checked LibreOffice rendering.
- `paper/results/`: aggregate reports, candidate grids, case counts and figure alternative text.
- `reproduction/2026-10-20/`: unchanged frozen scientific ZIP, original checksum and manifest, dependency lock and reproduction instructions.
- `paper/publication_manifest.json`: byte counts and SHA-256 hashes for published manuscript and reproduction files (excluding the manifest itself).

## Validation

The local Python 3.12 revision environment passed all 16 tests using `PYTHONPATH=src python -m pytest`. The final source also uses quoting compatible with pre-3.12 f-string syntax; a separate Python 3.11 execution was not performed. Published manuscript build files were compared byte for byte with the reviewed source. The copied ZIP was checked for archive integrity and its original SHA-256 checksum.

The frozen scientific snapshot ID is `166012d5587ca9c66afc177f808691f4adc109d2050a58f23c1ff4110a0ae1b0`. The ZIP SHA-256 is `e97e6ca3c4717e0f8983cbbf8a5330dc590d0f778c80b1058e056b0452f4ec7b`. It predates the final Word formatting pass and publication documentation; the current Git tree and frozen analysis snapshot serve different reproducibility purposes.

## Scope and limitations

The historical fixed scores were not refitted. Retrospective policy selection is not an independent holdout validation. No human review queue, medical exceptions or feature-dependent appeal engine is connected. The 16-person exploratory study used volunteers, with no formal ethics-committee approval or exemption. Participant-level responses are excluded from this publication; aggregate reports remain available.

Word contains native editable equations. The checked LibreOffice renderer substitutes some mathematical fonts and sizes; native Microsoft Word rendering and ACM TAPS compliance were not verified. See `paper/README.md`.

Local experiment outputs, platform files, error logs and regenerated package metadata are excluded from this update. Existing dataset snapshots retain their original terms; publishing the code does not relicense data or third-party templates.
