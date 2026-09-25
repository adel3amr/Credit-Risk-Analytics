# Targeted follow-up after primary decomposition

Primary results establish real current conditional underprediction, separate from
realized-tail selection. Governed current model bias -12.65 pp; full conditional
mean >75% region bias -10.92 pp. 7,163/8,695 current facilities have known synthetic
downturn context, compared with 88/1,017 final workouts. Governed model does not
consume context; its downturn group bias is about -15.59 pp, versus +1.05 pp in
ordinary context. This is population transfer with an omitted legitimate driver,
not a newly discovered arithmetic defect or the old guarantee discontinuity.

S1 development has only one regime per industry; industry and context can therefore
act as competing proxies. Many current industry/regime combinations are unseen.
Existing enhanced model reduces bias, but does not fully remove conditional error.
S1 interest_rate is known before outcome and directly discounts recovery; neither
incumbent nor enhanced model consumes it. Existing future oracle cannot be promoted.

One narrowly targeted research candidate is authorized by this evidence: retain
fixed GB hyperparameters and all existing recovery inputs, remove industry (which
has no direct recovery-equation effect conditional on context and financial inputs)
and add known interest_rate. This is a MODEL SPECIFICATION / RESEARCH change, not a
bug fix. It addresses support/proxy dependence and known discount information.
No hyperparameter search, severity weighting, uplift or holdout calibration.
Train development only; evaluate existing selection/final/current retrospectively.
This is NOT a promotion test: final has already been examined, and no new untouched
cohort is being generated under this mandate. Any improvement remains a research
result requiring independent fresh validation and actual operational feature capture.

Also run a paired current counterfactual fixing only known context to zero, with
identical Monte Carlo seed/draws, to quantify DGP sensitivity. This modifies a
DIAGNOSTIC input copy only, not source data. Hold quality and other inputs fixed;
this is a conditional scenario contrast, not a causal real-economy estimate.
