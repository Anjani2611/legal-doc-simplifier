"""Test metrics on first gold annotation."""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from evaluation.metrics import EvaluationMetrics


def test_metrics_on_gold():
    """Load first annotation and calculate metrics."""
    
    # Find first annotation
    gold_root = Path(__file__).parent.parent / "data" / "gold_corpus"
    ann_file = None
    
    for clause_dir in gold_root.iterdir():
        if clause_dir.is_dir():
            for f in clause_dir.glob("*.json"):
                ann_file = f
                break
        if ann_file:
            break
    
    if not ann_file:
        print("✗ No annotations found. Run corpus_builder.py first.")
        return False
    
    print(f"\nLoading annotation: {ann_file.name}")
    
    with ann_file.open("r") as f:
        ann = json.load(f)
    
    original = ann["original_text"]
    simplified = ann["gold_simplification"]
    
    print(f"Original length: {len(original)} chars")
    print(f"Simplified length: {len(simplified)} chars")
    
    # Prepare entities
    original_entities = {
        "parties": [
            {"text": p["text"], "role": p.get("role", "general")}
            for p in ann["entities"].get("parties", [])
        ],
        "obligations": ann["entities"].get("obligations", []),
        "amounts": ann["entities"].get("amounts", []),
        "exceptions": ann["entities"].get("exceptions", []),
    }
    
    # Since we don't have extracted entities from simplified,
    # do a simple heuristic check
    simplified_entities = {
        "parties": original_entities["parties"],  # Assume same
        "obligations": [o for o in original_entities["obligations"] if o.lower() in simplified.lower()],
        "amounts": [a for a in original_entities["amounts"] if a in simplified],
        "exceptions": [e for e in original_entities["exceptions"] if e.lower() in simplified.lower()],
    }
    
    # Calculate metrics
    print("\nCalculating metrics...")
    metrics = EvaluationMetrics()
    
    result = metrics.comprehensive_score(
        original,
        simplified,
        original_entities,
        simplified_entities
    )
    
    print("\n" + "="*70)
    print("METRICS RESULTS")
    print("="*70)
    print(f"\nSemantic Similarity: {result['semantic_similarity']:.2%}")
    print(f"  Target: > 80%")
    print(f"  Status: {'✓ PASS' if result['semantic_similarity'] >= 0.80 else '✗ FAIL'}\n")
    
    print(f"Readability Improvement: {result['readability_improvement_grade_levels']:.1f} grade levels")
    print(f"  Target: > 2.0")
    print(f"  Status: {'✓ PASS' if result['readability_improvement_grade_levels'] >= 2.0 else '✗ FAIL'}\n")
    
    print(f"Fact Preservation:")
    for metric, value in result['fact_preservation_metrics'].items():
        print(f"  {metric}: {value:.1%}")
    
    print(f"\nComposite Score: {result['composite_score']:.2%}")
    print("  Weighted average of: semantic (40%) + fact preservation (40%) + readability (20%)")
    
    return True


if __name__ == "__main__":
    test_metrics_on_gold()
