-- Informational PostgreSQL DDL. Alembic migrations additionally install evidence guards.


CREATE TABLE audit_events (
	sequence SERIAL NOT NULL,
	actor VARCHAR NOT NULL,
	action VARCHAR NOT NULL,
	entity VARCHAR NOT NULL,
	recorded_at VARCHAR NOT NULL,
	details JSON NOT NULL,
	previous_hash VARCHAR NOT NULL,
	hash VARCHAR NOT NULL,
	PRIMARY KEY (sequence),
	UNIQUE (hash)
)

;


CREATE TABLE audit_head (
	id SERIAL NOT NULL,
	sequence INTEGER NOT NULL,
	hash VARCHAR NOT NULL,
	PRIMARY KEY (id)
)

;


CREATE TABLE configurations (
	id VARCHAR NOT NULL,
	kind VARCHAR NOT NULL,
	hash VARCHAR NOT NULL,
	payload JSON NOT NULL,
	recorded_at VARCHAR NOT NULL,
	PRIMARY KEY (id)
)

;


CREATE TABLE findings (
	id VARCHAR NOT NULL,
	component VARCHAR NOT NULL,
	severity VARCHAR NOT NULL,
	description VARCHAR NOT NULL,
	evidence JSON NOT NULL,
	owner VARCHAR NOT NULL,
	recorded_at VARCHAR NOT NULL,
	PRIMARY KEY (id)
)

;


CREATE TABLE models (
	id VARCHAR NOT NULL,
	family VARCHAR NOT NULL,
	version VARCHAR NOT NULL,
	status VARCHAR NOT NULL,
	manifest JSON NOT NULL,
	recorded_at VARCHAR NOT NULL,
	PRIMARY KEY (id),
	CHECK (status in ('REFERENCE','BLOCKED','RESEARCH','RETIRED'))
)

;


CREATE TABLE principals (
	id VARCHAR NOT NULL,
	name VARCHAR NOT NULL,
	role VARCHAR NOT NULL,
	token_hash VARCHAR NOT NULL,
	active INTEGER NOT NULL,
	expires_at VARCHAR NOT NULL,
	created_at VARCHAR NOT NULL,
	PRIMARY KEY (id),
	CHECK (role in ('analyst','manager','validator','audit','admin')),
	CHECK (active in (0,1)),
	UNIQUE (name),
	UNIQUE (token_hash)
)

;


CREATE TABLE datasets (
	id VARCHAR NOT NULL,
	name VARCHAR NOT NULL,
	effective_date VARCHAR NOT NULL,
	recorded_at VARCHAR NOT NULL,
	source VARCHAR NOT NULL,
	hash VARCHAR NOT NULL,
	schema_version VARCHAR NOT NULL,
	status VARCHAR NOT NULL,
	dq JSON NOT NULL,
	actor VARCHAR NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (hash),
	FOREIGN KEY(actor) REFERENCES principals (id)
)

;


CREATE TABLE finding_events (
	id VARCHAR NOT NULL,
	finding_id VARCHAR NOT NULL,
	status VARCHAR NOT NULL,
	note VARCHAR NOT NULL,
	actor VARCHAR NOT NULL,
	recorded_at VARCHAR NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(finding_id) REFERENCES findings (id),
	FOREIGN KEY(actor) REFERENCES principals (id)
)

;


CREATE TABLE borrowers (
	dataset_id VARCHAR NOT NULL,
	id VARCHAR NOT NULL,
	industry VARCHAR NOT NULL,
	payload JSON NOT NULL,
	source_hash VARCHAR NOT NULL,
	PRIMARY KEY (dataset_id, id),
	FOREIGN KEY(dataset_id) REFERENCES datasets (id)
)

;


CREATE TABLE runs (
	id VARCHAR NOT NULL,
	request_key VARCHAR NOT NULL,
	request_hash VARCHAR NOT NULL,
	dataset_id VARCHAR NOT NULL,
	actor VARCHAR NOT NULL,
	status VARCHAR NOT NULL,
	purpose VARCHAR NOT NULL,
	started_at VARCHAR NOT NULL,
	ended_at VARCHAR,
	versions JSON NOT NULL,
	summary JSON NOT NULL,
	output_hash VARCHAR,
	PRIMARY KEY (id),
	CHECK (status in ('RUNNING','SUCCEEDED','FAILED','BLOCKED')),
	CHECK (purpose in ('reference','bank')),
	UNIQUE (request_key),
	FOREIGN KEY(dataset_id) REFERENCES datasets (id),
	FOREIGN KEY(actor) REFERENCES principals (id)
)

