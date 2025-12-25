"""Text simplification endpoints"""

from fastapi import APIRouter, HTTPException, Request
from src.middleware import limiter
from src.schemas.document import SimplifyRequest, SimplifyResponse
from src.pipelines.simplification import get_simplification_pipeline  # adjust path if different

router = APIRouter(prefix="/simplify", tags=["simplification"])


@router.post("/text", response_model=SimplifyResponse)
# @limiter.limit("30/minute")
async def simplify_text(
    request: Request,              # used for rate logging
    payload: SimplifyRequest,      # <-- JSON body goes here
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
