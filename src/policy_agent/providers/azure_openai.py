import logging
from typing import List
from src.policy_agent.schemas import PolicyRecord, CoverageVerdict, ExtractedIntent
from src.policy_agent.providers.base import BasePolicyProvider
from src.policy_agent.config import AgentConfig

logger = logging.getLogger(__name__)


class AzureOpenAIProvider(BasePolicyProvider):
    """
    Azure OpenAI Service provider (enterprise Azure AI Foundry stack).
    """

    def __init__(self):
        try:
            from openai import AzureOpenAI
            if not AgentConfig.AZURE_OPENAI_API_KEY or not AgentConfig.AZURE_OPENAI_ENDPOINT:
                raise ValueError("AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT must be set.")
            self.client = AzureOpenAI(
                api_key=AgentConfig.AZURE_OPENAI_API_KEY,
                azure_endpoint=AgentConfig.AZURE_OPENAI_ENDPOINT,
                api_version=AgentConfig.AZURE_OPENAI_API_VERSION
            )
            self.deployment = AgentConfig.AZURE_OPENAI_DEPLOYMENT_NAME
        except ImportError:
            raise ImportError("openai package is required for AzureOpenAIProvider. Run 'pip install openai'.")

    def generate_response(
        self,
        query: str,
        intent: ExtractedIntent,
        verdict: CoverageVerdict,
        matched_records: List[PolicyRecord],
        diagnostic_note: str
    ) -> str:
        if verdict == CoverageVerdict.OUT_OF_SCOPE:
            return (
                f"**Policy Notice: Out of Scope**\n\n"
                f"The question cannot be answered because it is not covered under the company travel expense policy.\n"
                f"Reason: {diagnostic_note}"
            )

        context_blocks = "\n".join([f"- {r.citation_label()}" for r in matched_records])
        system_prompt = (
            "You are a strict, helpful corporate travel expense assistant for an enterprise investment group. "
            "Your answers must be 100% grounded in the provided policy records. "
            "Never invent, assume, or extrapolate limits, rules, or covered regions. "
            "If the information is not explicitly present in the context, refuse to speculate. "
            "Always state the exact numerical limit, currency, conditions, and applicable region."
        )

        user_content = (
            f"Employee Question: {query}\n\n"
            f"Coverage Status: {verdict.value}\n"
            f"Diagnostic Finding: {diagnostic_note}\n\n"
            f"Ground Truth Policy Records:\n{context_blocks}\n\n"
            "Synthesize a clear, authoritative response based strictly on the above records."
        )

        try:
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.0
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"Azure OpenAI call failed: {e}. Falling back to deterministic output.")
            from src.policy_agent.providers.local_engine import LocalPolicyProvider
            return LocalPolicyProvider().generate_response(query, intent, verdict, matched_records, diagnostic_note)
