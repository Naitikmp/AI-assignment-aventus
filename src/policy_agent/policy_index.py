import re
from typing import List, Optional, Tuple

from src.policy_agent.schemas import CoverageVerdict, ExtractedIntent, PolicyRecord


class PolicyIndex:
    """
    Search and rule-evaluation index for corporate travel expense policies.
    Provides entity resolution, regional mapping, condition checks, and out-of-scope detection.
    """

    REGION_SYNONYMS = {
        "United Arab Emirates": ["uae", "united arab emirates", "emirates", "abu dhabi", "dubai", "sharjah"],
        "United Kingdom": ["uk", "united kingdom", "britain", "great britain", "england", "london"],
        "United States": ["us", "usa", "united states", "america", "american", "new york", "san francisco", "chicago"],
        "India": ["india", "indian", "delhi", "mumbai", "bengaluru", "bangalore", "hyderabad"],
        "Global": ["global", "worldwide", "international", "anywhere"],
    }

    CATEGORY_SYNONYMS = {
        "Meals": ["meal", "meals", "food", "dining", "lunch", "dinner", "breakfast", "per diem", "eating"],
        "Hotel": ["hotel", "hotels", "accommodation", "lodging", "room", "night", "stay", "suite"],
        "Taxi": ["taxi", "taxis", "cab", "cabs", "uber", "ride", "lyft", "rideshare"],
        "Airfare": ["airfare", "flight", "flights", "plane", "airline", "flying", "fly", "ticket", "business class", "economy"],
        "Incidentals": ["incidental", "incidentals", "misc", "miscellaneous"],
    }

    # Explicit list of out-of-scope keywords to immediately flag unsupported domains
    KNOWN_OUT_OF_SCOPE_TOPICS = [
        "car rental", "rental car", "gym", "laundry", "entertainment", "alcohol",
        "gift", "gifts", "clothing", "massage", "spa", "phone", "sim card", "visa",
        "passport", "dental", "medical", "insurance", "train", "metro"
    ]

    def __init__(self, records: List[PolicyRecord]):
        self.records = records

    def parse_intent(self, query: str) -> ExtractedIntent:
        q_lower = query.lower()

        # 1. Resolve All Matching Categories
        detected_categories: List[str] = []
        for cat, synonyms in self.CATEGORY_SYNONYMS.items():
            for syn in synonyms:
                pattern = rf"\b{re.escape(syn)}\b"
                if re.search(pattern, q_lower):
                    if cat not in detected_categories:
                        detected_categories.append(cat)
                    break

        # 2. Resolve Region
        detected_region = None
        for reg, synonyms in self.REGION_SYNONYMS.items():
            for syn in synonyms:
                pattern = rf"\b{re.escape(syn)}\b"
                if re.search(pattern, q_lower):
                    detected_region = reg
                    break
            if detected_region:
                break

        # 3. Detect flight duration if discussing airfare
        flight_hours = None
        is_airfare = ("Airfare" in detected_categories) or any(
            re.search(rf"\b{re.escape(term)}\b", q_lower) for term in ["flight", "flights", "airfare", "fly", "flying"]
        )
        if is_airfare and "Airfare" not in detected_categories:
            detected_categories.append("Airfare")

        if is_airfare:
            hour_match = re.search(r"(\d+(?:\.\d+)?)\s*[-\s]?\s*(?:hours?|hrs?)", q_lower)
            if hour_match:
                try:
                    flight_hours = float(hour_match.group(1))
                except ValueError:
                    pass

        # 4. Detect unsupported out-of-scope topics
        unsupported_found = []
        for unsupported in self.KNOWN_OUT_OF_SCOPE_TOPICS:
            if re.search(rf"\b{re.escape(unsupported)}\b", q_lower):
                unsupported_found.append(unsupported)

        is_asking_limit = any(term in q_lower for term in ["limit", "allowance", "max", "maximum", "how much", "rate", "cost"])
        is_asking_receipts = any(term in q_lower for term in ["receipt", "receipts", "actuals", "tip", "tips", "proof"])

        return ExtractedIntent(
            raw_query=query,
            detected_categories=detected_categories,
            detected_region=detected_region,
            flight_duration_hours=flight_hours,
            is_airfare=is_airfare,
            is_asking_limit=is_asking_limit,
            is_asking_receipts=is_asking_receipts,
            unsupported_topics=unsupported_found,
        )

    def _search_single_category(
        self,
        cat: str,
        region: Optional[str],
        flight_hours: Optional[float],
        raw_query: str
    ) -> Tuple[CoverageVerdict, List[PolicyRecord], str]:
        # Case 1: Airfare (Global category)
        if cat == "Airfare":
            airfare_records = [r for r in self.records if r.category == "Airfare"]
            if flight_hours is not None:
                if flight_hours < 6.0:
                    matched = [r for r in airfare_records if "under 6 hours" in r.notes.lower()]
                    return CoverageVerdict.COVERED, matched, "Matched policy for flights under 6 hours."
                else:
                    matched = [r for r in airfare_records if "over 6 hours" in r.notes.lower()]
                    return CoverageVerdict.COVERED, matched, "Matched policy for flights over 6 hours."
            return CoverageVerdict.COVERED, airfare_records, "Matched global airfare policy guidelines."

        # Case 2: Incidentals (Global category)
        if cat == "Incidentals":
            incidental_records = [r for r in self.records if r.category == "Incidentals"]
            return CoverageVerdict.COVERED, incidental_records, "Matched global incidentals policy."

        # Case 3: Regional Categories (Meals, Hotel, Taxi)
        if not region:
            unlisted_match = re.search(r"\b(?:in|for|to|at)\s+([a-zA-Z\s]+?)(?:\?|$|\.|\,)", raw_query, re.IGNORECASE)
            if unlisted_match:
                potential_place = unlisted_match.group(1).strip()
                generic_words = {"london", "hotel", "hotels", "meals", "food", "taxi", "business", "standard", "days", "day", "night", "flight", "flights"}
                if potential_place.lower() not in generic_words and len(potential_place) > 2:
                    return (
                        CoverageVerdict.OUT_OF_SCOPE,
                        [],
                        f"Region '{potential_place}' is not covered under the company travel expense policy. Covered regions are: United Kingdom, United States, United Arab Emirates, and India."
                    )

            cat_records = [r for r in self.records if r.category == cat]
            if cat_records:
                return (
                    CoverageVerdict.PARTIALLY_COVERED,
                    cat_records,
                    f"Policy defines {cat} rules per specific region. No specific region was specified."
                )
            return (
                CoverageVerdict.OUT_OF_SCOPE,
                [],
                f"Policy does not have entries for {cat}."
            )

        # Region was identified: check if policy covers (cat, region)
        matched = [r for r in self.records if r.category == cat and (r.region == region or r.region == "Global")]
        if matched:
            return CoverageVerdict.COVERED, matched, f"Matched {cat} policy for {region}."

        # Category is known, but NOT for this region!
        available_regions = [r.region for r in self.records if r.category == cat and r.region != "Global"]
        regions_str = ", ".join(sorted(set(available_regions))) if available_regions else "None"

        return (
            CoverageVerdict.OUT_OF_SCOPE,
            [],
            f"The policy covers {cat} only for: {regions_str}. Expenses for {cat} in '{region}' are not covered."
        )

    def search(self, intent: ExtractedIntent) -> Tuple[CoverageVerdict, List[PolicyRecord], str]:
        # If unsupported topic found and NO recognized categories:
        if intent.unsupported_topics and not intent.detected_categories:
            unsupported = intent.unsupported_topics[0]
            return (
                CoverageVerdict.OUT_OF_SCOPE,
                [],
                f"Expenses for '{unsupported}' are not covered under the current travel expense policy."
            )

        # If neither category nor unsupported topic was recognized:
        if not intent.detected_categories:
            return (
                CoverageVerdict.OUT_OF_SCOPE,
                [],
                "The question does not match any recognized travel expense category (Meals, Hotel, Taxi, Airfare, Incidentals)."
            )

        # If only 1 category and no unsupported topics, evaluate directly
        if len(intent.detected_categories) == 1 and not intent.unsupported_topics:
            return self._search_single_category(
                intent.detected_categories[0],
                intent.detected_region,
                intent.flight_duration_hours,
                intent.raw_query
            )

        # Multiple categories and/or combination with unsupported topics
        combined_records: List[PolicyRecord] = []
        covered_notes: List[str] = []
        uncovered_notes: List[str] = []
        partially_covered_notes: List[str] = []

        for u in intent.unsupported_topics:
            uncovered_notes.append(f"Expenses for '{u}' are not covered under the policy.")

        for cat in intent.detected_categories:
            verdict, records, note = self._search_single_category(
                cat, intent.detected_region, intent.flight_duration_hours, intent.raw_query
            )
            if verdict == CoverageVerdict.COVERED:
                combined_records.extend(records)
                covered_notes.append(note)
            elif verdict == CoverageVerdict.PARTIALLY_COVERED:
                combined_records.extend(records)
                partially_covered_notes.append(note)
            else:
                uncovered_notes.append(note)

        # Determine overall status
        if combined_records and not uncovered_notes and not partially_covered_notes:
            return CoverageVerdict.COVERED, combined_records, " ".join(covered_notes)

        if combined_records and (uncovered_notes or partially_covered_notes):
            diag_parts = []
            if covered_notes:
                diag_parts.append(" ".join(covered_notes))
            if partially_covered_notes:
                diag_parts.append(" ".join(partially_covered_notes))
            if uncovered_notes:
                diag_parts.append("Out of policy notes: " + " ".join(uncovered_notes))
            return CoverageVerdict.PARTIALLY_COVERED, combined_records, " | ".join(diag_parts)

        return CoverageVerdict.OUT_OF_SCOPE, [], " ".join(uncovered_notes) if uncovered_notes else "Not covered under travel expense policy."
