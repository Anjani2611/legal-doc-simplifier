import json
import os
from datetime import datetime
from pathlib import Path

import httpx

TEST_DOCS_DIR = Path("tests/docs")
OUTPUT_ROOT = Path("tests/outputs")

BACKEND_URL = os.getenv("SIMPLIFIER_URL", "http://127.0.0.1:8000")


def load_doc_meta(filename: str) -> dict:
    """
    Load per-document metadata from tests/docs/<name>_meta.json.
    If not present, return an empty dict.
    """
    meta_path = TEST_DOCS_DIR / filename.replace(".txt", "_meta.json")
    if meta_path.exists():
        return json.loads(meta_path.read_text(encoding="utf-8"))
    return {}


def main():
    run_id = datetime.utcnow().strftime("run_%Y%m%d_%H%M%S")
    out_dir = OUTPUT_ROOT / run_id
    out_dir.mkdir(parents=True, exist_ok=True)

    client = httpx.Client(
        timeout=httpx.Timeout(
            connect=5,
            read=180,  # 3 minutes for model inference
            write=30,
            pool=5,
        )
    )


    print(f"Running regression tests... (run_id: {run_id})")

    # Iterate over all *_raw.txt test docs
    for raw_path in sorted(TEST_DOCS_DIR.glob("*_raw.txt")):
        filename = raw_path.name
        doc_meta = load_doc_meta(filename)

        text = raw_path.read_text(encoding="utf-8")
        print(f"\n📄 Processing: {filename}")

        payload = {
            "text": text,
            "document_type": doc_meta.get("document_type", "contract"),
            "target_level": doc_meta.get("target_level", "simple"),
            "language": doc_meta.get("language", "en"),
        }

        resp = client.post(f"{BACKEND_URL}/simplify/text", json=payload)
        resp.raise_for_status()

        data = {
            "doc_id": filename,
            "raw_path": str(raw_path),
            "meta": doc_meta,
            "request_payload": payload,
            "output": resp.json(),
            "timestamp": datetime.utcnow().isoformat(),
        }

        out_file = out_dir / f"{filename.replace('.txt', '')}_out.json"
        out_file.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"   ✅ Saved to {out_file}")

    client.close()
    print(f"\n✅ All outputs saved to: {out_dir}")


if __name__ == "__main__":
    main()
