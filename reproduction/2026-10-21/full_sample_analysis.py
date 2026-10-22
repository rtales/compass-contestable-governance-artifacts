"""Recompute full-sample policy, uncertainty and optional restricted-study analyses.

File IO is parameterized; computational and statistical formulas are preserved
from the analysis accompanying the published fixed-score results.
"""
from pathlib import Path
import argparse
import sys, json, hashlib, math, itertools, copy, zipfile, os
os.environ.setdefault("MPLCONFIGDIR", str(Path(os.environ.get('TMPDIR','/tmp'))/'compass-matplotlib'))
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--skip-study',action='store_true',help='Recompute computational evidence only; do not substitute study data.')
parser.add_argument('--workspace-root',type=Path,required=True)
parser.add_argument('--application-root',type=Path,required=True)
parser.add_argument('--output-dir',type=Path,required=True)
parser.add_argument('--study-zip',type=Path)
ARGS=parser.parse_args()
if not ARGS.skip_study and ARGS.study_zip is None:parser.error('--study-zip is required unless --skip-study is used')
ROOT = ARGS.workspace_root.resolve()
PAPER = ROOT / 'paper'
APP = ARGS.application_root.resolve()
sys.path.insert(0, str(APP/'src'))
from compass.policy.decision import apply_topk_with_abstain, binary_entropy
from compass.policy.governance import audit_decisions, select_candidate, assess_constraints
OUT = ARGS.output_dir.resolve()
OUT.mkdir(parents=True,exist_ok=True)
GAMMAS = [.01,.05,.1,.15,.2,.3,.4,.5,.6,.7,.8,.9,.95,.99,.995,.999]
CONSTRAINTS = {'max_delta_eopp_at_k':.05, 'min_coverage':.5}
SPECS = {
 'assistments': ('compass_artifacts_repo/outputs/assistments_run_v1_assistments_2009_2010_v1_seed42_20260126T031036Z_LOCAL', [100,250,500,1000,2000],1000,.6),
 'oulad': ('compass_artifacts_repo/outputs/oulad_run_v1_oulad_v1_seed42_20260126T031033Z_LOCAL',[50,100,200,500,1000],500,.6),
 'synthetic': ('compass_github/compass-contestable-governance-artifacts/outputs/synthetic_run_v1_synthetic_v1_seed42_20260126T234652Z_LOCAL',[20,50,100,200,300],100,.65)}
LABELS={'assistments':'ASSISTments','oulad':'OULAD','synthetic':'Synthetic'}

def save(name,obj):
 (OUT/name).write_text(json.dumps(obj,indent=2,allow_nan=False)+'\n')

def table(name,caption,label,columns,header,rows,wide=False):
 env='table*' if wide else 'table'
 text=[f'\\begin{{{env}}}[t]',r'\centering',r'\small',f'\\caption{{{caption}}}',f'\\label{{{label}}}',
       f'\\begin{{tabular}}{{{columns}}}',r'\toprule',header+r' \\',r'\midrule']
 text += [' & '.join(map(str,r))+r' \\' for r in rows]
 text += [r'\bottomrule',r'\end{tabular}',f'\\end{{{env}}}']
 (PAPER/'tables'/f'{name}.tex').write_text('\n'.join(text)+'\n')

def ece(y,p):
 bins=np.minimum((p*10).astype(int),9)
 return sum(np.mean(bins==b)*abs(float(y[bins==b].mean()-p[bins==b].mean())) for b in range(10) if np.any(bins==b))

def wilson(errors,n):
 if n==0:return [None,None]
 q=errors/n;z=1.959963984540054;den=1+z*z/n
 c=(q+z*z/(2*n))/den;h=z*math.sqrt(q*(1-q)/n+z*z/(4*n*n))/den
 return [max(0,c-h),min(1,c+h)]

