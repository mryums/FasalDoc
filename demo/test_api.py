import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_read_root():
    """Test baseline GET / endpoint"""
    response = client.get("/")
    assert response.status_code == 200

def test_diagnose_no_image():
    """Negative Test: Diagnose endpoint without image should return validation error"""
    response = client.post("/diagnose")
    assert response.status_code == 422  # Unprocessable Entity

def test_ask_followup_valid():
    """Test follow-up question endpoint"""
    payload = {"question": "Iska ilaaj kya hai?"}
    response = client.post("/ask-followup", json=payload)
    assert response.status_code == 200
    assert "answer" in response.json()