from pathlib import Path
from typing import Optional, List
from src.policy_agent.schemas import AgentResponse, PolicyRecord, CoverageVerdict
from src.policy_agent.ingestion import PolicyLoader, IngestionStats
from src.policy_agent.policy_index import PolicyIndex
from src.policy_agent.providers.factory import ProviderFactory
from src.policy_agent.providers.base import BasePolicyProvider
from src.policy_agent.config import AgentConfig


class PolicyAssistant:
    """
    High-level orchestrator for corporate travel policy queries.
    Encapsulates ingestion, indexing, guardrail validation, and response synthesis.
    """

    def __init__(self, data_path: Optional[str | Path] = None, provider_name: Optional[str] = None):
        self.data_path = Path(data_path or AgentConfig.DATA_PATH)
        self.records, self.stats = PolicyLoader.load_from_csv(self.data_path)
        self.index = PolicyIndex(self.records)
        self.provider, self.provider_name = ProviderFactory.create(provider_name)

    def ask(self, query: str) -> AgentResponse:
        """
        Execute full conversational workflow:
        1. Extract query intent (category, region, constraints).
        2. Evaluate policy coverage & apply guardrails.
        3. Synthesize response using the active provider.
        4. Compile verifiable audit citations.
        """
        query_clean = query.strip()
        if not query_clean:
            return AgentResponse(
                query=query,
                verdict=CoverageVerdict.OUT_OF_SCOPE,
                answer="No question was provided. Please ask a question regarding corporate travel expenses.",
                citations=[],
                matched_records=[],
                provider_used=self.provider_name
            )

        intent = self.index.parse_intent(query_clean)
        verdict, matched_records, diagnostic_note = self.index.search(intent)

        # Generate grounded response
        answer_text = self.provider.generate_response(
            query=query_clean,
            intent=intent,
            verdict=verdict,
            matched_records=matched_records,
            diagnostic_note=diagnostic_note
        )

        citations = [rec.citation_label() for rec in matched_records]

        return AgentResponse(
            query=query_clean,
            verdict=verdict,
            answer=answer_text,
            citations=citations,
            matched_records=matched_records,
            provider_used=self.provider_name
        )
