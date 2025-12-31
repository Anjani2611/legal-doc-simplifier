import csv
from datetime import datetime
from pathlib import Path

LABELS_PATH = Path("data/known_bad/labels.csv")

def add_bad_case(doc_id: str, tag: str, comment: str) -> None:
    if tag not in {"too_long", "too_technical", "struct_lost", "hallucination"}:
        raise ValueError(f"Invalid tag: {tag}")

    with LABELS_PATH.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            doc_id,
            tag,
            comment,
            datetime.utcnow().isoformat()
        ])
    print(f"Added: {doc_id} | {tag}")

if __name__ == "__main__":
    doc_id = input("doc_id (e.g., doc_001): ").strip()
    tag = input("tag (too_long|too_technical|struct_lost|hallucination): ").strip()
    comment = input("short_comment: ").strip()
    add_bad_case(doc_id, tag, comment)
