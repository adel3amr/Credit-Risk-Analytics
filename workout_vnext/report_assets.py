"""Render frozen evidence without fitting or selecting models."""
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
from .generate import HERE,DATA,FEATURES
from .contracts import RANGES,SOURCES,CATEGORIES

def main():
    figures=HERE/'figures';figures.mkdir(exist_ok=True)
    metrics=pd.read_csv(HERE/'results/metrics.csv');segments=pd.read_csv(HERE/'results/segments.csv')
    fig,axes=plt.subplots(2,2,figsize=(13,9),layout='constrained')
    for model,color in [('direct_new','#186f9c'),('component','#b85636')]:
        d=metrics[metrics.model==model].set_index('split').loc[['development','validation','final']]
        axes[0,0].plot(d.index,d.rmse*100,'o-',label=model,color=color)
        tail=segments[(segments.model==model)&(segments.split=='final')&segments.group.isin(['all','cure','high60','high75','high90'])].set_index('group').loc[['all','cure','high60','high75','high90']]
        axes[0,1].plot(tail.index,tail.bias*100,'o-',label=model,color=color)
    axes[0,0].set(title='RMSE across populations',ylabel='LGD percentage points');axes[0,0].legend()
    axes[0,1].axhline(0,color='gray',linewidth=1);axes[0,1].set(title='Final bias · outcome cohorts are diagnostic',ylabel='Predicted minus realized, pp')
    pred=pd.read_csv(HERE/'results/predictions.csv.gz');z=pred[(pred.model=='component')&(pred.split=='final')]
    axes[1,0].hexbin(z.prediction,z.actual,gridsize=25,mincnt=1,cmap='Blues');axes[1,0].plot([0,1],[0,1],color='gray');axes[1,0].set(title='Component · 5,290 resolved snapshots',xlabel='Predicted LGD',ylabel='Realized LGD')
    s=pd.read_csv(HERE/'results/stress.csv');s=s[s.split=='final'];axes[1,1].barh(s.stress,s.mean_lgd_change*100,color='#b85636');axes[1,1].set(title='Sensitivity, not causal stress validation',xlabel='Mean LGD change, pp')
    fig.suptitle('WN-1 · frozen synthetic experiment · challenger NOT PROMOTED',fontsize=15)
    fig.savefig(figures/'validation.png',dpi=170);plt.close(fig)
    definitions={
      'predefault_pd':'Last dated predefault PD proxy; current default PD is separately one',
      'predefault_rating':'Dated predefault internal rating proxy',
      'rating_migration':'Dated reported change in rating; not future migration',
      'financial_strength':'Observed standardized synthetic financial-strength proxy',
      'previous_defaults':'Known prior-default indicator', 'utilization':'Last dated credit utilization',
      'delinquency':'Last dated days past due', 'age':'Months elapsed since default',
      'months_since_last_recovery':'Age minus latest observed recovery month; age if none',
      'recovered_ratio':'Observed cumulative cash recovery / default exposure',
      'collateral_ratio':'Last recorded appraised value / remaining EAD; not depleted security availability',
      'haircut':'Last known valuation haircut fraction', 'lien':'Known lien rank',
      'enforcement':'Observed enforcement initiation indicator',
      'guarantee_ratio':'Minimum of one and eligible nominal guarantee / remaining EAD; not payout-depleted',
      'guarantor_quality':'Known synthetic quality fraction', 'enforceability':'Known enforceability indicator',
      'claim':'Observed claim submission indicator', 'restructured':'Observed restructuring agreement indicator',
      'cost_ratio':'Observed accumulated costs / default exposure',
      'growth':'Contemporaneous annual output-growth assumption', 'unemployment':'Contemporaneous unemployment assumption',
      'price_change':'Contemporaneous collateral-price change fraction',
      'rate':'Fixed annual facility discount/accrual rate',
      'mi_ratio':'Cumulative postdefault suspended memorandum interest / remaining EAD',
      'ead':'Principal plus predefault interest minus cash recoveries already received; excludes suspended interest and writeoffs'}
    rows=[]
    for n in FEATURES:
        source=next(k for k,v in SOURCES.items() if n in v)
        unit='EUR' if n=='ead' else 'months' if n in ['age','months_since_last_recovery'] else 'days' if n=='delinquency' else 'percent' if n in ['growth','unemployment'] else 'rank' if n in ['lien','predefault_rating'] else 'standardized value' if n=='financial_strength' else 'numeric ratio / indicator'
        rows.append({'name':n,'definition':definitions[n],'type':'number','unit':unit,'source':source,'observation_time':'effective_date AND recorded_at <= observation_date','allowed_range':RANGES[n],'missing_policy':'reject','availability':'REQUIRES NEW DATA CAPTURE at institution; available in WN synthetic ledger','lineage':'known_event_ids; facility/default linkage; data manifest','model_usage':'direct-new and component; family ablations omit specified features','sensitivity':'synthetic public reference; future institutional equivalent confidential'})
    for n,values in CATEGORIES.items():rows.append({'name':n,'definition':'Known '+n,'type':'category','unit':'category','source':'borrower/facility/collateral','observation_time':'origination/default known','allowed_categories':values,'missing_policy':'reject','availability':'REQUIRES NEW DATA CAPTURE validation; synthetic available','lineage':'canonical entity ID','model_usage':'direct-new/component','sensitivity':'synthetic public'})
    (HERE/'feature_contract.json').write_text(json.dumps({'version':'WN-1','features':rows},indent=2)+'\n')
    text='# WN-1 feature contract\n\nAll features are available in the synthetic ledger at observation time; institutional availability has NOT been validated. Future cure, ultimate LGD, future cashflows, latent capacity and resolution duration are prohibited predictors. Development/validation/final coverage is in `results/feature_population.csv`; domains are enforced by `contracts.check`. No silent imputation.\n\n| Feature | Definition | Unit | Source | Range/categories |\n|---|---|---|---|---|\n'
    for r in rows:text+='| '+ ' | '.join([r['name'],r['definition'],r['unit'],r['source'],str(r.get('allowed_range',r.get('allowed_categories')))])+' |\n'
    text+='\nMachine-readable `feature_contract.json` also records model usage, availability, observation time, lineage and sensitivity. Zero is a real no-event/no-support value, not missingness. Ratios over one are allowed for collateral and costs where denominator economics imply them. Unknown categories and nonfinite values reject. `None` bounds mean no finite bound, not permission for NaN.\n'
    (HERE/'FEATURE_CONTRACT.md').write_text(text)
if __name__=='__main__':main()
