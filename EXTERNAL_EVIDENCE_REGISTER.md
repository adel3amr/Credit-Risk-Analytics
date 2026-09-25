# External evidence register

Accessed 24 September 2026. Sources guide architecture/controls; no imported empirical coefficient or accounting-policy redesign. Links are references, not redistributed licensed datasets.

| ID | Institution / document / date | Tier and population | Component / supported claim | Limitation and applicability | Reference |
|---|---|---|---|---|---|
| E01 | PostgreSQL, v16 constraints documentation, current manual | Official technical documentation | DB keys, FKs and checks | Database enforcement does not validate economic meaning | https://www.postgresql.org/docs/16/ddl-constraints.html |
| E02 | FastAPI security documentation, current | Official technical documentation | Backend identity dependencies | Framework capability is not security certification; this release uses opaque expiring tokens, not JWT/OIDC | https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/ |
| E03 | OWASP Authorization Cheat Sheet, current | Primary security guidance | Deny-by-default and server-side permissions | Needs deployment-specific threat modelling and penetration testing | https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html |
| E04 | BCBS, Principles for effective risk data aggregation and risk reporting, January 2013 | Tier 1 supervisory; initially systemically important banks | Traceable accurate aggregation and reporting controls | Architectural reference only; no claim of BCBS239 compliance | https://www.bis.org/publ/bcbs239.pdf |
| E05 | IFRS Foundation, IFRS9 issued standard, 2021 edition | Tier 1 accounting | Expected loss interpretation and distinction from prudential requirements | Referenced context; no assertion frozen synthetic ECL meets all accounting requirements | https://www.ifrs.org/content/dam/ifrs/publications/pdf-standards/english/2021/issued/part-a/ifrs-9-financial-instruments.pdf |
| E06 | pgserver project documentation | Primary software project | Optional local test server packaging | Test environment alternative only; startup failed; not a production dependency | https://github.com/orm011/pgserver |

GitHub connected tooling verified PR25 and V5 workflow status. No connected Scite/Exa/Supabase/Datadog/PostHog tool was identified. Public primary-source retrieval was used. No licensed external economic dataset was incorporated; licensing and redistribution gates therefore remain prerequisites for any future feed. The nine-month rule is PROJECT METHODOLOGY, never externally attributed.

E07 — Tilmann Gneiting, *Making and Evaluating Point Forecasts* (2009 preprint;
2011 journal publication), Tier 3 original statistical research, no institution-
specific population. https://arxiv.org/abs/0912.0902, accessed 2026-09-24.
Supports matching scoring to the mean/quantile target in the LGD conditional
expectation diagnostic. Supplies no recovery parameters or production approval.

E08 — EBA/GL/2017/16, *Guidelines on PD estimation, LGD estimation and treatment
of defaulted exposures*, 20 November 2017, Tier 1, prudential IRB population.
Primary reference linked in synthetic_bank/PROTOCOL.md; accessed 24 September 2026.
Context for representativeness and explicit economic recovery/cost data; not IFRS9
policy and no empirical parameter imported. S1 coefficients remain transparent
synthetic assumptions, not regulatory prescriptions.
