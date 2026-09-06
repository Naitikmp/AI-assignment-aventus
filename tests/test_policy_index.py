from src.policy_agent.policy_index import PolicyIndex
from src.policy_agent.schemas import CoverageVerdict


def test_uae_meal_query(loaded_records):
    records, _ = loaded_records
    index = PolicyIndex(records)
    intent = index.parse_intent("What is the daily meal limit in UAE?")
    assert intent.detected_category == "Meals"
    assert intent.detected_region == "United Arab Emirates"

    verdict, matched, _ = index.search(intent)
    assert verdict == CoverageVerdict.COVERED
    assert len(matched) == 1
    assert matched[0].daily_limit_usd == 90.0
    assert matched[0].region == "United Arab Emirates"


def test_uae_hotel_query(loaded_records):
    records, _ = loaded_records
    index = PolicyIndex(records)
    intent = index.parse_intent("What is the hotel allowance for Abu Dhabi?")
    assert intent.detected_category == "Hotel"
    assert intent.detected_region == "United Arab Emirates"

    verdict, matched, _ = index.search(intent)
    assert verdict == CoverageVerdict.COVERED
    assert len(matched) == 1
    assert matched[0].daily_limit_usd == 300.0


def test_uk_taxi_actuals(loaded_records):
    records, _ = loaded_records
    index = PolicyIndex(records)
    intent = index.parse_intent("How are taxis reimbursed in the UK?")
    assert intent.detected_category == "Taxi"
    assert intent.detected_region == "United Kingdom"

    verdict, matched, _ = index.search(intent)
    assert verdict == CoverageVerdict.COVERED
    assert len(matched) == 1
    assert matched[0].daily_limit_usd is None
    assert "actuals" in matched[0].notes.lower()


def test_flight_duration_under_6_hours(loaded_records):
    records, _ = loaded_records
    index = PolicyIndex(records)
    intent = index.parse_intent("I am booking a 4 hour flight. Can I fly business class?")
    assert intent.detected_category == "Airfare"
    assert intent.flight_duration_hours == 4.0

    verdict, matched, _ = index.search(intent)
    assert verdict == CoverageVerdict.COVERED
    assert len(matched) == 1
    assert "economy only" in matched[0].notes.lower()


def test_flight_duration_over_6_hours(loaded_records):
    records, _ = loaded_records
    index = PolicyIndex(records)
    intent = index.parse_intent("Can I fly business class for an 8-hour flight?")
    assert intent.detected_category == "Airfare"
    assert intent.flight_duration_hours == 8.0

    verdict, matched, _ = index.search(intent)
    assert verdict == CoverageVerdict.COVERED
    assert len(matched) == 1
    assert "business class permitted" in matched[0].notes.lower()


def test_incidentals(loaded_records):
    records, _ = loaded_records
    index = PolicyIndex(records)
    intent = index.parse_intent("Do I need receipts for incidentals?")
    assert intent.detected_category == "Incidentals"

    verdict, matched, _ = index.search(intent)
    assert verdict == CoverageVerdict.COVERED
    assert len(matched) == 1
    assert matched[0].daily_limit_usd == 25.0
    assert "no receipt required" in matched[0].notes.lower()
