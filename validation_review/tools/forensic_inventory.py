"""Capture Git evidence without checking out or modifying historical branches."""
from pathlib import Path
import subprocess, csv, json, ast, hashlib
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'validation_review/evidence'
OUT.mkdir(parents=True,exist_ok=True)
def git(*args): return subprocess.check_output(['git',*args],cwd=ROOT,text=True)
def save(name, rows):
 with (OUT/name).open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n'); w.writeheader(); w.writerows(rows)
refs=git('for-each-ref','--format=%(refname:short)|%(objectname)','refs/remotes/origin').splitlines()
branches=[]
for row in refs:
 ref,sha=row.split('|')
 if ref in ('origin','origin/HEAD'): continue
 branches.append(dict(branch=ref,commit=sha,ancestor_of_v5=subprocess.run(['git','merge-base','--is-ancestor',sha,'0dfe4c8'],cwd=ROOT).returncode==0))
save('branches.csv',branches)
commits=[]
for row in git('log','--remotes','--topo-order','--reverse','--format=%H|%P|%aI|%s').splitlines():
 sha,parents,date,subject=row.split('|',3)
 commits.append(dict(commit=sha,parents=parents,date=date,subject=subject))
save('commit_history.csv',commits)
# Phase boundaries are analytical groupings anchored to actual commits, not new version claims.
phases=[
('Initial upload','4d91d1e','None','Initial PD/ECL prototype','Balanced LR/RF; best holdout AUC selects model; PD-cutoff stages and 2.5/4x multipliers','Supplied CSV; no generator','notebooks/credit_risk_pipeline.py; src/ecl.py'),
('Hybrid and calibrated DGP','fda0edb','4d91d1e','Nested information sets and plausible default frequency','Unweighted classifiers; synthetic generator introduced','Full-sample derived qualitative variables, later reviewed','scripts/generate_sme_portfolio.py; src/pd_model.py'),
('Predictor and target separation','d9a37dd','fda0edb','Separate risk parameters and prospective target from reporting-date decisions','Explicit PD inputs; current impairment staging; constant-hazard term approximation','Not identical to later facility term treatment','src/data_preparation.py; src/ecl.py'),
('CI reduction','03c1db0','d9a37dd','Commit messages describe smoke-test simplification','Data/leakage and accounting assertions removed','Historical coverage regression; do not call a model improvement','.github/workflows/validate-hybrid-v2.yml'),
('EWS persistence and macro V2','29ede62','03c1db0','Separate monitoring, nine-month escalation, macro scenarios and audits','36-month synthetic history; LR fixed; scenario PD and borrower-term ECL','V2 historical release, PR 1','src/early_warning.py; src/ecl.py; config/macro_scenarios.csv'),
('Governance interface','a78bfe9','29ede62','Maker-checker and role-based demonstration','No new PD model; Streamlit and governance primitives','PR 2; fixed identities are not authentication','app.py; src/governance.py'),
('Credit workbench','4a6bac7','a78bfe9','Borrower decisions and prioritization','Interface expansion','PR 3','app.py'),
('EWS terminology correction','969df72','4a6bac7','Distinguish consecutive trigger months from operational watchlist duration','Existing persistence policy represented more explicitly','PR 4','scripts/generate_sme_portfolio.py; src/early_warning.py'),
('Collateral recovery rebuild','a3c46b4','969df72','Security-type-aware residual unsecured severity','Cash/mortgage/other/unsecured recognition; legacy proxy','PR 5; data generation changes prevent naive metric comparison','scripts/generate_sme_portfolio.py'),
('Limits and portfolio intelligence','f526939','a3c46b4','Separate direct/indirect limits, utilization and CCF exposure','Loan outstanding, OVD approved limit, trade CCF','PRs 9-10','scripts/generate_sme_portfolio.py; app.py'),
('Ratings and main checkpoint','b93a459','f526939','Operational rating and final UI iterations','1-10 rating; cash-only grade 1; validator workspace','PRs 11-17; main predates V4/V5','src/scorecard.py; app.py'),
('PCA experiment','c74d5dc','b93a459','Isolated PCA logistic challenger','PCA pipeline in main analytical notebook on separate branch','PR 18; never promoted into V5','src/pd_model.py; notebooks/credit_risk_pipeline.py'),
('Bootstrap experiment','0bf890d','b93a459','Estimate holdout metric uncertainty','2000 paired holdout resamples','PR 19; no refitting across vintages','experiments/bootstrap_confidence_intervals.py'),
('WOE experiment','0637926','b93a459','Traditional scorecard challenger','Training-only five-bin WOE with 0.5 smoothing; separate LR','PR 20; not a V5 production component','experiments/woe_credit_scorecard.py'),
('Stress experiment','519df2b','b93a459','Trace hypothetical borrower shocks','Frozen engine rescored under named scenarios','PR 21; sensitivity scenarios, not empirical forecasts','experiments/stress_sensitivity_testing.py'),
('Abandoned broader remediation','cfce69a','b93a459','Address reviewer model/software concerns','Includes generator, feature and ECL differences','PR 22 closed unmerged; not ancestor of V5','src/hybrid_features.py; src/ecl.py'),
('Code-only remediation','a90db85','b93a459','Software repair with existing risk semantics','Ordering/index/state guards; stale artifacts removed','PR 23; actual V4 base','notebooks/credit_risk_pipeline.py; tests/test_risk_logic.py'),
('Facility workout LGD and ECL','c85cdab','a90db85','Independent qualitative data and resolved-workout model','New facility LGD champion; remaining maturity and write-off rating','Early V4 integration; subsequent fixes still required','src/lgd_model.py; src/facility_ecl.py'),
('V4 recovery diagnostics and challengers','4f87d21','c85cdab','Cash friction, bias, segments and tail challenge','Fixed GB plus Huber/RF/Histogram/Ridge diagnostics','PR 24; fixed holdout repeatedly inspected','notebooks/lgd_model_pipeline.py'),
('V5 initial diagnostics','33c60ee','3ced224','Retain train/holdout stability evidence','No new governed model','V5 fork from V4 ancestor; initial PR 25','notebooks/lgd_model_pipeline.py'),
('Frozen V5 implementation release','0dfe4c8','33c60ee','Reconciliation, interface repair and release evidence','Approved models unchanged; fixed-cohort and realized-tail diagnostics','PR 25, frozen reference for this independent review','scripts/validate_v5.py; scripts/test_dashboard.py'),
]
phase_rows=[]; caps=[]
for name,sha,parent,obj,method,notes,evidence in phases:
 files=git('ls-tree','-r','--name-only',sha).splitlines()
 def source(path):
  return git('show',sha+':'+path) if path in files else ''
 ecl=source('src/ecl.py'); pipe=source('notebooks/credit_risk_pipeline.py')
 phase_rows.append(dict(phase=name,commit=git('rev-parse',sha).strip(),starting_point=parent,objective=obj,methodology=method,interpretation=notes,evidence=evidence))
 caps.append(dict(phase=name,commit=sha,portfolio='supplied + generator' if 'scripts/generate_sme_portfolio.py' in files else 'supplied CSV',PD='present',WOE='experiment' if any('woe_credit' in p for p in files) else 'absent',calibration='deciles' if 'calibration_table' in pipe else 'aggregate only',staging='PD cutoffs' if 'Stage 1":1.0' in ecl else 'reporting-date rules',EWS='present' if 'src/early_warning.py' in files else 'absent',LGD='facility workout' if 'src/lgd_model.py' in files else 'borrower proxy',EAD='facility terms' if 'src/facility_ecl.py' in files else 'borrower/products',ECL='facility aggregation' if 'src/facility_ecl.py' in files else 'borrower calculation',dashboard='root app' if 'app.py' in files else 'dashboard/app.py',tests=sum(p.startswith('tests/test_') for p in files),workflows=sum(p.startswith('.github/workflows/') for p in files)))
save('phases.csv',phase_rows); save('capability_matrix.csv',caps)
tests=[]
for p in sorted((ROOT/'tests').glob('test_*.py')):
 tree=ast.parse(p.read_text())
 for n in tree.body:
  if isinstance(n,ast.FunctionDef) and n.name.startswith('test_'):
   tests.append(dict(file=str(p.relative_to(ROOT)),test=n.name,assertions=sum(isinstance(x,ast.Assert) for x in ast.walk(n)),source_review_required=True,scope='Inspect source; assertion count alone is not assurance'))
save('test_inventory.csv',tests)
paths=['src/pd_model.py','src/data_preparation.py','src/lgd_model.py','src/ecl.py','src/early_warning.py','src/facility_ecl.py','src/scorecard.py','scripts/generate_sme_portfolio.py','scripts/generate_lgd_workout_history.py','config/macro_scenarios.csv']
save('frozen_source_hashes.csv',[dict(path=p,sha256=hashlib.sha256(git('show','0dfe4c8:'+p).encode()).hexdigest()) for p in paths])
print(len(commits),'commits;',len(branches),'remote branches;',len(phases),'material phases')
