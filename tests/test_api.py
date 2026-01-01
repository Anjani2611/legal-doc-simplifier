import pytest
from httpx import AsyncClient
from src.main import app


@pytest.mark.asyncio
async def test_health_endpoint():
    """Test /health returns 200 and valid structure."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_simplify_text_basic():
    """Test /simplify/text with valid input."""
    payload = {
        "text": "Either party may terminate this Agreement upon thirty (30) days prior written notice.",
        "target_level": "simple",
        "language": "en",
        "options": {
            "keep_bullets": False,
            "max_summary_sentences": 2
        }
    }
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/simplify/text", json=payload)
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert "original" in data
        assert "simplified" in data
        assert "reduction" in data
        
        # Validate content
        assert len(data["original"]) > 0
        assert len(data["simplified"]) > 0
        assert isinstance(data["reduction"], float)
        assert 0 <= data["reduction"] <= 100


@pytest.mark.asyncio
async def test_simplify_text_empty_input():
    """Test /simplify/text rejects empty text."""
    payload = {
        "text": "",
        "target_level": "simple",
        "language": "en",
        "options": {"keep_bullets": False, "max_summary_sentences": 2}
    }
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/simplify/text", json=payload)
        assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_simplify_text_invalid_level():
    """Test /simplify/text rejects invalid target_level."""
    payload = {
        "text": "Some legal text here.",
        "target_level": "invalid_level",
        "language": "en",
        "options": {"keep_bullets": False, "max_summary_sentences": 2}
    }
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/simplify/text", json=payload)
        assert response.status_code == 422


@pytest.mark.asyncio
async def test_simplify_text_output_reduction():
    """Test that simplified text is shorter than original."""
    payload = {
        "text": "This is a longer legal document that contains multiple clauses and provisions which require careful analysis and consideration by both parties involved in the transaction.",
        "target_level": "simple",
        "language": "en",
        "options": {"keep_bullets": False, "max_summary_sentences": 2}
    }
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/simplify/text", json=payload)
        assert response.status_code == 200
        data = response.json()
        
        # Simplified should generally be shorter
        assert len(data["simplified"]) <= len(data["original"]) * 1.1  # Allow 10% margin


@pytest.mark.asyncio
async def test_simplify_text_preserves_meaning():
    """Test that key numbers/dates are preserved in simplification."""
    payload = {
        "text": "The contract expires on January 15, 2025 and requires 30 days notice for termination.",
        "target_level": "simple",
        "language": "en",
        "options": {"keep_bullets": False, "max_summary_sentences": 2}
    }
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/simplify/text", json=payload)
        assert response.status_code == 200
        data = response.json()
        
        simplified_lower = data["simplified"].lower()
        
        # Check critical numbers preserved
        assert "30" in data["simplified"] or "thirty" in simplified_lower
        assert "2025" in data["simplified"] or "january" in simplified_lower
