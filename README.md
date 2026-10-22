# Governing by Artifacts scientific reproduction

Reference code, manuscript and fixed-score evidence for **Governing by Artifacts: An Auditable Constraint-Based Framework for Contestable Educational Decision Systems**.

The [current manuscript](paper/artigo_revisado.pdf) has 13 pages, 17 tables and five authors. Its [LaTeX project](paper/latex/main.tex) is the scientific source. The evaluated system predicts interaction correctness or student success and studies decision-policy mechanics; it does not demonstrate early-warning intervention benefit.

## Reproduce the reported analyses

Use Python 3.12 and the tested dependency lock:

```bash
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install -r reproduction/2026-10-21/requirements.lock
python reproduction/2026-10-21/reproduce.py --output-dir reproduction/2026-10-21/actual
```

On Windows activate `.venv\Scripts\activate` instead. Installing dependencies may require network access; the analysis uses local versioned inputs. Other Python versions/platforms may require compatibility work.

The command verifies publication hashes, confirms that 52 live source/test files match the evaluated snapshot, and reproduces:

- The retrospective validation/test partition, frozen threshold choices, test metrics and intervals.
- Seven synthetic fault fixtures and the nested export contract, plus 20 application tests.
- Three 80-candidate policy grids, fixed-budget selections, variable-budget profiles and taxonomy replay.
- Calibration, entropy/error correlation, row-bootstrap intervals and group-specific selective risks.
- The diagnostic figure from published aggregate case counts.

Expected outputs are compared with stored results. Full-sample JSON is compared structurally, three candidate CSVs byte for byte, and figure pixels exactly. This is reproduction of fixed scores, not refitting historical predictors. The study's individual-level analysis is **skipped explicitly** unless an authorized local response ZIP is supplied; no substitute participants are generated.

## Scientific artifacts

| Artifact | Purpose |
| --- | --- |
| [Manuscript PDF](paper/artigo_revisado.pdf) and [LaTeX source](paper/latex/main.tex) | Current scientific text, figures, tables and bibliography |
| [Numerical reports](paper/results/) | Full precision metrics, case counts and expected computational outcomes |
| [Reproduction instructions and scope](reproduction/2026-10-21/README.md) | Portable execution, fixed snapshot and restricted-study boundaries |
| [Export contract](docs/EXPORT_CONTRACT.md) | Replay, evidence verification, constraints and technical export permission |
| [Publication manifest](paper/publication_manifest.json) | SHA-256 identity of manuscript, code, scripts and scientific inputs |
| [Citation metadata](CITATION.cff) | Software and manuscript attribution |
| [Publication inventory](docs/PUBLICATION_2026-10-21.md) | Included artifacts, exclusions and verification scope |

The frozen snapshot mentioned in the manuscript is distributed as `reproduction/2026-10-21/pacote_avaliador.zip`, SHA-256 `108d5ff9f550dec882b6691b24ec2b5340c5515ab3fd550a198e32e72e947688`. It is the identical archive identified by its author's local path in the PDF. Its embedded paper is historical; `paper/` contains the current consolidated manuscript. The `2026-10-20` archive remains immutable and supplies historical comparison CSVs.

## Interpretation and data access

Entropy is in bits. Capacity K is a ceiling. `utility_at_k` is a legacy name for the observed positive-outcome rate among actually selected cases (PosRate), not intervention benefit. The gate grants technical export permission under declared empirical checks; it does not establish institutional authority or deliver human review. See the manuscript for retrospective sampling and uncertainty limits.

The exploratory human study has 16 volunteers and eight scenarios. No formal ethics-committee approval or exemption was obtained. Diagnosis and remediation correctness coincide across the responses. Participant responses and free text are not published; aggregate figures cannot reproduce paired individual-level statistical tests.

The code is [MIT licensed](LICENSE). ASSISTments, OULAD and derived snapshots retain their original data terms. Case packets contain snapshot-scoped IDs, scores, evaluation labels and audit groups, not raw questionnaire responses. [Data and reproducibility details](docs/REPRODUCIBILITY.md).

## Application execution and manuscript compilation

`src/`, `tests/`, `configs/`, `scripts/`, `data/` and `snapshots/` provide the application and processed snapshot workflow. After installing the locked environment, run `PYTHONPATH=src python -m pytest` for live application checks. Recipe commands such as `PYTHONPATH=src python -m compass.cli run configs/recipes/synthetic.yaml` generate new run artifacts; they are distinct from the frozen-score analysis above. The application does not download data during a run.

Compile the article with the `acmart` class and standard ACM/LaTeX packages, for example `cd paper/latex` and `tectonic main.tex`. Word exports, rendering images, local review diaries, virtual environments and temporary outputs are excluded from the current scientific publication. Prior versions remain available in Git history and frozen archives.
