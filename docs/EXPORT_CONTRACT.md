# Evaluated fixed score export contract

This documents the supported path in the current implementation; it adds no runtime behavior or institutional authorization.

- R: `replay_only` in `scripts/verify_fault_contracts.py` applies the accessible policy to supplied scores and IDs and matches the recorded decision states. It does not check the expected whole-batch roster.
- V: additional checks in `verify_run` pass: required fields, schema/unit/epsilon/scope, policy/content digests, dataset-manifest and model-byte digests, packet digests, unique roster equality to run metadata, and recomputed entropy (`atol=1e-12`, `rtol=0`).
- I = R AND V: complete acceptance by `verify_run`. The legacy result field `replayable` means I, not the narrower R used in the experiment.
- F: `assess_constraints` accepts the computable empirical metrics under restrictions actually configured and enabled. A required non-estimable gap fails. An absent restriction is not certified by an empty violations list.
- A = I AND F: the runner records technical export permission and emits `authorized_decisions.json` only if accepted; otherwise it preserves candidate evidence and writes `review_required.json` without delivering a human review.

Hence A implies I and I implies R. The seven fixtures yield: control 111; four evidence faults 100; unavailable policy 000; constraint violation 110. The 100 and 110 cases disprove the converses; the predicates are not logically independent.

These equivalences apply to a supported nonempty batch with finite probability scores, persistent IDs, accessible policy/metadata and computable audit inputs, including the specified failure handling. They are not sufficient conditions for legitimate deployment. The expected roster is anchored in unsigned local metadata. Digests do not establish authenticity against coordinated rewriting, truth of labels, legitimate policy authorship, that a model generated the scores, population fairness, or institutional remedy. The historical predictors are not re-executed by hashing their bytes.

Code correspondence: `src/compass/artifacts/validation.py`, `src/compass/policy/governance.py`, `src/compass/pipeline/run.py`, and `scripts/verify_fault_contracts.py`. No API field is renamed by this documentation. The publication manifest and frozen computational snapshot identify the evaluated source. The reproduction runner checks the live source against that inventory before executing; the older published base commit is a distinct version.
