"""Reproduce the published fixed-score analyses without the author's workspace."""
from pathlib import Path
from zipfile import ZipFile
import argparse, hashlib, json, os, shutil, subprocess, sys, tempfile
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
SNAPSHOT_SHA256 = '108d5ff9f550dec882b6691b24ec2b5340c5515ab3fd550a198e32e72e947688'
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--output-dir', type=Path, default=HERE / 'actual')
p.add_argument('--study-zip', type=Path, help='Optional authorized local response ZIP; never included in this repository.')
a = p.parse_args()
out = a.output_dir.resolve(); out.mkdir(parents=True, exist_ok=True)
study = a.study_zip.resolve() if a.study_zip else None
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
manifest = json.loads((REPO / 'paper/publication_manifest.json').read_text())
for name, rec in manifest['files'].items():
    if sha(REPO / name) != rec['sha256']:
        raise SystemExit('Publication hash mismatch: ' + name)
snapshot = HERE / 'pacote_avaliador.zip'
if sha(snapshot) != SNAPSHOT_SHA256:
    raise SystemExit('Frozen snapshot checksum mismatch')
env = os.environ.copy(); env['PYTHONPATH'] = str(REPO / 'src')
env['MPLCONFIGDIR'] = str(out / 'matplotlib-cache')

def run(args, log, **kwargs):
    result = subprocess.run([sys.executable, *map(str, args)], env=env, text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, **kwargs)
    log.write_text(result.stdout)
    if result.returncode:
        raise SystemExit(f'Execution failed; see {log}')

def equal_json(actual, expected):
    if json.loads(actual.read_text()) != json.loads(expected.read_text()):
        raise SystemExit(f'Expected/observed mismatch: {actual.name}')

with tempfile.TemporaryDirectory(prefix='compass-scientific-') as folder:
    temp = Path(folder); bundle = temp / 'bundle'; bundle.mkdir()
    with ZipFile(snapshot) as z:
        # The externally checked digest fixes the archive; reject unsafe names too.
        for info in z.infolist():
            dest = (bundle / info.filename).resolve()
            if not dest.is_relative_to(bundle.resolve()):
                raise SystemExit('Unsafe archive member')
        z.extractall(bundle)
    roots = list(bundle.rglob('SOURCE_IDENTITY.json'))
    if len(roots) != 1:
        raise SystemExit('Expected one scientific snapshot root')
    bundle = roots[0].parent
    identity = json.loads((bundle / 'SOURCE_IDENTITY.json').read_text())
    for name, expected in identity['source_files'].items():
        if sha(REPO / name) != expected:
            raise SystemExit('Live source differs from evaluated snapshot: ' + name)
    print('Publication hashes and 52 evaluated source/test files verified.', flush=True)
    run([bundle / 'reproduce.py', '--output-dir', out / 'selection_test'],
        out / 'selection_test_execution.log', cwd=bundle)
    verification = json.loads((out / 'selection_test/verification.json').read_text())
    print('Selection/test, seven fault vectors and 20 application tests passed.', flush=True)

    # Reuse already published historical CSVs; no second unpacked dataset is versioned.
    workspace = temp / 'workspace'; paper = workspace / 'paper'
    (paper / 'tables').mkdir(parents=True); (paper / 'figures').mkdir()
    (paper / 'paper_assets/sweeps').mkdir(parents=True)
    (paper / 'paper_assets/appeals').mkdir()
    expected_full = json.loads((REPO / 'paper/results/computational_report.json').read_text())
    for name, data in expected_full.items():
        packet = bundle / 'inputs' / name / 'artifacts/decision_packets.jsonl'
        if sha(packet) != data['sha256']:
            raise SystemExit('Historical packet identity mismatch: ' + name)
        dest = workspace / data['packet_path']; dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(packet, dest)
    old_archive = REPO / 'reproduction/2026-10-20/pacote_revisao.zip'
    with ZipFile(old_archive) as z:
        suffixes = [f'paper_assets/sweeps/{n}_candidates.csv' for n in expected_full]
        suffixes += [f'paper_assets/appeals/case_C{i}.json' for i in range(1, 9)]
        for suffix in suffixes:
            members = [n for n in z.namelist() if n.endswith('/' + suffix)]
            if len(members) != 1:
                raise SystemExit('Ambiguous or missing historical input: ' + suffix)
            (paper / suffix).write_bytes(z.read(members[0]))
    args = [HERE / 'full_sample_analysis.py', '--workspace-root', workspace,
            '--application-root', REPO, '--output-dir', out / 'full_sample']
    args += ['--study-zip', study] if study else ['--skip-study']
    print('Recomputing 80-candidate grids, calibration, intervals and group risks...', flush=True)
    run(args, out / 'full_sample_execution.log', cwd=REPO)
    equal_json(out / 'full_sample/computational_report.json', REPO / 'paper/results/computational_report.json')
    for name in expected_full:
        filename = name + '_candidates.csv'
        if (out / 'full_sample' / filename).read_bytes() != (REPO / 'paper/results' / filename).read_bytes():
            raise SystemExit('Candidate CSV mismatch: ' + filename)
    if study:
        equal_json(out / 'full_sample/study_report.json', REPO / 'paper/results/study_report.json')
        shutil.copyfile(paper / 'figures/human_label_accuracy_by_case.png', out / 'study_from_responses.png')

# The diagnostic plot can be regenerated from published aggregate counts alone.
run([HERE / 'plot_study_aggregates.py', '--output', out / 'study_from_aggregates.png'],
    out / 'study_figure_execution.log', cwd=REPO)
from PIL import Image, ImageChops
with Image.open(out / 'study_from_aggregates.png') as actual, Image.open(REPO / 'paper/latex/figures/human_label_accuracy_by_case.png') as expected:
    if actual.size != expected.size or ImageChops.difference(actual.convert('RGB'), expected.convert('RGB')).getbbox():
        raise SystemExit('Aggregate study figure differs from manuscript pixels')
result = {'publication_files_verified': len(manifest['files']),
          'evaluated_live_source_files_verified': len(identity['source_files']),
          'snapshot_sha256': SNAPSHOT_SHA256,
          'frozen_snapshot': verification,
          'full_sample_report': 'exact structural match',
          'three_candidate_csvs': 'byte-identical',
          'aggregate_study_figure': 'identical RGB pixels',
          'human_individual_reanalysis': 'recomputed from supplied local authorized ZIP' if study else 'skipped; restricted participant responses not distributed',
          'historical_predictors_refit': False,
          'scope': 'Author-run reproduction; not independent certification or prospective validation.'}
(out / 'verification.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2), flush=True)
