"""
Prompt templates for legal document simplification and explanation.
"""

from typing import Optional


def build_clause_explanation_prompt(
    clause_text: str,
    clause_type: Optional[str] = None,
) -> str:
    """
    Build prompt for BART summarization (not instruction-following).
    
    BART works better with direct text to summarize rather than complex
    instructions. We format the clause with section headers so the model
    can generate a structured summary.
    """
    type_hint = f"[{clause_type.upper()}]" if clause_type else "[LEGAL CLAUSE]"
    
    # Format that BART can summarize naturally
    prompt = f"""{type_hint}

ORIGINAL CLAUSE:
{clause_text}

PLAIN ENGLISH EXPLANATION:
This clause means:"""

    return prompt
