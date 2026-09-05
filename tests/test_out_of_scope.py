import pytest
from src.policy_agent.schemas import CoverageVerdict
from src.policy_agent.workflow import PolicyAssistant


def test_taxi_in_uae_out_of_scope(assistant: PolicyAssistant):
    """
    Policy only defines taxi reimbursement for the United Kingdom.
    Asking for Taxi in UAE/Dubai must explicitly refuse as out-of-scope.
    """
    response = assistant.ask("Can I expense a taxi in Dubai?")
    assert response.verdict == CoverageVerdict.OUT_OF_SCOPE
    assert "not covered" in response.answer.lower()
    assert len(response.matched_records) == 0


def test_car_rental_out_of_scope(assistant: PolicyAssistant):
    response = assistant.ask("What is the allowance for car rental?")
    assert response.verdict == CoverageVerdict.OUT_OF_SCOPE
    assert "car rental" in response.answer.lower()


def test_gym_membership_out_of_scope(assistant: PolicyAssistant):
    response = assistant.ask("Can I claim reimbursement for my gym membership?")
    assert response.verdict == CoverageVerdict.OUT_OF_SCOPE
    assert "not covered" in response.answer.lower()


def test_unsupported_region_for_meals(assistant: PolicyAssistant):
    response = assistant.ask("What is the meal allowance in Germany?")
    assert response.verdict == CoverageVerdict.OUT_OF_SCOPE
    assert "germany" in response.answer.lower() or "not covered" in response.answer.lower()


def test_empty_query(assistant: PolicyAssistant):
    response = assistant.ask("")
    assert response.verdict == CoverageVerdict.OUT_OF_SCOPE
    assert "No question was provided" in response.answer
