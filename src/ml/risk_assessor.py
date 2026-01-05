"""
Risk Assessor: Score legal clause risk level (low/medium/high).
Uses keyword patterns + clause type heuristics.
"""

import logging
import re
from typing import Dict

logger = logging.getLogger(__name__)


class RiskAssessor:
    """Assess risk level of legal clauses."""

    # High risk keywords (3 points each)
    HIGH_RISK_KEYWORDS = [
        r"\bpenalty\b", r"\bliability\b", r"\bindemnif(?:y|ication)\b",
        r"\bbreach\b", r"\bterminat(?:e|ion)\b", r"\bwaive\b",
        r"\bunlimited\b", r"\bdamage(?:s)?\b", r"\bforfeiture\b",
        r"\bdefault\b", r"\bsever(?:able|ance)\b",
    ]

    # Medium risk keywords (2 points each)
    MEDIUM_RISK_KEYWORDS = [
        r"\bshall\b", r"\bmust\b", r"\bobligat(?:ed|ion)\b",
        r"\bwithin\s+\d+\s+days\b", r"\brequired to\b",
        r"\bcontingent\b", r"\bconditional\b", r"\bprovided that\b",
        r"\brestrict(?:ion|ed)?\b", r"\bprohibit(?:ed)?\b",
    ]

    # Low risk keywords (-1 point each, reduces score)
    LOW_RISK_KEYWORDS = [
        r"\bdefinition\b", r"\bmeans\b", r"\bfor clarity\b",
        r"\bas follows\b", r"\bbackground\b", r"\brecital\b",
        r"\badministrative\b", r"\binformational\b",
    ]

    # Risk by clause type
    TYPE_RISK_SCORES = {
        "liability": 3,
        "termination": 3,
        "payment_obligation": 2,
        "warranty": 2,
        "confidentiality": 2,
        "condition": 2,
        "general_obligation": 1,
        "definition": 0,
        "general": 1,
    }

    @classmethod
    def assess_risk(cls, clause_text: str, clause_type: str, entities: Dict) -> str:
        """
        Assess risk level for a clause.
        Returns: "low", "medium", or "high"
        """
        if not clause_text:
            return "low"

        score = 0
        text_lower = clause_text.lower()

        # Score keywords
        for pattern in cls.HIGH_RISK_KEYWORDS:
            if re.search(pattern, text_lower):
                score += 3

        for pattern in cls.MEDIUM_RISK_KEYWORDS:
            if re.search(pattern, text_lower):
                score += 2

        for pattern in cls.LOW_RISK_KEYWORDS:
            if re.search(pattern, text_lower):
                score -= 1

        # Score by type
        score += cls.TYPE_RISK_SCORES.get(clause_type, 0)

        # Additional scoring from entities
        if entities.get("amount"):
            score += 1  # Money = risk
        if entities.get("deadline"):
            score += 1  # Time-sensitive = risk
        if entities.get("conditions"):
            score += 1  # Conditional = risk

        # Thresholds
        if score >= 6:
            return "high"
        elif score >= 3:
            return "medium"
        else:
            return "low"
