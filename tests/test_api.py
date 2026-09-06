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


def test_service_selects_qwen_provider_when_configured(monkeypatch):
    monkeypatch.setenv("DASHSCOPE_API_KEY", "sk-test-valid-key")
    diagnosis_service.reset_provider()
    provider = diagnosis_service.get_provider()
    from backend.services.qwen_provider import QwenDiagnosisProvider
    assert isinstance(provider, QwenDiagnosisProvider)
    diagnosis_service.reset_provider()


def test_service_selects_gemini_provider_when_qwen_absent_but_gemini_configured(monkeypatch):
    # No live network call happens here: constructing a genai.Client is a
    # local operation, and no diagnose()/generate_content() call is made.
    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key")
    diagnosis_service.reset_provider()
    provider = diagnosis_service.get_provider()
    from backend.services.gemini_provider import GeminiDiagnosisProvider
    assert isinstance(provider, GeminiDiagnosisProvider)
    diagnosis_service.reset_provider()


def test_service_falls_back_to_mock_when_gemini_key_is_placeholder(monkeypatch):
    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "your_key_here")
    diagnosis_service.reset_provider()
    provider = diagnosis_service.get_provider()
    assert isinstance(provider, diagnosis_service.MockDiagnosisProvider)
    diagnosis_service.reset_provider()


def test_qwen_still_takes_priority_over_gemini_when_both_configured(monkeypatch):
    monkeypatch.setenv("DASHSCOPE_API_KEY", "sk-test-valid-key")
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key")
    diagnosis_service.reset_provider()
    provider = diagnosis_service.get_provider()
    from backend.services.qwen_provider import QwenDiagnosisProvider
    assert isinstance(provider, QwenDiagnosisProvider)
    diagnosis_service.reset_provider()



def test_service_run_diagnosis_matches_model():
    result = diagnosis_service.run_diagnosis("x.png", data=b"abc", content_type="image/png")
    assert result["filename"] == "x.png"
    assert 0 <= result["confidence"] <= 1


def test_service_answer_followup_returns_string():
    assert isinstance(diagnosis_service.answer_followup("why?"), str)


# --- Member 2 context & optional question tests -----------------------------

def test_diagnose_with_optional_question():
    diagnosis_service.reset_provider()
    response = client.post(
        "/diagnose",
        files={"image": VALID_IMAGE},
        data={"question": "Why are yellow spots appearing on leaves?"},
    )
    assert response.status_code == 200
    ctx = diagnosis_service.get_latest_context()
    assert ctx is not None
    assert ctx["original_question"] == "Why are yellow spots appearing on leaves?"
    assert ctx["diagnosis"] == "Early Blight"
    assert ctx["confidence"] == 0.70


def test_diagnose_without_question_sets_none_original_question():
    diagnosis_service.reset_provider()
    response = client.post("/diagnose", files={"image": VALID_IMAGE})
    assert response.status_code == 200
    ctx = diagnosis_service.get_latest_context()
    assert ctx is not None
    assert ctx["original_question"] is None


def test_session_context_used_in_followup():
    diagnosis_service.reset_provider()

    # Create a spy provider to verify context is received
    received_contexts = []

    class ContextSpyProvider:
        def diagnose(self, image: diagnosis_service.ImageInput) -> dict:
            return {
                "filename": image.filename,
                "diagnosis": "Powdery Mildew",
                "confidence": 0.85,
                "advice": "Apply fungicide.",
                "needs_expert": False,
            }

        def answer_followup(self, question: str, context: diagnosis_service.Optional[dict] = None) -> str:
            received_contexts.append((question, context))
            return f"Answer for '{question}' with diag={context.get('diagnosis') if context else None}"

    diagnosis_service._provider = ContextSpyProvider()

    # Step 1: Diagnose with question
    diag_resp = client.post(
        "/diagnose",
        files={"image": VALID_IMAGE},
        data={"question": "What is this white powder?"},
    )
    assert diag_resp.status_code == 200
    assert diag_resp.json()["diagnosis"] == "Powdery Mildew"

    # Step 2: Ask follow-up
    followup_resp = client.post(
        "/ask-followup",
        json={"question": "How often to apply fungicide?"},
    )
    assert followup_resp.status_code == 200
    assert "Answer for 'How often to apply fungicide?' with diag=Powdery Mildew" in followup_resp.json()["answer"]

    # Verify context details passed to provider
    assert len(received_contexts) == 1
    q, ctx = received_contexts[0]
    assert q == "How often to apply fungicide?"
    assert ctx == {
        "diagnosis": "Powdery Mildew",
        "confidence": 0.85,
        "advice": "Apply fungicide.",
        "needs_expert": False,
        "original_question": "What is this white powder?",
    }
    diagnosis_service.reset_provider()

