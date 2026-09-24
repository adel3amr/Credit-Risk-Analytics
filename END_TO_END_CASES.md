# End-to-end worked cases

`platform_evidence/worked_cases.json` contains full raw source, features, PD/scenario PD, EWS, stage triggers, watchlist/rating, LGD features, model hashes, EAD, effective PD, ECL, reporting date and run/dataset references for healthy Stage1, watchlist Stage1, Stage2, default, secured, unsecured, guaranteed, high LGD, high EAD and high ECL facilities.

Reproduce with `python scripts/platform_shadow.py`. Use each trace's effective_pd × lgd × ead to recalculate ECL. Source money uses one synthetic currency unit. These are actual generated reference cases, not invented bank loans.

`tests/platform/test_platform.py` separately exercises Stage2→Stage1 cure under the existing current-condition policy, 8/9-month EWS boundary, Stage3 precedence, zero/subunit/large exposures, full cash/guarantee, invalid data, borrower without facilities, duplicate/orphan records, failed artifacts/database, authorization and two-person overrides. Transition fixtures test software policy behavior, not calibrated macro/credit dynamics.