report={}; initial_rows=[];counts_rows=[];sweep_rows=[];profile_rows=[];recovered_rows=[];unc_rows=[];tax_rows=[]
for name,(path,ks,k,gamma) in SPECS.items():
 packet_path=ROOT/path/'artifacts/decision_packets.jsonl'
 rows=[json.loads(x) for x in packet_path.open()]
 df=pd.DataFrame(rows); p=df.score.to_numpy(float);y=df.y_true.to_numpy(int);groups=df.sensitive.to_numpy(int)
 # Stable identities are scoped to the historical run, not new cross-snapshot claims.
 ids=df.case_id.astype(str).to_numpy()
 h=binary_entropy(p)
 assert np.allclose(h,df.entropy.to_numpy(),atol=1e-12,rtol=0)
 initial=apply_topk_with_abstain(p,k,gamma,case_ids=ids)
 disagreement=int(np.sum(initial['decision']!=df.decision.to_numpy()))
 # Compare exact historical labels independently from corrected stable tie rules.
 historical=audit_decisions(y,groups,df.decision.to_numpy(),h<=gamma)
 regenerated=audit_decisions(y,groups,initial['decision'],initial['eligible'])
 candidates=[]
 for kk in ks:
  for gg in GAMMAS:
   d=apply_topk_with_abstain(p,kk,gg,case_ids=ids)
   candidates.append({'candidate_id':f'{name}:k={kk:06d}:g={gg:.3f}', 'k':kk,'gamma_entropy':gg,
                      **audit_decisions(y,groups,d['decision'],d['eligible'])})
 flat=[{key:value for key,value in c.items() if key!='group_counts'} for c in candidates]
 pd.DataFrame(flat).to_csv(OUT/f'{name}_candidates.csv',index=False)
 fixed=[c for c in candidates if c['k']==k]
 selection=select_candidate(fixed,CONSTRAINTS)
 chosen=selection['selected'];assert chosen is not None
 profiles={}
 for profile,order in [('Fairness-first',['min_abs_delta_eopp','max_utility','min_abstain_rate']),
                       ('Utility-first',['max_utility','min_abs_delta_eopp','min_abstain_rate'])]:
  res=select_candidate(candidates,CONSTRAINTS,order)
  profiles[profile]=res
  z=res['selected'];profile_rows.append([LABELS[name],profile,z['k'],f"{z['gamma_entropy']:.3f}",f"{z['utility_at_k']:.3f}",f"{z['abs_delta_eopp_at_k']:.5f}",f"{z['coverage']:.6f}"])
 old=pd.read_csv(PAPER/f'paper_assets/sweeps/{name}_candidates.csv')
 new=pd.DataFrame(flat)
 historical_comparison={}
 for key in ['utility_at_k','coverage','abstain_rate','abs_delta_eopp_at_k','n_selected','n_non_abstain']:
  nk='n_eligible' if key=='n_non_abstain' else key
  a=old[key].to_numpy(float); b=new[nk].to_numpy(float); valid=np.isfinite(a)&np.isfinite(b)
  historical_comparison[key]=float(np.max(abs(a[valid]-b[valid]))) if valid.any() else None
  historical_comparison[key+'_undefined_mismatch_count']=int(np.sum(np.isfinite(a)!=np.isfinite(b)))
 validations={}
 for temp in [1,.5,2]:
  pp=p if temp==1 else 1/(1+np.exp(-np.log(np.clip(p,1e-12,1-1e-12)/(1-np.clip(p,1e-12,1-1e-12)))/temp))
  hh=binary_entropy(pp)
  validations[str(temp)]={'ece':ece(y,pp),'spearman_entropy_abs_error':float(spearmanr(hh,abs(y-pp)).statistic)}
 # Row-bootstrap intervals are conditional diagnostics, not student-cluster generalization.
 rng=np.random.default_rng(42)
 boot=[]
 for _ in range(200):
  ix=rng.integers(0,len(y),len(y))
  boot.append([ece(y[ix],p[ix]),float(spearmanr(h[ix],abs(y[ix]-p[ix])).statistic)])
 intervals=np.quantile(boot,[.025,.975],axis=0)
 validations['row_bootstrap']={'replicates':200,'seed':42,'ece_ci':intervals[:,0].tolist(),'spearman_ci':intervals[:,1].tolist(),
  'limitation':'Conditional row resampling; historical packets lack student cluster IDs. ASSISTments intervals do not establish cluster-robust population uncertainty.'}
 risks=[]
 for gg in GAMMAS:
  for group in [None,*sorted(set(groups.tolist()))]:
   m=(h<=gg) & (np.ones(len(y),bool) if group is None else groups==group)
   count=int(m.sum());err=int(np.sum((p[m]>=.5)!=y[m]))
   risks.append({'gamma_bits':gg,'group':'all' if group is None else str(group),'n_eligible':count,
                 'n_errors':err,'risk':err/count if count else None,'wilson_ci':wilson(err,count)})
 validations['selective_risk']=risks
 all_sel=select_candidate(candidates,CONSTRAINTS)
 perms=[]
 for order in itertools.permutations(['min_abs_delta_eopp','max_utility','min_abstain_rate']):
  result=select_candidate(candidates,CONSTRAINTS,list(order))
  perms.append({'order':order,'candidate_id':result['selected']['candidate_id']})
 report[name]={'packet_path':str(packet_path.relative_to(ROOT)),'sha256':hashlib.sha256(packet_path.read_bytes()).hexdigest(),
               'initial_historical':historical,'initial_recomputed':regenerated,'initial_decision_mismatches':disagreement,
               'grid':{'k':ks,'gamma_bits':GAMMAS},'max_difference_from_historical_csv':historical_comparison,
               'fixed_k':selection,'variable_k':all_sel,'profiles':profiles,'stability':perms,'uncertainty':validations}
 label=LABELS[name]
 initial_rows.append([label,k,f'{gamma:.2f}',f"{historical['utility_at_k']:.3f}",f"{historical['coverage']:.6f}",f"{historical['abstain_rate']:.6f}",f"{historical['abs_delta_eopp_at_k']:.5f}",assess_constraints(historical,CONSTRAINTS)['status'].upper()])
 counts_rows.append([label,historical['n'],historical['n_eligible'],historical['n_selected'],historical['n_rejected'],historical['n_abstained']])
 sweep_rows.append([label,len(candidates),all_sel['n_feasible'],selection['n_candidates'],selection['n_feasible'],selection['n_pareto']])
 recovered_rows.append([label,chosen['k'],f"{chosen['gamma_entropy']:.3f}",chosen['n_selected'],f"{chosen['utility_at_k']:.3f}",f"{chosen['abs_delta_eopp_at_k']:.5f}",f"{chosen['coverage']:.6f}",f"{chosen['abstain_rate']:.6f}"])
 unc_rows.append([label,f"{validations['1']['ece']:.4f}",f"{validations['1']['spearman_entropy_abs_error']:.4f}",f"{validations['2']['ece']:.4f}",f"{validations['2']['spearman_entropy_abs_error']:.4f}"])
 if name=='assistments':
  for title,mode,scope in [('Global abstention','allocation','global'),('Top-K-only abstention','allocation','topk'),('Defer remainder','screening','global')]:
   d=apply_topk_with_abstain(p,k,gamma,case_ids=ids,mode=mode,abstain_scope=scope)
   met=audit_decisions(y,groups,d['decision'],d['eligible'])
   tax_rows.append([title,f"{met['utility_at_k']:.3f}",f"{met['coverage']:.6f}",f"{met['abstain_rate']:.6f}",f"{met['abs_delta_eopp_at_k']:.5f}"])
   report[name].setdefault('taxonomy',{})[title]=met
