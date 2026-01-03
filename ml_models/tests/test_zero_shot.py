"""
Test that zero-shot classification works on CPU.
This is your fallback if no fine-tuning happens.
"""
from transformers import pipeline

def test_zero_shot_classifier():
    print("Loading zero-shot classifier (first run downloads model)...")
    classifier = pipeline(
        "zero-shot-classification",
        model="facebook/bart-large-mnli"
    )
    
    # Test clause
    clause = """The Indemnifying Party shall defend, indemnify and hold harmless 
    the Indemnified Party from any and all claims, damages, and losses arising 
    from the negligence of the Indemnifying Party."""
    
    # Clause types
    labels = [
        "indemnity",
        "confidentiality",
        "termination",
        "liability_limitation",
        "payment_terms"
    ]
    
    # Classify
    result = classifier(clause, labels)
    
    print("\n" + "="*60)
    print("ZERO-SHOT CLASSIFICATION TEST")
    print("="*60)
    print(f"Input clause (truncated):\n{clause[:100]}...\n")
    print(f"Detected type: {result['labels'][0]}")
    print(f"Confidence: {result['scores'][0]:.1%}\n")
    print("Scores for all labels:")
    for label, score in zip(result['labels'], result['scores']):
        print(f"  {label:25} {score:6.1%}")
    print("="*60)
    
    # Assert minimum confidence
    assert result['scores'][0] > 0.5, "Confidence too low"
    print("\n✓ TEST PASSED: Zero-shot classifier working on CPU")

if __name__ == "__main__":
    test_zero_shot_classifier()
