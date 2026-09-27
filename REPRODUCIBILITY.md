# Reproduce the platform

Latest S2-R1 verification: `python -c "from s2_remediation.evaluate import verify, verify_lock; verify(); verify_lock()"`,
then `python -m pytest -q` (**151 passed locally**) and
`python -m s2_remediation.review`. Full commands, isolated regeneration and
rebuild guidance: [s2_remediation/README.md](s2_remediation/README.md).
The fixed candidate was independently refitted on development data and reproduced
all 6,000 calibration predictions exactly (`results/reproducibility.json`).
No candidate was promoted. The API/Copilot now retrieve this latest decision.

The following S2 paragraph records the preceding 136-test release:

S2 successor module is additive and NOT PROMOTED. Frozen files are included; do not
regenerate them. Run `python -m economic_lgd.review` to recalculate exported
metrics/support, and `python -m pytest -q tests/platform/test_economic_lgd.py` for
targeted verification. Full suite now contains 136 tests. The UI's Economic LGD
validation view and Model risk Copilot question "Explain S2 observable economic
LGD" retrieve the frozen decision. See `economic_lgd/DECISION.md` for full rebuild
instructions in a separate directory. Active V5 scoring instructions below remain.

Python 3.12. Start from branch `platform/production-foundation`. Historical branches remain unchanged.

## Local reference (SQLite)

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements-platform-lock.txt
python scripts/run_v5.py
python -m credit_platform.cli build-models
python -m alembic upgrade head
python -m credit_platform.cli seed-governance
python -m credit_platform.cli issue-token --name analyst --role analyst
python -m credit_platform.cli issue-token --name validator --role validator
python -m credit_platform.cli issue-token --name auditor --role audit
python -m credit_platform.cli export-reference --output /tmp/reference.json
python -m credit_platform.cli run-reference --operator analyst
python scripts/platform_shadow.py
python scripts/platform_verify_frozen.py
python -m pytest -q
python -m credit_platform.cli audit-verify
python -m uvicorn credit_platform.api:app --host 127.0.0.1 --port 8000 --no-access-log --log-config deployment/logging.json
```

Copy the one-time displayed credential privately into the UI at `http://127.0.0.1:8000`. It is never stored cleartext by the application. Do not commit or include credentials in shared reports. On Windows use the corresponding virtualenv activation and temporary path. UI dataset upload accepts canonical JSON produced above. Use a validator credential for reconciliation. Owner/administrator is not automatically authorized to run or approve credit actions.

`build-models` verifies frozen raw hashes and persists trusted reference models. It does not tune/select models. `platform_shadow.py` compares all 5,172 facility decisions with original V5; independent EAD rounding discrepancy up to one cent is reported explicitly. `platform_contracts.py` refreshes measured feature support and contract docs from frozen outputs. Existing research reproduction remains in `lgd_research/REPRODUCIBILITY.md`; never regenerate frozen research data to improve scores.

## PostgreSQL reference composition

Generate separate random hex passwords and set POSTGRES_PASSWORD and APP_DB_PASSWORD in a local ignored `.env`. Do not use example placeholders. Then:

```bash
docker compose up --build -d
```

`prepare` reproduces frozen reference artifacts; `migrate` creates schema and grants; API starts after both complete. PostgreSQL has no published host port. API is loopback only. Provision credentials through the migration-owner environment:

```bash
docker compose run --rm migrate python -m credit_platform.cli issue-token --name analyst --role analyst
docker compose run --rm migrate python -m credit_platform.cli seed-governance
```

Export canonical reference JSON from the prepared environment or use `docker compose run --rm api python -m credit_platform.cli export-reference --output /tmp/reference.json` with an explicit bind mount for export; a removed container's `/tmp` is not a persistent deliverable. The recommended local export command above is simpler. The API database role cannot create credentials, delete evidence or run DDL.

PostgreSQL/container commands are provided for reproducibility but were not executable in this workspace. Hosted CI includes PostgreSQL 16 migrations and shadow calculation. Treat its result as unverified until run; do not equate SQLite success with PostgreSQL success.

## Gates

`python scripts/assess_bank_readiness.py --purpose bank` and `python -m lgd_research.research_gate` return 2. API bank-purpose run status is BLOCKED. No command-line or API approval flag waives this.
