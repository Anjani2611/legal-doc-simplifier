"""Verify training data is in correct format."""
import json
from pathlib import Path

def test_classifier_data():
    """Check JSONL format for classifier."""
    path = Path("data/training/clause_types.jsonl")
    
    if not path.exists():
        print("✗ Classifier data file not found")
        return False
    
    with path.open("r") as f:
        for i, line in enumerate(f, 1):
            try:
                rec = json.loads(line)
                assert "text" in rec, f"Line {i}: missing 'text'"
                assert "label" in rec, f"Line {i}: missing 'label'"
            except json.JSONDecodeError as e:
                print(f"✗ Line {i}: invalid JSON - {e}")
                return False
    
    print(f"✓ Classifier data: {i} valid records")
    return True


def test_simplification_data():
    """Check JSONL format for simplification."""
    path = Path("data/training/simplifications.jsonl")
    
    if not path.exists():
        print("✗ Simplification data file not found")
        return False
    
    with path.open("r") as f:
        for i, line in enumerate(f, 1):
            try:
                rec = json.loads(line)
                assert "source" in rec, f"Line {i}: missing 'source'"
                assert "target" in rec, f"Line {i}: missing 'target'"
            except json.JSONDecodeError as e:
                print(f"✗ Line {i}: invalid JSON - {e}")
                return False
    
    print(f"✓ Simplification data: {i} valid records")
    return True


def test_ner_data():
    """Check CoNLL format for NER."""
    path = Path("data/training/entities.conll")
    
    if not path.exists():
        print("✗ NER data file not found")
        return False
    
    docs = 0
    tokens = 0
    
    with path.open("r") as f:
        for line in f:
            if not line.strip():
                docs += 1
            elif "\t" in line:
                tokens += 1
    
    print(f"✓ NER data: {docs} docs, {tokens} tokens")
    return True


if __name__ == "__main__":
    print("\n" + "="*70)
    print("TRAINING DATA FORMAT VALIDATION")
    print("="*70 + "\n")
    
    all_ok = all([
        test_classifier_data(),
        test_simplification_data(),
        test_ner_data(),
    ])
    
    if all_ok:
        print("\n✓ ALL TESTS PASSED")
    else:
        print("\n✗ SOME TESTS FAILED - Fix before proceeding")
