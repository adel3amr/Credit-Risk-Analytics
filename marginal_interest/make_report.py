"""Render results from immutable outputs; does not fit, select, or score."""
import json
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from marginal_interest.experiment import HERE,OUT,DATA


def table(df):
    return '| '+' | '.join(df.columns)+' |\n| '+' | '.join(['---']*len(df.columns))+' |\n'+'\n'.join('| '+' | '.join(str(v) for v in row)+' |' for row in df.itertuples(index=False,name=None))

def main():
    m=pd.read_csv(OUT/'metrics.csv');s=pd.read_csv(OUT/'segments.csv');p=pd.read_csv(OUT/'paired_uncertainty.csv');g=json.loads((OUT/'promotion_gates.json').read_text());e=json.loads((OUT/'independent_ecl.json').read_text());manifest=json.loads((DATA/'manifest.json').read_text())
    f=m[(m.split=='final')&(m.scenario=='baseline')].copy();f[['mae','rmse','bias','predicted_mean','realized_mean']]*=100
    performance=f[['model','n','mae','rmse','bias','r2','predicted_mean','realized_mean']].round(4)
    inc=p[(p.split=='final')&(p.scenario=='baseline')&(((p.model=='M3')&(p.control=='M1'))|((p.model=='M4')&(p.control=='M4_without_mi'))|((p.model=='M4')&(p.control=='M0')))].copy()
    for c in ['delta_rmse','delta_rmse_low','delta_rmse_high']:inc[c]*=100
    inc=inc[['model','control','grouping','delta_rmse','delta_rmse_low','delta_rmse_high']].round(4)
    tails=s[(s.split=='final')&(s.scenario=='baseline')&(s.model.isin(['M0','M4']))&(s.segment.isin(['realized_gt60','realized_gt75','realized_ge90','low_le10','cure','guarantee:full']))].copy()
    for c in ['bias','bias_low','bias_high']: tails[c]*=100
    tails=tails[['model','segment','n','bias','bias_low','bias_high']].round(3)
    sup=pd.read_csv(OUT/'support.csv.gz'); support=sup.groupby(['split','scenario']).agg(n=('supported','size'),supported=('supported','sum'),new_feature_outside=('new_feature_outside_range','sum')).reset_index();support['rejected']=support.n-support.supported
    cal=s[(s.split=='final')&(s.scenario=='baseline')&(s.model.isin(['M0','M4']))&s.segment.str.startswith('predicted:')].copy()
    for c in ['predicted_mean','realized_mean','bias','bias_low','bias_high']:cal[c]*=100
    cal=cal[['model','segment','n','predicted_mean','realized_mean','bias','bias_low','bias_high']].round(3)
    report=f'''# Marginal Interest LGD experiment — MI-1

## 1. Executive conclusion
**No robust incremental benefit from Marginal Interest was demonstrated.** This is disposition5 for historical feasibility and an inconclusive/negative incremental-value result for the new hypothetical experiment. M4 improved final RMSE versus M0 by0.264pp, but adding MI beyond age changed RMSE by+0.0033pp and adding it beyond compact workout controls changed RMSE by−0.0104pp; both paired95% intervals include zero. The broader observed workout state appears useful within this chosen simulator, while a distinct contribution from MI is not established. No positive empirical/bank claim follows. **CHALLENGER_NOT_PROMOTED; institutional production BLOCKED.**

## 2. Research question
Does observation-time suspended contractual interest contain robust incremental information about remaining impaired-facility recovery severity? The prespecified comparisons and stopping rule in PROTOCOL.md were committed before generation/fitting. No tuning followed validation or final results.

## 3–4. Definition and accounting/EAD treatment
MI is the cumulative memorandum interest balance from opening monthly principal×rate/12 through observation. No compounding, interest payments or capitalization; principal payments reduce later accrual. It is neither IFRS interest revenue nor an additional loss. EAD is remaining principal. MI is only a predictor. The target is remaining discounted principal-recovery loss at observation; it is deliberately a new research target and cannot silently replace historical default-date LGD. See FEATURE_CONTRACTS.md and EXTERNAL_EVIDENCE.md.

## 5–7. Observation-time availability, lineage and leakage
Source static facilities -> fixed borrower split -> default date and monthly principal-payment/accrual ledger -> observation snapshot -> independent future recovery draws -> resolved outcome. Future outcomes never construct predictors. Allowlist excludes final LGD,cure,writeoff/future cashflows,latent willingness/security quality/guarantor strength and oracle means. Perturbation tests and independent ledger arithmetic pass. Final outcomes were generated and hash-frozen but not evaluated until model lock. Reading bytes for hash/integrity verification is not outcome inspection. The final target is now opened engineering evidence and must never be reused as a fresh holdout. Frozen R1 transfer diagnostic saw source development covariates historically; it is not an independent matched-training benchmark.

## 8. Dataset/DGP changes
Historical data unchanged. New hypothetical MI-1 release,12,000 borrowers/20,747 facilities; split counts below. Pre-observation willingness and quarter shocks influence payments and future capacity; coefficients are hypotheses,not empirical estimates. Irreducible future recovery/cure noise retained. No outcome balancing. The extra full-payoff cure path is hypothetical and reported cure labels do not enumerate the original simulator's hidden cure channel.

An initial metadata/API defect stopped generation before outcomes. Later two truncated archives were detected before fitting. Deterministic recovery preserved exact prefix bytes; the final-outcome file matches its original frozen hash. The ledger was truncated before hashing,so its repaired hash was recorded before fitting with the old manifest preserved. No alternative seeds/distributions were selected. See GENERATION_LOG.md and recovery_verification.json; original damaged evidence retained.

## 9. Development/validation/final design
Development7,200 borrowers/12,416 facilities; validation2,400/4,170; final2,400/4,161. Borrower and facility IDs disjoint. Hypothetical observation vintages are temporally ordered; all facilities from each borrower stay together. Source covariates are reused from known historical development; macro values are not actual historical observations for these new dates. No claim of institution-level temporal representativeness. Seeds and outcomes frozen before model fitting.

## 10. Candidates and controls
Same retained S2-R1 histogram boosting settings for every newly fitted candidate:350 iterations,.05 rate,31 leaves,minleaf80,L2=5,seed94001,original monotonic signs,no search. M0 refits retained feature specification on new target; M1 adds age; M2 adds MI amount/ratio; M3 adds age+MI; M4 adds compact observed recovery/restructuring/default-principal controls. M4_without_mi is a prespecified diagnostic ablation,not an extra selected model. Validation chose M4 among M1–M4; the ablation was slightly better on validation and is transparently retained. Balance,rate,products,protection and financial-risk proxies are controlled. Actual PD/rating are absent and were not invented; a fully PD/rating-controlled conclusion remains untested. MI/EAD is identical to MI/principal and excluded as redundant.

## 11. Final baseline-scenario performance
Errors,bias and meanLGD in percentage points/percent; R² unitless. N=4,161 for all. Frozen_R1_transfer is an old-target transfer diagnostic,not comparable historical published RMSE.

{table(performance)}

## 12. Predicted-band calibration
Fixed bands declared before results; all uncertainty here is400-draw paired borrower bootstrap. Outcome-selected cohorts below are separate diagnostics. Small samples are not evidence of precise calibration.

{table(cal)}

## 13–14. Severe loss,low loss and cure
Bias intervals in pp; >90% cohort has only92 observations and is insufficient for strong claims. Explicit full-payoff cure is a future outcome label,not an input; large retrospective cure bias does not establish forecast miscalibration on an observable cohort.

{table(tails)}

## 15–16. Support and stability
Existing joint macro×collateral×guarantee support rules unchanged. All scenarios and all new feature ranges checked; unsupported predictions are diagnostic-only and cannot be deployed. Additional-feature joint density is not certified. feature_stability.csv reports missingness,KS and ranges; temporal_stability.csv reports yearly error/bias. Current platform has no captured MI ledger: live missingness/distribution cannot be estimated. Source/current population comparability is therefore unproven.

{table(support)}

## 17–19. Incremental value,age controls and uncertainty
Paired changes in RMSE,pp; negative means lower error.400 borrower and400 sector/observation-quarter bootstrap replicates; both reported,no selection of the narrower interval. No tuning or post-result feature search. M4-vs-M0 shows a small improvement within this DGP; the two MI-specific tests are inconclusive. MI is algebraically determined by balance history,rate and age,so it cannot add new information relative to the complete ledger; finite-model approximation benefits would not change that fact. Partial observability and an assumed common cause are part of this simulator,not empirical proof. Confidence intervals do not cover DGP misspecification,coefficient uncertainty or institutional transfer.

{table(inc)}

## 20. Scenarios
Upside/baseline/downside reuse the existing economic-coordinate mapping with preregistered scenario values. Every new candidate and the fixed ablation had zero reversals across validation and final. No prediction sorting or overlays. Source support nevertheless fails most materially under downside. MI's causal effect is not constrained or established by these macro monotonicity checks.

## 21. Feature availability
New ledger fields are RESEARCH ONLY/REQUIRES NEW DATA CAPTURE. No live operational integration,accounting reconciliation or as-of posting-delay validation exists. Marginal ratios use positive remaining principal; invalid/missing values fail closed. No Stage1/2 imputation. Source snapshots may be stale; no true PD/rating control. Production gate remains blocked independently of numerical performance.

## 22. Controlled ECL bridge
Validation-selected M4 locked before final ECL calculation. Identical4,161 facilities,borrowers,Stage3,PD1,EAD and scenario weights. Only LGD changes. Scenario-weighted **M0 ECL={e['benchmark']:,.2f}**, **M4 ECL={e['challenger']:,.2f}**, difference **{e['difference']:,.2f} ({e['percent_change']:.4f}%)**, unspecified currency units. Stage1/2=N/A because this is impaired-only research. All impact is Stage3. Sector contributions in ecl_sector_bridge.csv. This is unbooked impact,not a model selection criterion; this reduction is not attributable solely to MI.

## 23. Promotion gates
Historical230 numerical checks independently recomputed with agreement; historical19 evidence hashes verified. Existing historical adverse gate decisions retained. New target conditional-mean gates cannot be passed using a latent-state oracle masquerading as observable conditional expectation. Original-S2 same-target acceptance and current live feature-availability gates are not available and remain blocked. Existing1pp overall/regime and2pp segment tolerances were NOT weakened; realized clustered calibration intervals were additionally assessed,with{sum(v['status']=='FAIL' for v in g['calibration'])} failed/insufficient final checks. This supplement is not claimed to replace the original conditional-equivalence framework. Joint support FAIL; zero scenario reversals PASS; engineering/test evidence separately recorded. All requirements must pass for promotion; they do not.

## 24–25. Disposition and remaining limitations
CHALLENGER_NOT_PROMOTED; institutional production BLOCKED. Historical question is not retrospectively answerable. Hypothetical experiment does not demonstrate MI's robust incremental value. Data-capture/PD-rating controls,complete cure labels,macro support,prediction calibration,independent institutional validation and deployment qualification remain unresolved. No modelling search should continue on this opened final set. Next legitimate evidence would be a governed real observation-time ledger or a separately justified hypothesis,not repeated synthetic tuning.

## 26. Tests,reconciliation and release track
Full-suite results in full_tests.txt. Independent cashflow recomputation,equal ECL inputs and portfolio aggregation are saved in reconciliation.json/independent_ecl.json; historical files unchanged. Release branch remains7773beb86df8480d964daaaf62199cedc15d356a. GitHub publication/authentication is blocked; final reviewed-commit CI not run; rendered browser verification outstanding. These do not alter research findings. No production model was changed or promoted.

Reproduce/check: install requirements-platform-lock.txt; run `python -m pytest -q`; inspect LOCK.json and FINAL_OPENED.json; run `python -m marginal_interest.audit` and `python -m marginal_interest.make_report` to recalculate reports from known outputs. Generator/fit/final evaluator refuse overwrite/reopening. Do not delete lock evidence to rerun a favourable experiment. Model prediction artifacts and fixed datasets are committed for reproducibility.
'''
    (HERE/'REPORT.md').write_text(report)
    fig,axes=plt.subplots(1,2,figsize=(12,4.5))
    plot=f[f.model!='frozen_R1_transfer'];axes[0].bar(plot.model,plot.rmse,color=['#5b7083']*4+['#167d8d','#8bb6bc']);axes[0].set_ylabel('Final RMSE (percentage points)');axes[0].tick_params(axis='x',rotation=35);axes[0].set_title('Fixed candidates · new remaining-LGD target')
    q=inc[inc.grouping=='customer_id'];y=np.arange(len(q));axes[1].errorbar(q.delta_rmse,y,xerr=np.array([q.delta_rmse-q.delta_rmse_low,q.delta_rmse_high-q.delta_rmse]),fmt='o',color='#167d8d');axes[1].axvline(0,color='grey',ls='--');axes[1].set_yticks(y,q.model+' minus '+q.control);axes[1].set_xlabel('Paired RMSE change (pp), borrower 95% CI');axes[1].set_title('MI-specific intervals include zero')
    fig.suptitle('MI-1 hypothetical synthetic research · NOT PROMOTED');fig.tight_layout();fig.savefig(OUT/'research_summary.png',dpi=180);plt.close(fig)

if __name__=='__main__':main()
