# Scientific reproduction snapshot 2026 10 21

Run `python reproduction/2026-10-21/reproduce.py --output-dir <new-output-directory>` from the repository root after installing `requirements.lock` in a Python 3.12 environment. It does not require the author's Dropbox tree or any files outside this Git repository.

## Execution and expected results

1. Verify `paper/publication_manifest.json` and the immutable computational archive. Confirm all 52 evaluated live Python source/test files match its source inventory.
2. Extract the archive to a temporary directory and execute its runner: four JSON reports match the expected structures (Python patch metadata excluded), all 20 application tests pass, and all seven export-contract vectors match.
3. Reuse the three fixed-score inputs and retrieve only historical sweep CSVs and scenario scoring keys from the already versioned 2026-10-20 archive. Recompute the full-sample analyses using live application code. Compare `computational_report.json` structurally and the three 80-candidate CSVs byte for byte with `paper/results/`.
4. Rebuild the diagnostic plot from `study_case_counts.csv` and compare its RGB pixels with the manuscript figure. Write scope and verification results to `<output-directory>/verification.json`.

The fixed-score snapshot is `pacote_avaliador.zip`, SHA-256 `108d5ff9f550dec882b6691b24ec2b5340c5515ab3fd550a198e32e72e947688`. This is byte-identical to the archive cited in the manuscript as `revisao_artigo/rodada4/pacote_avaliador.zip`; the path differs between the author's project and this repository. Its bundled paper is retained as part of its frozen identity. The current manuscript is in `../../paper/`, not that archive. Do not replace the ZIP's embedded sources or its manifest to update the article.

The 2026-10-20 archive remains unchanged. Its inputs are accessed selectively to avoid committing another expanded copy of the same datasets. Full-precision current expected results are in `../../paper/results/`; split IDs and frozen policies are also inside the fixed snapshot.

## Study access

The default execution explicitly skips participant-level reanalysis. It verifies the published aggregate plot, which cannot establish paired p-values or participant bootstrap intervals on its own.

Researchers with authorized access to the original response CSV ZIP can supply `--study-zip /local/path/responses.zip`. The script reads it locally, applies the scenario keys, signed-rank sign enumeration, Holm adjustment and participant bootstrap, and compares its aggregate report with the published study report. The ZIP must use the original G1/G2 CSV schema; no generic new data schema is implied. Do not add the ZIP or response texts to Git. This optional path requires restricted data and is distinct from the publicly reproducible default.

No formal historical ethics approval or exemption was obtained. Voluntary participation/consent does not create permission for public redistribution. Human-study limitations are disclosed in the manuscript.

## Scope and provenance

- ASSISTments: 105107 interaction cases; positive means correct; school parity is a synthetic audit proxy.
- OULAD: 6519 cases; Pass/Distinction positive; binary gender used for auditing.
- Synthetic: 1000 mechanism-test cases.
- Historical predictors are not refit. Tests create separate synthetic fixtures.
- The validation/test analysis is retrospective on previously inspected scores, not a prospective, temporal or student-disjoint validation.
- `ANALYSIS_PROVENANCE.json` identifies the original analysis script; the portable adaptation changes file IO and removes internal editorial logs while preserving numerical/statistical procedures.
- Self-contained hashes establish internal consistency. Independent execution and trusted external authenticity are separate matters.

Application code is MIT licensed. Dataset and third-party terms remain applicable. The environment lock records the tested environment, not a guarantee that every platform can install all versions unchanged.
