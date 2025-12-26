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
@limiter.limit("30/minute")   # 30 simplifications per minute per IP
async def simplify_text(
    request: Request,
    payload: SimplifyRequest,
) -> SimplifyResponse:
    """Simplify raw legal text."""
    start_time = time.time()

    try:
        pipeline = get_simplification_pipeline()
        simplified = pipeline.simplify(payload.text)

        if not simplified:
            raise HTTPException(status_code=500, detail="Simplification failed")

        reduction = ((len(payload.text) - len(simplified)) / len(payload.text)) * 100

        # Trigger webhook after successful simplification
        await webhook_manager.trigger_webhook(
            event="document.simplified",
            document_id=0,  # TODO: replace with real document_id if available
            data={"simplified_length": len(simplified)},
        )

        duration = time.time() - start_time

        # Metrics: simplification count + duration
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
        # Optional: replace with logger.error(...)
        print(f"Simplification error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))
