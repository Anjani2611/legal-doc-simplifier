"""
Comprehensive evaluation metrics for legal simplification.
- Readability: FKGL, Flesch Reading Ease, etc.
- Semantic Similarity: Cosine similarity of embeddings
- Fact Preservation: Entity recall and preservation
"""
import textstat
from sentence_transformers import SentenceTransformer, util
import numpy as np
from typing import Dict


class EvaluationMetrics:
    """Central metrics calculator."""
    
    def __init__(self, sim_model: str = "all-MiniLM-L6-v2"):
        """
        Initialize with semantic similarity model.
        'all-MiniLM-L6-v2' is fast and good enough for legal text.
        """
        print("Loading semantic similarity model...")
        self.similarity_model = SentenceTransformer(sim_model)
        print("✓ Model loaded")
    
    def readability_score(self, text: str) -> Dict[str, float]:
        """
        Calculate multiple readability metrics.
        Lower FKGL = easier to read.
        Flesch Reading Ease: 0-100 (higher = easier)
        """
        return {
            "flesch_kincaid_grade": textstat.flesch_kincaid_grade(text),
            "flesch_reading_ease": textstat.flesch_reading_ease(text),
            "smog_index": textstat.smog_index(text),
            "coleman_liau_index": textstat.coleman_liau_index(text),
            "automated_readability_index": textstat.automated_readability_index(text),
            "avg_sentence_length": textstat.avg_sentence_length(text),
            "avg_word_length": textstat.avg_syllables_per_word(text),
        }
    
    def semantic_similarity(self, original: str, simplified: str) -> float:
        """
        Cosine similarity between embeddings.
        Range: 0.0 (completely different) to 1.0 (identical)
        Target: > 0.80 (meaning well preserved)
        """
        emb1 = self.similarity_model.encode(original, convert_to_tensor=True)
        emb2 = self.similarity_model.encode(simplified, convert_to_tensor=True)
        return float(util.cos_sim(emb1, emb2).item())
    
    def fact_preservation(
        self, 
        original_entities: Dict, 
        simplified_entities: Dict
    ) -> Dict[str, float]:
        """
        Check critical facts preserved.
        Calculates recall: (preserved facts) / (original facts)
        """
        metrics = {}
        
        # Party preservation (CRITICAL)
        orig_parties = set(e["text"] for e in original_entities.get("parties", []))
        simp_parties = set(e["text"] for e in simplified_entities.get("parties", []))
        if orig_parties:
            metrics["party_recall"] = len(orig_parties & simp_parties) / len(orig_parties)
        else:
            metrics["party_recall"] = 1.0
        
        # Obligation preservation (CRITICAL)
        orig_oblig = set(original_entities.get("obligations", []))
        simp_oblig = set(simplified_entities.get("obligations", []))
        if orig_oblig:
            metrics["obligation_recall"] = len(orig_oblig & simp_oblig) / len(orig_oblig)
        else:
            metrics["obligation_recall"] = 1.0
        
        # Amount preservation (MUST be 100%)
        orig_amounts = set(original_entities.get("amounts", []))
        simp_amounts = set(simplified_entities.get("amounts", []))
        if orig_amounts:
            metrics["amount_preservation"] = len(orig_amounts & simp_amounts) / len(orig_amounts)
        else:
            metrics["amount_preservation"] = 1.0
        
        # Exception preservation (CRITICAL)
        orig_except = set(original_entities.get("exceptions", []))
        simp_except = set(simplified_entities.get("exceptions", []))
        if orig_except:
            metrics["exception_recall"] = len(orig_except & simp_except) / len(orig_except)
        else:
            metrics["exception_recall"] = 1.0
        
        return metrics
    
    def comprehensive_score(
        self,
        original: str,
        simplified: str,
        original_entities: Dict,
        simplified_entities: Dict,
    ) -> Dict:
        """
        Holistic score combining all metrics.
        Weights: semantic (40%) + fact preservation (40%) + readability (20%)
        """
        readability = self.readability_score(simplified)
        semantic_sim = self.semantic_similarity(original, simplified)
        fact_pres = self.fact_preservation(original_entities, simplified_entities)
        
        # Readability improvement
        orig_grade = textstat.flesch_kincaid_grade(original)
        simp_grade = textstat.flesch_kincaid_grade(simplified)
        readability_improvement = orig_grade - simp_grade
        
        # Composite score (0-1)
        fact_pres_avg = float(np.mean(list(fact_pres.values())))
        readability_norm = min(1.0, readability_improvement / 5.0)  # Cap at 5 levels
        
        composite = (
            0.4 * semantic_sim +
            0.4 * fact_pres_avg +
            0.2 * readability_norm
        )
        
        return {
            "readability_metrics": readability,
            "semantic_similarity": semantic_sim,
            "fact_preservation_metrics": fact_pres,
            "readability_improvement_grade_levels": readability_improvement,
            "composite_score": composite,
            "pass_criteria": {
                "semantic_similarity_ok": semantic_sim >= 0.80,
                "fact_preservation_ok": fact_pres_avg >= 0.85,
                "readability_improved": readability_improvement >= 2.0,
            }
        }


if __name__ == "__main__":
    # Test metrics
    metrics = EvaluationMetrics()
    
    original = """The Indemnifying Party shall defend, indemnify and hold harmless 
    the Indemnified Party from any and all claims, damages, losses, liabilities, 
    costs and expenses (including reasonable attorneys' fees) arising from the acts, 
    omissions or negligence of the Indemnifying Party in the performance of services 
    under this Agreement, except to the extent caused by the gross negligence or 
    willful misconduct of the Indemnified Party."""
    
    simplified = """Party A must protect Party B from legal claims and cover all related 
    costs (including lawyer fees) if those claims arise from Party A's actions or 
    mistakes while performing the agreed services. However, Party A does NOT have to 
    protect Party B if the claims are caused by Party B's own serious negligence or 
    intentional wrongdoing."""
    
    original_entities = {
        "parties": [
            {"text": "Indemnifying Party", "role": "obligor"},
            {"text": "Indemnified Party", "role": "beneficiary"}
        ],
        "obligations": ["defend", "indemnify", "hold harmless"],
        "amounts": [],
        "exceptions": ["gross negligence", "willful misconduct"]
    }
    
    simplified_entities = {
        "parties": [
            {"text": "Party A", "role": "obligor"},
            {"text": "Party B", "role": "beneficiary"}
        ],
        "obligations": ["protect", "cover"],
        "amounts": [],
        "exceptions": ["serious negligence", "intentional wrongdoing"]
    }
    
    print("\n" + "="*70)
    print("EVALUATION METRICS TEST")
    print("="*70 + "\n")
    
    result = metrics.comprehensive_score(
        original,
        simplified,
        original_entities,
        simplified_entities
    )
    
    print(f"Semantic Similarity: {result['semantic_similarity']:.2%}")
    print(f"Readability Improvement: {result['readability_improvement_grade_levels']:.1f} grades")
    print(f"Composite Score: {result['composite_score']:.2%}")
    print(f"\nPass Criteria:")
    for criterion, passed in result['pass_criteria'].items():
        status = "✓" if passed else "✗"
        print(f"  {status} {criterion}")