save('computational_report.json',report)
table('run_initial','Historical recipe outcomes, recomputed from emitted states. Entropy thresholds are in bits; VIOL indicates a retrospective ECL violation, not a delivered human review.','tab:run-initial','lrrrrrrl',r'Dataset & $K$ & $\gamma$ & Utility & Coverage & Abstain & Gap & ECL',[[*r[:-1], 'OK' if r[-1]=='FEASIBLE' else 'VIOL'] for r in initial_rows],True)
table('state_counts','Exact initial state counts. $K$ is a capacity ceiling, not the realized number selected.','tab:state-counts','lrrrrr',r'Dataset & $n$ & Eligible & Select & Reject & Abstain',counts_rows,True)
table('run_sweep_summary',r'Candidate counts under gap $\leq0.05$ and coverage $\geq0.50$. Full grids vary $K$ and $\gamma$; fixed-budget analyses use only the 16 thresholds at the recipe budget.','tab:run-sweep','lrrrrr',r'Dataset & Full & Feas. & Fixed & Feas. & Pareto',sweep_rows)
table('recovered_metrics','Revised MAS selections from the fixed-$K$ feasible Pareto set. All tie tolerances are zero; persistent candidate ID is the final tie-breaker.','tab:recovered','lrrrrrrr',r'Dataset & $K$ & $\gamma$ & Selected & Utility & Gap & Coverage & Abstain',recovered_rows,True)
table('policy_profile_tradeoffs','Variable-$K$ profiles over the full 80-point grids; these are distinct from fixed-budget recovery. Fairness-first orders gap, utility, abstention; utility-first orders utility, gap, abstention.','tab:policy-profiles','llrrrrr',r'Dataset & Profile & $K$ & $\gamma$ & Utility & Gap & Coverage',profile_rows,True)
table('uncertainty_proxy_validation','Recomputed entropy validation. ECE uses 10 equal-width probability bins including score 1; Spearman uses average ranks for ties. Both baseline and temperature stress use entropy in bits.','tab:uncertainty_proxy_validation','lrrrr',r'Dataset & ECE & $\rho$ & ECE ($T=2$) & $\rho$ ($T=2$)',unc_rows)
table('policy_replay',r'ASSISTments taxonomy replay with fixed scores, $K=1000$ and $\gamma=0.60$ bits. Changes in automation coverage represent changes in decision responsibility, not demonstrated improvement in student outcomes.','tab:policy-replay','lrrrr',r'Policy & Utility & Coverage & Abstain & Gap',tax_rows,True)

