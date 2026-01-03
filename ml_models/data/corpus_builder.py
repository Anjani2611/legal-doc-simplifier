"""
Interactive builder for gold standard corpus.
Each annotation: original clause + manual simplification + entity tags.
"""
import json
from pathlib import Path
from typing import Tuple, List, Dict, Optional

CLAUSE_TYPES = [
    "indemnity",
    "confidentiality",
    "termination",
    "liability_limitation",
    "ip_assignment",
    "payment_terms",
    "warranty",
    "force_majeure",
    "dispute_resolution",
    "general_provision",
]

GOLD_ROOT = Path(__file__).parent / "gold_corpus"


class GoldCorpusBuilder:
    """Build and validate gold-standard clause annotations."""
    
    def __init__(self, root: Path = GOLD_ROOT):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
    
    def create_annotation_template(
        self, 
        clause_text: str, 
        clause_type: str, 
        clause_id: str
    ) -> Dict:
        """Generate annotation template for user to fill."""
        if clause_type not in CLAUSE_TYPES:
            raise ValueError(f"Invalid clause_type: {clause_type}")
        
        return {
            "id": clause_id,
            "clause_type": clause_type,
            "original_text": clause_text.strip(),
            "gold_simplification": "",  # User fills this
            "entities": {
                "parties": [],  # [{"text": "Party A", "role": "obligor"}, ...]
                "obligations": [],  # ["defend", "indemnify", ...]
                "coverage": [],  # ["claims", "damages", ...]
                "exceptions": [],  # ["gross negligence", ...]
                "amounts": [],  # ["₹5,00,000", ...]
                "deadlines": [],  # ["within 30 days", ...]
            },
            "key_facts": [],  # 2-3 critical points to preserve
        }
    
    def save_annotation(self, annotation: Dict) -> Path:
        """Save annotation to typed subfolder."""
        clause_type = annotation["clause_type"]
        clause_id = annotation["id"]
        
        out_dir = self.root / clause_type
        out_dir.mkdir(parents=True, exist_ok=True)
        
        out_path = out_dir / f"{clause_id}.json"
        
        with out_path.open("w", encoding="utf-8") as f:
            json.dump(annotation, f, ensure_ascii=False, indent=2)
        
        return out_path
    
    def validate_annotation(self, annotation: Dict) -> Tuple[bool, List[str]]:
        """Check annotation completeness."""
        errors: List[str] = []
        
        # Required fields
        for field in ["id", "clause_type", "original_text", "gold_simplification"]:
            if not annotation.get(field):
                errors.append(f"Missing or empty: {field}")
        
        # Clause type validation
        if annotation.get("clause_type") not in CLAUSE_TYPES:
            errors.append(f"Invalid clause_type: {annotation.get('clause_type')}")
        
        entities = annotation.get("entities", {})
        
        # At least 1 party
        parties = entities.get("parties", [])
        if not parties:
            errors.append("Add at least 1 party")
        
        for party in parties:
            if not party.get("text") or not party.get("role"):
                errors.append("Each party needs 'text' and 'role'")
        
        # Obligations/coverage for non-general clauses
        if annotation.get("clause_type") != "general_provision":
            if not entities.get("obligations"):
                errors.append("Add obligations for this clause type")
            if not entities.get("coverage"):
                errors.append("Add coverage items")
        
        # Key facts (2-3 minimum)
        if len(annotation.get("key_facts", [])) < 2:
            errors.append("Add at least 2 key facts")
        
        return (len(errors) == 0, errors)
    
    def interactive_create(self):
        """CLI to build annotations one by one."""
        print("\n" + "="*70)
        print("GOLD CORPUS BUILDER - Interactive Mode")
        print("="*70)
        print("Type 'exit' anytime to quit.\n")
        
        while True:
            print(f"\nClause types: {', '.join(CLAUSE_TYPES)}")
            clause_type = input("1. Clause type > ").strip()
            if clause_type.lower() == 'exit':
                break
            
            if clause_type not in CLAUSE_TYPES:
                print(f"  ✗ Invalid. Must be one of: {CLAUSE_TYPES}")
                continue
            
            clause_id = input("2. Clause ID (e.g., indemnity_001) > ").strip()
            if not clause_id:
                print("  ✗ ID cannot be empty")
                continue
            
            print("3. Paste original clause (end with blank line):")
            lines = []
            while True:
                line = input()
                if not line.strip():
                    break
                lines.append(line)
            original_text = "\n".join(lines).strip()
            
            if not original_text:
                print("  ✗ Clause cannot be empty")
                continue
            
            # Create template
            annotation = self.create_annotation_template(
                original_text, clause_type, clause_id
            )
            
            # Get simplification
            print("\n4. Write simplified explanation (1-3 sentences, plain language):")
            annotation["gold_simplification"] = input("> ").strip()
            
            # Get parties
            print("\n5. Enter parties as 'Name | role' (e.g., 'Company A | obligor')")
            print("   Roles: obligor, beneficiary, third-party, general")
            print("   (Blank line to finish)")
            parties = []
            while True:
                line = input("> ").strip()
                if not line:
                    break
                try:
                    name, role = [x.strip() for x in line.split("|", 1)]
                    parties.append({"text": name, "role": role})
                except ValueError:
                    print("  ✗ Format: Name | role")
            annotation["entities"]["parties"] = parties
            
            # Get obligations
            print("\n6. Obligations (verbs like 'defend', 'indemnify', etc.)")
            print("   (Blank line to finish)")
            obligations = []
            while True:
                line = input("> ").strip()
                if not line:
                    break
                obligations.append(line)
            annotation["entities"]["obligations"] = obligations
            
            # Get coverage
            print("\n7. Coverage (what's covered, e.g., 'claims', 'damages')")
            print("   (Blank line to finish)")
            coverage = []
            while True:
                line = input("> ").strip()
                if not line:
                    break
                coverage.append(line)
            annotation["entities"]["coverage"] = coverage
            
            # Get exceptions
            print("\n8. Exceptions (e.g., 'gross negligence', 'force majeure')")
            print("   (Blank line to finish)")
            exceptions = []
            while True:
                line = input("> ").strip()
                if not line:
                    break
                exceptions.append(line)
            annotation["entities"]["exceptions"] = exceptions
            
            # Get amounts
            print("\n9. Monetary amounts (e.g., '₹5,00,000')")
            print("   (Blank line to finish)")
            amounts = []
            while True:
                line = input("> ").strip()
                if not line:
                    break
                amounts.append(line)
            annotation["entities"]["amounts"] = amounts
            
            # Get key facts
            print("\n10. Key facts (2-3 critical points to preserve)")
            print("    (Blank line to finish)")
            key_facts = []
            while True:
                line = input("> ").strip()
                if not line:
                    break
                key_facts.append(line)
            annotation["key_facts"] = key_facts
            
            # Validate
            print("\n11. Validating annotation...")
            ok, errors = self.validate_annotation(annotation)
            
            if not ok:
                print("  ✗ Validation failed:")
                for error in errors:
                    print(f"    - {error}")
                print("  Annotation NOT saved. Please retry.")
                continue
            
            # Save
            path = self.save_annotation(annotation)
            print(f"  ✓ Saved to {path}")
            
            # Count existing
            total = sum(1 for _ in self.root.glob("*/*.json"))
            print(f"  Total annotations: {total}")


if __name__ == "__main__":
    builder = GoldCorpusBuilder()
    builder.interactive_create()
