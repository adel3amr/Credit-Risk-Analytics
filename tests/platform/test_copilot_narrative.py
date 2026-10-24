"""Check public narrative readability without running a local LLM."""
import json

import pytest
from credit_platform import copilot


def _evidence():
    return {
        "run_id": "test-run", "borrower_count": 3000, "facility_count": 5172,
        "ead": 2091914075.83, "ecl": 45265972.04, "bank_gate": "BLOCKED",
        "by_stage": {
            "Stage 1": {"facilities": 4772, "ecl": 28437247.57},
            "Stage 2": {"facilities": 385, "ecl": 14249690.53},
            "Stage 3": {"facilities": 15, "ecl": 2579033.95},
        },
        "by_industry": {
            "Services": {"ecl": 9144965.79, "mean_pd": .0353, "loss_intensity": .0183},
            "Hospitality": {"ecl": 5000000, "mean_pd": .0523, "loss_intensity": .0329},
        },
        "watchlist": {"borrowers": 287, "ead": 203932448.63},
        "unsecured": {"borrowers": 1037, "ead": 707413666.08},
        "portfolio_review_actions": [
            {"type": "deteriorating_high_utilization", "borrowers": 170, "ead": 120406892.47}
        ],
    }


def test_summary_is_readable_and_preserves_governed_facts():
    answer = copilot.DeterministicProvider().render(
        "Summarize the portfolio risk profile and the most important areas for human review.",
        _evidence(), "portfolio",
    )
    for part in ("### Portfolio risk overview", "3,000 scored borrowers", "5,172 facilities",
                 "2,091.91m", "45.27m", "Services", "Hospitality",
                 "Human-review priorities", "170", "BLOCKED"):
        assert part in answer
    assert "€" not in answer


@pytest.mark.parametrize("text", ["", "short", "The supplied data appears to be JSON and Python code."])
def test_unsuitable_ollama_output_raises_explicit_error(monkeypatch, text):
    class Response:
        def __enter__(self):
            return self
        def __exit__(self, *_args):
            return False
        def read(self, *_args):
            return json.dumps({"response": text}).encode()
    monkeypatch.setattr(copilot, "_llm_evidence_text", lambda *_: "governed context")
    monkeypatch.setattr(copilot, "urlopen", lambda *_a, **_k: Response())
    with pytest.raises(ValueError, match="empty or unsuitable narrative"):
        copilot.OllamaProvider().render("Summarize portfolio.", _evidence(), "portfolio")


def test_valid_ollama_answer_is_used(monkeypatch):
    class Response:
        def __enter__(self):
            return self
        def __exit__(self, *_args):
            return False
        def read(self, *_args):
            return json.dumps({"response":
                "Services is the largest absolute ECL industry. Hospitality has "
                "the highest PD. Review high utilization and unsecured exposures."
            }).encode()
    monkeypatch.setattr(copilot, "_llm_evidence_text", lambda *_: "governed context")
    monkeypatch.setattr(copilot, "urlopen", lambda *_a, **_k: Response())
    assert "Hospitality" in copilot.OllamaProvider().render("Summary.", _evidence(), "portfolio")
