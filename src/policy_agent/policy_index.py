import re
from typing import List, Tuple

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

        # 1. Resolve Category
        detected_category = None
        for cat, synonyms in self.CATEGORY_SYNONYMS.items():
            for syn in synonyms:
                pattern = rf"\b{re.escape(syn)}\b"
                if re.search(pattern, q_lower):
                    detected_category = cat
                    break
            if detected_category:
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
        is_airfare = detected_category == "Airfare" or any(
            re.search(rf"\b{re.escape(term)}\b", q_lower) for term in ["flight", "flights", "airfare", "fly", "flying"]
        )
        if is_airfare:
            detected_category = "Airfare"
            # Support "8 hour", "8-hour", "8 hrs", "8-hrs", "8hours"
            hour_match = re.search(r"(\d+(?:\.\d+)?)\s*[-\s]?\s*(?:hours?|hrs?)", q_lower)
            if hour_match:
                try:
                    flight_hours = float(hour_match.group(1))
                except ValueError:
                    pass

        is_asking_limit = any(term in q_lower for term in ["limit", "allowance", "max", "maximum", "how much", "rate", "cost"])
        is_asking_receipts = any(term in q_lower for term in ["receipt", "receipts", "actuals", "tip", "tips", "proof"])

        return ExtractedIntent(
            raw_query=query,
            detected_category=detected_category,
            detected_region=detected_region,
            flight_duration_hours=flight_hours,
            is_airfare=is_airfare,
            is_asking_limit=is_asking_limit,
            is_asking_receipts=is_asking_receipts
        )

    def search(self, intent: ExtractedIntent) -> Tuple[CoverageVerdict, List[PolicyRecord], str]:
        q_lower = intent.raw_query.lower()

        # Check for explicit unsupported expense categories
        for unsupported in self.KNOWN_OUT_OF_SCOPE_TOPICS:
            if re.search(rf"\b{re.escape(unsupported)}\b", q_lower):
                return (
                    CoverageVerdict.OUT_OF_SCOPE,
                    [],
                    f"Expenses for '{unsupported}' are not covered under the current travel expense policy."
                )

        # If no category detected
        if not intent.detected_category:
            return (
                CoverageVerdict.OUT_OF_SCOPE,
                [],
                "The question does not match any recognized travel expense category (Meals, Hotel, Taxi, Airfare, Incidentals)."
            )

        cat = intent.detected_category

        # Case 1: Airfare (Global category)
        if cat == "Airfare":
            airfare_records = [r for r in self.records if r.category == "Airfare"]
            if intent.flight_duration_hours is not None:
                if intent.flight_duration_hours < 6.0:
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
        region = intent.detected_region

        # Detect if an unlisted destination was mentioned using prepositions ("in <place>", "to <place>", "for <place>")
        if not region:
            unlisted_match = re.search(r"\b(?:in|for|to|at)\s+([a-zA-Z\s]+?)(?:\?|$|\.|\,)", intent.raw_query, re.IGNORECASE)
            if unlisted_match:
                potential_place = unlisted_match.group(1).strip()
                # Filter out generic words
                generic_words = {"london", "hotel", "hotels", "meals", "food", "taxi", "business", "standard", "days", "day", "night"}
                if potential_place.lower() not in generic_words and len(potential_place) > 2:
                    return (
                        CoverageVerdict.OUT_OF_SCOPE,
                        [],
                        f"Region '{potential_place}' is not covered under the company travel expense policy. Covered regions are: United Kingdom, United States, United Arab Emirates, and India."
                    )

            # Did user ask generically for a category across all regions?
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

        # Category is known, but NOT for this region! (e.g. Taxi in UAE, Meals in Germany)
        available_regions = [r.region for r in self.records if r.category == cat and r.region != "Global"]
        regions_str = ", ".join(sorted(set(available_regions))) if available_regions else "None"
        
        return (
            CoverageVerdict.OUT_OF_SCOPE,
            [],
            f"The policy covers {cat} only for: {regions_str}. Expenses for {cat} in '{region}' are not covered."
        )
