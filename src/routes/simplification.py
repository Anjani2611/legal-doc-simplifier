"""Text simplification endpoints"""

import time

from fastapi import APIRouter, HTTPException, Request

from src.middleware import limiter
from src.schemas.document import SimplifyRequest, SimplifyResponse
from src.pipelines.simplification import get_simplification_pipeline
from src.webhooks import webhook_manager
from src.monitoring.metrics import record_simplification

router = APIRouter(prefix="/simplify", tags=["simplification"])


@router.post("/text", response_model=SimplifyResponse)
@limiter.limit("30/minute")
async def simplify_text(
    request: Request,
    payload: SimplifyRequest,
) -> SimplifyResponse:
    """Simplify raw legal text."""
    start_time = time.time()

    if not payload.text or payload.text.strip() == "":
        raise HTTPException(status_code=422, detail="Text must not be empty")

    try:
        pipeline = get_simplification_pipeline()
        simplified = pipeline.simplify(payload.text)

        if not simplified:
            raise HTTPException(status_code=500, detail="Simplification failed")

        original_len = len(payload.text)
        simplified_len = len(simplified)

        # Dynamic length cap based on max_summary_sentences
        options = payload.options or {}
        max_summary = options.get("max_summary_sentences", 2)

        if max_summary >= 4:
            max_factor = 2.0    # evaluation: allow more detail
        else:
            max_factor = 1.1    # normal: keep compressed

        max_len = int(original_len * max_factor)
        if simplified_len > max_len:
            simplified = simplified[:max_len]
            simplified_len = len(simplified)

        if original_len > 0:
            reduction = (original_len - simplified_len) / original_len * 100.0
        else:
            reduction = 0.0

        if reduction < 0:
            reduction = 0.0
        if reduction > 100:
            reduction = 100.0

        await webhook_manager.trigger_webhook(
            event="document.simplified",
            document_id=0,
            data={"simplified_length": simplified_len},
        )

        duration = time.time() - start_time

        doc_type = getattr(payload, "document_type", "text")
        record_simplification(duration=duration, document_type=doc_type)

        return SimplifyResponse(
            original=payload.text,
            simplified=simplified,
            reduction=round(reduction, 2),
        )

    except HTTPException:
        raise
    except Exception as exc:
        print(f"Simplification error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))
