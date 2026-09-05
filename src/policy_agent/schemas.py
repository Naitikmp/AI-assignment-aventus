from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field


class CoverageVerdict(str, Enum):
    """Status indicating whether the query is covered by corporate policy."""
    COVERED = "COVERED"
    PARTIALLY_COVERED = "PARTIALLY_COVERED"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"


class PolicyRecord(BaseModel):
    """Validated representation of an individual travel policy record."""
    category: str = Field(description="Policy expense category, e.g., Meals, Hotel, Taxi, Airfare, Incidentals")
    region: str = Field(description="Applicable geographical region or 'Global'")
    daily_limit_usd: Optional[float] = Field(default=None, description="Maximum daily reimbursement limit in USD, if applicable")
    currency: str = Field(default="USD", description="Currency of reimbursement")
    notes: str = Field(default="", description="Policy restrictions, conditions, or guidelines")
    source_row: int = Field(default=0, description="1-indexed row number in the source data file")

    @property
    def has_monetary_limit(self) -> bool:
        return self.daily_limit_usd is not None

    def citation_label(self) -> str:
        limit_str = f"${self.daily_limit_usd:.2f} {self.currency}" if self.daily_limit_usd is not None else "Actuals / Rule-governed"
        return f"[Row {self.source_row}] {self.category} ({self.region}): {limit_str} — {self.notes}"


class ExtractedIntent(BaseModel):
    """Structured query analysis extracted from the user prompt."""
    raw_query: str
    detected_category: Optional[str] = None
    detected_region: Optional[str] = None
    flight_duration_hours: Optional[float] = None
    is_airfare: bool = False
    is_asking_limit: bool = False
    is_asking_receipts: bool = False


class AgentResponse(BaseModel):
    """Standardized response schema returned by the policy assistant."""
    query: str
    verdict: CoverageVerdict
    answer: str
    citations: List[str] = Field(default_factory=list)
    matched_records: List[PolicyRecord] = Field(default_factory=list)
    provider_used: str = "local"
