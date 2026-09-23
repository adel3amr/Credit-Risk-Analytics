"""Publication figures from independent review evidence (no model retraining)."""
from pathlib import Path
import sys
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
E = ROOT / 'evidence'
F = ROOT / 'figures'
F.mkdir(exist_ok=True)
plt.rcParams.update({'figure.dpi': 150, 'savefig.dpi': 180, 'font.size': 10,
                     'axes.spines.top': False, 'axes.spines.right': False})
NAVY, BLUE, RED = '#162A48', '#2878B5', '#C64D50'

history = pd.read_csv(E / 'historical_reproduction.csv')
chosen = history[history.snapshot.isin(['initial','v2_final','main_checkpoint',
        'v4_early_facility','v4_final','v5_frozen'])]
fig, axes = plt.subplots(1, 2, figsize=(11, 3.7), constrained_layout=True)
labels = ['Initial','V2','Main','Early V4','Final V4','Frozen V5']
axes[0].plot(range(len(chosen)), chosen.pd_auc, marker='o', color=BLUE)
axes[0].set_xticks(range(len(chosen)), labels, rotation=25, ha='right')
axes[0].set_ylim(.65, .82); axes[0].set_ylabel('PD holdout AUC')
axes[0].set_title('Historical snapshots: samples and rules differ')
axes[1].bar(range(len(chosen)), chosen.total_ecl / 1e6, color=NAVY)
axes[1].set_xticks(range(len(chosen)), labels, rotation=25, ha='right')
axes[1].set_ylabel('Holdout ECL (millions, synthetic units)')
axes[1].set_title('ECL is not a like-for-like performance score')
fig.savefig(F/'history.png', bbox_inches='tight'); plt.close(fig)

c = pd.read_csv(E/'independent_lgd_calibration.csv')
fig, ax = plt.subplots(figsize=(6.1, 4.2), constrained_layout=True)
ax.plot([0,1], [0,1], '--', color='#777777', label='Perfect group calibration')
ax.plot(c.predicted_mean, c.actual_mean, 'o-', color=BLUE, label='200 workouts per decile')
ax.set(xlabel='Mean forecast LGD', ylabel='Mean realized LGD',
       title='Facility LGD: independent holdout calibration', xlim=(0,.85), ylim=(0,.85))
ax.legend(loc='upper left'); fig.savefig(F/'lgd_calibration.png',bbox_inches='tight'); plt.close(fig)

s = pd.read_csv(E/'independent_lgd_segments.csv').set_index('segment')
names = ['all','realized <=10%','realized >60%','realized >75%',
         'realized >=90%','predicted top 10%']
values = s.loc[names, 'bias'].to_numpy()*100
fig, ax = plt.subplots(figsize=(8,3.8), constrained_layout=True)
bars = ax.barh(range(len(names)), values, color=[BLUE if v >= 0 else RED for v in values])
ax.set_yticks(range(len(names)), [f'{n} (n={int(s.loc[n,"n"]):,})' for n in names]); ax.invert_yaxis()
ax.axvline(0, color=NAVY, linewidth=.8)
ax.set(xlabel='Mean prediction − realized LGD (percentage points)',
       title='Realized-tail selection and forecast-risk tail are different diagnostics')
ax.bar_label(bars, fmt='%+.2f', padding=3)
fig.savefig(F/'lgd_tail_bias.png',bbox_inches='tight'); plt.close(fig)

f = pd.read_csv(Path(sys.argv[1])/'outputs/lgd_holdout_predictions.csv')
fig, ax = plt.subplots(figsize=(6.3,3.8), constrained_layout=True)
ax.hist((f.predicted_lgd-f.economic_lgd)*100, bins=np.arange(-60,65,4),
        color=BLUE, alpha=.85, edgecolor='white')
ax.axvline(0, linewidth=1, color=NAVY)
ax.set(xlabel='Forecast minus realized LGD (percentage points)', ylabel='Facilities',
       title='Holdout residuals: two-sided errors despite small mean bias')
fig.savefig(F/'lgd_residuals.png',bbox_inches='tight'); plt.close(fig)

print('Generated',len(list(F.glob('*.png'))),'figures')
