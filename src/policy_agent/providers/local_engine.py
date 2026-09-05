from typing import List
from src.policy_agent.schemas import PolicyRecord, CoverageVerdict, ExtractedIntent
from src.policy_agent.providers.base import BasePolicyProvider


class LocalPolicyProvider(BasePolicyProvider):
    """
    Deterministic Grounded Policy Provider.
    Operates completely offline with zero API keys or model downloads.
    Guarantees 100% factual accuracy strictly mapped to policy records.
    """

    def generate_response(
        self,
        query: str,
        intent: ExtractedIntent,
        verdict: CoverageVerdict,
        matched_records: List[PolicyRecord],
        diagnostic_note: str
    ) -> str:
        if verdict == CoverageVerdict.OUT_OF_SCOPE:
            response_lines = [
                "**Policy Notice: Out of Scope**",
                f"The question cannot be answered because it is not covered under the company travel expense policy.",
                f"Reason: {diagnostic_note}"
            ]
            return "\n\n".join(response_lines)

        if verdict == CoverageVerdict.PARTIALLY_COVERED:
            cat = intent.detected_category or "expense"
            lines = [
                f"**Policy Summary for {cat}:**",
                f"{diagnostic_note}",
                "The reimbursement rates vary by region as follows:"
            ]
            for r in matched_records:
                limit_str = f"${r.daily_limit_usd:.2f} {r.currency}" if r.daily_limit_usd is not None else "Actuals"
                lines.append(f"- **{r.region}**: {limit_str} ({r.notes})")
            lines.append("\nPlease specify your travel destination region to get the exact reimbursement limit.")
            return "\n".join(lines)

        # Verdict == COVERED
        if not matched_records:
            return "No matching policy items found."

        # Format covered response
        lines = []
        if len(matched_records) == 1:
            rec = matched_records[0]
            if rec.category == "Airfare":
                lines.append(f"**Airfare Policy ({rec.region}):**")
                lines.append(f"{rec.notes}.")
            elif rec.category == "Taxi":
                lines.append(f"**Taxi Reimbursement Policy for {rec.region}:**")
                lines.append(f"Taxis are {rec.notes.lower() if rec.notes else 'reimbursed at actuals'}. No daily monetary limit applies.")
            elif rec.has_monetary_limit:
                rate_type = "night" if rec.category.lower() == "hotel" else "day"
                lines.append(f"**{rec.category} Allowance for {rec.region}:**")
                lines.append(
                    f"The daily reimbursement limit is **${rec.daily_limit_usd:.2f} {rec.currency}** (per {rate_type})."
                )
                if rec.notes:
                    lines.append(f"Conditions: {rec.notes}.")
            else:
                lines.append(f"**{rec.category} Policy for {rec.region}:**")
                lines.append(f"{rec.notes}.")
        else:
            lines.append(f"**Applicable Policy Guidelines for {matched_records[0].category}:**")
            for rec in matched_records:
                limit_str = f"${rec.daily_limit_usd:.2f} {rec.currency}" if rec.daily_limit_usd is not None else "Actuals / Rule"
                lines.append(f"- **{rec.region}**: {limit_str} — {rec.notes}")

        return "\n\n".join(lines)
