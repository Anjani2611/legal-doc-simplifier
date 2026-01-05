"""
Clause Extractor: Segments legal text into semantic clause units.
Uses rule-based heuristics (markers, numbering, sentence boundaries).
"""

import logging
import re
from typing import List, Dict

logger = logging.getLogger(__name__)


class ClauseExtractor:
    """Extract and classify clauses from legal text."""

    # Clause boundary markers
    CLAUSE_MARKERS = [
        r"(?:^|\n)\s*(?:clause|section|article|paragraph)\s+\d+",
        r"(?:^|\n)\s*\d+\.\s+[A-Z]",
        r"(?:^|\n)\s*\([a-z]\)\s+",
        r"(?:^|\n)\s*\(i+\)\s+",
        r"\bprovided that\b",
        r"\bexcept that\b",
        r"\bnotwithstanding\b",
    ]

    # Clause type patterns (keyword-based inference)
    TYPE_PATTERNS = {
        "payment_obligation": [
            r"\bpay(?:ment|able|s)?\b",
            r"\b(?:invoice|fee|charge|price|cost|amount)\b",
            r"\b(?:compensat|remunerat)\w+\b",
        ],
        "liability": [
            r"\bliab(?:le|ility)\b",
            r"\bindemnif(?:y|ication)\b",
            r"\b(?:damage|loss)(?:es)?\b",
            r"\b(?:liable|responsible) for\b",
        ],
        "termination": [
            r"\bterminat(?:e|ion)\b",
            r"\b(?:cancel|cancellation)\b",
            r"\b(?:expire|expiration)\b",
            r"\bend this (?:agreement|contract)\b",
        ],
        "confidentiality": [
            r"\bconfidential(?:ity)?\b",
            r"\b(?:non-disclosure|nda)\b",
            r"\b(?:secret|proprietary)\b",
        ],
        "warranty": [
            r"\bwarrant(?:y|ies)\b",
            r"\bguarantee\b",
            r"\b(?:represent|representation)\b",
        ],
        "condition": [
            r"\bif\b",
            r"\bunless\b",
            r"\bsubject to\b",
            r"\bcontingent upon\b",
        ],
        "definition": [
            r"\bmeans\b",
            r"\bdefined as\b",
            r"\brefers to\b",
            r"\bfor purposes of\b",
        ],
        "general_obligation": [
            r"\bshall\b",
            r"\bmust\b",
            r"\brequired to\b",
            r"\bobligat(?:ed|ion)\b",
        ],
    }

    @classmethod
    def extract_clauses(cls, text: str) -> List[Dict]:
        """
        Extract clauses from legal text.
        Returns: List[Dict] with keys: id, original_text, type
        """
        if not text or not text.strip():
            return []

        text = text.strip()

        # Split into clause segments
        segments = cls._split_text(text)

        clauses = []
        for idx, segment_text in enumerate(segments, start=1):
            if not segment_text.strip():
                continue

            clause_type = cls._infer_type(segment_text)

            clauses.append({
                "id": f"clause_{idx}",
                "original_text": segment_text.strip(),
                "type": clause_type,
            })

        logger.info(f"Extracted {len(clauses)} clauses from {len(text)} chars")
        return clauses

    @classmethod
    def _split_text(cls, text: str) -> List[str]:
        """
        Split text into clause segments using markers + heuristics.
        """
        # Strategy: look for explicit markers, numbered/lettered lists, sentence breaks
        segments = []

        # First try: split by numbered sections (1., 2., etc.)
        numbered = re.split(r"(?:^|\n)\s*(\d+\.)\s+", text, flags=re.MULTILINE)
        if len(numbered) > 3:  # Looks like numbered sections
            current = ""
            for i, part in enumerate(numbered):
                if re.match(r"^\d+\.$", part.strip()):
                    if current:
                        segments.append(current)
                    current = part + " "
                else:
                    current += part
            if current:
                segments.append(current)
            return segments

        # Second try: split by sentence boundaries with clause markers
        sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z])", text)
        current_clause = ""
        for sent in sentences:
            current_clause += sent + " "
            # Check if this sentence ends a clause (has a strong boundary marker)
            if any(re.search(marker, sent, re.IGNORECASE) for marker in ["provided that", "except that"]):
                segments.append(current_clause.strip())
                current_clause = ""

        if current_clause.strip():
            segments.append(current_clause.strip())

        # Fallback: if no clear splits, treat whole text as one clause
        if not segments:
            segments = [text]

        return segments

    @classmethod
    def _infer_type(cls, text: str) -> str:
        """
        Infer clause type from content using keyword patterns.
        Returns best match or "general" if no match.
        """
        text_lower = text.lower()

        # Score each type
        scores = {}
        for clause_type, patterns in cls.TYPE_PATTERNS.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    score += 1
            if score > 0:
                scores[clause_type] = score

        if not scores:
            return "general"

        # Return type with highest score
        return max(scores, key=scores.get)
