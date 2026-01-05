"""
Hybrid Simplification Pipeline: ML + Rules.

Architecture:
  1. Extract clauses
  2. For each clause:
     a. Apply rule-based simplification (accurate, no hallucination)
     b. Extract structured fields with improved heuristics
  3. Return structured JSON with original + explanation
"""

import json
import logging
import re
import traceback
from typing import Optional, Dict, Any

import torch
from transformers import BartForConditionalGeneration, BartTokenizer

from src.ml.prompt_templates import build_clause_explanation_prompt
from src.ml.clause_extractor import ClauseExtractor
from src.ml.entity_extractor import EntityExtractor
from src.ml.risk_assessor import RiskAssessor
from src.ml.rule_based_simplifier import RuleBasedSimplifier
from src.validators.simplify_validators import SimplifyValidator

logger = logging.getLogger(__name__)


class SimplificationPipeline:
    """
    Hybrid pipeline: Rule-based simplification + ML-powered extraction.
    
    Prioritizes accuracy over fancy summaries. Rules handle simplification,
    heuristics extract structure. BART kept for future enhancements but not
    used for content generation to avoid hallucinations.
    """

    MODEL_NAME = "facebook/bart-large-cnn"
    FALLBACK_MODEL = "facebook/bart-base"
    MIN_INPUT_CONTENT_WORDS = 5

    def __init__(self):
        self.current_model = self.MODEL_NAME
        SimplifyValidator.init_known_bad()

        logger.info(f"Loading BART model: {self.MODEL_NAME}")
        try:
            self.tokenizer = BartTokenizer.from_pretrained(self.MODEL_NAME)
            device = "cuda" if torch.cuda.is_available() else "cpu"
            self.model = BartForConditionalGeneration.from_pretrained(
                self.MODEL_NAME
            ).to(device)
            self.device = device
            logger.info(f"✓ BART model loaded successfully on device: {device}")
        except Exception as e:
            logger.warning(
                f"Failed to load {self.MODEL_NAME}, falling back: {type(e).__name__}: {e}"
            )
            self.tokenizer = BartTokenizer.from_pretrained(self.FALLBACK_MODEL)
            device = "cuda" if torch.cuda.is_available() else "cpu"
            self.model = BartForConditionalGeneration.from_pretrained(
                self.FALLBACK_MODEL
            ).to(device)
            self.device = device
            self.current_model = self.FALLBACK_MODEL
            logger.info(f"✓ BART fallback model loaded on device: {device}")

    def simplify(
        self,
        text: str,
        target_style: str = "",
        max_words_per_clause: int = 100,
        language_mix: str = "",
        max_length: int = 180,
    ) -> str:
        """
        Main entry: returns JSON with hybrid rule-based + extracted explanations.
        """
        if not isinstance(text, str) or not text.strip():
            raise ValueError("Input text must be a non-empty string")

        original_text = text.strip()

        # Early guard
        content_words = [w for w in original_text.split() if any(c.isalpha() for c in w)]
        if len(content_words) < self.MIN_INPUT_CONTENT_WORDS:
            response = {
                "summary": original_text,
                "clauses": [],
                "warnings": [f"input_too_short_min_{self.MIN_INPUT_CONTENT_WORDS}"],
            }
            response_json = json.dumps(response, ensure_ascii=False)
            SimplifyValidator.log_known_bad(
                original_text=original_text,
                tag="input_too_short",
                short_comment=(
                    f"Skipped: {len(content_words)} content words, "
                    f"min {self.MIN_INPUT_CONTENT_WORDS}"
                ),
                output_json=response_json,
            )
            return response_json

        # Clause extraction
        try:
            raw_clauses = ClauseExtractor.extract_clauses(original_text)
        except Exception as e:
            logger.error(f"Clause extraction failed: {type(e).__name__}: {e}")
            raw_clauses = [
                {"id": "clause_1", "original_text": original_text, "type": "general"}
            ]

        processed_clauses = []
        pipeline_warnings = []

        for raw_clause in raw_clauses:
            clause_id = raw_clause.get("id", "clause_unknown")
            clause_type = raw_clause.get("type", "general")
            clause_text = raw_clause.get("original_text", "").strip()

            if not clause_text:
                continue

            # **HYBRID STEP**: Rule-based simplification + field extraction
            explanation, explanation_warnings = self._hybrid_explain_clause(
                clause_text=clause_text, clause_type=clause_type
            )

            # Entities
            entities = EntityExtractor.extract_entities(clause_text)

            # Risk
            risk_level = RiskAssessor.assess_risk(
                clause_text=clause_text, clause_type=clause_type, entities=entities
            )

            # Clause warnings
            clause_warnings = list(explanation_warnings)
            if entities.get("numerics"):
                clause_warnings.append("numerics_present")
            if entities.get("deadline"):
                clause_warnings.append("time_sensitive")
            if entities.get("conditions"):
                clause_warnings.append("conditional_clause")

            processed_clauses.append(
                {
                    "id": clause_id,
                    "type": clause_type,
                    "original_text": clause_text,
                    "explanation": explanation,
                    "risk_level": risk_level,
                    "key_entities": entities,
                    "warnings": clause_warnings,
                }
            )

        # Summary
        if processed_clauses:
            summary = " ".join(
                c["explanation"]["summary"] for c in processed_clauses[:3]
                if c["explanation"].get("summary")
            )
        else:
            summary = original_text

        response = {
            "summary": summary.strip(),
            "clauses": processed_clauses,
            "warnings": pipeline_warnings,
        }
        response_json = json.dumps(response, ensure_ascii=False)

        # Validation
        is_valid, error_msg = SimplifyValidator.validate(
            output_json_str=response_json,
            original_text=original_text,
            tag="hybrid_explanation_output",
        )

        if not is_valid:
            response["warnings"].append(f"validation_failed: {error_msg}")
            response_json = json.dumps(response, ensure_ascii=False)

        return response_json

    # -------------------------------------------------------------------------
    # HYBRID EXPLANATION: Rules + Extraction (NO ML HALLUCINATION)
    # -------------------------------------------------------------------------

    def _hybrid_explain_clause(
        self, clause_text: str, clause_type: str
    ) -> (Dict[str, Any], list):
        """
        Hybrid approach - prioritize accuracy over fancy ML summaries.
        
        1. Apply rule-based simplification to original clause (this is the summary)
        2. Extract structured fields with improved heuristics from original
        3. Don't rely on BART for content generation (avoids hallucination)
        """
        warnings = []

        # Step 1: Rule-based simplification of the ORIGINAL clause
        # This becomes our summary (accurate, just simpler wording)
        summary = RuleBasedSimplifier.simplify(
            text=clause_text, preserve_structure=True, aggressive=False
        )

        # Step 2: Extract structured fields from the ORIGINAL clause
        who_protected = self._extract_parties(clause_text, summary)
        what_covered = self._extract_coverage(clause_text, summary)
        exceptions = self._extract_exceptions(clause_text, summary)

        # Step 3: Apply rules to each extracted field for cleanup
        explanation = {
            "summary": summary,
            "who_is_protected": RuleBasedSimplifier.simplify(
                text=who_protected, preserve_structure=False
            ),
            "what_is_covered": RuleBasedSimplifier.simplify(
                text=what_covered, preserve_structure=False
            ),
            "exceptions": RuleBasedSimplifier.simplify(
                text=exceptions, preserve_structure=False
            ),
        }

        # Sanity check
        required_keys = ["summary", "who_is_protected", "what_is_covered", "exceptions"]
        for k in required_keys:
            if k not in explanation or not str(explanation[k]).strip():
                warnings.append(f"missing_field_{k}")

        # Log simplification stats
        try:
            stats = RuleBasedSimplifier.get_simplification_stats(
                original=clause_text, simplified=explanation["summary"]
            )
            logger.debug(f"Simplification stats for {clause_type}: {stats}")
        except Exception:
            pass

        return explanation, warnings

    # -------------------------------------------------------------------------
    # IMPROVED FIELD EXTRACTION HEURISTICS
    # -------------------------------------------------------------------------

    @staticmethod
    def _extract_parties(original: str, simplified: str) -> str:
        """Extract party information from clause - prioritize compound names."""
        # First try compound party names (2-3 words)
        compound_patterns = [
            r'\b(Receiving Party|Disclosing Party|Indemnifying Party|Indemnified Party|Licensing Party|Licensed Party)\b',
            r'\b(First Party|Second Party|Third Party)\b',
        ]
        
        found_parties = set()
        
        # Try compound names first
        for pattern in compound_patterns:
            matches = re.findall(pattern, original, re.IGNORECASE)
            found_parties.update(matches)
        
        # If compound names found, use those exclusively
        if found_parties:
            parties_list = sorted(set(p.strip() for p in found_parties))[:4]
            return ", ".join(parties_list)
        
        # Otherwise, fall back to single-word party names
        single_party_patterns = [
            r'\b(Company|Client|Vendor|Customer|Applicant|Court|Licensor|Licensee|Employer|Employee)\b',
            r'\b(Plaintiff|Defendant|Petitioner|Respondent|Grantor|Grantee)\b',
            r'\b(its officers?|directors?|employees?|agents?|successors?|assigns?|affiliates?)\b',
        ]
        
        for pattern in single_party_patterns:
            matches = re.findall(pattern, original, re.IGNORECASE)
            found_parties.update(matches)
        
        if found_parties:
            parties_list = sorted(set(p.strip() for p in found_parties))[:4]
            return ", ".join(parties_list)

        return "The parties mentioned in the clause"

    @staticmethod
    def _extract_coverage(original: str, simplified: str) -> str:
        """Extract what is covered/protected - broader patterns."""
        # Broader coverage patterns including NDA/confidentiality terms
        coverage_keywords = [
            # Contract/tort
            r'\b(claims?|damages?|losses?|liabilities?|costs?|expenses?|fees?|penalties?)\b',
            r'\b(breach|misconduct|negligence|violation|failure|default)\b',
            r'\b(compensation|indemnification|protection|defense|reimbursement)\b',
            
            # Confidentiality/IP
            r'\b(Confidential Information|confidential|proprietary information|trade secrets?)\b',
            r'\b(disclosure|use|dissemination|reproduction|distribution)\b',
            r'\b(inventions?|patents?|copyrights?|trademarks?|intellectual property)\b',
            
            # Employment
            r'\b(employment|services|work product|non-compete)\b',
            
            # General obligations
            r'\b(obligations?|duties|rights|restrictions?|limitations?|prohibitions?)\b',
        ]

        found_items = set()
        for pattern in coverage_keywords:
            matches = re.findall(pattern, original, re.IGNORECASE)
            found_items.update(matches)

        if found_items:
            # Deduplicate and limit
            items_list = sorted(set(i.strip() for i in found_items))[:6]
            return "Covers: " + ", ".join(items_list)

        return "Coverage details in the original clause"

    @staticmethod
    def _extract_exceptions(original: str, simplified: str) -> str:
        """Extract exception/limitation language - capture multi-part lists."""
        # Look for exception patterns with extended capture (including list items)
        exception_patterns = [
            # Capture from exception keyword to end of list (including (a), (b), (c))
            r'((?:except|provided|however|unless|but|excluding)[^.]*(?:\([a-z]\)[^.]*)*)',
            r'(does not apply[^.]*(?:\([a-z]\)[^.]*)*)',
            r'(no obligation[^.]*(?:\([a-z]\)[^.]*)*)',
            r'(may[^.]*discretion[^.]*)',
            r'(shall not apply[^.]*(?:\([a-z]\)[^.]*)*)',
        ]

        # Find exception clauses
        found_exceptions = []
        
        for pattern in exception_patterns:
            matches = re.findall(pattern, original, re.IGNORECASE | re.DOTALL)
            for match in matches:
                cleaned = match.strip()
                if len(cleaned) > 25:  # Skip very short matches
                    # Apply rules to simplify
                    simplified_exc = RuleBasedSimplifier.simplify(
                        text=cleaned, preserve_structure=False
                    )
                    if simplified_exc:
                        found_exceptions.append(simplified_exc)

        if found_exceptions:
            # Return the longest/most substantial exception
            main_exception = max(found_exceptions, key=len)
            # Capitalize first letter
            return main_exception[0].upper() + main_exception[1:] if main_exception else main_exception

        return "No major exceptions specified"

    # -------------------------------------------------------------------------
    # BART GENERATION (Kept for future use, not used in current pipeline)
    # -------------------------------------------------------------------------

    def _generate(self, prompt: str, max_length: int = 256, min_length: int = 40) -> str:
        """
        Generic BART generation.
        Currently not used to avoid hallucinations, but kept for future enhancements.
        """
        inputs = self.tokenizer(
            prompt,
            max_length=1024,
            truncation=True,
            return_tensors="pt",
            padding=True,
        ).to(self.device)

        with torch.no_grad():
            out_ids = self.model.generate(
                inputs["input_ids"],
                attention_mask=inputs.get("attention_mask"),
                max_length=max_length,
                min_length=min_length,
                num_beams=4,
                early_stopping=True,
                do_sample=True,
                temperature=0.8,
                top_p=0.9,
                top_k=50,
                no_repeat_ngram_size=3,
                repetition_penalty=1.2,
                length_penalty=0.9,
                encoder_no_repeat_ngram_size=3,
            )

        return self.tokenizer.decode(
            out_ids[0], skip_special_tokens=True, clean_up_tokenization_spaces=True
        ).strip()


_pipeline: Optional[SimplificationPipeline] = None


def get_simplification_pipeline() -> SimplificationPipeline:
    """Get or create singleton pipeline instance."""
    global _pipeline
    if _pipeline is None:
        _pipeline = SimplificationPipeline()
    return _pipeline
