from fastapi import FastAPI

app = FastAPI(
    title="Legal Document Simplifier",
    version="0.1.0",
    description="Backend API for legal document simplification and analysis.",
)


@app.get("/", tags=["root"])
async def read_root():
    return {"message": "Legal Document Simplifier API is running"}


@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok"}
