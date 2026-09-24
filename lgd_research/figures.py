"""Eighteen reproducible diagnostic figures from frozen selection evidence."""
from pathlib import Path
from io import BytesIO
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
OUT = HERE / "figures"
OUT.mkdir(exist_ok=True)
S = pd.read_csv(HERE / "results/development_scorecard.csv")
P = pd.read_csv(HERE / "results/selection_predictions.csv")
V = pd.read_csv(HERE / "data/r2_selection.csv")
F = pd.read_csv(HERE / "results/feature_support.csv")
T = pd.read_csv(HERE / "results/stress_responses.csv")
W = V.merge(P.query("model == 'A V5 H' and population == 'R2 selection'")[['facility_id','prediction']],
            on='facility_id', validate='one_to_one')
W['error'] = W.prediction-W.economic_lgd
W['band'] = pd.cut(W.economic_lgd,[0,.2,.4,.6,.75,.9,1.00001],include_lowest=True,
                   labels=['0-20','20-40','40-60','60-75','75-90','90-100'])
B = W.groupby('band',observed=True).agg(n=('error','size'),ead=('ead_at_default','sum'),bias=('error','mean'),
                                        mae=('error',lambda x: abs(x).mean()),
                                        rmse=('error',lambda x: np.sqrt(np.mean(x*x))),
                                        actual=('economic_lgd','mean'),pred=('prediction','mean'),
                                        error_sum=('error','sum'))
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.spines.top':False,'axes.spines.right':False})


def plot(name,title,x,y=None,kind='bar',xlabel='',ylabel='LGD fraction',note='R2 selection; synthetic; model as labelled',rotation=0):
    fig,ax=plt.subplots(figsize=(7.5,4.3))
    if kind=='scatter':
        ax.scatter(x,y,alpha=.18,s=10,color='#136e83')
        if name=='01_actual_predicted': ax.plot([0,1],[0,1],'--',color='#ce6243',label='Equal');ax.legend()
        else: ax.axhline(0,ls='--',color='#ce6243')
    elif kind=='hist': ax.hist(x,bins=35,color='#136e83',edgecolor='white')
    elif kind=='line': ax.plot(x,y,marker='o',color='#136e83')
    elif kind=='grouped':
        labels=list(x); groups=y
        for i,(legend,vals) in enumerate(groups.items()):ax.bar(np.arange(len(labels))+(i-(len(groups)-1)/2)*(.75/len(groups)),vals,width=.75/len(groups),label=legend)
        ax.set_xticks(np.arange(len(labels)),labels);ax.legend(frameon=False,fontsize=8)
    else: ax.bar(x,y,color=['#ce6243' if z < 0 else '#136e83' for z in y])
    ax.set_title(title,loc='left',fontweight='bold',pad=13)
    ax.set_xlabel(xlabel);ax.set_ylabel(ylabel)
    if rotation:ax.tick_params(axis='x',labelrotation=rotation)
    fig.text(.11,.012,note,fontsize=7,color='#535c64')
    fig.tight_layout(rect=(0,.035,1,1))
    buffer=BytesIO()
    fig.savefig(buffer,format='png',dpi=190,bbox_inches='tight')
    content=buffer.getvalue()
    if len(content)<1000: raise RuntimeError(f'Incomplete figure: {name}')
    (OUT/f'{name}.png').write_bytes(content)
    plt.close(fig)


