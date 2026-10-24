# Reproduce the current publication build

For an end-user setup guide, including **both no-Ollama and local-Ollama paths plus Ollama installation**, see [RUN_INSTRUCTIONS.md](RUN_INSTRUCTIONS.md). This file focuses on reproducibility and qualification evidence.

This file describes the **current consolidated publication state**. Historical research modules retain their own protocols and locks; they are linked below rather than being silently rewritten.

## Current lines

- Public/default branch: `main`
- Consolidated integration lineage: `release/final-institutional-platform`
- Last independently confirmed fully green integrated build: `79a031192f4477351528e7384004d1d4e970a488` (24 October 2026; main and release branches)
- Runtime: Python **3.12**
- Current clean-run automated suite: **256 passed, 1 upstream warning**
- V5 release checks: **30/30**
- Reference shadow: **5,172 facilities**, **0 stage mismatches**, audit **VERIFIED**

## Clean-clone public demo (recommended)

See [RUN_INSTRUCTIONS.md](RUN_INSTRUCTIONS.md) for the quick Windows/macOS/Linux launcher and optional Ollama. On Windows, after cloning, run `py -3.12 run_demo.py`; on macOS/Linux run `python3.12 run_demo.py`. The launcher automates the same dependency, frozen-artifact and database initialization steps used below.

### Manual installation (advanced)

The following commands are the explicit underlying setup after creating and activating a Python 3.12 virtual environment:

```bash
python -m pip install -r requirements-platform-lock.txt
python scripts/run_v5.py
python -m credit_platform.cli build-models
python -m alembic upgrade head
python -m credit_platform.cli seed-governance
python -m streamlit run app.py --server.port 8510
```

The Streamlit workbench automatically creates a local demo actor and reference run when needed by Risk Copilot. No paid LLM is needed. For local conversational Ollama, see the run guide.

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

The standard Linux `Platform reference validation` workflow starts from a fresh Ubuntu runner and PostgreSQL 16 service, then:

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

At the October 24, 2026 qualification this produced **256 passed**, V5 **30/30**, PostgreSQL shadow reconciliation with **0 stage mismatches**, WN-1 persistence **VERIFIED**, Streamlit smoke **PASS**, and Docker build **PASS**.

The separate `Validate V5 Risk Engine` workflow also passed on the same functional baseline.

## Generated vs versioned evidence

`data/raw/*.csv`, `data/processed/*.csv`, `outputs/*`, local databases and generated platform model binaries are intentionally ignored. They are rebuilt locally. Frozen research cohorts/results that form part of the research evidence are versioned inside their dedicated modules.

Frozen text identities normalize LF/CRLF line endings for declared text evidence on Windows while retaining exact hashes for binary artifacts. This is not permission to alter frozen values. The public-release Windows smoke workflow tests installation and local reference setup independently.

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
