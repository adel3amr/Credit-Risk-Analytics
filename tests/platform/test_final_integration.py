from pathlib import Path

from credit_platform import copilot


ROOT = Path(__file__).resolve().parents[2]


def test_final_streamlit_workbench_keeps_copilot_and_validation():
    text = (ROOT / "app.py").read_text(encoding="utf-8")
    for label in (
        "Portfolio Cockpit",
        "Borrower Credit File",
        "Risk Management",
        "Risk Copilot",
        "Model Validation",
    ):
        assert label in text


def test_final_copilot_provider_selection(monkeypatch):
    monkeypatch.setenv("COPILOT_PROVIDER", "auto")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OLLAMA_MODEL", raising=False)
    assert isinstance(copilot.provider(), copilot.DeterministicProvider)

    monkeypatch.setenv("OLLAMA_MODEL", "llama3.2")
    assert isinstance(copilot.provider(), copilot.OllamaProvider)

    monkeypatch.setenv("OPENAI_API_KEY", "test-only-placeholder")
    assert isinstance(copilot.provider(), copilot.OpenAIResponsesProvider)


def test_final_portfolio_copilot_uses_service_single_source():
    source = Path(copilot.__file__).read_text(encoding="utf-8")
    assert "base = service.portfolio(conn, run_id)" in source
    assert "service.portfolio" in source
    assert "workout_lgd" in source
    assert "Institutional production remains BLOCKED" in source


def test_final_service_is_canonical_portfolio_evidence():
    from credit_platform import service
    source = Path(service.__file__).read_text(encoding="utf-8")
    for field in (
        "collateral_type",
        "top_borrowers_by_ecl",
        "scenario_mean_pd",
        "risk_indicator_counts",
        "risk_patterns",
        "portfolio_review_actions",
    ):
        assert field in source


def test_final_borrower_copilot_keeps_full_decision_context():
    source = Path(copilot.__file__).read_text(encoding="utf-8")
    for field in (
        "risk_rating",
        "risk_direction",
        "scenario_pd",
        "collateral_coverage",
        "guarantee_coverage",
        "remaining_months",
    ):
        assert field in source
