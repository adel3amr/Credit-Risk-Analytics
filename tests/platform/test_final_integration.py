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


def test_riskiest_industry_is_metric_specific():
    evidence = {
        "run_id": "r1",
        "borrower_count": 100,
        "facility_count": 120,
        "ead": 1000.0,
        "ecl": 50.0,
        "bank_gate": "BLOCKED",
        "by_stage": {
            "Stage 1": {"facilities": 100, "borrowers": 90, "ead": 800.0, "ecl": 25.0},
            "Stage 2": {"facilities": 15, "borrowers": 12, "ead": 150.0, "ecl": 15.0},
            "Stage 3": {"facilities": 5, "borrowers": 4, "ead": 50.0, "ecl": 10.0},
        },
        "by_industry": {
            "Services": {
                "borrowers": 45, "facilities": 55, "ead": 500.0, "ecl": 20.0,
                "mean_pd": 0.035, "mean_lgd": 0.40, "loss_intensity": 0.04,
            },
            "Hospitality": {
                "borrowers": 20, "facilities": 25, "ead": 180.0, "ecl": 12.0,
                "mean_pd": 0.0523, "mean_lgd": 0.4541, "loss_intensity": 0.067,
            },
        },
        "watchlist": {"borrowers": 10, "facilities": 12, "ead": 100.0, "ecl": 6.0},
        "unsecured": {"borrowers": 25, "facilities": 28, "ead": 250.0, "ecl": 14.0},
        "guaranteed": {"borrowers": 15, "facilities": 16, "ead": 120.0, "ecl": 4.0},
        "portfolio_review_actions": [],
        "risk_patterns": [],
        "review_basis": "Top facilities by reference ECL.",
        "top_risk_cases": [],
        "count_basis": "Distinct borrowers and facility-level exposures.",
    }
    answer = copilot.DeterministicProvider().render(
        "riskiest industry", evidence, "portfolio"
    )
    assert "no single universal definition" in answer.lower()
    assert "Highest mean PD: Hospitality" in answer
    assert "Highest ECL/EAD loss intensity: Hospitality" in answer
    assert "Highest mean LGD: Hospitality" in answer
    assert "Largest absolute ECL concentration: Services" in answer


def test_conversational_providers_do_not_prepend_deterministic_block():
    source = Path(copilot.__file__).read_text(encoding="utf-8")
    assert 'return verified + "\\n\\nCopilot interpretation:' not in source


def test_customer_concentration_uses_borrower_ecl_ranking():
    evidence = {
        "run_id": "r1",
        "borrower_count": 10,
        "facility_count": 12,
        "ead": 1000.0,
        "ecl": 100.0,
        "bank_gate": "BLOCKED",
        "by_stage": {},
        "by_industry": {},
        "top_borrowers_by_ecl": [
            {
                "borrower_id": f"B{i}",
                "industry": "Services",
                "stage": "Stage 1",
                "risk_rating": 3,
                "ead": 50.0 + i,
                "ecl": 10.0 - i,
                "max_pd": 0.05 + i / 1000,
                "max_lgd": 0.40,
            }
            for i in range(1, 6)
        ],
        "top_risk_cases": [],
        "watchlist": {"borrowers": 0, "facilities": 0, "ead": 0.0, "ecl": 0.0},
        "unsecured": {"borrowers": 0, "facilities": 0, "ead": 0.0, "ecl": 0.0},
        "guaranteed": {"borrowers": 0, "facilities": 0, "ead": 0.0, "ecl": 0.0},
        "portfolio_review_actions": [],
        "risk_patterns": [],
        "review_basis": "",
        "count_basis": "",
    }
    answer = copilot.DeterministicProvider().render(
        "riskiest 5 customers and their concentration", evidence, "portfolio"
    )
    assert "ranks borrowers by governed reference ECL" in answer
    assert "Top-5 concentration:" in answer
    assert "B1" in answer and "B5" in answer
    assert copilot._exact_analytics_intent(
        "riskiest 5 customers and their concentration", "portfolio"
    )


def test_borrower_adverse_indicators_include_source_features():
    evidence = {
        "borrower_id": "SME06857",
        "source_profile": {
            "features": {
                "credit_utilization": 0.861,
                "delinquencies_12m": 1,
                "days_past_due": 0,
                "leverage_ratio": 2.2,
                "previous_defaults": 0,
                "limit_breach_count": 0,
                "months_above_80_utilization": 2,
            }
        },
        "facilities": [
            {
                "stage": "Stage 1",
                "pd": 0.0963,
                "lgd": 0.42,
                "ead": 600000.0,
                "ecl": 30000.0,
                "stage_reasons": ["no_stage2_or_stage3_trigger"],
                "watchlist": False,
                "sicr": False,
                "ews": [],
                "risk_rating": 5,
                "risk_direction": "Watch",
            },
            {
                "stage": "Stage 1",
                "pd": 0.0963,
                "lgd": 0.40,
                "ead": 393689.60,
                "ecl": 17790.24,
                "stage_reasons": ["no_stage2_or_stage3_trigger"],
                "watchlist": False,
                "sicr": False,
                "ews": [],
                "risk_rating": 5,
                "risk_direction": "Watch",
            },
        ],
        "bank_gate": "BLOCKED",
    }
    answer = copilot.DeterministicProvider().render(
        "what are the key adverse indicators?", evidence, "borrower"
    )
    assert "high utilization 86.1%" in answer
    assert "1 delinquency event(s)" in answer
    assert "2 month(s) above 80% utilization" in answer
    assert "Stage 1" in answer
    assert copilot._exact_analytics_intent(
        "what are the key adverse indicators?", "borrower"
    )
