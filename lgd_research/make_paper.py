"""Generate a standalone study directly from locked CSV evidence."""
from pathlib import Path
import pandas as pd

HERE=Path(__file__).resolve().parent
R=HERE/'results'
select=pd.read_csv(R/'development_scorecard.csv')
final=pd.read_csv(R/'final_scorecard.csv')
ci=pd.read_csv(R/'paired_bootstrap.csv')
stress=pd.read_csv(R/'stress_responses.csv')


def row(df,name,cohort='all',population='R2 selection'):
    x=df[(df.model==name)&(df.population==population)&(df.cohort==cohort)]
    assert len(x)==1,(name,cohort,population)
    return x.iloc[0]


def table(df,population):
    names=['A V5 H','V5 R2 full','GB enhanced R2','two-stage enhanced R2',
           'component R2','oracle FUTURE INFORMATION','quantile p90 RISK ONLY']
    out=['| Model | N | EAD m | MAE pp | RMSE pp | Bias pp | >75 N | >75 EAD m | >75 bias pp | >90 bias pp |',
         '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for n in names:
        a,b,c=(row(df,n,k,population) for k in ['all','realized_gt75','realized_gt90'])
        out.append(f"| {n} | {int(a.n):,} | {a.ead/1e6:.1f} | {a.mae*100:.2f} | {a.rmse*100:.2f} | {a.bias*100:+.2f} | {int(b.n)} | {b.ead/1e6:.1f} | {b.bias*100:+.2f} | {c.bias*100:+.2f} |")
    return '\n'.join(out)


v5=row(final,'A V5 H',population='R2 final holdout')
enh=row(final,'GB enhanced R2',population='R2 final holdout')
two=row(final,'two-stage enhanced R2',population='R2 final holdout')
oracle=row(final,'oracle FUTURE INFORMATION',population='R2 final holdout')
severe_v5=row(final,'A V5 H','realized_gt75','R2 final holdout')
severe_two=row(final,'two-stage enhanced R2','realized_gt75','R2 final holdout')
ci_rmse=ci[(ci.comparison=='two-stage enhanced R2 minus A V5 H')&(ci.cohort=='all')&(ci.metric=='rmse')].iloc[0]
a,b,c,d=(row(select,n) for n in ['A V5 H','B V5 R2 equal N','C two-stage H','D two-stage R2 equal N'])
effect_data=b.rmse-a.rmse
effect_method=c.rmse-a.rmse
effect_interaction=d.rmse-b.rmse-c.rmse+a.rmse
pre=str(R/'dataset_hashes.csv')

intro=f"""# From aggregate calibration to tail risk

## Diagnosing facility-level LGD through data and model experiments

**Research study · 24 September 2026 · controlled synthetic experiment · published V5 reference `0dfe4c8`**

### Abstract

We reconstructed the frozen V5 facility workout LGD model, reproduced its 2,000-facility MAE 11.40 pp and near-zero mean bias −0.31 pp, and showed why the 327 realized losses above 75% still have −15.59 pp mean underprediction. The original workout training data contain almost no facilities with zero guarantee coverage even though 79.2% of active synthetic facilities have zero. A new separately versioned economic recovery generator adds security quality, guarantor strength, correlated downturns and stochastic resolution. We froze 9,000 development, 3,000 model-selection and 3,000 final-holdout cases before model comparisons. On the final synthetic holdout, the original-H-trained V5 model has MAE {v5.mae*100:.2f} pp, RMSE {v5.rmse*100:.2f} pp and severe-realization bias {severe_v5.bias*100:+.2f} pp. The enhanced two-stage research challenger has MAE {two.mae*100:.2f} pp, RMSE {two.rmse*100:.2f} pp and severe-realization bias {severe_two.bias*100:+.2f} pp. Its paired overall RMSE difference has a 95% bootstrap interval of [{ci_rmse.lower_95*100:+.2f}, {ci_rmse.upper_95*100:+.2f}] pp against transferred V5. A non-deployable oracle with future workout information has MAE {oracle.mae*100:.2f} pp, supporting an information-set limitation in this *synthetic* economy. The new proxy features do not exist in the live V5 source. No challenger is promoted, and bank production use remains blocked pending real recovery data and approval.

## 1. Research question and governance

The goal is to explain the observed loss-tail weakness and compare data and method changes, not to fit a known metric. The published V5 branch at `0dfe4c8` is unchanged; all scripts, datasets, fitted research objects and results live under `lgd_research/` on a separate research branch. H historical data and the original 2,000-case holdout have been repeatedly viewed, so they serve as reference diagnostics, never a fresh final selection set. `FINAL_EVALUATION_LOCK.md` records the candidates and the SHA of the final holdout before evaluation.

## 2. Existing framework and independent reproduction

V5 uses a fixed 220-tree Gradient Boosting regressor with six numeric and four categorical features. Its target is bounded economic LGD `clip(1 − discounted net cash recoveries/EAD, 0, 1)`. Source-independent recalculation of the V5 predictions yields MAE .11396453, RMSE .16579849 and prediction-minus-realization bias −.00305172 on 2,000 original holdouts. For 327 realized LGDs >.75, bias is −.15592783; for the top 200 by **predicted** LGD it is −.02534385. The latter is a deployable cohort; the former is known only after resolution. Source integrity, independent accounting identities and history are detailed in `LGD_ROOT_CAUSE_ANALYSIS.md` and the earlier whole-repository review.

## 3. Why the aggregate score conceals the tail

The original 391 outcomes ≤20% contribute +79.01 percentage-error units; the 526 between 20–40% contribute another +19.18. Outcomes above 40% collectively contribute −104.30, leaving total −6.10 / 2,000 = −.00305. Cures (322) contribute +88.39 units and non-cures (1,678) −94.49. Conditional-mean predictions tend to lie between divergent eventual outcomes. Neither this identity nor the oracle alone proves that a given bank's extreme losses are irreducible; it tests the synthetic information set.

## 4. Severe-loss population and support

Original H development has 980 >75% cases and 1/6,000 exactly zero guarantees; original H holdout has 327 >75% and zero exact zero guarantees. Current V5 facility data show 4,096/5,172 zero guarantees. Separate R2 development contains 1,447 >75% cases and 5,414/9,000 zero guarantees. R2 selection has 491 >75% and 1,796/3,000 zero guarantees. Original H to R2 transfer alters outcomes and input mix, so a favorable score is not retrospective V5 improvement. The feature-support audit covers quantiles, missingness and every categorical level in `results/feature_support.csv` and `LGD_FEATURE_SUPPORT_MATRIX.md`. Most importantly, R2's new quality proxies are absent in the current scoring portfolio.

## 5. Economic recovery process and prediction time

R2 generates EAD, sector, product, borrower financial condition, collateral coverage/type/legal quality, guarantee coverage/strength and downturn state at **default**, before workout. Future random market, guarantee and collection shocks affect the realized component recoveries; stochastic cure, length and costs affect dated net cash flows at months 1, 6, 12, 24, 36 and 60. Each component is capped by residual EAD, then the cash flows are discounted using a facility rate. Correlated downturn lowers recoveries while increasing delays and costs. `lgd_research/generate_r2.py` documents every coefficient; none is a regulatory or empirical bank estimate. `LGD_DATA_GENERATION_REGISTER.md` was written before R2 creation. Hashes and seeds appear in `results/dataset_hashes.csv`. R2 final holds 3,000 observations and was evaluated only after the precommitted lock. The generator tests recalculate PV and LGD independently. Future cure, shock, realized recoveries and timing are explicitly excluded from deployable features.

## 6. Comparative designs and data-vs-method attribution

For the controlled 2×2, original H and R2 each contribute 6,000 training cases; both are scored on the same R2 selection set. A is unchanged V5 trained on H; B is unchanged V5 trained on R2; C is common-input two-stage trained on H; D is common-input two-stage trained on R2. Their RMSEs are {a.rmse:.5f}, {b.rmse:.5f}, {c.rmse:.5f} and {d.rmse:.5f}. Data effect B−A = {effect_data:+.5f}; method effect C−A = {effect_method:+.5f}; interaction D−B−C+A = {effect_interaction:+.5f}. These are differences of scores under *different synthetic recovery processes* and not causal estimates for a bank. Holding R2 data fixed, enhanced input features reduce RMSE from {row(select,'V5 R2 full').rmse:.5f} to {row(select,'GB enhanced R2').rmse:.5f}; this bundles information availability and interaction with the estimator. The new inputs are not available to live V5, so no deployed improvement follows.

## 7. Baselines, challenger methodology and leakage

The simple collateral/product segment mean has much higher RMSE than V5 on R2 selection. Fixed alternatives include unchanged Huber and Random Forest; the enhanced GB adds synthetic observable-at-default information; the two-stage mixture models the *probability* of a >75% regime then recombines conditional expected losses; the component approach separately predicts recoveries, costs and duration under an EAD cash budget. These are research methodology changes and do not affect ECL. The p90 conditional quantile illustrates an upper-risk bound, **not** an unbiased expected loss: its large aggregate positive bias is therefore unsurprising. The oracle alone sees future cure, resolution duration and realization shocks; it is non-deployable by design. Target and postdefault recovery values never enter deployable candidate features.

## 8. Ablation and information sufficiency

On R2 selection, enhanced GB RMSE is {row(select,'GB enhanced R2').rmse:.5f}. Removing collateral-related inputs raises it to {row(select,'ablate collateral').rmse:.5f}, guarantees to {row(select,'ablate guarantee').rmse:.5f}, borrower inputs to {row(select,'ablate borrower').rmse:.5f}, and the three new quality/downturn proxies to {row(select,'ablate new information').rmse:.5f}. Removing facility size/product makes little difference in this synthetic generator ({row(select,'ablate facility').rmse:.5f}). These are conditional model perturbations, not causal effects. The oracle's large advantage supports the specific hypothesis that future workout variability is informative but hidden at prediction time; adding postdefault outcomes to a deployable model would be leakage.

## 9. Final holdout: all finalists on identical facilities

The following results use only the frozen 3,000-case R2 final sample. Each tail has its own N and exposure denominator; the detailed cohort and EAD-weighted figures are in `results/final_scorecard.csv` and paired uncertainty in `results/paired_bootstrap.csv`.

{table(final,'R2 final holdout')}

These severity cohorts are retrospective. Forecast-decile calibration and the *fixed V5 forecast-selected* top decile must be reviewed separately; they are not interchangeable. Paired bootstrap draws resample facility rows under the synthetic iid assumption and therefore omit generator misspecification, shared-borrower dependence and bank-specific uncertainty.

## 10. Economic stress and sensitivity

Under the same random seed, a combined synthetic downturn raises realized mean LGD by {stress.query("scenario == 'combined' and model == 'A V5 H'").iloc[0].actual_shift*100:.2f} pp. The H-trained V5 forecast responds by 0.00 pp because its available inputs omit the added downturn/security-quality indicators; the enhanced GB responds by {stress.query("scenario == 'combined' and model == 'GB enhanced R2'").iloc[0].forecast_shift*100:.2f} pp. Remaining gap includes shocks that are genuinely unobservable when scoring. Separate collateral, guarantee, recovery, timing and cost stresses are all recorded in `results/stress_responses.csv`. Stress responses reveal risk sensitivity, not a claim that the real portfolio will undergo these shifts.

## 11. Model risk and decision

The R2 challengers improve several synthetic metrics but do not remove severe-outcome error. R2's new observable-at-default proxies are absent in the current portfolio; R2 is a constructed data-generating process with one independent seed rather than multiple real economic vintages. The conditional quantile is useful as a **separate research risk bound**; adding it to ECL as an overlay would require explicit policy and quantitative allowance-impact approval. Accordingly the decision is **retain published V5 as an educational benchmark, do not promote a challenger, and retain the blocked bank-use gate**. The substantive research outcome is **G: further redevelopment required**, with an identified synthetic information limitation. This is a model governance decision rather than a numerical declaration that no better model can exist.

## 12. Production gate, monitoring and limitations

`scripts/assess_bank_readiness.py --purpose bank` still blocks use. Future use requires real facility-level collateral/guarantee documentation, recovered cash-flow vintages, a time-aligned prediction timestamp, independent out-of-time tests and an authorized methodology decision. `MONITORING_SPECIFICATION.md` defines input provenance, drift, resolution lags, cohort calibration, tail EAD and independent escalation without invented numeric approval thresholds. No external accounting-compliance or institutional performance claim is made. The synthetic generator encodes chosen assumptions; results can overstate how much quality inputs will help on unknown real populations. One holdout plus bootstrap uncertainty cannot solve that transport problem.

## 13. Reproducibility and audit trail

Use `REPRODUCIBILITY.md`, `LGD_EXPERIMENT_REGISTER.md`, `LGD_METHODOLOGY_CHANGELOG.md`, `LGD_FINDINGS_REGISTER.md`, the frozen lock, versioned data and manifest hashes. All displayed percentages are percentages of loss or percentage-point errors, not euros. Historic source results remain tied to commit `0dfe4c8`; this research branch does not merge model changes into V5.

## Appendix: diagnostic figures

All 18 charts are generated directly from selection data by `figures.py`. They are research diagnostics and never replace the quantitative scorecards. Figures 1–3 show scatter/residuals, 4–9 calibration, band and EAD distributions, 10–12 feature support, 13–16 challenger/cancellation/ablation/oracle evidence, and 17–18 stress and data/method attribution.

"""
for i in range(1,19):
    p=next((HERE/'figures').glob(f'{i:02d}_*.png'))
    intro+=f"\n### Figure {i}: {p.stem.replace('_',' ')}\n\n![{p.stem}](figures/{p.name})\n"
(HERE/'FROM_AGGREGATE_CALIBRATION_TO_TAIL_RISK.md').write_text(intro)
print('Research paper created',len(intro),'characters')
