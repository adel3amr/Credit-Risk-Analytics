# Review-branch change log

Reference V5 commit: `0dfe4c883a8314704394c49fa096dfb45525096c`. These changes are confined to `validation_review/` and README documentation; approved methodology and model code are unmodified.

| Classification | Change | Reason |
|---|---|---|
| VALIDATION ENHANCEMENT | Independent read-only PD, LGD, EWS, SICR, scenario and facility ECL recalculator, with machine-readable evidence | Separate source-reported outputs from distinct arithmetic. |
| VALIDATION ENHANCEMENT | Clean historical snapshot reproducer and full commit/branch/PR inventory | Distinguish merged chronology from experiments and unmerged proposals. |
| DOCUMENTATION | Forensic report, executive conclusion, worked facility examples, figures, evidence mapping, dictionary, inventory and limitation register | Make every material claim auditable and keep adverse results visible. |
| METHODOLOGICAL CHANGE | **None implemented** | PD, LGD, SICR, EAD, ECL, EWS and rating policy remain frozen. |

The report does not claim that new documentation cures model risk. A further approved implementation branch could adopt the independent oracle as CI and address documentation wording without changing any model rule.
