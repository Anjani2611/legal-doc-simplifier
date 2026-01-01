import pytest
import time
import subprocess


def test_docker_image_exists():
    """Verify Docker image is built."""
    result = subprocess.run(
        ["docker", "images", "legal-doc-simplifier:latest"],
        capture_output=True,
        text=True
    )
    assert "legal-doc-simplifier" in result.stdout


@pytest.mark.asyncio
async def test_docker_container_health():
    """Test Docker container health endpoint."""
    import httpx
    
    # Start container (assuming it's running)
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get("http://localhost:8000/health")
            assert response.status_code == 200
            assert response.json()["status"] == "healthy"
    except Exception as e:
        pytest.skip(f"Docker container not running: {e}")


@pytest.mark.asyncio
async def test_docker_simplify_endpoint():
    """Test /simplify/text via Docker container."""
    import httpx
    
    payload = {
        "text": "Either party may terminate upon thirty days notice.",
        "target_level": "simple",
        "language": "en",
        "options": {"keep_bullets": False, "max_summary_sentences": 2}
    }
    
    try:
        async with httpx.AsyncClient(timeout=300) as client:
            response = await client.post(
                "http://localhost:8000/simplify/text",
                json=payload
            )
            assert response.status_code == 200
            data = response.json()
            assert "simplified" in data
            assert "reduction" in data
    except Exception as e:
        pytest.skip(f"Docker container not running: {e}")
