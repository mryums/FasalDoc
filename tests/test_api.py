"""Minimal offline API tests for the FasalDoc backend.

These tests use FastAPI's TestClient and never call any external/AI service.
"""
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_home_returns_200():
    response = client.get("/")
    assert response.status_code == 200


def test_ask_followup_valid_question():
    response = client.post("/ask-followup", json={"question": "How do I treat blight?"})
    assert response.status_code == 200
    assert response.json()["question"] == "How do I treat blight?"


def test_ask_followup_empty_question_rejected():
    # Whitespace-only question triggers the validate_question() -> HTTP 400 path.
    response = client.post("/ask-followup", json={"question": "   "})
    assert response.status_code == 400


def test_diagnose_invalid_file_type_returns_400():
    response = client.post(
        "/diagnose",
        files={"image": ("leaf.gif", b"fake-image-bytes", "image/gif")},
    )
    assert response.status_code == 400
