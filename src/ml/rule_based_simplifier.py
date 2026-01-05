"""
Rule-based simplification for legal text.

This module applies deterministic lexical substitutions, sentence splitting,
and redundancy removal to legal clauses. It operates on model-generated
explanations to enforce plain-language constraints without relying solely
on neural outputs.
"""

import re
from typing import Dict, Any


class RuleBasedSimplifier:
    """
    Applies rule-based simplification operations to legal text.
    
    Operations:
      - Lexical substitution (legalese → plain English)
      - Sentence splitting for overly long sentences
      - Redundant phrase removal
      - Preserve critical legal entities (amounts, dates, parties)
    """

    # Legalese → Plain English mapping
    # Based on legal text simplification research
    LEXICAL_SUBSTITUTIONS = {
        # Common doublets and triplets (redundant legal phrases)
        r'\b(null and void|void and of no effect)\b': 'void',
        r'\b(cease and desist)\b': 'stop',
        r'\b(give and grant)\b': 'give',
        r'\b(final and conclusive)\b': 'final',
        r'\b(force and effect)\b': 'effect',
        r'\b(terms and conditions)\b': 'terms',
        r'\b(by and between)\b': 'between',
        r'\b(made and entered into)\b': 'entered',
        r'\b(due and payable)\b': 'due',
        r'\b(sole and exclusive)\b': 'sole',
        r'\b(right, title,? and interest)\b': 'rights',
        r'\b(authorize and empower)\b': 'authorize',
        r'\b(false and bogus)\b': 'false',
        r'\b(fabricated,? concocted,? and without any basis)\b': 'fabricated',
        r'\b(fabricated and concocted)\b': 'fabricated',
        r'\b(ready and willing)\b': 'willing',
        
        # Archaic and formal terms
        r'\bhereby\b': '',
        r'\bherein\b': 'in this document',
        r'\bhereinafter\b': 'later in this document',
        r'\bhereof\b': 'of this',
        r'\bheretofore\b': 'previously',
        r'\bhereunder\b': 'under this agreement',
        r'\bherewith\b': 'with this',
        r'\btherein\b': 'in that',
        r'\bthereof\b': 'of that',
        r'\bthereunder\b': 'under that',
        r'\bwherein\b': 'where',
        r'\bwhereby\b': 'by which',
        r'\bwhereas\b': 'since',
        r'\baforesaid\b': 'mentioned above',
        r'\bforthwith\b': 'immediately',
        r'\btherefor\b': 'for that',
        
        # Complex verbs
        r'\bcommence\b': 'start',
        r'\bterminate\b': 'end',
        r'\bconstitute\b': 'is',
        r'\bprovide that\b': 'if',
        r'\bin the event that\b': 'if',
        r'\bin the event of\b': 'if',
        r'\bprovided that\b': 'except',
        r'\bprovided,? however,?\b': 'except',
        r'\bsubject to\b': 'depending on',
        r'\bpursuant to\b': 'under',
        r'\bin accordance with\b': 'following',
        r'\bwith respect to\b': 'about',
        r'\bin connection with\b': 'relating to',
        r'\bprior to\b': 'before',
        r'\bsubsequent to\b': 'after',
        r'\bshall have no obligation\b': 'does not need',
        r'\bshall not\b': 'must not',
        r'\bshall\b': 'must',
        r'\bmay not\b': 'cannot',
        
        # Legal nouns
        r'\bindemnification\b': 'compensation',
        r'\bindemnify\b': 'compensate',
        r'\bremuneration\b': 'payment',
        r'\bobligation\b': 'duty',
        r'\bliability\b': 'responsibility',
        r'\bliabilities\b': 'responsibilities',
        r'\bjurisdiction\b': 'authority',
        r'\bconsideration\b': 'payment',
        r'\bcovenants and agrees\b': 'agrees',
        
        # Wordy phrases - FIXED: preserve grammar
        r'\bduring such time as\b': 'while',
        r'\bat such time as\b': 'when',
        r'\bfor the reason that\b': 'because',
        r'\bfor the purpose of\b': 'for',  # Changed from 'to' to preserve grammar
        r'\bin order to\b': 'to',
        r'\bby means of\b': 'by',
        r'\bby virtue of\b': 'because of',
        r'\bnotwithstanding the fact that\b': 'although',
        r'\bto the extent that\b': 'if',
        r'\barising out of or in connection with\b': 'arising from',
    }

    # Phrases that should be completely removed (no replacement)
    REMOVE_PHRASES = [
        r'\bvery\s+',
        r'\bquite\s+',
        r'\bsomewhat\s+',
        r'\bat all\b',
        r'\bin any manner\b',
        r'\bof any kind\b',
        r'\bwhatsoever\b',
        r'\bwithout limitation\b',
        r'\bincluding without limitation\b',
        r'\bincluding,? without limitation,?\b',
        r'\bany and all\b',
    ]

    MAX_SENTENCE_LENGTH_WORDS = 35  # Split sentences longer than this

    @classmethod
    def simplify(
        cls,
        text: str,
        preserve_structure: bool = True,
        aggressive: bool = False
    ) -> str:
        """
        Apply rule-based simplification to text.

        Args:
            text: Input text (typically model-generated explanation)
            preserve_structure: Keep paragraph breaks and formatting
            aggressive: Apply more aggressive simplification (may remove more info)

        Returns:
            Simplified text
        """
        if not text or not text.strip():
            return text

        simplified = text.strip()

        # 1. Lexical substitution (legalese → plain English)
        simplified = cls._apply_lexical_substitutions(simplified)

        # 2. Remove redundant phrases
        simplified = cls._remove_redundant_phrases(simplified)

        # 3. Sentence splitting for long sentences
        if aggressive or not preserve_structure:
            simplified = cls._split_long_sentences(simplified)

        # 4. Clean up whitespace
        simplified = cls._normalize_whitespace(simplified)

        return simplified

    @classmethod
    def _apply_lexical_substitutions(cls, text: str) -> str:
        """Apply dictionary-based legalese → plain English substitutions."""
        result = text
        for pattern, replacement in cls.LEXICAL_SUBSTITUTIONS.items():
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
        return result

    @classmethod
    def _remove_redundant_phrases(cls, text: str) -> str:
        """Remove wordy, redundant phrases that add no meaning."""
        result = text
        for pattern in cls.REMOVE_PHRASES:
            result = re.sub(pattern, '', result, flags=re.IGNORECASE)
        return result

    @classmethod
    def _split_long_sentences(cls, text: str) -> str:
        """
        Split sentences that exceed MAX_SENTENCE_LENGTH_WORDS.
        
        Strategy: Find natural break points (conjunctions, relative clauses)
        and insert sentence breaks.
        """
        sentences = re.split(r'([.!?]\s+)', text)
        result_sentences = []

        for i in range(0, len(sentences), 2):
            if i >= len(sentences):
                break
            
            sentence = sentences[i]
            delimiter = sentences[i + 1] if i + 1 < len(sentences) else ''
            
            word_count = len(sentence.split())
            
            if word_count > cls.MAX_SENTENCE_LENGTH_WORDS:
                # Try to split at natural break points
                split_sentence = cls._split_at_natural_breaks(sentence)
                result_sentences.append(split_sentence)
            else:
                result_sentences.append(sentence)
            
            if delimiter:
                result_sentences.append(delimiter)

        return ''.join(result_sentences)

    @classmethod
    def _split_at_natural_breaks(cls, sentence: str) -> str:
        """
        Split a long sentence at conjunctions or relative clause markers.
        
        Priority break points:
          - ", and" → ". And"
          - ", but" → ". But"
          - ", which" → ". This"
          - ", provided that" → ". However,"
        """
        # Try splitting at conjunctions
        patterns = [
            (r',\s+(and|or)\s+', '. {conjunction} '),
            (r',\s+but\s+', '. But '),
            (r',\s+which\s+', '. This '),
            (r',\s+provided that\s+', '. However, '),
            (r',\s+provided,? however,?\s+', '. However, '),
            (r',\s+except\s+', '. Except '),
        ]

        result = sentence
        for pattern, replacement in patterns:
            match = re.search(pattern, result, flags=re.IGNORECASE)
            if match:
                conjunction = match.group(1) if '{conjunction}' in replacement else ''
                repl = replacement.format(conjunction=conjunction.capitalize())
                result = re.sub(pattern, repl, result, count=1, flags=re.IGNORECASE)
                break  # Only split once per sentence

        return result

    @classmethod
    def _normalize_whitespace(cls, text: str) -> str:
        """Clean up extra whitespace while preserving paragraph structure."""
        # Remove multiple spaces
        text = re.sub(r' {2,}', ' ', text)
        # Remove space before punctuation
        text = re.sub(r'\s+([.,;:!?])', r'\1', text)
        # Remove trailing/leading whitespace per line
        lines = [line.strip() for line in text.split('\n')]
        # Remove multiple blank lines
        result = '\n'.join(lines)
        result = re.sub(r'\n{3,}', '\n\n', result)
        return result.strip()

    @classmethod
    def get_simplification_stats(cls, original: str, simplified: str) -> Dict[str, Any]:
        """
        Compute basic stats about the simplification.
        
        Returns dict with:
          - original_word_count
          - simplified_word_count
          - reduction_pct
          - avg_sentence_length_before
          - avg_sentence_length_after
        """
        orig_words = len(original.split())
        simp_words = len(simplified.split())
        
        orig_sentences = [s.strip() for s in re.split(r'[.!?]+', original) if s.strip()]
        simp_sentences = [s.strip() for s in re.split(r'[.!?]+', simplified) if s.strip()]
        
        avg_len_before = (
            sum(len(s.split()) for s in orig_sentences) / len(orig_sentences)
            if orig_sentences else 0
        )
        avg_len_after = (
            sum(len(s.split()) for s in simp_sentences) / len(simp_sentences)
            if simp_sentences else 0
        )
        
        return {
            'original_word_count': orig_words,
            'simplified_word_count': simp_words,
            'reduction_pct': round((1 - simp_words / orig_words) * 100, 1) if orig_words > 0 else 0,
            'avg_sentence_length_before': round(avg_len_before, 1),
            'avg_sentence_length_after': round(avg_len_after, 1),
        }
