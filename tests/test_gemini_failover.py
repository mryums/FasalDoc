"""Offline tests for resilient Gemini MODEL FAILOVER.

Nothing here touches the network: a scripted fake ``google.genai``-shaped
client decides, per model name, whether a call raises (with a transient or a
non-transient error) or answers. The chain under test is always

    gemini-test-primary -> gemini-test-fallback-a -> gemini-test-fallback-b

so the tests are independent of the real model names in .env, and the
production default chain is asserted separately.
"""
import json
import logging
import re

import pytest

from backend.services.diagnosis_service import ImageInput
from backend.services.gemini_provider import GeminiDiagnosisProvider, _model_chain

PRIMARY = "gemini-test-primary"
FALLBACK_A = "gemini-test-fallback-a"
FALLBACK_B = "gemini-test-fallback-b"

URDU_RE = re.compile(r"[\u0600-\u06FF]")

URDU_ADVICE = (
    "متاثرہ پتوں کو فوری طور پر ہٹا کر تلف کریں اور پودوں کے درمیان "
    "ہوا کی آمد و رفت بہتر بنائیں۔"
)
URDU_NAME = "ٹماٹر میں لیٹ بلائٹ"
ROM_ADVICE = (
    "Mutaasira patton ko foran hata dein aur paudon ke darmiyan hawa ki "
    "aamad-o-raft behtar banayein."
)
ROM_NAME = "Tamatar mein Late Blight"


@pytest.fixture(autouse=True)
def _hermetic_failover(monkeypatch):
    """ML off (Vision path only) + a fixed, predictable 3-model chain."""
    monkeypatch.setenv("FASALDOC_ML_ENABLED", "0")
    monkeypatch.setenv("GEMINI_MODEL", PRIMARY)
    monkeypatch.setenv("GEMINI_FALLBACK_MODELS", f"{FALLBACK_A},{FALLBACK_B}")


class _APIErrorShaped(RuntimeError):
    """Mimics the slice of ``google.genai.errors.APIError`` we classify:
    numeric ``code``, gRPC-style ``status`` and a ``message``."""

    def __init__(self, code, status, message="provider trouble"):
        super().__init__(f"{code} {status}. {message}")
        self.code = code
        self.status = status
        self.message = message


def _exhausted():
    return _APIErrorShaped(429, "RESOURCE_EXHAUSTED", "Quota exceeded for this model.")


def _unavailable():
    return _APIErrorShaped(503, "UNAVAILABLE", "The model is currently unavailable.")


def _auth_error():
    return _APIErrorShaped(401, "UNAUTHENTICATED", "API key not valid. Please pass a valid API key.")


def _bad_request():
    return _APIErrorShaped(400, "INVALID_ARGUMENT", "Unsupported input: corrupt image.")


class _FakeResponse:
    def __init__(self, text):
        self.text = text


_UNSET = object()


class _ScriptedModels:
    """client.models stand-in driven by per-model scripts.

    A script value is a text string (always answers that), an exception
    (always raises it) or a list consumed one entry per call — the LAST entry
    repeats once the list runs out, so "always fail" needs only `[exc]`.
    """

    def __init__(self, **scripts):
        self._scripts = scripts
        self._cursor = {}
        self.calls = []

    def generate_content(self, **kwargs):
        self.calls.append(kwargs)
        model = kwargs.get("model")
        script = self._scripts.get(model, _UNSET)
        if script is _UNSET:
            raise AssertionError(f"unscripted model called: {model!r}")
        if isinstance(script, list):
            index = self._cursor.get(model, 0)
            self._cursor[model] = index + 1
            script = script[index] if index < len(script) else script[-1]
        if isinstance(script, BaseException):
            raise script
        return _FakeResponse(script)

    @property
    def models_called(self):
        return [call["model"] for call in self.calls]


def _provider(expected_chain=None, **scripts):
    client_models = _ScriptedModels(**scripts)

    class _Client:
        models = client_models

    provider = GeminiDiagnosisProvider(client=_Client())
    assert provider.model_chain == (expected_chain or [PRIMARY, FALLBACK_A, FALLBACK_B])
    return provider, client_models


def _image(language="en"):
    return ImageInput(
        filename="leaf.jpg",
        content_type="image/jpeg",
        data=b"fake-jpeg-bytes",
        question="What is wrong with my tomato?",
        language=language,
    )


def _vision_json(diagnosis, advice, confidence=0.85, localized=None):
    payload = {
        "is_plant_photo": True,
        "diagnosis": diagnosis,
        "confidence": confidence,
        "advice": advice,
        "needs_expert": confidence < 0.6,
    }
    if localized is not None:
        payload["diagnosis_localized"] = localized
    return json.dumps(payload, ensure_ascii=False)


