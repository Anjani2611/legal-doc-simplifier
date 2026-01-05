from fastapi import FastAPI, UploadFile, File, Query, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import json
from pathlib import Path
from datetime import datetime
import PyPDF2
from docx import Document

from src.export.pdf_generator import PDFGenerator
from src.export.json_exporter import JSONExporter
from src.export.simple_pdf_generator import SimplePDFGenerator
from src.pipelines.simplification import get_simplification_pipeline

# -----------------------------------------------------------------------------
# App setup
# -----------------------------------------------------------------------------

app = FastAPI(
    title="Legal Document Simplifier",
    description="Phase 5: File Upload & Export",
    version="5.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static frontend
if Path("frontend").exists():
    app.mount("/static", StaticFiles(directory="frontend"), name="static")

# Session storage
SESSION_DIR = Path("sessions")
SESSION_DIR.mkdir(exist_ok=True)

# Single shared pipeline instance (lazy singleton)
pipeline = get_simplification_pipeline()

# -----------------------------------------------------------------------------
# Helper functions
# -----------------------------------------------------------------------------

def _extract_pdf_text(file_path: str) -> str:
    text = ""
    try:
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                page_text = page.extract_text() or ""
                text += page_text + "\n"
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"PDF extraction failed: {e}")
    return text.strip()


def _extract_docx_text(file_path: str) -> str:
    text = ""
    try:
        doc = Document(file_path)
        for p in doc.paragraphs:
            text += (p.text or "") + "\n"
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"DOCX extraction failed: {e}")
    return text.strip()


def _session_json_path(session_id: str) -> Path:
    return SESSION_DIR / f"{session_id}.json"


def _save_session(session_id: str, metadata: dict) -> None:
    p = _session_json_path(session_id)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False)


def _load_session(session_id: str) -> dict:
    p = _session_json_path(session_id)
    if not p.exists():
        raise HTTPException(status_code=404, detail="Session not found")
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

# -----------------------------------------------------------------------------
# Core endpoints
# -----------------------------------------------------------------------------

@app.get("/")
def root():
    return {"message": "Legal Document Simplifier - Phase 5", "frontend": "/app"}


@app.get("/app", response_class=HTMLResponse)
def serve_app():
    index_path = Path("frontend/index.html")
    if not index_path.exists():
        raise HTTPException(status_code=500, detail="frontend/index.html not found")
    return index_path.read_text(encoding="utf-8")


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Phase 5: upload PDF/DOCX, extract text, run full pipeline,
    persist session, return structured result.
    """
    try:
        if file.content_type not in [
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ]:
            raise HTTPException(status_code=400, detail="Only PDF and DOCX files allowed")

        content = await file.read()
        if len(content) > 25 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File too large (max 25MB)")

        session_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        session_dir = SESSION_DIR / session_id
        session_dir.mkdir(parents=True, exist_ok=True)

        file_path = session_dir / file.filename
        with open(file_path, "wb") as f:
            f.write(content)

        if file.filename.lower().endswith(".pdf"):
            text = _extract_pdf_text(str(file_path))
        else:
            text = _extract_docx_text(str(file_path))

        # Pipeline returns JSON string → parse to dict
        simplify_json = pipeline.simplify(text)
        simplify_output = json.loads(simplify_json)

        metadata = {
            "session_id": session_id,
            "filename": file.filename,
            "file_path": str(file_path),
            "upload_timestamp": datetime.now().isoformat(),
            "extracted_text": text,
            "simplify_output": simplify_output,
        }
        _save_session(session_id, metadata)

        return {
            "session_id": session_id,
            "filename": file.filename,
            "message": "File uploaded and processed successfully",
            "simplify_output": simplify_output,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# -----------------------------------------------------------------------------
# Exports
# -----------------------------------------------------------------------------

@app.post("/export/pdf")
async def export_pdf(session_id: str = Query(...)):
    """Full analysis PDF."""
    try:
        metadata = _load_session(session_id)
        gen = PDFGenerator()
        pdf_bytes = gen.generate(
            filename=metadata["filename"],
            simplify_output=metadata["simplify_output"],
            timestamp=metadata["upload_timestamp"],
        )

        # FastAPI FileResponse from bytes: use StreamingResponse-like pattern
        from fastapi.responses import Response

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{Path(metadata["filename"]).stem}_report.pdf"'
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/export/pdf/simple")
async def export_simple_pdf(session_id: str = Query(...)):
    """Simplified-text-only PDF."""
    try:
        metadata = _load_session(session_id)
        gen = SimplePDFGenerator()
        pdf_bytes = gen.generate(
            filename=metadata["filename"],
            simplify_output=metadata["simplify_output"],
            timestamp=metadata["upload_timestamp"],
        )

        from fastapi.responses import Response

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{Path(metadata["filename"]).stem}_simplified.pdf"'
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/export/json")
async def export_json(session_id: str = Query(...)):
    """Structured JSON export."""
    try:
        metadata = _load_session(session_id)
        exporter = JSONExporter()
        json_bytes = exporter.export(
            filename=metadata["filename"],
            simplify_output=metadata["simplify_output"],
            upload_timestamp=metadata["upload_timestamp"],
        )

        from fastapi.responses import Response

        return Response(
            content=json_bytes,
            media_type="application/json",
            headers={
                "Content-Disposition": f'attachment; filename="{Path(metadata["filename"]).stem}_data.json"'
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# -----------------------------------------------------------------------------
# Session maintenance
# -----------------------------------------------------------------------------

@app.get("/session/{session_id}")
def get_session(session_id: str):
    try:
        metadata = _load_session(session_id)
        return {
            "session_id": session_id,
            "filename": metadata["filename"],
            "upload_timestamp": metadata["upload_timestamp"],
            "clauses_count": len(metadata.get("simplify_output", {}).get("clauses", [])),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/session/{session_id}")
def delete_session(session_id: str):
    try:
        session_dir = SESSION_DIR / session_id
        if session_dir.exists():
            import shutil
            shutil.rmtree(session_dir)

        json_path = _session_json_path(session_id)
        if json_path.exists():
            json_path.unlink()

        return {"status": "deleted", "session_id": session_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# -----------------------------------------------------------------------------
# Phase‑4 compatible text endpoint (used by /app.js)
# -----------------------------------------------------------------------------

@app.get("/simplify/text")
def simplify_text(text: str = Query(...), target_level: str = Query(default="simple")):
    """
    Phase‑4 style endpoint used by the new UI.

    It calls SimplificationPipeline.simplify(text), which returns a JSON string,
    then parses it to a dict so the frontend gets `summary`, `clauses`, etc.
    """
    try:
        simplify_json = pipeline.simplify(text)
        result = json.loads(simplify_json)
        return result
    except Exception as e:
        import traceback
        print("ERROR in simplify_text:", e)
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Simplification error: {e}")

# -----------------------------------------------------------------------------

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
