"""Question-relevant local Ollama prompts keep the public demo responsive."""

import json

from credit_platform import copilot


def portfolio():
    by_industry = {
        f"Sector {idx}": {
            "borrowers": 100, "facilities": 125,
            "ead": 10000000 + idx, "ecl": 100000 + idx,
            "mean_pd": 0.04, "mean_lgd": 0.4, "loss_intensity": 0.01,
        }
        for idx in range(22)
    }
    return {
        "run_id": "test", "borrower_count": 3000, "facility_count": 5172,
        "ead": 2091914075.83, "ecl": 45265972.04, "bank_gate": "BLOCKED",
        "by_stage": {
            "Stage 1": {"facilities": 4772, "ecl": 28437247.57},
            "Stage 2": {"facilities": 385, "ecl": 14249690.53},
            "Stage 3": {"facilities": 15, "ecl": 2579033.95},
        },
        "by_industry": by_industry,
        "watchlist": {"borrowers": 287, "ead": 203932448.63},
        "unsecured": {"borrowers": 1037, "ead": 707413666.08},
        "guaranteed": {"borrowers": 1076, "ead": 237096064.40},
        "portfolio_review_actions": [
            {"type": "unsecured_stage_2_3", "borrowers": 78, "ead": 50972280.07}
        ],
        "risk_patterns": [],
        "top_borrowers_by_ecl": [
            {"borrower_id": f"SME{i}", "ead": 10000000, "ecl": 100000}
            for i in range(15)
        ],
        "top_borrowers_by_ead": [
            {"borrower_id": f"SME{i}", "ead": 10000000, "ecl": 100000}
            for i in range(15)
        ],
        "top_risk_cases": [
            {"borrower_id": f"SME{i}", "facility_id": f"F{i}", "ead": 100000}
            for i in range(10)
        ],
    }


def test_summary_payload_is_smaller_but_grounded():
    evidence = portfolio()
    text, comprehensive = copilot._ollama_context(
        "Summarize the portfolio risk profile and areas for review.",
        evidence, "portfolio",
    )
    assert comprehensive is False
    assert "3000" in text and "5172" in text
    assert "45265972.04" in text
    assert "STAGES" in text and "INDUSTRIES" in text
    assert "HUMAN REVIEW ACTIONS" in text
    assert "50972280.07" in text
    assert "BANK" not in text or "BLOCKED" in text
    assert "SME14" not in text
    assert len(text) < len(copilot._llm_evidence_text(
        "Summarize the portfolio risk profile and areas for review.", evidence, "portfolio"
    ))


def test_requested_customer_details_are_included():
    text, comprehensive = copilot._ollama_context(
        "Discuss the top borrower exposures and concentration",
        portfolio(), "portfolio",
    )
    assert not comprehensive
    assert "TOP_BORROWERS_BY_ECL" in text
    assert "SME0" in text
    assert "SME14" not in text


def test_full_context_is_available_on_explicit_request():
    question = "Please use full context with all available evidence"
    text, comprehensive = copilot._ollama_context(
        question, portfolio(), "portfolio"
    )
    assert comprehensive is True
    assert "SME14" in text


def test_local_ollama_request_uses_compact_budgets_and_keeps_verification(monkeypatch):
    monkeypatch.setenv("OLLAMA_NUM_CTX", "16384")
    monkeypatch.setenv("OLLAMA_NUM_PREDICT", "640")
    monkeypatch.delenv("OLLAMA_FULL_CONTEXT", raising=False)
    observed = {}

    class Response:
        def __enter__(self):
            return self
        def __exit__(self, *_):
            return False
        def read(self, *_):
            return json.dumps({
                "response": "The watchlist exposure requires targeted human review. "
                "Stage 2 and Stage 3 facilities warrant additional monitoring."
            }).encode()

    def fake_urlopen(request, timeout):
        observed.update(json.loads(request.data))
        return Response()

    monkeypatch.setattr(copilot, "urlopen", fake_urlopen)
    answer = copilot.OllamaProvider().render(
        "Summarize portfolio risk", portfolio(), "portfolio"
    )
    assert "watchlist exposure" in answer
    assert observed["options"]["num_ctx"] == 4096
    assert observed["options"]["num_predict"] == 400
    assert "VERIFIED QUESTION-SPECIFIC FACTS" in observed["prompt"]
    assert "45265972.04" in observed["prompt"]
    assert len(observed["prompt"]) < 9000
