"""Fast tests for the public cross-platform launcher; no pip/download required."""

import importlib.util
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "run_demo.py"
spec = importlib.util.spec_from_file_location("public_demo_launcher", MODULE)
launcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(launcher)


def _test_workspace(monkeypatch, tmp_path):
    monkeypatch.setattr(launcher, "ROOT", tmp_path)
    monkeypatch.setattr(launcher, "VENV", tmp_path / ".venv")
    monkeypatch.setattr(launcher, "MARKER", tmp_path / ".venv" / ".credit-risk-demo-ready")
    (tmp_path / "requirements-platform-lock.txt").write_text("pandas==2.2.3\n")
    (tmp_path / "alembic.ini").write_text("[alembic]\n")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "risk.py").write_text("VALUE = 1\n")
    interpreter = launcher.python_in_venv()
    interpreter.parent.mkdir(parents=True, exist_ok=True)
    interpreter.touch()
    for output in launcher.REQUIRED_OUTPUTS:
        path = tmp_path / output
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch()


def test_demo_reuses_complete_build_and_invalidates_changes(monkeypatch, tmp_path):
    _test_workspace(monkeypatch, tmp_path)
    assert not launcher.is_ready()
    launcher.MARKER.write_text(launcher.build_fingerprint())
    assert launcher.is_ready()
    (tmp_path / "src" / "risk.py").write_text("VALUE = 2\n")
    assert not launcher.is_ready()


def test_demo_does_not_accept_missing_generated_outputs(monkeypatch, tmp_path):
    _test_workspace(monkeypatch, tmp_path)
    launcher.MARKER.write_text(launcher.build_fingerprint())
    assert launcher.is_ready()
    (tmp_path / "outputs" / "borrower_audit_trace.csv").unlink()
    assert not launcher.is_ready()


def test_demo_restarts_without_rebuilding(monkeypatch, tmp_path):
    _test_workspace(monkeypatch, tmp_path)
    launcher.MARKER.write_text(launcher.build_fingerprint())
    commands = []
    monkeypatch.setattr(launcher, "command", lambda *args: commands.append(args))
    launcher.setup()
    assert commands == []
