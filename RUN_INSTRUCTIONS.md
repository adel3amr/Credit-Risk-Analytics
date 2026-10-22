# Run Instructions

This guide covers the two supported local demo modes:

1. **Core platform without Ollama** — all Credit Risk calculations, dashboards, governance, validation and the deterministic Risk Copilot run locally with no external AI dependency.
2. **Full local GenAI with Ollama** — the same platform plus the conversational full-context Risk Copilot using a local `llama3.2` model.

**No paid API is required for either path.** OpenAI is optional and is not needed for the public demo.

---

## What runs in both modes

Both modes include the same governed Credit Risk platform:

- Portfolio Cockpit
- Borrower Credit File
- Risk Management
- Model Validation
- PD and internal rating
- EWS / Watchlist / SICR
- IFRS 9-style staging
- LGD / EAD / ECL
- macro scenarios
- concentration and portfolio analytics
- model-risk / challenger evidence
- governance, overrides and audit evidence
- Risk Copilot over governed evidence

The only difference is the **narrative provider**:

- without Ollama: deterministic local provider;
- with Ollama: local conversational LLM reasoning over the same governed evidence.

Exact calculations, rankings, concentrations, stages, PD/LGD/EAD/ECL and other risk-engine results remain outside the LLM in both modes.

---

# Common setup — fresh machine

## 1. Requirements

Install:

- **Git**
- **Python 3.12**

Then clone the repository:

```powershell
git clone --depth 1 https://github.com/adel3amr/Credit-Risk-Analytics.git
cd Credit-Risk-Analytics
```

Create and activate a virtual environment.

### Windows PowerShell

```powershell
py -3.12 -m venv .venv
Set-ExecutionPolicy -Scope Process Bypass
.\.venv\Scripts\Activate.ps1
```

### macOS / Linux

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

Install the pinned project dependencies:

```bash
python -m pip install --upgrade pip
pip install -r requirements-platform-lock.txt
```

Build the frozen reference data/models and initialize the local platform database:

```bash
python scripts/run_v5.py
python -m credit_platform.cli build-models
python -m alembic upgrade head
python -m credit_platform.cli seed-governance
```

The generated raw/reference outputs and local database are intentionally rebuilt on the user's machine rather than depending on the author's workstation.

---

# Option A — run without Ollama

This is the simplest path. It needs **no Ollama, no OpenAI key and no paid API**.

## Windows PowerShell

```powershell
$env:COPILOT_PROVIDER="deterministic"
python -m streamlit run app.py --server.port 8510
```

## macOS / Linux

```bash
export COPILOT_PROVIDER=deterministic
python -m streamlit run app.py --server.port 8510
```

Open:

```text
http://localhost:8510
```

The Risk Copilot works in deterministic governed mode. Exact borrower/portfolio analytics, concentration calculations and model-risk facts are available; the response style is controlled rather than conversational.

---

# Option B — run with local Ollama

Use this mode for the **full conversational local GenAI Copilot**.

Ollama is external software and is not bundled in this repository. The model also has to be downloaded once on the viewer's computer.

## 1. Install Ollama

Official download page:

```text
https://ollama.com/download
```

### Windows

Open PowerShell and run the current official Ollama installer command:

```powershell
irm https://ollama.com/install.ps1 | iex
```

Windows 10 or later is required by Ollama.

After installation, open a **new PowerShell window** and verify:

```powershell
ollama --version
```

If the command is still not recognized, reopen the terminal or install manually from the official download page.

### macOS

Use the official installer:

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

Alternatively install the Ollama desktop application from:

```text
https://ollama.com/download
```

Verify:

```bash
ollama --version
```

### Linux

Run the official install script:

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

Verify:

```bash
ollama --version
```

If the local Ollama service is not available, start it in a separate terminal:

```bash
ollama serve
```

---

## 2. Download the local model

The project is configured for `llama3.2` by default.

```bash
ollama pull llama3.2
```

