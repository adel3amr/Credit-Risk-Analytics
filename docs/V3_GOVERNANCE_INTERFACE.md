# V3 Governance & Credit Decisioning Interface

V3 places a governed decisioning layer above the V2 analytical engine.

## Design principle

**Model output != policy decision != human override.**

The original model result is never overwritten. A manual intervention creates a separate, attributable decision record.

## Roles

- **Credit Analyst** — borrower view, assessment execution, override proposal.
- **Risk Manager** — analyst capabilities plus override approval and controlled policy/macro changes.
- **Model Validation** — read-only model diagnostics and governance evidence.
- **Auditor** — read-only borrower and audit history.
- **Admin** — user/role administration and audit access; admin status alone does not grant model or credit-policy approval authority.

This is application-level RBAC for the portfolio project, not enterprise authentication/IAM.

## Governed modules

### Borrower 360
Financials, current behaviour, 36-month trajectory, facilities, collateral, EAD/LGD, governed PD, score/risk band, EWS, stage, ECL and decision history.

### Override workflow
PD/rating, SICR/stage, watchlist and recovery/collateral interventions are recorded separately from model outputs. Every proposal requires a reason code and rationale. Approval follows maker-checker: the proposer cannot approve their own override.

### Macroeconomic scenario management
Authorized Risk Managers can prepare scenario amendments to GDP, unemployment, policy rate, inflation and scenario weights. Weights must remain non-negative and sum to 100%. A proposed scenario set should be simulated before approval and should retain version/effective-date metadata.

### Policy and model parameters
Validated model coefficients are read-only in the operational interface. Credit-policy parameters are separately configurable only through controlled change workflow. This prevents an operational user from silently re-engineering the PD model.

### Audit trail
Events should preserve actor, role, timestamp, action, old value, proposed/new value, reason, approver, model version, policy version and scenario version.

## V3 implementation boundary

The first implementation establishes RBAC permissions, maker-checker override primitives, macro validation and append-only audit-event support. A production system would replace local identity/audit storage with enterprise IAM, a transactional database, cryptographic/retention controls and formal model/policy deployment workflows.
