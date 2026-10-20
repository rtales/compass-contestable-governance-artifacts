# Frozen scientific revision package

This package preserves the original directory layout needed by the scientific reanalysis. It predates the final Word formatting pass; the current editable Word is in `../../paper/`. The ZIP is retained byte for byte with its original manifest and SHA-256 checksum.

Verify, extract and run the computational reanalysis:

```bash
shasum -a 256 -c pacote_revisao.sha256
unzip pacote_revisao.zip -d extracted
cd extracted
python -m venv .venv
. .venv/bin/activate
python -m pip install -r revisao_artigo/requirements.lock
python revisao_artigo/scripts/recalcular_evidencias.py --skip-study
```

The lock records the tested Python 3.12 revision environment. Platform and Python-version compatibility should be checked when installing it elsewhere. The application supports Python 3.11–3.13 separately from this exact analysis environment.

Participant-level responses and free-text study evidence are excluded. `--skip-study` deliberately omits the human-study recomputation; it never generates replacement participants. Published study aggregates remain included. Historical fixed-score packets support replay and retrospective checks, not new inference or feature-dependent exceptions. The ZIP contains the earlier scientific source snapshot; the Git repository contains the current publication and documentation updates.