if ARGS.skip_study:
 save('analysis_scope.json', {'computational':'recomputed','study':'skipped; existing study assets not reanalysed'})
 print('Computational evidence rebuilt; study explicitly skipped.')
 sys.exit(0)
save('analysis_scope.json', {'computational':'recomputed','study':'recomputed from local original responses'})

# Study: author confirmed G1 odd=A; G2 odd=B, 2026-10-20.
gold={i:json.loads((PAPER/f'paper_assets/appeals/case_C{i}.json').read_text()) for i in range(1,9)}
responses=[]
with zipfile.ZipFile(ARGS.study_zip) as z:
 for filename in sorted(z.namelist()):
  for _,row in pd.read_csv(z.open(filename)).iterrows():
   for i in range(1,9):
    cond='A' if ((i%2==1)==filename.startswith('G1')) else 'B'
    responses.append({'participant':str(row.iloc[2]),'case':i,'condition':cond,
      'diagnosis':int(row[f'[C{i}] Motivo (rótulo)']==gold[i]['ground_truth_label']),
      'remediation':int(row[f'[C{i}] Ação recomendada (remediação)']==gold[i]['ground_truth_remediation']),
      'confidence':float(row[f'[C{i}] Confiança']),
      'evidence_characters':len(str(row[f'[C{i}] Evidência citada']))})
s=pd.DataFrame(responses)
assert s.participant.nunique()==16 and len(s)==128 and not s.duplicated(['participant','case']).any()
study={'n_participants':16,'n_case_responses':128,'n_per_condition':64,'assignment':'G1 odd=A/even=B; G2 reversed; author confirmed 2026-10-20',
       'ethics':'Author reports voluntary participation and authorization; no formal ethics committee approval or exemption.',
       'analysis':'Retrospective revision; two-sided exact sign enumeration of nonzero Wilcoxon midranks; Holm over four endpoints; 10000 participant bootstrap replicates, seed 42.',
       'diagnosis_remediation_agreement':int((s.diagnosis==s.remediation).sum()),'outcomes':{}}
