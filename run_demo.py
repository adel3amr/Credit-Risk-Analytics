"""One-command local demo launcher. Requires Python 3.12; no paid services."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from urllib.error import URLError
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parent
VENV = ROOT / ".venv"
MARKER = VENV / ".credit-risk-demo-ready"
REQUIRED_OUTPUTS = (
    "data/raw/sme_credit_portfolio.csv",
    "data/raw/lgd_workout_history.csv",
    "outputs/borrower_audit_trace.csv",
    "outputs/facility_ecl_predictions.csv",
    "models/platform/manifest.json",
    "platform.db",
)


def python_in_venv() -> Path:
    return VENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def build_fingerprint() -> str:
    """Track inputs affecting the local build, not unrelated Markdown changes."""
    source_paths = [
        ROOT / "requirements-platform-lock.txt",
        ROOT / "alembic.ini",
        *sorted((ROOT / "config").glob("*.csv")),
    ]
    for dirname in ("src", "credit_platform", "notebooks", "scripts", "migrations"):
        source_paths.extend(sorted((ROOT / dirname).rglob("*.py")))
    result = hashlib.sha256()
    for path in source_paths:
        if not path.is_file():
            raise RuntimeError(f"Missing project input: {path.relative_to(ROOT)}")
        result.update(str(path.relative_to(ROOT)).encode("utf-8"))
        result.update(hashlib.sha256(path.read_bytes()).digest())
    return result.hexdigest()


def is_ready() -> bool:
    return (
        python_in_venv().is_file()
        and MARKER.is_file()
        and MARKER.read_text(encoding="utf-8").strip() == build_fingerprint()
        and all((ROOT / name).is_file() for name in REQUIRED_OUTPUTS)
    )


def command(*args: str) -> None:
    print("\n> " + " ".join(args), flush=True)
    subprocess.run(args, cwd=ROOT, check=True)


def setup(rebuild: bool = False) -> None:
    if is_ready() and not rebuild:
        print("Existing demo setup found; skipping installation and model rebuild.")
        return
    if not python_in_venv().is_file():
        print("Creating an isolated Python environment...")
        command(sys.executable, "-m", "venv", str(VENV))
    py = str(python_in_venv())
    MARKER.unlink(missing_ok=True)
    print("Installing pinned dependencies and creating the local synthetic demo...")
    command(py, "-m", "pip", "install", "-r", "requirements-platform-lock.txt")
    command(py, "scripts/run_v5.py")
    command(py, "-m", "credit_platform.cli", "build-models")
    command(py, "-m", "alembic", "upgrade", "head")
    command(py, "-m", "credit_platform.cli", "seed-governance")
    MARKER.write_text(build_fingerprint(), encoding="utf-8")
    print("Local demo setup completed.")


def check_ollama(model: str) -> None:
    """Fail early with an actionable message instead of showing a silent fallback."""
    try:
        with urlopen("http://127.0.0.1:11434/api/tags", timeout=3) as response:
            models = json.load(response).get("models", [])
    except (URLError, TimeoutError, OSError, ValueError, json.JSONDecodeError) as exc:
        raise RuntimeError(
            "Ollama is not reachable. Install/start Ollama from "
            "https://ollama.com/download, then run: ollama pull llama3.2"
        ) from exc
    names = {str(row.get("name", "")) for row in models}
    if not any(name == model or name.startswith(model + ":") for name in names):
        raise RuntimeError(f"Model '{model}' is not installed. Run: ollama pull {model}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the local Credit Risk research demo")
    parser.add_argument("--ollama", action="store_true", help="Use the optional local LLM")
    parser.add_argument("--rebuild", action="store_true", help="Regenerate the local reference data/models")
    parser.add_argument("--port", type=int, default=8510, help="Local Streamlit port (default: 8510)")
    args = parser.parse_args()

    if sys.version_info[:2] != (3, 12):
        parser.error("Use Python 3.12: py -3.12 run_demo.py (Windows) or python3.12 run_demo.py")
    if not 1 <= args.port <= 65535:
        parser.error("--port must be between 1 and 65535")

    provider = "ollama" if args.ollama else "deterministic"
    env = os.environ.copy()
    env["COPILOT_PROVIDER"] = provider
    if args.ollama:
        model = env.get("OLLAMA_MODEL", "llama3.2")
        check_ollama(model)
        env.setdefault("OLLAMA_MODEL", model)
        env.setdefault("OLLAMA_NUM_CTX", "16384")
        env.setdefault("OLLAMA_NUM_PREDICT", "640")
    try:
        setup(rebuild=args.rebuild)
        print(f"\nStarting Credit Risk research demo at http://localhost:{args.port}")
        print(f"Copilot: {provider}. Stop with Ctrl+C.\n", flush=True)
        subprocess.run(
            [
                str(python_in_venv()),
                "-m",
                "streamlit",
                "run",
                "app.py",
                "--server.port",
                str(args.port),
                "--server.address",
                "127.0.0.1",
            ],
            cwd=ROOT,
            env=env,
            check=True,
        )
        return 0
    except KeyboardInterrupt:
        print("\nDemo stopped.")
        return 0
    except subprocess.CalledProcessError as exc:
        print(f"\nA setup or launch command failed (exit {exc.returncode}).", file=sys.stderr)
        print("Fix the error above and run the same command again.", file=sys.stderr)
        return exc.returncode or 1
    except (RuntimeError, OSError) as exc:
        print(f"\n{exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
