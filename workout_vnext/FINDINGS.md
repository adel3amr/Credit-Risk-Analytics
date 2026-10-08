# WN-1 findings and disposition

All findings retained; no model promoted. No change to predeclared acceptance criteria.

| ID | Severity | Finding | Evidence | Disposition |
|---|---|---|---|---|
| WN-001 | High | Overall and material segment calibration fail; MAE noninferiority fails | segments.csv, paired.csv | BLOCKED; no post-final tuning |
| WN-002 | High | Resolved-only target selection; 1,020 unresolved episodes | ledger_audit.json, episodes.csv.gz | OPEN; no invented ultimate outcomes |
| WN-003 | High | Last collateral value and nominal guarantee may persist after realization/payout | generate.snapshot; recovery ledger | OPEN; these features describe last known/nominal support, not residual available security. No post-final retrofit |
| WN-004 | High | 4,466 final stress reversal occurrences across scenarios | stress.csv | BLOCKED; not unique facilities; no sorting or monotonic adjustment |
| WN-005 | High | 13 numerical feature-range violations and untested joint support | support.csv | BLOCKED; count is feature-observation occurrences |
| WN-006 | High | Borrower credit snapshots largely remain at default during impaired workout | generate.py | OPEN; new synthetic proxy history does not equal live institutional capture |
| WN-007 | High | Institutional feature capture, empirical recovery calibration and accounting approval absent | feature contract, evidence register | BLOCKED for institutional use |
| WN-008 | Medium | Simplified paid cure, one facility/episode per borrower, fixed-rate discounting, conditional-default cohort | PROTOCOL.md | Reference scope only |
| WN-009 | High | Current PostgreSQL/container/browser/hosted CI qualification not demonstrated | closeout release evidence | Release gate separately outstanding |

Severe realized-loss bias is outcome-conditioned and does not by itself establish conditional-mean miscalibration. It remains an important diagnostic. Here it coexists with prediction-time calibration failures, support violations and implausible scenario responses; the blocking conclusion does not rely on that diagnostic alone.

A new study could calculate consumed/remaining security, capture refreshed workout credit information and estimate censor-adjusted recoveries. Those changes require a new protocol/version and untouched population. They are not implemented in this bounded closeout. The component model's plausible decomposition is not evidence of superior accuracy. Public schema alignment is not empirical validation.
