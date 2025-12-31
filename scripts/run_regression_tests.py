import json
import os
from datetime import datetime
from pathlib import Path

import httpx

TEST_DOCS_DIR = Path("tests/docs")
META_PATH = TEST_DOCS_DIR / "meta.json"
OUTPUT_ROOT = Path("tests/outputs")

BACKEND_URL = os.getenv("SIMPLIFIER_URL", "http://127.0.0.1:8000")

def load_meta():
    return json.loads(META_PATH.read_text(encoding="utf-8"))

def main():
    run_id = datetime.utcnow().strftime("run_%Y%m%d_%H%M%S")
    out_dir = OUTPUT_ROOT / run_id
    out_dir.mkdir(parents=True, exist_ok=True)

    meta = load_meta()
    client = httpx.Client(timeout=60)

    print(f"Running regression tests... (run_id: {run_id})")

    for filename, cfg in meta.items():
        raw_path = TEST_DOCS_DIR / filename
        if not raw_path.exists():
            print(f"⚠️ {filename} not found, skipping")
            continue

        text = raw_path.read_text(encoding="utf-8")
        print(f"\n📄 Processing: {filename}")

        payload = {
            "text": text,
            "style": cfg["style"],
            "max_words_per_clause": cfg["max_words_per_clause"],
            "generation_params": {
                "temperature": 0.2,
                "top_p": 0.9
            }
        }

        resp = client.post(f"{BACKEND_URL}/simplify/text", json=payload)
        resp.raise_for_status()

        data = {
            "doc_id": filename,
            "raw_path": str(raw_path),
            "style": cfg["style"],
            "model_params": payload["generation_params"],
            "output": resp.json(),
            "timestamp": datetime.utcnow().isoformat()
        }

        out_file = out_dir / f"{filename.replace('.txt', '')}_out.json"
        out_file.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        print(f"   ✅ Saved to {out_file}")

    client.close()
    print(f"\n✅ All outputs saved to: {out_dir}")

if __name__ == "__main__":
    main()
