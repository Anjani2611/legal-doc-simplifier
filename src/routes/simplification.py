"""Text simplification endpoints (JSON contract)."""

import json
import logging
import time

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from src.middleware import limiter
from src.schemas.document import SimplifyRequest  # has .text, .options, .document_type
from src.pipelines.simplification import get_simplification_pipeline
from src.monitoring.metrics import record_simplification
from src.webhooks import webhook_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/simplify", tags=["simplification"])

MAX_DOC_SIZE = 8000  # characters

_pipeline = get_simplification_pipeline()


@router.post("/text")
@limiter.limit("30/minute")
async def simplify_text(
    request: Request,
    payload: SimplifyRequest,
):
    """
    Simplify raw legal text and return structured JSON as produced by the model.

    Success response shape:
    {
      "summary": "...",
      "clauses": [...],
      "warnings": [...]
    }

    Error codes:
    - DOC_TOO_LONG
    - NOT_LEGAL_DOCUMENT
    - MODEL_OUTPUT_INVALID
    - MODEL_ERROR
    """
    start_time = time.time()

    text = payload.text or ""
    if not text.strip():
        raise HTTPException(status_code=422, detail="Text must not be empty")

    # 4.1: size guardrail
    if len(text) > MAX_DOC_SIZE:
        return JSONResponse(
            {
                "code": "DOC_TOO_LONG",
                "message": (
                    f"Document exceeds {MAX_DOC_SIZE} characters. "
                    "Please split into smaller sections."
                ),
                "max_size": MAX_DOC_SIZE,
                "current_size": len(text),
            },
            status_code=400,
        )

    try:
        options = payload.options or {}
        target_style = options.get(
            "target_style",
            "Plain English, numbered clauses, short sentences",
        )
        max_words_per_clause = options.get("max_words_per_clause", 100)
        language_mix = options.get("language_mix", "English with legal terms")

        # 3.3: call pipeline → JSON string
        raw_output = _pipeline.simplify(
            text=text,
            target_style=target_style,
            max_words_per_clause=max_words_per_clause,
            language_mix=language_mix,
        )

        # Try to parse as JSON
        try:
            result = json.loads(raw_output)

            # NOT_LEGAL_DOCUMENT case
            if result.get("error") == "NOT_LEGAL_DOCUMENT":
                return JSONResponse(
                    {
                        "code": "NOT_LEGAL_DOCUMENT",
                        "message": result.get(
                            "message",
                            "Input does not appear to be a legal document or is too short.",
                        ),
                    },
                    status_code=400,
                )

            # Normal success: record metrics and trigger webhook
            duration = time.time() - start_time
            doc_type = getattr(payload, "document_type", "text")
            record_simplification(duration=duration, document_type=doc_type)

            await webhook_manager.trigger_webhook(
                event="document.simplified",
                document_id=0,
                data={"duration": duration},
            )

            return result

        except json.JSONDecodeError as e:
            logger.error(f"JSON parse failed: {e}; raw_output={raw_output!r}")
            return JSONResponse(
                {
                    "code": "MODEL_OUTPUT_INVALID",
                    "message": "Model output was not valid JSON",
                },
                status_code=500,
            )

    except HTTPException:
        # Already a proper HTTP error
        raise
    except Exception as e:
        logger.error(f"Simplification failed: {e}")
        return JSONResponse(
            {
                "code": "MODEL_ERROR",
                "message": "Simplification failed, please try again",
            },
            status_code=500,
        )