def _no_kb_grounding(provider):
    """Isolate the transport tests from KB retrieval side effects."""
    provider._retrieve_kb_entries = lambda *t: []
    return provider


# --- 1+2+3. Transient primary failures fall over (vision) -------------------

@pytest.mark.parametrize("failure", [_exhausted, _unavailable, lambda: TimeoutError("read timed out")])
def test_transient_primary_failure_falls_over_on_the_vision_call(failure):
    answer = _vision_json("Tomato Late Blight", "Remove infected leaves immediately.")
    provider, models = _provider(**{PRIMARY: failure(), FALLBACK_A: answer})
    _no_kb_grounding(provider)

    result = provider.diagnose(_image())

    assert result["diagnosis"] == "Tomato Late Blight"
    assert result["advice"] == "Remove infected leaves immediately."
    assert models.models_called == [PRIMARY, FALLBACK_A]
    assert provider.last_model_used == FALLBACK_A
    assert "error" not in result  # recovered, not an outage


def test_vision_failover_still_sends_the_image_and_question():
    """A fallback attempt must be a full multimodal call, not a text retry."""
    answer = _vision_json("Tomato Late Blight", "Remove infected leaves.")
    provider, models = _provider(**{PRIMARY: _exhausted(), FALLBACK_A: answer})
    _no_kb_grounding(provider)

    provider.diagnose(_image())

    retry = models.calls[-1]
    assert retry["model"] == FALLBACK_A
    assert len(retry["contents"]) == 2                # image part + question
    assert "What is wrong with my tomato?" in retry["contents"][1]
    assert retry["config"].temperature == 0.2         # same generation config


def test_second_fallback_model_used_when_first_also_fails():
    answer = _vision_json("Potato Late Blight", "Destroy infected tubers.")
    provider, models = _provider(
        **{PRIMARY: _unavailable(), FALLBACK_A: _unavailable(), FALLBACK_B: answer}
    )
    _no_kb_grounding(provider)

    result = provider.diagnose(_image())

    assert models.models_called == [PRIMARY, FALLBACK_A, FALLBACK_B]
    assert result["diagnosis"] == "Potato Late Blight"


# --- 4. Whole chain unavailable -> existing localized safe fallback ---------

@pytest.mark.parametrize("language", ["en", "ur", "rom"])
def test_entire_chain_down_returns_the_localized_safe_fallback(language):
    provider, models = _provider(
        **{PRIMARY: _exhausted(), FALLBACK_A: _exhausted(), FALLBACK_B: _exhausted()}
    )

    result = provider.diagnose(_image(language))

    assert models.models_called == [PRIMARY, FALLBACK_A, FALLBACK_B]  # 1 attempt each
    assert result["diagnosis"] == "Unknown"
    assert result["confidence"] == 0.0
    assert result["needs_expert"] is True
    assert result["error"].startswith("Gemini request failed:")
    advice = result["advice"]
    urdu_chars = len(URDU_RE.findall(advice))
    if language == "ur":
        assert urdu_chars >= 8            # proper Urdu script, not Roman
    else:
        assert urdu_chars == 0            # en/rom stay Latin-only
    assert "expert" in advice.lower() or language != "en"


# --- 5. Non-transient errors must NOT fail over ----------------------------

def test_authentication_error_does_not_try_other_models():
    provider, models = _provider(**{PRIMARY: _auth_error()})

    result = provider.diagnose(_image())

    assert models.models_called == [PRIMARY]        # exactly one attempt
    assert result["diagnosis"] == "Unknown"
    assert result["needs_expert"] is True


def test_invalid_request_error_does_not_try_other_models():
    provider, models = _provider(**{PRIMARY: _bad_request()})

    provider.diagnose(_image())

    assert models.models_called == [PRIMARY]


def test_programming_error_does_not_try_other_models():
    provider, models = _provider(**{PRIMARY: ValueError("bug: bad slice index")})

    provider.diagnose(_image())

    assert models.models_called == [PRIMARY]


# --- 6. One attempt per model, never the same model twice ------------------

def test_a_fallback_named_like_the_primary_is_never_called_twice(monkeypatch):
    """GEMINI_MODEL pointing at a fallback name must collapse the chain."""
    monkeypatch.setenv("GEMINI_MODEL", FALLBACK_A)
    provider, models = _provider(
        expected_chain=[FALLBACK_A, FALLBACK_B],
        **{FALLBACK_A: _exhausted(), FALLBACK_B: _exhausted()},
    )

    provider.diagnose(_image())

    called = models.models_called
    assert called == [FALLBACK_A, FALLBACK_B]
    assert len(called) == len(set(called))          # no duplicates
    assert provider.model_chain == [FALLBACK_A, FALLBACK_B]


