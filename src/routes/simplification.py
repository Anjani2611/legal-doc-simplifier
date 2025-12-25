"""Text simplification endpoints"""

from fastapi import APIRouter, HTTPException, Request
from src.middleware import limiter
from src.schemas.document import SimplifyRequest, SimplifyResponse
from src.pipelines.simplification import get_simplification_pipeline
from src.webhooks import webhook_manager  

router = APIRouter(prefix="/simplify", tags=["simplification"])


@router.post("/text", response_model=SimplifyResponse)
# @limiter.limit("30/minute")
async def simplify_text(
    request: Request,
    payload: SimplifyRequest,
):
    """
    Simplify raw legal text.
    """
    try:
        pipeline = get_simplification_pipeline()
        simplified = pipeline.simplify(payload.text)

        if not simplified:
            raise HTTPException(status_code=500, detail="Simplification failed")

        reduction = ((len(payload.text) - len(simplified)) / len(payload.text)) * 100

        # Webhook trigger after successful simplification
        await webhook_manager.trigger_webhook(
            "document.simplified",
            document_id:=0,  # agar doc_id nahi hai to yahan actual id use karo
            {"simplified_length": len(simplified)},
        )

        return SimplifyResponse(
            original=payload.text,
            simplified=simplified,
            reduction=round(reduction, 2),
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Simplification error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
