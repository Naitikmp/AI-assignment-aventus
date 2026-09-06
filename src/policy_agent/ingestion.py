import csv
import logging
from pathlib import Path
from typing import List, Optional, Tuple

from src.policy_agent.schemas import PolicyRecord

logger = logging.getLogger(__name__)


class IngestionStats:
    def __init__(self):
        self.total_rows_read: int = 0
        self.duplicates_removed: int = 0
        self.records_loaded: int = 0

    def __repr__(self) -> str:
        return (
            f"IngestionStats(read={self.total_rows_read}, "
            f"duplicates_removed={self.duplicates_removed}, "
            f"loaded={self.records_loaded})"
        )


class PolicyLoader:
    """
    Ingests and sanitizes corporate policy data from CSV or tabular sources.
    Implements business identity deduplication and schema validation.
    """

    @staticmethod
    def _parse_float(value: Optional[str]) -> Optional[float]:
        if not value or not value.strip():
            return None
        try:
            return float(value.strip().replace("$", "").replace(",", ""))
        except ValueError:
            return None

    @classmethod
    def load_from_csv(cls, file_path: str | Path) -> Tuple[List[PolicyRecord], IngestionStats]:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Policy data file not found at: {path}")

        stats = IngestionStats()
        records: List[PolicyRecord] = []
        seen_business_keys = set()

        with open(path, mode="r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            # Normalize column names: strip whitespace and lowercase
            if reader.fieldnames:
                reader.fieldnames = [fn.strip().lower() for fn in reader.fieldnames]

            for line_idx, row in enumerate(reader, start=2):  # start=2 because line 1 is header
                stats.total_rows_read += 1

                raw_cat = row.get("category", "").strip()
                raw_region = row.get("region", "").strip()
                raw_limit = row.get("daily_limit_usd", "").strip()
                raw_currency = row.get("currency", "USD").strip().upper() or "USD"
                raw_notes = row.get("notes", "").strip()

                if not raw_cat or not raw_region:
                    continue  # Skip empty or corrupted lines

                parsed_limit = cls._parse_float(raw_limit)

                # Deduplication logic:
                # 1. Catch explicit duplicate marker in notes (e.g. Row 14: "(duplicate of row 1...)")
                # 2. For category + region with fixed monetary limits (Meals, Hotel),
                #    multiple identical entries for the same region represent a collision.
                # For non-limit rules (e.g. Airfare), differentiate by specific condition keywords.
                is_explicit_dup = "duplicate" in raw_notes.lower()
                
                if parsed_limit is not None:
                    business_key = (raw_cat.lower(), raw_region.lower(), parsed_limit, raw_currency)
                else:
                    # When limit is None (like Airfare or Taxi), use core condition descriptor
                    condition_signature = "under_6" if "under 6" in raw_notes.lower() else (
                        "over_6" if "over 6" in raw_notes.lower() else raw_notes.lower()
                    )
                    business_key = (raw_cat.lower(), raw_region.lower(), condition_signature, raw_currency)

                if is_explicit_dup or business_key in seen_business_keys:
                    stats.duplicates_removed += 1
                    logger.debug(f"Deduplicated duplicate policy row {line_idx}: {raw_cat} - {raw_region}")
                    continue

                seen_business_keys.add(business_key)

                record = PolicyRecord(
                    category=raw_cat,
                    region=raw_region,
                    daily_limit_usd=parsed_limit,
                    currency=raw_currency,
                    notes=raw_notes,
                    source_row=line_idx
                )
                records.append(record)

        stats.records_loaded = len(records)
        return records, stats
