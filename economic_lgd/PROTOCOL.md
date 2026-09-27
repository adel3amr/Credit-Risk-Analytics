# S2 observable-economic recovery remediation — frozen protocol

Starting release: 281f114. Date: 2026-09-27. Classification: DATA / METHODOLOGY /
MODEL IMPLEMENTATION / VALIDATION. S1 and V5 remain frozen. This is a successor
synthetic recovery experiment, not retroactive repair of S1 or institutional data.

Reuse S1 borrower/facility characteristics and links. Generate new, independently
seeded economic histories and conditional-on-default recovery observations for
12,000 development, 3,000 selection, 3,000 final facilities and all current
facilities. These are hypothetical workouts conditional on default, not observed
default frequencies. Borrowers are disjoint by cohort; macro conditions are shared
within sector/period, not independently drawn for each facility. Development dates
2000–2002, selection 2009–2011, final 2018–2020, current 2026. Each economic vintage
is published before scoring; 60-month development and selection recoveries mature
before the following phase. Original S1 observed dates are replaced only in S2
fixtures and are not claimed to be actual historical information.

Small observable set: output growth (%), unemployment (%), annual collateral-price
change (%), market liquidity (0–1). Latent persistent sector regime influences
these noisy observables only, never scoring or an extra hidden loss shift. Rates
retain existing facility effective interest rates for discounting. Quality remains
unobserved simulation heterogeneity and is excluded from the candidate model.
Recovery mechanisms preserve collateral type, coverage, guarantees, seniority,
financials, cure, costs and discounted cashflows. Coefficients are transparent
synthetic assumptions; no empirical banking estimates are claimed.

One candidate: existing 220-tree depth-3 GradientBoosting specification with four
additional observable columns and existing effective interest rate. Train only on
one realized recovery per development facility. No algorithm search, no oracle
labels in training, no tuning on selection/final/current. Selection is diagnostic;
no calibration or MoC fitted in this first implementation. A residual problem is
reported rather than adding an unsupported uplift. Final opened once after the
data and model hashes are frozen. Conditional mean evaluated with 512 independent
draws, separate from the development outcome seed; not a production feature.

Compare incumbent and corrected candidate on identical S2 populations; S1 -12.65 pp
and oracle +0.55 pp are historical and cannot be used as S2 before/after results.
Report realized MAE/RMSE/bias, conditional bias by normal/downturn, band, collateral,
coverage, guarantee, industry, product, lien, EAD and period, with macro-cluster
uncertainty. Retrospective loss tails remain diagnostic. Preserve irreducible risk.

Use existing scenario names, weights and PD shifts. Explicit S2 mapping from those
scenario GDP/unemployment changes to asset prices/liquidity is a new synthetic
scenario assumption, stored and versioned. Per-scenario lifetime transformation
precedes weighting. Report separately the effect of that ordering correction and
the LGD change. PD estimates, EAD, stage, EWS and watchlist remain untouched.

Promotion is NOT automatic on a favorable aggregate metric. Require conditional
calibration across states/segments, sensible scenario responses, as-of/support
controls, independent arithmetic and passing tests. No arbitrary numerical
threshold is declared to obtain a pass; unqualified scenario reversals or material
segment error block promotion. Institutional gates remain blocked regardless of
synthetic performance. If not promoted, integrate as isolated shadow execution.

External basis reviewed before coding: ECB Working Paper 2954 (2024),
https://www.ecb.europa.eu/pub/pdf/scpwps/ecb.wp2954~1d1f8942c9.en.pdf — timing of
recoveries matters for macro sensitivity (European confidential defaulted-loan
cashflows; no coefficients imported). IFRS Foundation multiple-scenarios material
(2016), https://www.ifrs.org/news-and-events/news/2016/07/25-webcast-on-ifrs-9/ —
scenario consistency/nonlinearity, not a prescription for this synthetic model.
