"""
Convert gold corpus annotations into task-specific training formats.
"""
import json
from pathlib import Path
from typing import Dict, List

GOLD_ROOT = Path(__file__).parent / "gold_corpus"
TRAIN_ROOT = Path(__file__).parent / "training"


class TrainingDataBuilder:
    """Generate training datasets from gold corpus."""
    
    def __init__(self, gold_root: Path = GOLD_ROOT, out_root: Path = TRAIN_ROOT):
        self.gold_root = gold_root
        self.out_root = out_root
        self.out_root.mkdir(parents=True, exist_ok=True)
    
    def _iter_annotations(self):
        """Iterate all gold annotations."""
        for clause_dir in sorted(self.gold_root.iterdir()):
            if not clause_dir.is_dir():
                continue
            for f in sorted(clause_dir.glob("*.json")):
                with f.open("r", encoding="utf-8") as fp:
                    yield json.load(fp)
    
    def build_classifier_data(self):
        """
        For clause type classification task.
        Format: JSONL (one JSON per line)
        {"text": "...", "label": "indemnity"}
        """
        out_path = self.out_root / "clause_types.jsonl"
        
        with out_path.open("w", encoding="utf-8") as out:
            count = 0
            for ann in self._iter_annotations():
                rec = {
                    "text": ann["original_text"],
                    "label": ann["clause_type"],
                }
                out.write(json.dumps(rec, ensure_ascii=False) + "\n")
                count += 1
        
        print(f"✓ Classifier data: {out_path}")
        print(f"  Total records: {count}")
        return out_path
    
    def build_simplification_pairs(self):
        """
        For text simplification task (T5 training).
        Format: JSONL
        {"source": "original", "target": "simplified"}
        """
        out_path = self.out_root / "simplifications.jsonl"
        
        with out_path.open("w", encoding="utf-8") as out:
            count = 0
            for ann in self._iter_annotations():
                if not ann.get("gold_simplification"):
                    continue
                rec = {
                    "source": ann["original_text"],
                    "target": ann["gold_simplification"],
                }
                out.write(json.dumps(rec, ensure_ascii=False) + "\n")
                count += 1
        
        print(f"✓ Simplification pairs: {out_path}")
        print(f"  Total pairs: {count}")
        return out_path
    
    def build_ner_data_conll(self):
        """
        For NER task (token classification).
        Format: CoNLL-style (tab-separated, blank line between docs)
        """
        out_path = self.out_root / "entities.conll"
        
        with out_path.open("w", encoding="utf-8") as out:
            doc_count = 0
            token_count = 0
            
            for ann in self._iter_annotations():
                text = ann["original_text"]
                entities = ann["entities"]
                
                # Build simple char-span map
                spans = self._build_entity_spans(text, entities)
                
                # Tokenize by whitespace (simple)
                tokens = text.split()
                char_pos = 0
                
                for token in tokens:
                    # Find token position
                    start = text.find(token, char_pos)
                    end = start + len(token)
                    char_pos = end
                    
                    # Get tag
                    tag = spans.get((start, end), "O")
                    
                    out.write(f"{token}\t{tag}\n")
                    token_count += 1
                
                # Blank line between documents
                out.write("\n")
                doc_count += 1
        
        print(f"✓ NER data: {out_path}")
        print(f"  Documents: {doc_count}, Tokens: {token_count}")
        return out_path
    
    def _build_entity_spans(self, text: str, entities: Dict) -> Dict:
        """Map entity text to character spans."""
        spans = {}
        
        def mark_span(entity_text: str, label: str):
            """Find entity in text and mark span."""
            lower_text = text.lower()
            lower_entity = entity_text.lower()
            
            start = lower_text.find(lower_entity)
            if start == -1:
                return
            
            end = start + len(entity_text)
            spans[(start, end)] = label
        
        # Mark all entity types
        for party in entities.get("parties", []):
            mark_span(party["text"], "B-PARTY")
        
        for oblig in entities.get("obligations", []):
            mark_span(oblig, "B-OBLIGATION")
        
        for coverage in entities.get("coverage", []):
            mark_span(coverage, "B-COVERAGE")
        
        for exception in entities.get("exceptions", []):
            mark_span(exception, "B-EXCEPTION")
        
        for amount in entities.get("amounts", []):
            mark_span(amount, "B-AMOUNT")
        
        for deadline in entities.get("deadlines", []):
            mark_span(deadline, "B-DATE")
        
        return spans
    
    def build_all(self):
        """Build all training datasets."""
        print("\n" + "="*70)
        print("TRAINING DATA BUILDER")
        print("="*70 + "\n")
        
        self.build_classifier_data()
        self.build_simplification_pairs()
        self.build_ner_data_conll()
        
        print("\n✓ All training data generated")


if __name__ == "__main__":
    builder = TrainingDataBuilder()
    builder.build_all()
