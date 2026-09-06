from abc import ABC, abstractmethod
from typing import List

from src.policy_agent.schemas import CoverageVerdict, ExtractedIntent, PolicyRecord


class BasePolicyProvider(ABC):
    """Abstract base class for policy answer generation providers."""

    @abstractmethod
    def generate_response(
        self,
        query: str,
        intent: ExtractedIntent,
        verdict: CoverageVerdict,
        matched_records: List[PolicyRecord],
        diagnostic_note: str
    ) -> str:
        """
        Generate a strictly grounded natural language response.
        
        Args:
            query: User's raw question.
            intent: Extracted category, region, and duration.
            verdict: Policy coverage verdict (COVERED, PARTIALLY_COVERED, OUT_OF_SCOPE).
            matched_records: Filtered, relevant policy items.
            diagnostic_note: Diagnostic reasoning from the policy index.
        """
        pass
