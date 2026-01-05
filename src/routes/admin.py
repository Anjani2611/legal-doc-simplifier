from datetime import datetime
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/admin", tags=["admin"])

KNOWN_BAD_FILE = Path("data/known_bad.jsonl")


class MarkBadRequest(BaseModel):
    input_text: str
    tag: Literal["too_long", "too_technical", "struct_lost", "hallucination", "other"]
    short_comment: str
    input_path: str = ""
    output_snapshot_path: str = ""


@router.post("/mark_bad")
async def mark_bad(req: MarkBadRequest):
    """
    Append a bad output to known_bad.jsonl for error analysis and future eval.
    """
    import json
    
    record = {
        "id": datetime.utcnow().strftime("%Y-%m-%d-%H%M%S"),
        "tag": req.tag,
        "short_comment": req.short_comment,
        "input_path": req.input_path,
        "output_snapshot_path": req.output_snapshot_path,
        "input_text_length": len(req.input_text),
        "timestamp": datetime.utcnow().isoformat(),
    }
    
    # Ensure data directory exists
    KNOWN_BAD_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    # Append as JSONL (one JSON per line)
    with open(KNOWN_BAD_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    
    return {
        "status": "recorded",
        "id": record["id"],
        "tag": req.tag,
    }
