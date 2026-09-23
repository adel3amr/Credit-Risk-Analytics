"""Read-only extraction and best-effort execution of material historical snapshots.

Snapshots are isolated under /tmp and are never patched. Tests or pipeline failures
are evidence, not an excuse to change an older commit.
"""
from pathlib import Path
import subprocess, tempfile, tarfile, io, csv, json, os, concurrent.futures, time, hashlib
import pandas as pd
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'validation_review/evidence'
REVISIONS=[('initial','4d91d1e',None),('v2_pre_final','b6db5b2',None),
 ('v2_final','29ede62',None),('v3_interface','a78bfe9',None),
 ('main_checkpoint','b93a459',None),('broader_remediation_unmerged','cfce69a',None),
 ('code_only_base','a90db85',None),('v4_early_facility','c85cdab',None),
 ('v4_final','4f87d21',None),('v5_initial','33c60ee',None),
 ('v5_frozen','0dfe4c8',None),('pca_experiment','c74d5dc',None),
 ('woe_experiment','0637926','experiments/woe_credit_scorecard.py'),
 ('bootstrap_experiment','0bf890d','experiments/bootstrap_confidence_intervals.py'),
 ('stress_experiment','519df2b','experiments/stress_sensitivity_testing.py')]

def run(item):
 name,revision,experiment=item
 tmp=Path(tempfile.mkdtemp(prefix='cra-history-'+name+'-'))
 archive=subprocess.check_output(['git','archive','--format=tar',revision],cwd=ROOT)
 with tarfile.open(fileobj=io.BytesIO(archive)) as tf: tf.extractall(tmp,filter='data')
 prehash={str(p.relative_to(tmp)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (tmp/'data/raw').glob('*.csv')}
 commands=[]; results=[]
 if (tmp/'scripts/generate_sme_portfolio.py').exists(): commands.append('scripts/generate_sme_portfolio.py')
 if (tmp/'scripts/generate_lgd_workout_history.py').exists(): commands.append('scripts/generate_lgd_workout_history.py')
 if (tmp/'notebooks/lgd_model_pipeline.py').exists(): commands.append('notebooks/lgd_model_pipeline.py')
 if (tmp/'notebooks/credit_risk_pipeline.py').exists(): commands.append('notebooks/credit_risk_pipeline.py')
 if experiment: commands.append(experiment)
 env=os.environ.copy();env.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MPLBACKEND='Agg')
 for path in commands:
  try:
   cp=subprocess.run(['python',str(tmp/path)],cwd=tmp,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=150)
   status='PASS' if cp.returncode==0 else 'FAIL'
   results.append(dict(command=path,status=status,detail=cp.stdout[-1200:]))
   if cp.returncode:break
  except subprocess.TimeoutExpired:
   results.append(dict(command=path,status='TIMEOUT',detail='150s limit'));break
 row=dict(snapshot=name,revision=revision,commands='; '.join(f'{r["command"]}:{r["status"]}' for r in results),
          fail_detail=results[-1]['detail'] if results and results[-1]['status']!='PASS' else '',
          raw_files_before=json.dumps(prehash),generated_borrowers='',generated_defaults='',generated_default_rate='',
          holdout_borrowers='',holdout_stage_counts='',pd_auc='',pd_gini='',pd_brier='',lgd_mae='',lgd_rmse='',total_ead='',total_ecl='',notes='')
 try:
  raw=pd.read_csv(tmp/'data/raw/sme_credit_portfolio.csv');row['generated_borrowers']=len(raw);row['generated_defaults']=int(raw.default.sum());row['generated_default_rate']=float(raw.default.mean())
 except Exception as e:row['notes']+='raw:'+str(e)[:80]+';'
 try:
  scored=pd.read_csv(tmp/'data/processed/scored_portfolio.csv');row['holdout_borrowers']=len(scored)
  row['holdout_stage_counts']=json.dumps(scored.stage.astype(str).value_counts().to_dict()) if 'stage' in scored else ''
  row['total_ead']=float(scored.ead.sum());row['total_ecl']=float(scored.ecl.sum()) if 'ecl' in scored else float(scored.ecl_12m.sum())
 except Exception as e:row['notes']+='scored:'+str(e)[:80]+';'
 try:
  m=pd.read_csv(tmp/'outputs/model_validation.csv').iloc[0];row['pd_auc']=float(m.ROC_AUC);row['pd_gini']=float(m.Gini);row['pd_brier']=float(m.Brier)
 except Exception as e:row['notes']+='pd:'+str(e)[:80]+';'
 try:
  lgd=pd.read_csv(tmp/'outputs/lgd_model_validation.csv');m=lgd[lgd.Model=='Gradient Boosting'].iloc[0]
  row['lgd_mae']=float(m.MAE);row['lgd_rmse']=float(m.RMSE)
 except Exception:pass
 return row

if __name__=='__main__':
 rows=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
  futures={pool.submit(run,item):item for item in REVISIONS}
  for future in concurrent.futures.as_completed(futures):
   r=future.result();rows.append(r);print(r['snapshot'],r['commands'],flush=True)
 rows.sort(key=lambda r:[name for name,*_ in REVISIONS].index(r['snapshot']))
 with (OUT/'historical_reproduction.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
