"""
Entity Extractor: Extract structured entities from legal clauses.
Focuses on: parties, amounts, deadlines, conditions, numerics.
"""

import logging
import re
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class EntityExtractor:
    """Extract key entities from legal text."""

    # Party keywords (legal roles)
    PARTY_KEYWORDS = [
        "buyer", "seller", "purchaser", "vendor", "lessor", "lessee",
        "customer", "client", "contractor", "subcontractor", "employer",
        "employee", "licensor", "licensee", "borrower", "lender",
        "party", "parties", "provider", "recipient",
    ]

    # Currency patterns
    CURRENCY_PATTERNS = [
        r"\$\s?\d[\d,]*(?:\.\d{2})?",  # $1000, $1,000.00
        r"\d[\d,]*(?:\.\d{2})?\s?(?:USD|EUR|GBP|INR)",  # 1000 USD
        r"(?:USD|EUR|GBP|INR)\s?\d[\d,]*(?:\.\d{2})?",  # USD 1000
    ]

    # Time/deadline patterns
    TIME_PATTERNS = [
        r"\d+\s+(?:day|week|month|year)s?",  # 30 days
        r"within\s+\d+\s+(?:day|week|month|year)s?",  # within 30 days
        r"before\s+\d+\s+(?:day|week|month|year)s?",  # before 30 days
        r"(?:by|on|before)\s+\w+\s+\d{1,2},?\s+\d{4}",  # by Jan 1, 2024
    ]

    # Condition keywords
    CONDITION_KEYWORDS = [
        "if", "unless", "provided that", "except that", "subject to",
        "contingent", "conditional", "in the event", "should",
    ]

    @classmethod
    def extract_entities(cls, clause_text: str) -> Dict[str, Any]:
        """
        Extract entities from a single clause.
        Returns dict with: party_1, party_2, amount, deadline, conditions, numerics
        """
        if not clause_text:
            return {}

        entities = {
            "party_1": None,
            "party_2": None,
            "amount": None,
            "deadline": None,
            "conditions": False,
            "numerics": [],
        }

        text_lower = clause_text.lower()

        # Extract parties
        parties = cls._extract_parties(clause_text)
        if len(parties) >= 1:
            entities["party_1"] = parties[0]
        if len(parties) >= 2:
            entities["party_2"] = parties[1]

        # Extract amounts
        amounts = cls._extract_amounts(clause_text)
        if amounts:
            entities["amount"] = amounts[0]  # Take first

        # Extract deadlines
        deadlines = cls._extract_deadlines(clause_text)
        if deadlines:
            entities["deadline"] = deadlines[0]  # Take first

        # Check for conditions
        entities["conditions"] = any(kw in text_lower for kw in cls.CONDITION_KEYWORDS)

        # Extract numerics (all numbers)
        numerics = re.findall(r"\b\d+\b", clause_text)
        entities["numerics"] = numerics[:5]  # Max 5

        return entities

    @classmethod
    def _extract_parties(cls, text: str) -> List[str]:
        """Extract legal parties (buyer, seller, etc.) from text."""
        found = []
        text_lower = text.lower()

        for keyword in cls.PARTY_KEYWORDS:
            # Look for "the buyer", "Buyer", etc.
            pattern = r"\b(?:the\s+)?" + keyword + r"\b"
            if re.search(pattern, text_lower):
                found.append(keyword)

        return found

    @classmethod
    def _extract_amounts(cls, text: str) -> List[str]:
        """Extract currency amounts."""
        amounts = []
        for pattern in cls.CURRENCY_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            amounts.extend(matches)
        return amounts

    @classmethod
    def _extract_deadlines(cls, text: str) -> List[str]:
        """Extract time/deadline expressions."""
        deadlines = []
        for pattern in cls.TIME_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            deadlines.extend(matches)
        return deadlines
