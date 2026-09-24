-- Run as migration owner after schema creation. Role is provisioned separately.
REVOKE ALL ON ALL TABLES IN SCHEMA public FROM PUBLIC;
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
GRANT USAGE ON SCHEMA public TO platform_app;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO platform_app;
GRANT INSERT ON datasets, borrowers, facilities, models, configurations, runs,
 decisions, findings, finding_events, overrides, approvals, validations, audit_events TO platform_app;
GRANT UPDATE ON runs, audit_head TO platform_app;
-- No DELETE, DDL, credential creation/revocation or evidence UPDATE for API role.
