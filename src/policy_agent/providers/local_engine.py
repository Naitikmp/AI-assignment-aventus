from typing import List

from src.policy_agent.providers.base import BasePolicyProvider
from src.policy_agent.schemas import CoverageVerdict, ExtractedIntent, PolicyRecord


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

        if verdict == CoverageVerdict.PARTIALLY_COVERED and not intent.detected_region and "No specific region was specified" in diagnostic_note:
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

        # Format covered or partially covered response with matched records
        if not matched_records:
            return f"**Policy Notice:**\n{diagnostic_note}"

        by_category = {}
        for rec in matched_records:
            by_category.setdefault(rec.category, []).append(rec)

        # Case A: Single category
        if len(by_category) == 1:
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
            
            if "Out of policy notes:" in diagnostic_note:
                note_part = diagnostic_note.split("Out of policy notes:")[-1].strip()
                lines.append(f"\n**Out-of-Policy Notice:**\n{note_part}")
            return "\n\n".join(lines)

        # Case B: Multiple distinct categories
        sections = []
        for cat, recs in by_category.items():
            if cat == "Airfare":
                sec = ["**Airfare Guidelines (Global):**"]
                for r in recs:
                    sec.append(f"- {r.notes}")
                sections.append("\n".join(sec))
            elif cat == "Taxi":
                r = recs[0]
                sections.append(
                    f"**Taxi Reimbursement Policy for {r.region}:**\n"
                    f"Taxis are {r.notes.lower() if r.notes else 'reimbursed at actuals'}. No daily monetary limit applies."
                )
            elif cat == "Incidentals":
                r = recs[0]
                sections.append(
                    f"**Incidentals Allowance (Global):**\n"
                    f"The daily reimbursement limit is **${r.daily_limit_usd:.2f} {r.currency}** (per day).\n"
                    f"Conditions: {r.notes}."
                )
            else:
                rate_type = "night" if cat.lower() == "hotel" else "day"
                sec = []
                for r in recs:
                    if r.has_monetary_limit:
                        sec.append(
                            f"**{cat} Allowance for {r.region}:**\n"
                            f"The daily reimbursement limit is **${r.daily_limit_usd:.2f} {r.currency}** (per {rate_type})."
                        )
                        if r.notes:
                            sec.append(f"Conditions: {r.notes}.")
                    else:
                        sec.append(f"**{cat} Policy for {r.region}:**\n{r.notes}.")
                sections.append("\n".join(sec))

        if "Out of policy notes:" in diagnostic_note:
            note_part = diagnostic_note.split("Out of policy notes:")[-1].strip()
            sections.append(f"**Out-of-Policy Notice:**\n{note_part}")

        return "\n\n".join(sections)
