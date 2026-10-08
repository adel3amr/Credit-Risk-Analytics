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


def test_frozen_text_hash_is_crlf_portable(tmp_path):
    from credit_platform.common import frozen_text_hash
    lf = tmp_path / "lf.csv"
    crlf = tmp_path / "crlf.csv"
    lf.write_bytes(b"a,b\n1,2\n")
    crlf.write_bytes(b"a,b\r\n1,2\r\n")
    assert frozen_text_hash(lf) == frozen_text_hash(crlf)


def test_copilot_rejects_meta_json_answers():
    assert not copilot._valid_narrative(
        "The provided data appears to be JSON. I can provide a Python code snippet to parse it."
    )
    assert copilot._valid_narrative(
        "Hospitality has the highest mean PD, while Services contributes the largest absolute ECL. "
        "Prioritize the unsecured Stage 2/3 population and high-utilization deteriorating borrowers."
    )


def test_deterministic_portfolio_summary_is_risk_complete():
    evidence = {
        "run_id": "r1",
        "borrower_count": 100,
        "facility_count": 120,
        "ead": 1000.0,
        "ecl": 50.0,
        "bank_gate": "BLOCKED",
        "by_stage": {
            "Stage 1": {"facilities": 90, "borrowers": 80, "ead": 700.0, "ecl": 20.0},
            "Stage 2": {"facilities": 25, "borrowers": 18, "ead": 250.0, "ecl": 20.0},
            "Stage 3": {"facilities": 5, "borrowers": 4, "ead": 50.0, "ecl": 10.0},
        },
        "by_industry": {
            "Services": {
                "borrowers": 40, "facilities": 50, "ead": 450.0, "ecl": 25.0,
                "mean_pd": 0.04, "mean_lgd": 0.40, "loss_intensity": 25.0 / 450.0,
            },
            "Hospitality": {
                "borrowers": 20, "facilities": 25, "ead": 200.0, "ecl": 15.0,
                "mean_pd": 0.08, "mean_lgd": 0.45, "loss_intensity": 15.0 / 200.0,
            },
        },
        "watchlist": {"borrowers": 12, "facilities": 14, "ead": 140.0, "ecl": 8.0},
        "unsecured": {"borrowers": 30, "facilities": 34, "ead": 300.0, "ecl": 18.0},
        "guaranteed": {"borrowers": 15, "facilities": 16, "ead": 120.0, "ecl": 4.0},
        "portfolio_review_actions": [
            {
                "type": "unsecured_stage_2_3",
                "borrowers": 8,
                "ead": 90.0,
                "reason": "Unsecured Stage 2/3 borrowers require collateral/recovery review.",
            }
        ],
        "risk_patterns": [],
        "review_basis": "Top facilities by reference ECL.",
        "top_risk_cases": [],
        "count_basis": "Distinct borrowers and facility-level exposures.",
    }
    answer = copilot.DeterministicProvider().render(
        "Summarize the portfolio risk profile and the most important areas for human review.",
        evidence,
        "portfolio",
    )
    assert "Services" in answer
    assert "Hospitality" in answer
    assert "Watchlist" in answer
    assert "Unsecured" in answer
    assert "Human-review priorities" in answer
