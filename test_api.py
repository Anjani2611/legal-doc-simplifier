"""API integration tests"""

import requests
import json
import time
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"

def test_health():
    """Test health endpoint"""
    print("\n🏥 Testing /health...")
    resp = requests.get(f"{BASE_URL}/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["database"] == "ok"
    print(f"✓ Health check passed: {data['status']}")

def test_list_documents():
    """Test document listing"""
    print("\n📄 Testing GET /documents...")
    resp = requests.get(f"{BASE_URL}/documents")
    assert resp.status_code == 200
    data = resp.json()
    print(f"✓ Found {data['total']} documents")
    return data

def test_upload_document():
    """Test file upload"""
    print("\n📤 Testing POST /documents/upload...")
    
    # Create test file
    test_content = """SERVICE AGREEMENT
    Whereas, the parties desire to enter into a service agreement...
    The Provider shall deliver services without limitation on liability."""
    
    with open("test_upload.txt", "w") as f:
        f.write(test_content)
    
    with open("test_upload.txt", "rb") as f:
        files = {"file": f}
        resp = requests.post(
            f"{BASE_URL}/documents/upload",
            files=files,
            data={"document_type": "contract"}
        )
    
    assert resp.status_code == 200
    data = resp.json()
    print(f"✓ Uploaded document ID: {data['id']}")
    
    # Cleanup
    Path("test_upload.txt").unlink()
    
    return data["id"]

def test_simplify_text():
    """Test text simplification"""
    print("\n✨ Testing POST /simplify/text...")
    
    legal_text = """Notwithstanding any provision herein to the contrary, 
    the indemnifying party shall defend, indemnify, and hold harmless 
    the indemnified parties from and against any and all claims."""
    
    resp = requests.post(
        f"{BASE_URL}/simplify/text",
        json={"text": legal_text}
    )
    
    assert resp.status_code == 200
    data = resp.json()
    print(f"✓ Original: {len(data['original'])} chars")
    print(f"✓ Simplified: {len(data['simplified'])} chars")
    print(f"✓ Reduction: {data['reduction']}%")

def test_analyze_document(doc_id):
    """Test risk analysis"""
    print(f"\n⚠️  Testing POST /analyze/document/{doc_id}...")
    
    resp = requests.post(f"{BASE_URL}/analyze/document/{doc_id}")
    
    assert resp.status_code == 200
    data = resp.json()
    print(f"✓ Risks detected: {data['risks_detected']}")
    print(f"✓ Average risk score: {data['avg_risk_score']}")
    
    if data['risks']:
        for risk in data['risks'][:3]:
            print(f"  - {risk['risk_level']}: {risk['description']}")

def test_simplify_document(doc_id):
    """Test document simplification"""
    print(f"\n📝 Testing POST /simplify/document/{doc_id}...")
    
    resp = requests.post(f"{BASE_URL}/simplify/document/{doc_id}")
    
    assert resp.status_code == 200
    data = resp.json()
    print(f"✓ Status: {data['status']}")
    print(f"✓ Original: {data['original_length']} chars")
    print(f"✓ Simplified: {data['simplified_length']} chars")

def main():
    """Run all tests"""
    print("=" * 60)
    print("Legal Document Simplifier - API Test Suite")
    print("=" * 60)
    
    try:
        # Basic health check
        test_health()
        
        # List documents
        test_list_documents()
        
        # Upload
        doc_id = test_upload_document()
        time.sleep(2)  # Let file process
        
        # Simplify text
        test_simplify_text()
        
        # Analyze
        test_analyze_document(doc_id)
        
        # Simplify document
        test_simplify_document(doc_id)
        
        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
    
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()
