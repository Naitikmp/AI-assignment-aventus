import pytest
from src.policy_agent.schemas import CoverageVerdict
from src.policy_agent.workflow import PolicyAssistant


def test_end_to_end_uae_meal_with_citations(assistant: PolicyAssistant):
    response = assistant.ask("What is the meal limit in United Arab Emirates?")
    assert response.verdict == CoverageVerdict.COVERED
    assert "$90.00 USD" in response.answer
    assert len(response.citations) == 1
    assert "United Arab Emirates" in response.citations[0]
    assert "90.00 USD" in response.citations[0]


def test_end_to_end_uk_hotel_allowance(assistant: PolicyAssistant):
    response = assistant.ask("How much is covered for hotel stay in London, UK?")
    assert response.verdict == CoverageVerdict.COVERED
    assert "$220.00 USD" in response.answer
    assert "standard room" in response.citations[0].lower()


def test_end_to_end_provider_fallback():
    # Attempting to initialize with a non-existent remote provider gracefully defaults to local
    assistant = PolicyAssistant(provider_name="non_existent_provider")
    assert assistant.provider_name == "local"
    res = assistant.ask("What is the incidental allowance?")
    assert res.verdict == CoverageVerdict.COVERED
    assert "$25.00 USD" in res.answer