for outcome in ['diagnosis','remediation','confidence','evidence_characters']:
 paired=s.groupby(['participant','condition'])[outcome].mean().unstack()
 delta=paired.B-paired.A; nonzero=delta[delta!=0]
 ranks=nonzero.abs().rank(method='average').to_numpy()
 observed=float(ranks[nonzero.to_numpy()>0].sum());total=float(ranks.sum())
 sums=np.array([0.])
 for r in ranks:sums=np.concatenate([sums,sums+r])
 pvalue=min(1.,2*min(float(np.mean(sums>=observed-1e-12)),float(np.mean(sums<=observed+1e-12))))
 rng=np.random.default_rng(42)
 boot=delta.to_numpy()[rng.integers(0,16,(10000,16))].mean(axis=1)
 ci=np.quantile(boot,[.025,.975]).tolist()
 study['outcomes'][outcome]={'A':float(paired.A.mean()),'B':float(paired.B.mean()),'difference':float(delta.mean()),
                            'difference_ci':ci,'p_two_sided':pvalue,'n_zero_differences':int((delta==0).sum()),
                            'rank_biserial':(2*observed-total)/total if total else None}
ordered=sorted(study['outcomes'],key=lambda k:study['outcomes'][k]['p_two_sided']);last=0
for i,key in enumerate(ordered):
 last=max(last,min(1,(len(ordered)-i)*study['outcomes'][key]['p_two_sided']))
 study['outcomes'][key]['p_holm']=last
case_rows=[];figdata=[]
for i in range(1,9):
 parts=[]
 for cond in ['A','B']:
  v=s[(s.case==i)&(s.condition==cond)]
  figdata.append({'case':i,'condition':cond,'correct':int(v.diagnosis.sum()),'n':len(v)})
  parts.append(f'{int(v.diagnosis.sum())}/{len(v)}')
 case_rows.append([f'C{i}',*parts])
study['case_counts']=figdata
save('study_report.json',study)
pd.DataFrame(figdata).to_csv(OUT/'study_case_counts.csv',index=False)
table('human_study_summary',r'Exploratory N=16 study; 64 case responses per condition. Participant means and paired differences with 95\% participant-bootstrap intervals. $p_H$ is the two-sided signed-rank sign-enumeration p-value adjusted by Holm over four endpoints; diagnosis/remediation correctness coincides in all 128 responses.','tab:human-study-summary','lrrrr',r'Outcome & A & B & Difference [95\% CI] & $p_H$',[
 [label,f"{v['A']:.3f}",f"{v['B']:.3f}",f"{v['difference']:.3f} [{v['difference_ci'][0]:.3f}, {v['difference_ci'][1]:.3f}]",f"{v['p_holm']:.5f}"]
 for key,label in [('diagnosis','Diagnosis'),('remediation','Remediation'),('confidence','Confidence'),('evidence_characters','Evidence (characters)')]
 for v in [study['outcomes'][key]]],True)
table('human_study_keycases','Diagnostic counts by case and condition. Every cell has eight responses; case materials are standardized research scenarios.','tab:human-study-keycases','lrr','Case & A & B',case_rows)
fig,ax=plt.subplots(figsize=(7,3.5));x=np.arange(8)
for offset,cond,color in [(-.18,'A','#4477aa'),(.18,'B','#ee7733')]:
 vals=[v for v in figdata if v['condition']==cond]
 bars=ax.bar(x+offset,[v['correct']/v['n'] for v in vals],.36,label=f'{cond}: '+('logs/cards' if cond=='A' else 'structured evidence'),color=color)
 ax.bar_label(bars,labels=[f"{v['correct']}/{v['n']}" for v in vals],fontsize=7,padding=2)
ax.set(xticks=x,xticklabels=[f'C{i}' for i in range(1,9)],xlabel='Appeal case',ylabel='Diagnostic accuracy',ylim=(0,1.22))
ax.legend(fontsize=8,loc='upper left',ncol=2);fig.tight_layout();fig.savefig(PAPER/'figures/human_label_accuracy_by_case.png',dpi=180);plt.close(fig)
(OUT/'figure_alt_text.txt').write_text('Grouped bars compare diagnostic accuracy for baseline A and structured-evidence B across eight appeal cases. Exact correct/total counts are given in study_case_counts.csv and the manuscript table. B is equal to A in C4 and higher in the other seven cases. Each bar represents eight responses.\n')

