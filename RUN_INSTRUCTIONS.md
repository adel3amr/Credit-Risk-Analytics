# Run the Credit Risk Analytics demo

**Two steps after installing Git and Python 3.12:** clone the repository, then run the launcher. It creates its own virtual environment, installs pinned packages, generates the synthetic reference data/models, initializes the local database, and starts Streamlit. On a clean machine the first build takes longer than later restarts. No API key, PostgreSQL server, Docker, or paid service is needed for this local demo.

## 1. Install prerequisites

- [Git](https://git-scm.com/downloads)
- [Python 3.12](https://www.python.org/downloads/) (use Python **3.12**, not 3.13; on Windows enable the Python launcher during installation).

## 2. Clone and launch — no Ollama needed

**Windows PowerShell**

```powershell
git clone https://github.com/adel3amr/Credit-Risk-Analytics.git
cd Credit-Risk-Analytics
py -3.12 run_demo.py
```

**macOS / Linux terminal**

```bash
git clone https://github.com/adel3amr/Credit-Risk-Analytics.git
cd Credit-Risk-Analytics
python3.12 run_demo.py
```

Open **http://localhost:8510** if the browser does not open automatically. Select a demo role using the sidebar. You can explore the Portfolio Cockpit, Borrower Credit File, Risk Management, Model Validation (select Model Validation role), and Risk Copilot.

The first run prepares locally generated data. Later runs use the same command and reuse the completed installation **provided the build inputs have not changed**. Updating the repository with build-relevant code changes may require re-running setup.

## 3. Optional: enable conversational GenAI with Ollama

The **core project runs without Ollama**. To add a free local LLM:

1. Install Ollama from its **[official downloads](https://ollama.com/download)** for Windows, macOS, or Linux. Reopen the terminal after installing.
2. Download the model with `ollama pull llama3.2`. Ensure the Ollama desktop app/service is running; on Linux you can start it with `ollama serve` in another terminal.
3. From inside the cloned repository run:

**Windows**

```powershell
py -3.12 run_demo.py --ollama
```

**macOS / Linux**

```bash
python3.12 run_demo.py --ollama
```

In Risk Copilot the configured provider is **Ollama local GenAI + deterministic grounding**. Successful conversational answers show `ollama-local` as their actual provider. Exact analytical questions may route to `deterministic-local` by design; timeout/unusable-answer fallbacks display a clear warning. Ollama runs locally; no paid provider is needed. Numerical risk calculations are performed by the deterministic engine. Generated text requires human review.

## Useful commands

| Action | Windows | macOS / Linux |
|---|---|---|
| Restart demo | `py -3.12 run_demo.py` | `python3.12 run_demo.py` |
| Start with Ollama | `py -3.12 run_demo.py --ollama` | `python3.12 run_demo.py --ollama` |
| Rebuild data/models | `py -3.12 run_demo.py --rebuild` | `python3.12 run_demo.py --rebuild` |
| Change port | `py -3.12 run_demo.py --port 8511` | `python3.12 run_demo.py --port 8511` |

Press **Ctrl+C** in the running terminal to stop the app. If setup fails halfway through, fix the error and rerun the same command; the launcher will complete the setup before starting the UI.

## Troubleshooting

- **Python 3.12 not found:** install Python 3.12, reopen the terminal, and use the commands above. Do not rely on an unsupported default Python version.
- **`git` not found:** install Git, reopen the terminal, and retry cloning.
- **Port already in use:** stop the earlier Streamlit process with Ctrl+C or append `--port 8511` and open http://localhost:8511.
- **Ollama not reachable or model missing:** start the Ollama app/service; run `ollama pull llama3.2`, then retry `--ollama`.
- **Ollama responds to simple questions but times out in the Copilot:** make sure you're on the current `main` branch (`git pull --ff-only origin main`). Typical portfolio questions now use **question-focused evidence**, a capped 4K context and a capped 400-token answer. Requests for `full context` are intentionally slower; use them only when needed.
- **An existing project already has working models:** if you just pulled an interface/Copilot update, you can run `.\\.venv\\Scripts\\python.exe -m streamlit run app.py --server.port 8510` on Windows after setting `$env:COPILOT_PROVIDER=\"ollama\"`, instead of rebuilding the reference models. See the normal launcher path above for fresh installations.
- **Broken local outputs after changing code:** use `--rebuild`. The script regenerates only the local reference environment; it does not retrain or promote any frozen research challengers.
- **Want to run commands manually?** The exact lower-level sequence is in [REPRODUCIBILITY.md](REPRODUCIBILITY.md).

## Verify independently

After starting the demo once, stop it with Ctrl+C and run these commands from the repository root:

**Windows**

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe scripts/validate_v5.py
.\.venv\Scripts\python.exe -m credit_platform.cli audit-verify
```

**macOS / Linux**

```bash
./.venv/bin/python -m pytest -q
./.venv/bin/python scripts/validate_v5.py
./.venv/bin/python -m credit_platform.cli audit-verify
```

The published synthetic-reference evidence includes a full hosted CI suite, a 5,172-facility EAD/ECL reconciliation, audit verification, and working headless Streamlit startup. [Reproducibility evidence](REPRODUCIBILITY.md) and [validation/limitations](PUBLICATION_READINESS.md) provide details.

**Scope:** this is a synthetic Credit Risk research demonstration, not software or a model qualified for real banking decisions.