Check that it is installed:

```bash
ollama list
```

You should see `llama3.2` in the local model list.

---

## 3. Start the platform with Ollama

Activate the same Python virtual environment first if it is not already active.

### Windows PowerShell

```powershell
.\.venv\Scripts\Activate.ps1

$env:COPILOT_PROVIDER="ollama"
$env:OLLAMA_MODEL="llama3.2"
$env:OLLAMA_NUM_CTX="16384"
$env:OLLAMA_NUM_PREDICT="640"

python -m streamlit run app.py --server.port 8510
```

### macOS / Linux

```bash
source .venv/bin/activate

export COPILOT_PROVIDER=ollama
export OLLAMA_MODEL=llama3.2
export OLLAMA_NUM_CTX=16384
export OLLAMA_NUM_PREDICT=640

python -m streamlit run app.py --server.port 8510
```

Open:

```text
http://localhost:8510
```

In **Risk Copilot**, the provider label should show:

```text
Ollama local GenAI + deterministic grounding
```

Ollama receives the governed full-context evidence packet available to the selected scope, while exact numerical calculations remain controlled by the deterministic risk layer.

---

# Subsequent runs

After the repository has already been initialized, a normal restart does **not** require rebuilding everything.

## Without Ollama — Windows

```powershell
cd Credit-Risk-Analytics
.\.venv\Scripts\Activate.ps1
$env:COPILOT_PROVIDER="deterministic"
python -m streamlit run app.py --server.port 8510
```

## With Ollama — Windows

```powershell
cd Credit-Risk-Analytics
.\.venv\Scripts\Activate.ps1

$env:COPILOT_PROVIDER="ollama"
$env:OLLAMA_MODEL="llama3.2"
$env:OLLAMA_NUM_CTX="16384"
$env:OLLAMA_NUM_PREDICT="640"

python -m streamlit run app.py --server.port 8510
```

The equivalent macOS/Linux commands use `source .venv/bin/activate` and `export` instead of PowerShell environment-variable syntax.

---

# Verify the repository

To run the automated checks:

```bash
python -m pytest -q
python scripts/validate_v5.py
python scripts/platform_shadow.py
python scripts/platform_verify_frozen.py
python -m credit_platform.cli audit-verify
```

The current publication baseline has been qualified on clean GitHub-hosted runners with:

- **240 passed, 1 upstream warning**
- V5 release checks **30/30**
- **5,172 facilities** reconciled
- **0 stage mismatches**
- audit chain **VERIFIED**
- PostgreSQL migration/shadow **PASS**
- WN-1 PostgreSQL persistence **VERIFIED**
- Streamlit headless startup **PASS**
- Docker image build **PASS**

---

# Troubleshooting

## PowerShell blocks virtual-environment activation

Run:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
```

Then activate again:

```powershell
.\.venv\Scripts\Activate.ps1
```

## `ollama` is not recognized

Close and reopen the terminal after installing Ollama, then run:

```powershell
ollama --version
```

If it is still unavailable, install from the official Ollama download page.

## Ollama is installed but the Copilot cannot connect

Check:

```bash
ollama list
```

If necessary, start the service:

```bash
ollama serve
```

Then restart Streamlit.

The default local endpoint used by the project is:

```text
http://127.0.0.1:11434/api/generate
```

## `llama3.2` is not installed

Run:

```bash
ollama pull llama3.2
```

## Port 8510 is already in use

Use another port:

```bash
python -m streamlit run app.py --server.port 8511
```

and open `http://localhost:8511`.

---

## No paid AI dependency

The repository does **not** require an OpenAI API key.

- deterministic Copilot: fully local;
- Ollama Copilot: fully local model inference;
- OpenAI integration: optional adapter only.

For the architecture and control design see [GENAI_COPILOT_GUIDE.md](GENAI_COPILOT_GUIDE.md). For exact clean-build evidence see [REPRODUCIBILITY.md](REPRODUCIBILITY.md).
