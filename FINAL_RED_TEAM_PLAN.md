# Final independent red-team review protocol

Starting commit: `33d3ad4670bd7c5cfad31ac5d6b54f8f42224180`.
Starting branch: `feature/final-platform-closeout`; observed clean working tree.
Review branch: `review/final-red-team-release`.

## Protocol registered before remediation

1. Reproduce baseline tests; inventory current source, policy, contracts, historical decisions and evidence.
2. Trace canonical inputs through reference decisions, independently check arithmetic and precedence, and attack malformed inputs and integrity boundaries.
3. Review persistence, migrations, transactions, overrides, authentication, API, artifacts and Copilot. Reproduce defects before fixing; add focused regression tests.
4. Reconcile LGD chronology and existing results without fitting candidates or opening a new final population. Distinguish conditional calibration from realized-tail selection and missing prediction-time information.
5. Attempt PostgreSQL, container, browser and CI checks where capabilities permit. Record exact failures and distinguish environment limitations from defects.
6. Run final full verification, record changed files and evidence hashes, consolidate findings and release disposition, commit and provide a bundle if authenticated push remains unavailable.

No dataset regeneration, methodological changes, promotion, threshold weakening, historical rewrite or modification to other worktrees is authorized by this protocol. Reference readiness and institutional approval are separate decisions. Current claims (168 tests; R1 not promoted; bank gate blocked) require verification. Review findings will distinguish code-fixable defects, methodology requirements, unavailable data and external qualification.
