import logging
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from typing import Optional

logger = logging.getLogger(__name__)


class SimplificationPipeline:
    """Simplifies legal text using improved model and prompt engineering"""
    
    MODEL_NAME = "google/flan-t5-large"
    FALLBACK_MODEL = "pszemraj/long-t5-tglobal-base-sci-simplify"
    
    def __init__(self):
        """Load model and tokenizer on initialization"""
        logger.info(f"Loading model: {self.MODEL_NAME}")
        
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.MODEL_NAME)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(self.MODEL_NAME)
            self.current_model = self.MODEL_NAME
            logger.info("✓ Model loaded successfully")
        except Exception as e:
            logger.warning(f"Failed to load {self.MODEL_NAME}, falling back: {e}")
            try:
                self.tokenizer = AutoTokenizer.from_pretrained(self.FALLBACK_MODEL)
                self.model = AutoModelForSeq2SeqLM.from_pretrained(self.FALLBACK_MODEL)
                self.current_model = self.FALLBACK_MODEL
                logger.info("✓ Fallback model loaded successfully")
            except Exception as fallback_error:
                logger.error(f"Failed to load fallback model: {fallback_error}")
                raise
    
    def simplify(
        self,
        text: str,
        max_length: int = 256,
        min_length: int = 80,
        num_beams: int = 4,
    ) -> str:
        """
        Simplify legal text while preserving key terms and meaning.
        
        Args:
            text: Legal text to simplify
            max_length: Max output length
            min_length: Min output length
            num_beams: Beam search width
        
        Returns:
            Simplified text
        """
        if not text or not isinstance(text, str):
            raise ValueError("Input text must be a non-empty string")
        
        if len(text.strip()) == 0:
            raise ValueError("Input text cannot be empty")
        
        try:
            prompt = (
                "Simplify the following legal text into plain English. "
                "RULES:\n"
                "1. Keep ALL numbers and dates (30 days stays 30 days)\n"
                "2. Keep ALL legal terms (terminate, agreement, obligation)\n"
                "3. Keep ALL party names unchanged\n"
                "4. DO NOT change legal meaning\n"
                "5. Use simple, short sentences\n"
                "6. Replace 'shall' with 'must', 'may' with 'can'\n"
                "7. Avoid double negatives\n"
                "8. Use common words instead of legal jargon\n\n"
                f"Text:\n{text}\n\n"
                "Simplified:\n"
            )

            inputs = self.tokenizer(
                prompt,
                max_length=1024,
                truncation=True,
                return_tensors="pt",
                padding=True,
            )
            
            summary_ids = self.model.generate(
                inputs["input_ids"],
                max_length=max_length,
                min_length=min_length,
                num_beams=num_beams,
                early_stopping=True,
                do_sample=False,
                no_repeat_ngram_size=2,
                length_penalty=1.0,
            )
            
            simplified = self.tokenizer.batch_decode(
                summary_ids,
                skip_special_tokens=True,
                clean_up_tokenization_spaces=True,
            )[0].strip()
            
            if not simplified or len(simplified) < 5:
                logger.warning("Output too short, using truncated original")
                simplified = text[:max_length].strip()
            
            logger.info(f"Simplified {len(text)} chars -> {len(simplified)} chars")
            return simplified
        
        except Exception as e:
            logger.error(f"Simplification failed: {str(e)}")
            raise


_pipeline: Optional[SimplificationPipeline] = None


def get_simplification_pipeline() -> SimplificationPipeline:
    """Get or create global simplification pipeline"""
    global _pipeline
    if _pipeline is None:
        _pipeline = SimplificationPipeline()
    return _pipeline
