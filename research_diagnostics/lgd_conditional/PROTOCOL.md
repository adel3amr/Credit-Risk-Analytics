# LGD conditional expectation diagnostic — protocol

Classification: VALIDATION / RESEARCH. No new production model, calibration,
threshold, generator or holdout modification. Historical V5 and R2 remain frozen.

Question: how much of the adverse outcome-conditioned tail error remains when
predicting the R2 simulator's conditional expected loss rather than fitting a tree?
The earlier future-information oracle conditions on realized future shocks; this
experiment instead integrates over independent shocks with inputs held fixed.

Use all 3,000 already-examined R2 final cases. This is retrospective diagnosis,
NOT a new protected holdout or evidence for model selection. Use ONLY R2's 13
prediction-time feature columns for simulation. Resample future cure, recovery,
resolution, cost and discount draws using the unchanged ordinary R2 equations.
Use 4,096 draws per case and seed 2026092401; report Monte Carlo standard errors.
Do not tune draw count, seed, parameters or model against observed results.
Report all, >60%, >75%, >90% realized tails, low loss and fixed prediction bands.
Compare frozen V5 and enhanced two-stage forecasts to the conditional mean.
Decompose each mean error exactly into model-minus-conditional-mean plus
conditional-mean-minus-realization. Keep negative findings and all denominators.

Independent check: reproduce original R2 outcomes exactly from its captured
pre-outcome RNG state using a separate transcription of the outcome equations.
Assert no output/future column is consumed and outcomes stay bounded. The extra
R2 quality/downturn features remain unavailable live; this diagnostic is not a
production candidate. Generator correctness in this experiment is not evidence
that its assumptions describe an institution.

External methodological context: Gneiting, *Making and Evaluating Point Forecasts*,
https://arxiv.org/abs/0912.0902 (accessed 2026-09-24): scoring functions must match
the target functional. This supports distinguishing mean from quantile forecasts;
it supplies no recovery parameter and does not excuse prediction-time bias.
