"""Offline API tests for the FasalDoc backend.

Everything here uses FastAPI's TestClient / direct service calls and NEVER
makes an external or AI/cloud request.
"""
from fastapi.testclient import TestClient

from backend.main import app
from backend.services import diagnosis_service

client = TestClient(app)

VALID_IMAGE = ("leaf.jpg", b"fake-jpeg-bytes", "image/jpeg")


# --- Health -----------------------------------------------------------------

def test_home_returns_200():
    response = client.get("/")
    assert response.status_code == 200


def test_home_message():
    assert client.get("/").json() == {"message": "FasalDoc API is running"}


# --- /ask-followup ----------------------------------------------------------

def test_ask_followup_valid_question():
    response = client.post("/ask-followup", json={"question": "How do I treat blight?"})
    assert response.status_code == 200
    assert response.json()["question"] == "How do I treat blight?"


def test_ask_followup_returns_nonempty_answer():
    body = client.post("/ask-followup", json={"question": "When to water?"}).json()
    assert set(body) == {"question", "answer"}
    assert body["answer"].strip()


def test_ask_followup_empty_question_rejected():
    # Whitespace-only question triggers the validate_question() -> HTTP 400 path.
    response = client.post("/ask-followup", json={"question": "   "})
    assert response.status_code == 400


def test_ask_followup_missing_question_is_422():
    response = client.post("/ask-followup", json={})
    assert response.status_code == 422


# --- /diagnose --------------------------------------------------------------

def test_diagnose_valid_image_returns_contract():
    response = client.post("/diagnose", files={"image": VALID_IMAGE})
    assert response.status_code == 200
    data = response.json()
    assert set(data) == {"filename", "diagnosis", "confidence", "advice", "needs_expert"}
    assert data["filename"] == "leaf.jpg"
    assert 0 <= data["confidence"] <= 1
    assert isinstance(data["needs_expert"], bool)


def test_diagnose_invalid_file_type_returns_400():
    response = client.post(
        "/diagnose",
        files={"image": ("leaf.gif", b"fake-image-bytes", "image/gif")},
    )
    assert response.status_code == 400


def test_diagnose_empty_image_returns_400():
    response = client.post(
        "/diagnose",
        files={"image": ("empty.jpg", b"", "image/jpeg")},
    )
    assert response.status_code == 400


def test_diagnose_too_large_returns_400():
    oversized = b"x" * (10 * 1024 * 1024 + 1)
    response = client.post(
        "/diagnose",
        files={"image": ("big.jpg", oversized, "image/jpeg")},
    )
    assert response.status_code == 400


def test_diagnose_missing_field_is_422():
    response = client.post("/diagnose")
    assert response.status_code == 422


# --- OpenAPI / docs ---------------------------------------------------------

def test_docs_available():
    assert client.get("/docs").status_code == 200


def test_openapi_exposes_expected_endpoints():
    paths = client.get("/openapi.json").json()["paths"]
    assert {"/", "/diagnose", "/ask-followup"}.issubset(paths.keys())


# --- CORS -------------------------------------------------------------------

def test_cors_allows_local_frontend_origin():
    response = client.get("/", headers={"Origin": "http://localhost:5173"})
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"


# --- Service layer (offline mock fallback) ----------------------------------

def test_service_falls_back_to_mock_without_credentials(monkeypatch):
    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
    diagnosis_service.reset_provider()
    provider = diagnosis_service.get_provider()
    assert isinstance(provider, diagnosis_service.MockDiagnosisProvider)


def test_service_run_diagnosis_matches_model():
    result = diagnosis_service.run_diagnosis("x.png", data=b"abc", content_type="image/png")
    assert result["filename"] == "x.png"
    assert 0 <= result["confidence"] <= 1


def test_service_answer_followup_returns_string():
    assert isinstance(diagnosis_service.answer_followup("why?"), str)
