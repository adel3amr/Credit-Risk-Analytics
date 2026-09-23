# V4 Model Limitations and Mitigations

This document records known limitations of the synthetic SME credit-risk engine. A limitation is not treated as a defect when it follows from the educational/synthetic scope; where practical, the repository exposes diagnostics or governance controls rather than hiding it.

## Data and validation
- **Synthetic data:** borrower, behaviour, default and workout histories are generated rather than observed. Results demonstrate architecture and methodology only. **Mitigation:** deterministic generators, explicit assumptions, separate PD/LGD holdouts, audit outputs, and no claims of production/regulatory validation.
- **Random LGD holdout rather than temporal validation:** the resolved-workout history has no genuine economic vintage structure. **Mitigation:** the 25% holdout is kept separate for out-of-sample diagnostics. A production implementation should use out-of-time/vintage validation and backtesting.
- **Limited PD defaults:** the 3,000-borrower holdout has roughly 102 defaults, so decile default rates and small AUC differences are noisy. **Mitigation:** report calibration, bootstrap uncertainty in the incremental-information experiment, and avoid holdout-driven tuning.

## PD and underwriting information
- **Qualitative information does not improve frozen-holdout AUC:** the independent qualitative layer is economically plausible but did not add convincing OOS discrimination. **Mitigation:** retain the negative result and keep qualitative information available for underwriting/governance rather than tuning the DGP until it improves.
- **Trajectory variables add little incremental discrimination:** trajectory remains more useful as monitoring/EWS information than as forced core-PD complexity. **Mitigation:** maintain architectural separation between PD and EWS.

## LGD and recovery
- **Severe-loss tail underprediction:** governed Gradient Boosting has near-zero portfolio bias but underpredicts the highest-loss tail (top-10% EAD-weighted bias about -4.41 pp; top-5% about -6.48 pp). **Mitigation:** expose segment/tail diagnostics and challengers. Do not recalibrate or promote a challenger after inspecting the same frozen holdout; a future development sample should be used for any redesign.
- **Workout uncertainty remains material:** holdout RMSE is about 16.58 pp despite good aggregate calibration. This reflects heterogeneous recovery outcomes and cannot responsibly be eliminated by fitting the validation sample. **Mitigation:** report MAE, RMSE, bias, EAD-weighted metrics, calibration deciles and segment diagnostics together.
- **Facility collateral allocation is simplified:** live facilities inherit borrower-level collateral type/coverage with deterministic lien logic; this is not a legal collateral-allocation engine. **Mitigation:** label the assumption and keep facility/product/seniority explicit. Production use would require collateral IDs, liens, priority, eligibility, legal enforceability and allocation rules.
- **Guarantee coverage is synthetic:** current-portfolio guarantee assumptions are recovery-support assumptions and are distinct from trade-finance CCFs. **Mitigation:** keep the fields and concepts separate in code and documentation.
- **Cash collateral retains residual LGD:** even fully recognized cash can have small synthetic recovery friction/cost. **Mitigation:** cash has separate short timing/high recovery assumptions. A production implementation could distinguish cash legally controlled/pledged to the bank from generic cash collateral.

## IFRS 9 / ECL
- **SICR is simplified:** there is no true origination/reference PD or lifetime relative-change assessment. **Mitigation:** Stage 2 uses transparent DPD/conduct/history and fixed EWS-persistence proxies and is explicitly labelled IFRS 9-style, not full IFRS 9 compliance.
- **Lifetime PD is a constant-hazard approximation:** facility remaining maturity is respected, but a full marginal PD term structure is not estimated. **Mitigation:** facility-level maturity is preferable to one borrower term; production use would require term structures by scenario.
- **Macro satellite model is synthetic:** scenario shocks and PD sensitivities are fixed assumptions, not econometrically estimated elasticities or official forecasts. **Mitigation:** scenarios, weights and outputs are explicit and auditable.
- **EAD/CCF assumptions are simplified:** term loans use current outstanding, OVD uses approved limit, and trade products use fixed synthetic CCFs. **Mitigation:** assumptions are transparent; production use would estimate/use governed CCF/EAD rules by product and horizon.
- **Stage 3 uses modelled workout LGD:** direct discounted collateral-workout shortfall is retained only as a diagnostic. **Mitigation:** governed and challenger calculations are separately identifiable.

## Governance and implementation
- **Internal rating thresholds are synthetic policy:** PD bands, EWS thresholds and the 9-month persistence rule are not regulatory prescriptions or empirically optimized cutoffs. **Mitigation:** thresholds are fixed ex ante and documented.
- **Human overrides are workflow demonstrations:** the Streamlit approval/audit mechanism is not an enterprise IAM, database or immutable audit system. **Mitigation:** role separation and audit semantics are demonstrated; production deployment would require authenticated users, persistent storage, access control and change management.
- **No production MLOps:** there is no model registry, scheduled monitoring, drift service, feature store or deployment approval platform. **Mitigation:** CI regenerates deterministic data, runs tests/pipelines and retains validation artifacts; production controls are outside project scope.

## Governance conclusion
The project is intentionally a production-style **architecture demonstration**, not a production-ready model. Known statistical limitations are surfaced rather than tuned away. Future methodology changes should be developed on new development data and validated on a fresh untouched sample.
