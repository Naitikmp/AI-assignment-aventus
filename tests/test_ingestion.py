import pytest
from pathlib import Path
from src.policy_agent.ingestion import PolicyLoader


def test_csv_loading_and_deduplication(default_csv_path):
    """
    Verifies that the CSV is successfully parsed and that Row 14's deliberate duplicate
    is caught and removed, ensuring data integrity.
    """
    records, stats = PolicyLoader.load_from_csv(default_csv_path)

    # 13 data rows in file, 1 intentional duplicate
    assert stats.total_rows_read == 13
    assert stats.duplicates_removed == 1
    assert stats.records_loaded == 12
    assert len(records) == 12

    # Verify no duplicate UK meal entries exist
    uk_meals = [r for r in records if r.category == "Meals" and r.region == "United Kingdom"]
    assert len(uk_meals) == 1
    assert uk_meals[0].daily_limit_usd == 75.0


def test_schema_types(loaded_records):
    records, _ = loaded_records
    for r in records:
        assert isinstance(r.category, str)
        assert isinstance(r.region, str)
        assert r.currency == "USD"
        if r.daily_limit_usd is not None:
            assert isinstance(r.daily_limit_usd, float)
            assert r.daily_limit_usd > 0


def test_missing_file_raises_error():
    with pytest.raises(FileNotFoundError):
        PolicyLoader.load_from_csv("non_existent_policy.csv")