;


CREATE TABLE copilot_requests (
	id VARCHAR NOT NULL,
	request_id VARCHAR NOT NULL,
	actor VARCHAR NOT NULL,
	role VARCHAR NOT NULL,
	use_case VARCHAR NOT NULL,
	run_id VARCHAR,
	borrower_id VARCHAR,
	question_hash VARCHAR NOT NULL,
	provider VARCHAR NOT NULL,
	provider_version VARCHAR NOT NULL,
	prompt_version VARCHAR NOT NULL,
	status VARCHAR NOT NULL,
	tool_calls JSON NOT NULL,
	sources JSON NOT NULL,
	response_hash VARCHAR NOT NULL,
	recorded_at VARCHAR NOT NULL,
	PRIMARY KEY (id),
	CHECK (use_case in ('borrower','portfolio','model_risk','credit_review')),
	CHECK (status in ('ANSWERED','REFUSED','INSUFFICIENT_EVIDENCE')),
	UNIQUE (request_id),
	FOREIGN KEY(actor) REFERENCES principals (id),
	FOREIGN KEY(run_id) REFERENCES runs (id)
)

;


CREATE TABLE decisions (
	run_id VARCHAR NOT NULL,
	facility_id VARCHAR NOT NULL,
	borrower_id VARCHAR NOT NULL,
	stage VARCHAR NOT NULL,
	pd FLOAT NOT NULL,
	lgd FLOAT NOT NULL,
	ead FLOAT NOT NULL,
	ecl FLOAT NOT NULL,
	trace JSON NOT NULL,
	hash VARCHAR NOT NULL,
	PRIMARY KEY (run_id, facility_id),
	CHECK (stage in ('Stage 1','Stage 2','Stage 3')),
	CHECK (pd >= 0 and pd <= 1 and lgd >= 0 and lgd <= 1 and ead >= 0 and ecl >= 0),
	FOREIGN KEY(run_id) REFERENCES runs (id)
)

;


CREATE TABLE facilities (
	dataset_id VARCHAR NOT NULL,
	id VARCHAR NOT NULL,
	borrower_id VARCHAR NOT NULL,
	product VARCHAR NOT NULL,
	payload JSON NOT NULL,
	source_hash VARCHAR NOT NULL,
	PRIMARY KEY (dataset_id, id),
	FOREIGN KEY(dataset_id, borrower_id) REFERENCES borrowers (dataset_id, id)
)

;


CREATE TABLE validations (
	id VARCHAR NOT NULL,
	run_id VARCHAR NOT NULL,
	kind VARCHAR NOT NULL,
	payload JSON NOT NULL,
	hash VARCHAR NOT NULL,
	actor VARCHAR NOT NULL,
	recorded_at VARCHAR NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(run_id) REFERENCES runs (id),
	FOREIGN KEY(actor) REFERENCES principals (id)
)

;


CREATE TABLE overrides (
	id VARCHAR NOT NULL,
	run_id VARCHAR NOT NULL,
	facility_id VARCHAR NOT NULL,
	proposer VARCHAR NOT NULL,
	original_ecl FLOAT NOT NULL,
	proposed_ecl FLOAT NOT NULL,
	reason VARCHAR NOT NULL,
	recorded_at VARCHAR NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(run_id, facility_id) REFERENCES decisions (run_id, facility_id),
	CHECK (proposed_ecl >= 0),
	UNIQUE (run_id, facility_id),
	FOREIGN KEY(proposer) REFERENCES principals (id)
)

;


CREATE TABLE approvals (
	override_id VARCHAR NOT NULL,
	approver VARCHAR NOT NULL,
	decision VARCHAR NOT NULL,
	recorded_at VARCHAR NOT NULL,
	PRIMARY KEY (override_id),
	CHECK (decision in ('APPROVED','REJECTED')),
	FOREIGN KEY(override_id) REFERENCES overrides (id),
	FOREIGN KEY(approver) REFERENCES principals (id)
)

;

CREATE INDEX ix_datasets_effective ON datasets (effective_date, recorded_at);
CREATE INDEX ix_runs_dataset ON runs (dataset_id);
CREATE INDEX ix_decisions_borrower ON decisions (borrower_id);
CREATE INDEX ix_facilities_borrower ON facilities (dataset_id, borrower_id);
