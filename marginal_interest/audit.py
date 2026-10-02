"""Post-freeze independent arithmetic, stability and reporting; never fits models."""
import json
import subprocess
import numpy as np
import pandas as pd
from scipy.stats import ks_2samp
from marginal_interest.experiment import ROOT,HERE,DATA,OUT,EXTRA,WEIGHTS,sha,writej,csv


def main():
    lock=json.loads((OUT/'LOCK.json').read_text()); chosen=lock['selected']
    pred=pd.read_csv(OUT/'predictions.csv.gz'); dev=pd.read_csv(DATA/'development_inputs.csv.gz')
    shifts=[]; temporal=[]; reconciled=[]
    for split in ['validation','final']:
        x=pd.read_csv(DATA/f'{split}_inputs.csv.gz')
        for field in list(dict.fromkeys(EXTRA['M4']+['ead_at_default','interest_rate','collateral_coverage','guarantee_coverage'])):
            shifts.append({'split':split,'feature':field,'missing':int(x[field].isna().sum()),'ks':ks_2samp(dev[field],x[field]).statistic,'development_mean':dev[field].mean(),'evaluation_mean':x[field].mean(),'below_dev_min':int((x[field]<dev[field].min()).sum()),'above_dev_max':int((x[field]>dev[field].max()).sum())})
        for name in ['M0',chosen]:
            p=pred[(pred.split==split)&(pred.scenario=='baseline')&(pred.model==name)].merge(x[['facility_id','reporting_date']],on='facility_id',validate='one_to_one')
            p['year']=pd.to_datetime(p.reporting_date).dt.year
            for year,g in p.groupby('year'):
                error=g.prediction-g.actual
                temporal.append({'split':split,'model':name,'observation_year':int(year),'n':len(g),'rmse':np.sqrt(np.mean(error**2)),'bias':error.mean()})
    final=pred[pred.split=='final']; totals={}; bridge=[]
    for name in ['M0',chosen]:
        z=final[final.model==name].copy();z['weighted_ecl']=[r.prediction*r.ead_at_default*WEIGHTS[r.scenario] for r in z.itertuples()]
        facility=z.groupby('facility_id').weighted_ecl.sum(); byborrower=z.groupby('customer_id').weighted_ecl.sum()
        scalar=sum(float(r.prediction)*float(r.ead_at_default)*WEIGHTS[r.scenario] for r in z.itertuples())
        totals[name]=float(facility.sum())
        reconciled.append({'model':name,'facility_count':len(facility),'scenario_rows':len(z),'stage_unique':sorted(z.stage.unique().tolist()),'pd_unique':sorted(z.pd.unique().tolist()),'facility_vs_borrower_error':abs(facility.sum()-byborrower.sum()),'scalar_vs_vector_error':abs(scalar-facility.sum())})
        for sector,g in z.groupby('industry'): bridge.append({'model':name,'industry':sector,'ecl':g.weighted_ecl.sum()})
    a=final[final.model=='M0'].sort_values(['facility_id','scenario']); b=final[final.model==chosen].sort_values(['facility_id','scenario'])
    same={c:bool(np.array_equal(a[c].to_numpy(),b[c].to_numpy())) for c in ['facility_id','customer_id','scenario','pd','stage','ead_at_default']}
    csv(OUT/'feature_stability.csv',pd.DataFrame(shifts));csv(OUT/'temporal_stability.csv',pd.DataFrame(temporal));csv(OUT/'ecl_sector_bridge.csv',pd.DataFrame(bridge))
    writej(OUT/'independent_ecl.json',{'selected':chosen,'benchmark':totals['M0'],'challenger':totals[chosen],'difference':totals[chosen]-totals['M0'],'percent_change':100*(totals[chosen]/totals['M0']-1),'stage1':'N/A: impaired-only cohort','stage2':'N/A: impaired-only cohort','stage3':totals,'same_inputs':same,'reconciliation':reconciled,'booked':False})
    # Replicate historical immutability and verify historical gate evidence hash chain.
    changes=subprocess.check_output(['git','diff','7773beb86df8480d964daaaf62199cedc15d356a','--name-only'],cwd=ROOT,text=True).splitlines()
    old=json.loads((ROOT/'s2_remediation/results/decision.json').read_text())
    matches={p:sha(ROOT/p)==h for p,h in old['source_hashes'].items()}
    writej(OUT/'historical_integrity.json',{'reviewed_sha':subprocess.check_output(['git','rev-parse','review/final-red-team-release'],cwd=ROOT,text=True).strip(),'changed_historical_paths':[p for p in changes if not p.startswith(('marginal_interest/','tests/test_marginal_interest.py'))],'historical_evidence_hashes':matches})
    paired=pd.read_csv(OUT/'paired_uncertainty.csv'); gates=json.loads((OUT/'promotion_gates.json').read_text())
    comparisons=paired[(paired.split=='final')&(paired.scenario=='baseline')&(((paired.model=='M3')&(paired.control=='M1'))|((paired.model=='M4')&(paired.control=='M4_without_mi')))]
    demonstrated=bool((comparisons.delta_rmse_high<0).all() and (comparisons.delta_mae_high<=0).all())
    writej(OUT/'incremental_decision.json',{'increment_demonstrated_under_prespecified_CI_rule':demonstrated,'comparisons':comparisons.to_dict('records'),'interpretation':'Hypothetical DGP only; no empirical bank inference, no actual PD/rating control and incomplete cure labels','promotion':gates['disposition']})

if __name__=='__main__':main()