plot('01_actual_predicted','Actual vs forecast LGD',W.economic_lgd,W.prediction,'scatter','Actual LGD','Forecast LGD')
plot('02_residual_distribution','Forecast minus actual: residuals',W.error,kind='hist',xlabel='Error',ylabel='Facilities')
plot('03_residual_vs_forecast','Residual vs forecast',W.prediction,W.error,'scatter','Forecast LGD','Forecast minus actual')
W['decile']=pd.qcut(W.prediction.rank(method='first'),10,labels=False)
C=W.groupby('decile').agg(actual=('economic_lgd','mean'),pred=('prediction','mean'))
plot('04_calibration','Forecast-decile calibration',C.index+1,{'Actual':C.actual,'Forecast':C.pred},'grouped','Forecast decile')
plot('05_bias_by_band','Bias by realized loss band',B.index.astype(str),B.bias,xlabel='Realized LGD band',ylabel='Forecast minus actual')
plot('06_mae_rmse_by_band','Error by realized loss band',B.index.astype(str),{'MAE':B.mae,'RMSE':B.rmse},'grouped','Realized LGD band')
plot('07_count_by_band','Facilities by realized loss band',B.index.astype(str),B.n,xlabel='Realized LGD band',ylabel='Facilities')
plot('08_ead_by_band','EAD by realized loss band',B.index.astype(str),B.ead/1e6,xlabel='Realized LGD band',ylabel='Synthetic EAD (millions)')
plot('09_severe_actual_vs_pred','Severe loss: actual vs forecast',B.index.astype(str)[-2:],{'Actual':B.actual[-2:],'Forecast':B.pred[-2:]},'grouped','Realized LGD band')
Q=F.query("feature == 'guarantee_coverage' and status == 'present'")
plot('10_guarantee_support','Zero-guarantee support by population',Q.population.str.replace('Current synthetic facilities','Current').str.replace('H held out (historically viewed)','H holdout'),Q.zero_count/Q.n,xlabel='Population',ylabel='Fraction zero',rotation=25,note='Development/selection vs current; different source populations')
G=V.groupby('product_type').guarantee_coverage.agg(['mean',lambda x:(x==0).mean()])
plot('11_guarantee_by_product','R2 guarantee distribution by product',G.index,{'Mean coverage':G['mean'],'Zero share':G['<lambda_0>']},'grouped','Product',rotation=20)
D=W.groupby('collateral_type').agg(bias=('error','mean'),mae=('error',lambda x:abs(x).mean()))
plot('12_collateral_errors','Error by collateral type',D.index,{'Bias':D.bias,'MAE':D.mae},'grouped','Collateral type')
A=S.query("population == 'R2 selection' and cohort == 'all' and not model.str.startswith('ablate')",engine='python')
plot('13_challenger_comparison','Candidate MAE and RMSE',A.model,{'MAE':A.mae,'RMSE':A.rmse},'grouped','Research candidate',rotation=65,note='Quantile p90 and future-information oracle are not expected-LGD deployment candidates')
plot('14_error_cancellation','Sum of errors by realized band',B.index.astype(str),B.error_sum,xlabel='Realized LGD band',ylabel='Sum of forecast-minus-actual')
ab=S.query("population == 'R2 selection' and cohort == 'all' and model.str.startswith('ablate')",engine='python')
base=A.query("model == 'GB enhanced R2'").iloc[0]
plot('15_ablation','Removal of input groups: RMSE',list(ab.model.str.replace('ablate ',''))+['all groups'],list(ab.rmse)+[base.rmse],xlabel='Omitted group',ylabel='RMSE',rotation=20)
oracle=A[A.model.isin(['A V5 H','GB enhanced R2','oracle FUTURE INFORMATION'])]
plot('16_oracle_gap','Deployable vs non-deployable oracle',oracle.model,{'MAE':oracle.mae,'RMSE':oracle.rmse},'grouped','Information set',rotation=16,note='Oracle uses future cure, shocks and duration; cannot be scored in advance')
ts=T[T.model.eq('GB enhanced R2')]
plot('17_stress_response','Paired synthetic stress: label vs forecast',ts.scenario,{'Realized shift':ts.actual_shift,'Forecast shift':ts.forecast_shift},'grouped','Stress channel',rotation=20,note='Same random seed; stressed future shocks may not be observable at scoring')
four=S.query("population == 'R2 selection' and cohort == 'all' and model in ['A V5 H','B V5 R2 equal N','C two-stage H','D two-stage R2 equal N']")
plot('18_data_vs_model','2x2 research: data and method',four.model,{'MAE':four.mae,'RMSE':four.rmse},'grouped','Data / method',rotation=18,note='6,000 training rows in both H and R2; same R2 selection sample')
print('Generated',len(list(OUT.glob('*.png'))),'research figures')
assert len(list(OUT.glob('*.png')))==18 and all(p.stat().st_size>1000 for p in OUT.glob('*.png'))
