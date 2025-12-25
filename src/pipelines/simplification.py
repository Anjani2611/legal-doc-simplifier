"""Text simplification pipeline using BART model"""

import logging
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from typing import Optional

logger = logging.getLogger(__name__)


class SimplificationPipeline:
    """Simplifies legal text using fine-tuned BART model"""
    
    # Model from Hugging Face (pre-trained on legal documents)
    MODEL_NAME = "pszemraj/long-t5-tglobal-base-sci-simplify"
    
    def __init__(self):
        """Load model and tokenizer on initialization"""
        logger.info(f"Loading model: {self.MODEL_NAME}")
        
        self.tokenizer = AutoTokenizer.from_pretrained(self.MODEL_NAME)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(self.MODEL_NAME)
        
        logger.info("✓ Model loaded successfully")
    
    def simplify(
        self,
        text: str,
        max_length: int = 256,
        min_length: int = 50,
        num_beams: int = 4,
    ) -> str:
        """
        Simplify legal text
        
        Args:
            text: Legal text to simplify
            max_length: Max output length
            min_length: Min output length
            num_beams: Beam search width (higher = better but slower)
        
        Returns:
            Simplified text
        """
        try:
            # Tokenize input
            inputs = self.tokenizer(
                text,
                max_length=1024,
                truncation=True,
                return_tensors="pt",
            )
            
            # Generate simplified text
            summary_ids = self.model.generate(
                inputs["input_ids"],
                max_length=max_length,
                min_length=min_length,
                num_beams=num_beams,
                early_stopping=True,
                temperature=0.7,
            )
            
            # Decode and return
            simplified = self.tokenizer.batch_decode(
                summary_ids,
                skip_special_tokens=True,
            )[0]
            
            logger.info(f"Simplified {len(text)} chars -> {len(simplified)} chars")
            return simplified
        
        except Exception as e:
            logger.error(f"Simplification failed: {str(e)}")
            raise


# Global instance (lazy loaded)
_pipeline: Optional[SimplificationPipeline] = None


def get_simplification_pipeline() -> SimplificationPipeline:
    """Get or create global simplification pipeline"""
    global _pipeline
    if _pipeline is None:
        _pipeline = SimplificationPipeline()
    return _pipeline