# --- 7+8. Contract + language gate survive a fallback model ----------------

def test_fallback_model_output_keeps_canonical_english_diagnosis():
    """Requirement: `diagnosis` stays the English KB key, `diagnosis_localized`
    follows the requested language — no matter which model answered."""
    answer = _vision_json(
        "Tomato Late Blight", URDU_ADVICE, localized=URDU_NAME
    )
    provider, models = _provider(**{PRIMARY: _unavailable(), FALLBACK_A: answer})
    _no_kb_grounding(provider)

    result = provider.diagnose(_image("ur"))

    assert models.models_called == [PRIMARY, FALLBACK_A]
    assert result["diagnosis"] == "Tomato Late Blight"   # canonical English
    assert result["diagnosis_localized"] == URDU_NAME
    assert len(URDU_RE.findall(result["advice"])) >= 8


def test_language_gate_still_applies_to_a_fallback_models_answer():
    """A fallback model that ignores the Urdu script requirement gets the same
    enforced rewrite as the primary would — the wrong-script text never ships."""
    roman_answer = _vision_json("Tomato Late Blight", ROM_ADVICE, localized=ROM_NAME)
    provider, models = _provider(
        **{PRIMARY: [_exhausted()], FALLBACK_A: [roman_answer, URDU_ADVICE]}
    )
    _no_kb_grounding(provider)

    result = provider.diagnose(_image("ur"))

    assert result["advice"] == URDU_ADVICE           # rewritten, never Roman
    assert result["diagnosis_localized"] != ROM_NAME  # Roman label never surfaces
    # Vision probe (primary fail + fallback answer), then the rewrite probe.
    assert models.models_called == [PRIMARY, FALLBACK_A, PRIMARY, FALLBACK_A]


# --- 9. Text-only KB/RAG call fails over too ------------------------------

def test_kb_grounding_text_call_falls_back_after_vision_succeeded():
    """The failure mode the goal calls out: Vision answers, then the grounding
    call must not be unrecoverable."""
    vision = _vision_json("Tomato Late Blight", "Yellow-brown lesions on leaves.")
    grounded = "Apply Mancozeb after confirming the dose with a local expert."
    provider, models = _provider(
        **{PRIMARY: [vision, _exhausted()], FALLBACK_A: [grounded]}
    )
    provider._retrieve_kb_entries = lambda *t: [
        {
            "issue_name_english": "Tomato Late Blight",
            "crop": "Tomato",
            "symptom_keywords": ["late blight"],
            "low_cost_treatment_urdu": "میں کیڑے مار ادویات",
        }
    ]

    result = provider.diagnose(_image("en"))

    assert result["advice"] == grounded
    assert result["diagnosis"] == "Tomato Late Blight"
    assert models.models_called == [PRIMARY, PRIMARY, FALLBACK_A]
    assert "knowledge base" in models.calls[-1]["contents"][0]


def test_grounding_failure_keeps_the_vision_advice():
    """A fully dead chain on the grounding call must not lose the diagnosis:
    the advice from the successful vision answer is kept."""
    vision = _vision_json("Tomato Late Blight", "Yellow-brown lesions on leaves.")
    provider, models = _provider(
        **{PRIMARY: [vision, _unavailable()], FALLBACK_A: _unavailable(),
           FALLBACK_B: _unavailable()}
    )
    provider._retrieve_kb_entries = lambda *t: [
        {"issue_name_english": "Tomato Late Blight", "symptom_keywords": ["late blight"]}
    ]

    result = provider.diagnose(_image("en"))

    assert result["diagnosis"] == "Tomato Late Blight"
    assert result["advice"] == "Yellow-brown lesions on leaves."
    # One vision attempt on the primary, then the grounding call probes the
    # whole chain (twice: the answer is empty, so it retries with a stronger
    # instruction) — never the same model twice inside one attempt sequence.
    assert models.models_called[0] == PRIMARY
    for attempt in models.calls[1:]:
        assert attempt["model"] in (PRIMARY, FALLBACK_A, FALLBACK_B)


def test_followup_call_falls_back_to_next_model():
    provider, models = _provider(
        **{PRIMARY: _exhausted(), FALLBACK_A: "Spray again after 10 days if needed."}
    )

    answer = provider.answer_followup("When should I spray again?", {"language": "en"})

    assert answer == "Spray again after 10 days if needed."
    assert models.models_called == [PRIMARY, FALLBACK_A]


