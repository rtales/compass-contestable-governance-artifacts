# Governance revision 2

The 2026-10-20 revision preserves old outputs and changes the reference implementation, not the historical fitted scores. All new audit metrics are retrospective sample diagnostics.

- `policy/decision.py`: binary entropy in bits, validated probabilities and thresholds, explicit global/topk abstention and allocation/screening, persistent-ID tie rules.
- `policy/governance.py`: exact feasible Pareto filtering and criterion tolerances, empty-set reporting, complete counts and optional finite policy grids. An explicit grid is passed in `policy.mas.grid.k` and `policy.mas.grid.gamma_entropy`; omitting it gives one candidate. `selection_report.json` records the evaluated domain. This is not validation on a separate holdout.
- `pipeline/run.py`: saves policy content, source hashes, fitted-model bytes and configuration hash separately; produces a deployment authorization gate. Infeasible or unverifiable candidates do not produce `authorized_decisions.json`. `review_required.json` is a local record with no connected human queue.
- `artifacts/validation.py`: verifies actual persisted evidence and replay; never executes a model snapshot to check its digest.

Case IDs are snapshot-scoped source-row identities. Legacy packet indices are not cross-snapshot student IDs. Labels and audit groups support evaluation; fixed-score decision reconstruction does not depend on future labels. The v2 engine does not implement medical exceptions, correction of raw features, or new model inference from packet-only data. Treat such appeal materials as illustrations, not executed capability demonstrations.

Run tests with `PYTHONPATH=src python -m pytest`. The revision environment and evidence scripts live in the parent project `revisao_artigo/`. Historical model results were not refit. Never unpickle an untrusted model merely to verify it. Local revisions are identified by file hashes in addition to Git HEAD. Old dataclass scorecards were assertions; new runs use the verifier.
