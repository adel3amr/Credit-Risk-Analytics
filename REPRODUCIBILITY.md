# Reproduce the current publication build

This file describes the **current consolidated publication state**. Historical research modules retain their own protocols and locks; they are linked below rather than being silently rewritten.

## Current lines

- Public/default branch: `main`
- Consolidated integration lineage: `release/final-institutional-platform`
- Functional qualification baseline before this documentation refresh: `8deaeff3664a42812aff8ec01b0170628705cb49`
- Runtime: Python **3.12**
- Current clean-run automated suite: **240 passed, 1 upstream warning**
- V5 release checks: **30/30**
- Reference shadow: **5,172 facilities**, **0 stage mismatches**, audit **VERIFIED**

## Clean clone — Windows PowerShell

```powershell
git clone --depth 1 https://github.com/adel3amr/Credit-Risk-Analytics.git
cd Credit-Risk-Analytics

py -3.12 -m venv .venv
Set-ExecutionPolicy -Scope Process Bypass
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
pip install -r requirements-platform-lock.txt

python scripts/run_v5.py
python -m credit_platform.cli build-models
python -m alembic upgrade head
python -m credit_platform.cli seed-governance

python -m streamlit run app.py
```

The Streamlit workbench creates a local demo principal and a governed reference run when Risk Copilot evidence is first required. No paid LLM is needed.

### Local Ollama

```powershell
ollama pull llama3.2
$env:COPILOT_PROVIDER="ollama"
$env:OLLAMA_MODEL="llama3.2"
$env:OLLAMA_NUM_CTX="16384"
$env:OLLAMA_NUM_PREDICT="640"
python -m streamlit run app.py
```

## Verification commands

```powershell
python -m pytest -q
python scripts/validate_v5.py
python scripts/platform_shadow.py
python scripts/platform_verify_frozen.py
python -m credit_platform.cli audit-verify
```

For the PostgreSQL path, use `docker compose up --build -d` after creating an ignored `.env` from `.env.example`.

## What the clean CI actually proves

The `Platform reference validation` workflow starts from a fresh Ubuntu runner and PostgreSQL 16 service, then:

1. installs `requirements-platform-lock.txt`;
2. regenerates the frozen V5 reference data with `scripts/run_v5.py`;
3. rebuilds trusted reference artifacts;
4. verifies frozen source/data identities;
5. verifies the linked synthetic-bank evidence and frozen S2/WN-1 research locks;
6. runs the full pytest suite;
7. migrates a fresh PostgreSQL database;
8. executes the full 5,172-facility shadow calculation and audit verification;
9. persists the WN-1 relational workout domain to PostgreSQL;
10. starts the Streamlit workbench headlessly and requires a healthy response;
11. compiles the platform/research modules; and
12. builds the Docker image.

At the October 9, 2026 qualification baseline this produced **240 passed**, V5 **30/30**, PostgreSQL shadow reconciliation with **0 stage mismatches**, WN-1 persistence **VERIFIED**, Streamlit smoke **PASS**, and Docker build **PASS**.

The separate `Validate V5 Risk Engine` workflow also passed on the same functional baseline.

## Generated vs versioned evidence

`data/raw/*.csv`, `data/processed/*.csv`, `outputs/*`, local databases and generated platform model binaries are intentionally ignored. They are rebuilt locally. Frozen research cohorts/results that form part of the research evidence are versioned inside their dedicated modules.

Frozen text identities normalize LF/CRLF line endings before hashing so the same controlled CSV content verifies across Linux and Windows checkouts.

## Research reproduction map

| Stream | Current evidence / command |
|---|---|
| Frozen V5 engine | `python scripts/run_v5.py` + `python scripts/validate_v5.py` |
| Independent/platform shadow | `python scripts/platform_shadow.py` |
| Linked synthetic bank | `python -m synthetic_bank.validate` |
| Economic S2 | `python -m economic_lgd.review` |
| S2-R1 | `python -c "from s2_remediation.evaluate import verify, verify_lock; verify(); verify_lock()"` |
| Post-R1 hardening | `python -m lgd_hardening.decision` |
| Marginal Interest | see `marginal_interest/README.md` and frozen `results/` |
| WN-1 workout engine | see `workout_vnext/README.md`, `PROTOCOL.md` and frozen `results/` |
| Whole-repository validation | see `validation_review/` and `FINAL_INDEPENDENT_VALIDATION_REPORT.md` |

Do not regenerate or retune frozen final/holdout evidence simply to improve a result. New research should be versioned as a separate experiment with a new protocol and evidence boundary.