def test_followup_chain_exhaustion_still_raises_for_a_clean_500():
    provider, _ = _provider(
        **{PRIMARY: _unavailable(), FALLBACK_A: _unavailable(), FALLBACK_B: _unavailable()}
    )

    with pytest.raises(RuntimeError, match="Gemini follow-up failed"):
        provider.answer_followup("When should I spray again?", {"language": "en"})


# --- Error classification -------------------------------------------------

@pytest.mark.parametrize(
    "exc,transient",
    [
        (_APIErrorShaped(429, "RESOURCE_EXHAUSTED"), True),
        (_APIErrorShaped(503, "UNAVAILABLE"), True),
        (_APIErrorShaped(504, "DEADLINE_EXCEEDED"), True),
        (_APIErrorShaped(500, "INTERNAL"), True),
        (_APIErrorShaped(401, "UNAUTHENTICATED"), False),
        (_APIErrorShaped(403, "PERMISSION_DENIED"), False),
        (_APIErrorShaped(400, "INVALID_ARGUMENT"), False),
        (_APIErrorShaped(404, "NOT_FOUND"), False),
        (_APIErrorShaped(415, "INVALID_ARGUMENT"), False),
        (TimeoutError("the read operation timed out"), True),
        (ConnectionResetError("connection reset by peer"), True),
        (OSError("temporary failure in name resolution"), True),
        (RuntimeError("network is down"), True),
        (ValueError("unexpected value"), False),
        (KeyError("advice"), False),
        (TypeError("unsupported operand"), False),
    ],
)
def test_transient_error_classification(exc, transient):
    from backend.services.gemini_provider import _is_transient_error

    assert _is_transient_error(exc) is transient


def test_real_google_genai_error_shapes_are_classified():
    """The SDK's own APIError (``.code`` + ``.status``) drives the same logic."""
    errors = pytest.importorskip("google.genai.errors")

    quota = errors.APIError(
        429, {"error": {"code": 429, "message": "Resource has been exhausted",
                        "status": "RESOURCE_EXHAUSTED"}}, None
    )
    down = errors.ServerError(
        503, {"error": {"code": 503, "message": "The model is currently unavailable",
                        "status": "UNAVAILABLE"}}, None
    )
    bad_key = errors.ClientError(
        401, {"error": {"code": 401, "message": "API key not valid",
                        "status": "UNAUTHENTICATED"}}, None
    )
    from backend.services.gemini_provider import _is_transient_error

    assert _is_transient_error(quota) is True
    assert _is_transient_error(down) is True
    assert _is_transient_error(bad_key) is False


# --- Chain configuration / readability ------------------------------------

def test_default_chain_is_primary_then_the_two_project_fallbacks(monkeypatch):
    from backend.services.gemini_provider import DEFAULT_MODEL

    monkeypatch.delenv("GEMINI_FALLBACK_MODELS", raising=False)
    assert _model_chain("gemini-3.5-flash-lite") == [
        "gemini-3.5-flash-lite", "gemini-3.8-flash", "gemini-3.6-flash",
    ]
    # No primary configured -> the module default leads, still no duplicates.
    assert _model_chain(None)[0] == DEFAULT_MODEL
    assert _model_chain(DEFAULT_MODEL) == [DEFAULT_MODEL, "gemini-3.8-flash"]


def test_chain_is_configurable_and_deduplicated(monkeypatch):
    monkeypatch.setenv("GEMINI_FALLBACK_MODELS", "  b-model ,, a-model, b-model ")
    assert _model_chain("a-model") == ["a-model", "b-model"]
    assert _model_chain("")[0] == "gemini-3.6-flash"  # blank primary -> default


# --- Logging safety -------------------------------------------------------

def test_failover_logs_name_models_but_never_the_api_key(caplog):
    key = "AIzaFAKEdeadbeef1234567890ABCDEF"
    leaky = _APIErrorShaped(503, "UNAVAILABLE", f"request with api_key={key} rejected")
    provider, _ = _provider(**{PRIMARY: leaky, FALLBACK_A: leaky, FALLBACK_B: leaky})

    with caplog.at_level(logging.INFO, logger="fasaldoc.gemini_provider"):
        provider.diagnose(_image())

    text = caplog.text
    assert key not in text
    assert PRIMARY in text and FALLBACK_A in text   # which model failed / was tried
    assert "[redacted]" in text


def test_non_transient_failure_is_logged_as_such_without_fallover(caplog):
    provider, models = _provider(**{PRIMARY: _auth_error()})

    with caplog.at_level(logging.INFO, logger="fasaldoc.gemini_provider"):
        provider.diagnose(_image())

    assert models.models_called == [PRIMARY]
    assert "non-transient" in caplog.text
    assert "not failing over" in caplog.text
