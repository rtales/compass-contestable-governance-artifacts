"""Regenerate the diagnostic plot from published counts, not participant responses."""
from pathlib import Path
import argparse
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
repo=Path(__file__).resolve().parents[2]
data=pd.read_csv(repo/'paper/results/study_case_counts.csv')
assert len(data)==16 and set(data.condition)=={'A','B'}
assert not data.duplicated(['case','condition']).any() and (data.n==8).all()
assert set(data['case'])==set(range(1,9)) and data.correct.between(0,data.n).all()
fig,ax=plt.subplots(figsize=(7,3.5));x=np.arange(8)
for offset,cond,color in [(-.18,'A','#4477aa'),(.18,'B','#ee7733')]:
 vals=data[data.condition==cond].sort_values('case')
 bars=ax.bar(x+offset,vals.correct/vals.n,.36,label=f'{cond}: '+('logs/cards' if cond=='A' else 'structured evidence'),color=color)
 ax.bar_label(bars,labels=[f'{r.correct}/{r.n}' for r in vals.itertuples()],fontsize=7,padding=2)
ax.set(xticks=x,xticklabels=[f'C{i}' for i in range(1,9)],xlabel='Appeal case',ylabel='Diagnostic accuracy',ylim=(0,1.22))
ax.legend(fontsize=8,loc='upper left',ncol=2);fig.tight_layout();a.output.parent.mkdir(parents=True,exist_ok=True)
fig.savefig(a.output,dpi=180);plt.close(fig)
