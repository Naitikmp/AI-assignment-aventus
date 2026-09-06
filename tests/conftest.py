from pathlib import Path

import pytest

from src.policy_agent.ingestion import PolicyLoader
from src.policy_agent.workflow import PolicyAssistant


@pytest.fixture(scope="session")
def default_csv_path() -> Path:
    base = Path(__file__).resolve().parent.parent
    data_path = base / "data" / "travel_expense_policy.csv"
    if not data_path.exists():
        data_path = base / "travel_expense_policy.csv"
    return data_path


@pytest.fixture
def assistant(default_csv_path) -> PolicyAssistant:
    return PolicyAssistant(data_path=default_csv_path, provider_name="local")


@pytest.fixture
def loaded_records(default_csv_path):
    records, stats = PolicyLoader.load_from_csv(default_csv_path)
    return records, stats
