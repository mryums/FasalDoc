"""Offline tests for the MobileNetV2-first diagnosis flow.

The trained classifier is faked at the ``ml_classifier.get_classifier()``
seam, so NOTHING here needs TensorFlow or the network. A final pair of
tests runs the REAL model and auto-skips when TensorFlow is absent (e.g.
the Python 3.13 .venv on Intel Macs).
"""
import glob
import importlib.util
import os

import pytest

from backend.models import DiagnosisResponse
from backend.services import ml_classifier
from backend.services.diagnosis_service import ImageInput
from backend.services.gemini_provider import GeminiDiagnosisProvider

HAS_TF = importlib.util.find_spec("tensorflow") is not None


class _FakeResponse:
    def __init__(self, text):
        self.text = text


class _FakeModels:
    def __init__(self, response=None, exc=None, responses=None):
        self._response = response
        self._exc = exc
        # Optional per-call sequence (retry tests need different text each call).
        self._responses = list(responses) if responses is not None else None
        self.calls = []

    def generate_content(self, **kwargs):
        self.calls.append(kwargs)
        if self._exc is not None:
            raise self._exc
        if self._responses is not None:
            text = self._responses.pop(0) if self._responses else ""
            return _FakeResponse(text)
        return self._response


class _FakeClient:
    def __init__(self, response=None, exc=None, responses=None):
        self.models = _FakeModels(response=response, exc=exc, responses=responses)


class _FakeClassifier:
    """Stands in for MLClassifier with a canned predict() result."""

    def __init__(self, result):
        self.result = result
        self.predict_calls = 0

    def predict(self, image_bytes):
        self.predict_calls += 1
        return self.result


def _ml_ok(class_name, confidence):
    return {
        "status": ml_classifier.STATUS_OK,
        "class_name": class_name,
        "display_name": ml_classifier.format_display_name(class_name),
        "confidence": confidence,
        "threshold": 0.60,
        "error": None,
    }


def _ml_failed(status, error):
    return {
        "status": status,
        "class_name": None,
        "display_name": None,
        "confidence": 0.0,
        "threshold": 0.60,
        "error": error,
    }


@pytest.fixture(autouse=True)
def _ml_enabled_env(monkeypatch):
    """This suite tests the ML-first flow, so the kill-switch is ON here
    regardless of the ambient environment (test_api/test_gemini disable it)."""
    monkeypatch.setenv("FASALDOC_ML_ENABLED", "1")


@pytest.fixture
def fake_classifier(monkeypatch):
    fake = _FakeClassifier(_ml_failed(ml_classifier.STATUS_UNAVAILABLE, "no TF"))

    def _install(result=None):
        if result is not None:
            fake.result = result
        monkeypatch.setattr(ml_classifier, "get_classifier", lambda: fake)
        return fake

    return _install


def _image(language=None, filename="leaf.jpg"):
    return ImageInput(
        filename=filename,
        content_type="image/jpeg",
        data=b"fake-jpeg-bytes",
        question="What is wrong with my tomato?",
        language=language,
    )


# --- ML unavailable / failed -> existing Gemini vision path preserved --------

def test_ml_unavailable_falls_back_to_gemini_vision(fake_classifier):
    fake_classifier()  # status unavailable
    payload = (
        '{"is_plant_photo": true, "diagnosis": "Early Blight", '
        '"confidence": 0.8, "advice": "Remove affected leaves.", '
        '"needs_expert": false}'
    )
    provider = GeminiDiagnosisProvider(client=_FakeClient(response=_FakeResponse(payload)))
    # No KB grounding match for this synthetic advice text -> single vision call.
    provider._retrieve_kb_entries = lambda *t: []

    result = provider.diagnose(_image())

    assert result["diagnosis"] == "Early Blight"
    assert result["needs_expert"] is False
    contents = provider._client.models.calls[0]["contents"]
    assert len(contents) == 2  # image part + question text (original flow)


def test_ml_prediction_error_falls_back_to_gemini_vision(fake_classifier):
    fake_classifier(_ml_failed(ml_classifier.STATUS_ERROR, "corrupt image"))
    payload = (
        '{"is_plant_photo": true, "diagnosis": "Leaf curl", '
        '"confidence": 0.7, "advice": "Watch the new growth.", '
        '"needs_expert": false}'
    )
    provider = GeminiDiagnosisProvider(client=_FakeClient(response=_FakeResponse(payload)))
    provider._retrieve_kb_entries = lambda *t: []

    result = provider.diagnose(_image())

    assert result["diagnosis"] == "Leaf curl"


# --- Confident ML prediction: diagnosis is FIXED, Gemini only explains -------

def test_confident_ml_prediction_fixes_diagnosis(fake_classifier):
    fake_classifier(_ml_ok("Tomato___Early_blight", 0.93))
    client = _FakeClient(response=_FakeResponse("should not be reached"))
    provider = GeminiDiagnosisProvider(client=client)
    provider._verify_ml_crop = lambda *a, **k: "supported"  # in-domain crop
    provider._grounded_advice = lambda *a, **k: "Grounded KB advice."

    result = provider.diagnose(_image())

    assert result["diagnosis"] == "Tomato Early Blight"
    assert result["confidence"] == pytest.approx(0.93)
    assert result["advice"] == "Grounded KB advice."
    assert result["needs_expert"] is False
    assert "error" not in result
    # Gemini was never asked to diagnose — no vision call at all.
    assert client.models.calls == []


def test_confident_ml_without_kb_match_uses_fixed_diagnosis_explanation(fake_classifier):
    fake_classifier(_ml_ok("Tomato___Early_blight", 0.81))
    client = _FakeClient(response=_FakeResponse("Spray copper fungicide; confirm dose locally."))
    provider = GeminiDiagnosisProvider(client=client)
    provider._verify_ml_crop = lambda *a, **k: "supported"  # in-domain crop
    provider._retrieve_kb_entries = lambda *t: []  # force KB miss

    result = provider.diagnose(_image())

    assert result["diagnosis"] == "Tomato Early Blight"
    assert result["needs_expert"] is False
    prompt = client.models.calls[0]["contents"][0]
    # Explanation-only call (no image part) that pins the ML diagnosis.
    assert "This diagnosis is FINAL" in prompt
    assert "Tomato Early Blight" in prompt
    assert "MUST NOT replace it" in prompt


# --- Out-of-domain crop handling (confidently-wrong ML, e.g. wheat) ----------

def test_verify_ml_crop_detects_out_of_domain():
    provider = GeminiDiagnosisProvider(client=_FakeClient(response=_FakeResponse(
        '{"crop_seen": "wheat", "is_supported_crop": false, "matches_ml_crop": false}'
    )))
    assert provider._verify_ml_crop(_image(language="en"), "Corn___healthy") == "ood"


def test_verify_ml_crop_confirms_supported_crop():
    provider = GeminiDiagnosisProvider(client=_FakeClient(response=_FakeResponse(
        '{"crop_seen": "tomato", "is_supported_crop": true, "matches_ml_crop": true}'
    )))
    assert provider._verify_ml_crop(_image(), "Tomato___Early_blight") == "supported"


def test_verify_ml_crop_keyword_fallback_when_no_boolean():
    provider = GeminiDiagnosisProvider(client=_FakeClient(response=_FakeResponse(
        '{"crop_seen": "rice paddy"}'
    )))
    assert provider._verify_ml_crop(_image(), "Corn___healthy") == "ood"


def test_verify_ml_crop_unclear_on_unparseable_keeps_ml():
    provider = GeminiDiagnosisProvider(client=_FakeClient(response=_FakeResponse("not json")))
    assert provider._verify_ml_crop(_image(), "Corn___healthy") == "unclear"


def test_verify_ml_crop_unclear_when_call_raises():
    provider = GeminiDiagnosisProvider(client=_FakeClient(exc=RuntimeError("net down")))
    assert provider._verify_ml_crop(_image(), "Corn___healthy") == "unclear"


@pytest.mark.parametrize(
    "is_supported, matches, expected",
    [
        (True, True, "supported"),   # both confirm -> trust the ML class
        (True, False, "ood"),        # supported crop but NOT the predicted one
        (False, True, "ood"),        # unsupported wins even if it "matches"
        (False, False, "ood"),       # clearly out of domain
    ],
)
def test_verify_ml_crop_requires_both_supported_and_matching(
    is_supported, matches, expected
):
    """A crop match is accepted ONLY when Gemini confirms BOTH that the crop is
    in the model's supported set AND that it matches MobileNetV2's predicted
    crop. `is_supported_crop=true` alone must never be enough to keep ML final.
    """
    payload = (
        '{"crop_seen": "potato", "is_supported_crop": %s, "matches_ml_crop": %s}'
        % ("true" if is_supported else "false", "true" if matches else "false")
    )
    provider = GeminiDiagnosisProvider(client=_FakeClient(response=_FakeResponse(payload)))
    verdict = provider._verify_ml_crop(_image(), "Tomato___Late_blight")
    assert verdict == expected


def test_supported_but_mismatched_crop_defers_to_gemini_vision(fake_classifier):
    """Potato-mismatch regression: MobileNetV2 confidently predicts
    Tomato___Late_blight, but Gemini sees a *supported* crop (potato) that does
    NOT match the predicted crop. The tomato disease must NOT be shown -- the
    image is routed to Gemini Vision instead of keeping the ML diagnosis.
    """
    fake_classifier(_ml_ok("Tomato___Late_blight", 0.97))
    verify = '{"crop_seen": "potato", "is_supported_crop": true, "matches_ml_crop": false}'
    vision = (
        '{"is_plant_photo": true, "diagnosis": "Potato Late Blight", '
        '"confidence": 0.82, "advice": "Remove infected tubers.", '
        '"needs_expert": false}'
    )
    client = _FakeClient(responses=[verify, vision])
    provider = GeminiDiagnosisProvider(client=client)
    provider._retrieve_kb_entries = lambda *t: []

    result = provider.diagnose(_image(language="en"))

    assert result["diagnosis"] == "Potato Late Blight"  # never the ML tomato class
    assert len(client.models.calls) == 2  # crop check + vision diagnosis


def test_confident_ml_out_of_domain_defers_to_gemini_vision(fake_classifier):
    """Wheat regression: a confident 'Corn healthy' ML class must NOT be shown
    when Gemini Vision identifies the crop as wheat — it defers to Vision."""
    fake_classifier(_ml_ok("Corn___healthy", 0.99))
    verify = '{"crop_seen": "wheat", "is_supported_crop": false, "matches_ml_crop": false}'
    vision = (
        '{"is_plant_photo": true, "diagnosis": "Wheat Yellow Rust", '
        '"confidence": 0.75, "advice": "Apply a recommended fungicide.", '
        '"needs_expert": false}'
    )
    client = _FakeClient(responses=[verify, vision])
    provider = GeminiDiagnosisProvider(client=client)
    provider._retrieve_kb_entries = lambda *t: []

    result = provider.diagnose(_image(language="en"))

    assert result["diagnosis"] == "Wheat Yellow Rust"  # never "Corn Healthy"
    assert len(client.models.calls) == 2  # crop check + vision diagnosis


def test_confident_ml_supported_crop_stays_ml_final_after_verification(fake_classifier):
    """A Gemini-corroborated supported crop keeps ML final (Gemini only explains)."""
    fake_classifier(_ml_ok("Tomato___Early_blight", 0.9))
    verify = '{"crop_seen": "tomato", "is_supported_crop": true, "matches_ml_crop": true}'
    client = _FakeClient(responses=[verify])  # only the crop-verification call runs
    provider = GeminiDiagnosisProvider(client=client)
    provider._grounded_advice = lambda *a, **k: "Grounded KB advice."

    result = provider.diagnose(_image(language="en"))

    assert result["diagnosis"] == "Tomato Early Blight"
    assert result["advice"] == "Grounded KB advice."
    assert len(client.models.calls) == 1  # just crop verification; ML stays final


# --- Conservative confidence / reject-class behavior --------------------------

def test_low_confidence_ml_defers_to_gemini_vision(fake_classifier):
    """A weak softmax (conf < 0.60) is no longer blindly shown: the image is
    sent to Gemini Vision for a second opinion instead of trusting the ML
    class. When Vision confidently diagnoses, its result is used."""
    fake_classifier(_ml_ok("Tomato___Late_blight", 0.42))
    payload = (
        '{"is_plant_photo": true, "diagnosis": "Tomato Late Blight", '
        '"confidence": 0.8, "advice": "Remove infected leaves.", '
        '"needs_expert": false}'
    )
    client = _FakeClient(response=_FakeResponse(payload))
    provider = GeminiDiagnosisProvider(client=client)
    provider._retrieve_kb_entries = lambda *t: []

    result = provider.diagnose(_image(language="rom"))

    assert len(client.models.calls) >= 1  # Gemini WAS consulted
    assert any(len(c["contents"]) == 2 for c in client.models.calls)  # image sent
    assert result["diagnosis"] == "Tomato Late Blight"


def test_low_confidence_ml_vision_also_unsure_returns_localized_unknown(fake_classifier):
    """If Gemini Vision is also unsure, the localized Unknown + needs_expert
    safety net is returned (Latin-only in Roman mode)."""
    fake_classifier(_ml_ok("Tomato___Late_blight", 0.42))
    payload = (
        '{"is_plant_photo": true, "diagnosis": "Unknown", '
        '"confidence": 0.2, "advice": "", "needs_expert": true}'
    )
    client = _FakeClient(response=_FakeResponse(payload))
    provider = GeminiDiagnosisProvider(client=client)

    result = provider.diagnose(_image(language="rom"))

    assert result["diagnosis"] == "Unknown"
    assert result["needs_expert"] is True
    assert not any(ord(ch) > 0x0590 for ch in result["advice"])  # Latin only


def test_background_class_runs_gemini_vision_sanity_check(fake_classifier):
    """A confident reject-class prediction must NOT auto-reject the photo: it
    defers to the existing Gemini Vision flow, which re-checks plant-ness and
    diagnoses the real plant the classifier failed to place."""
    fake_classifier(_ml_ok(ml_classifier.BACKGROUND_CLASS, 0.97))
    payload = (
        '{"is_plant_photo": true, "diagnosis": "Tomato Late Blight", '
        '"confidence": 0.8, "advice": "Remove infected leaves.", '
        '"needs_expert": false}'
    )
    client = _FakeClient(response=_FakeResponse(payload))
    provider = GeminiDiagnosisProvider(client=client)
    provider._retrieve_kb_entries = lambda *t: []

    # English keeps this test focused on the Background->Vision wiring (one
    # call); Urdu script enforcement on this same path is covered by the
    # test_vision_path_* tests below.
    result = provider.diagnose(_image(language="en"))

    # Gemini Vision was consulted (image part sent) and its diagnosis is used.
    assert len(client.models.calls) == 1
    assert len(client.models.calls[0]["contents"]) == 2  # image + prompt
    assert result["diagnosis"] == "Tomato Late Blight"
    assert result["needs_expert"] is False


def test_background_class_genuine_non_plant_still_rejected(fake_classifier):
    """Vision also sees no plant -> the localized not-a-plant response is kept."""
    fake_classifier(_ml_ok(ml_classifier.BACKGROUND_CLASS, 0.97))
    payload = (
        '{"is_plant_photo": false, "diagnosis": "Unknown", '
        '"confidence": 0.0, "advice": "", "needs_expert": true}'
    )
    client = _FakeClient(response=_FakeResponse(payload))
    provider = GeminiDiagnosisProvider(client=client)

    result = provider.diagnose(_image(language="ur"))

    assert result["diagnosis"] == "Unknown"
    assert result["needs_expert"] is True
    assert any("\u0600" <= ch <= "\u06FF" for ch in result["advice"])  # Urdu script


def test_background_class_low_confidence_defers_to_gemini_vision(fake_classifier):
    """Low confidence now defers to Vision even for the reject class, so an
    image the classifier was unsure about still gets Gemini's eyes. When Vision
    also sees no plant, the localized not-a-plant/Unknown is kept."""
    fake_classifier(_ml_ok(ml_classifier.BACKGROUND_CLASS, 0.30))
    payload = (
        '{"is_plant_photo": false, "diagnosis": "Unknown", '
        '"confidence": 0.0, "advice": "", "needs_expert": true}'
    )
    client = _FakeClient(response=_FakeResponse(payload))
    provider = GeminiDiagnosisProvider(client=client)

    result = provider.diagnose(_image(language="rom"))

    assert len(client.models.calls) == 1  # vision sanity check ran
    assert result["diagnosis"] == "Unknown"
    assert result["needs_expert"] is True
    assert not any(ord(ch) > 0x0590 for ch in result["advice"])  # Latin only


# --- Script enforcement + one retry on generated advice (1E) ------------------

def test_urdu_advice_wrong_script_retries_then_falls_back(fake_classifier):
    fake_classifier(_ml_ok("Tomato___Late_blight", 0.90))
    # Attempt 1 (English) and attempt 2 (Roman Urdu) both fail the Urdu-script
    # check -> localized Urdu fallback + error, ML diagnosis stays visible.
    client = _FakeClient(responses=["Remove affected leaves now.", "Patte hata dein."])
    provider = GeminiDiagnosisProvider(client=client)
    provider._verify_ml_crop = lambda *a, **k: "supported"  # in-domain crop
    provider._retrieve_kb_entries = lambda *t: []  # force KB-miss explanation path

    result = provider.diagnose(_image(language="ur"))

    assert len(client.models.calls) == 2  # first answer + one retry
    assert "CRITICAL SCRIPT REQUIREMENT" in client.models.calls[1]["contents"][0]
    assert result["diagnosis"] == "Tomato Late Blight"
    assert result["needs_expert"] is True
    assert any("\u0600" <= ch <= "\u06FF" for ch in result["advice"])  # Urdu fallback

def test_urdu_advice_recovered_on_retry(fake_classifier):
    fake_classifier(_ml_ok("Tomato___Late_blight", 0.90))
    urdu = "متاثرہ پتوں کو فوری طور پر ہٹا کر تباہ کر دیں۔"
    client = _FakeClient(responses=["Remove affected leaves now.", urdu])
    provider = GeminiDiagnosisProvider(client=client)
    provider._verify_ml_crop = lambda *a, **k: "supported"  # in-domain crop
    provider._retrieve_kb_entries = lambda *t: []

    result = provider.diagnose(_image(language="ur"))

    assert len(client.models.calls) == 2
    assert result["advice"] == urdu
    assert result["needs_expert"] is False
    assert "error" not in result

def test_roman_urdu_advice_rejects_urdu_script(fake_classifier):
    fake_classifier(_ml_ok("Corn___Common_rust", 0.85))
    # Attempt 1 came back in Urdu script (wrong for Roman mode) -> retried and
    # the Latin-only second answer is accepted.
    latin = "Zadid fouwaron se bachain aur dor ki fasal se rotation karein."
    client = _FakeClient(responses=["فungicide سپرے کریں", latin])
    provider = GeminiDiagnosisProvider(client=client)
    provider._verify_ml_crop = lambda *a, **k: "supported"  # in-domain crop
    provider._retrieve_kb_entries = lambda *t: []

    result = provider.diagnose(_image(language="rom"))

    assert len(client.models.calls) == 2
    assert result["advice"] == latin
    assert not any("\u0600" <= ch <= "\u06FF" for ch in result["advice"])


# --- Vision-path script enforcement (Roman-Urdu-in-Urdu-mode leak, Part 2) ---

_ROMAN_LEAK = (
    "Ye tasweer makki (corn) ki patton par Northern Corn Leaf Blight ki "
    "nishaniyan dikha rahi hai."
)


def _vision_json(advice, diagnosis="Northern Corn Leaf Blight", confidence=0.85):
    # advice must be quote-free so it embeds cleanly in the synthetic JSON.
    safe = advice.replace('"', "")
    return (
        '{"is_plant_photo": true, "diagnosis": "' + diagnosis + '", '
        '"confidence": ' + str(confidence) + ', "advice": "' + safe + '", '
        '"needs_expert": false}'
    )


def test_vision_path_roman_urdu_in_urdu_mode_retries_then_urdu_fallback(fake_classifier):
    """Regression: ML unavailable -> Gemini vision JSON returns a ROMAN Urdu
    advice. The vision path previously shipped it untouched; it must now retry
    once and, if the model still ignores the script, fall back to Urdu script.
    The diagnosis itself is never hidden or shortened."""
    fake_classifier()  # default: ML unavailable -> vision path
    json_roman = _vision_json(_ROMAN_LEAK)
    client = _FakeClient(responses=[json_roman, _ROMAN_LEAK, _ROMAN_LEAK])
    provider = GeminiDiagnosisProvider(client=client)
    provider._retrieve_kb_entries = lambda *t: []  # KB miss -> raw advice path

    result = provider.diagnose(_image(language="ur"))

    assert len(client.models.calls) == 3            # vision + rewrite + one retry
    assert "CRITICAL SCRIPT REQUIREMENT" in client.models.calls[2]["contents"][0]
    assert result["diagnosis"] == "Northern Corn Leaf Blight"  # diagnosis kept
    assert _ROMAN_LEAK[:20] not in result["advice"]           # Roman leak gone
    assert any("\u0600" <= ch <= "\u06FF" for ch in result["advice"])  # Urdu fallback


def test_vision_path_roman_urdu_recovered_by_rewrite(fake_classifier):
    """When the rewrite call returns proper Urdu, that full advice is used
    (not the generic safety-net fallback)."""
    fake_classifier()
    urdu = "یہ تصویر مکئی کے پتوں پر ناردرن کورن لیف بلائٹ کی علامات دکھا رہی ہے۔"
    client = _FakeClient(responses=[_vision_json(_ROMAN_LEAK), urdu])
    provider = GeminiDiagnosisProvider(client=client)
    provider._retrieve_kb_entries = lambda *t: []

    result = provider.diagnose(_image(language="ur"))

    assert len(client.models.calls) == 2            # vision + successful rewrite
    assert result["advice"] == urdu
    assert result["diagnosis"] == "Northern Corn Leaf Blight"


def test_vision_path_english_is_untouched_no_extra_call(fake_classifier):
    fake_classifier()
    payload = _vision_json(
        "Remove affected leaves and improve airflow.", diagnosis="Early Blight", confidence=0.8
    )
    client = _FakeClient(response=_FakeResponse(payload))
    provider = GeminiDiagnosisProvider(client=client)
    provider._retrieve_kb_entries = lambda *t: []

    result = provider.diagnose(_image(language="en"))

    assert len(client.models.calls) == 1            # no enforcement for English
    assert result["advice"] == "Remove affected leaves and improve airflow."


def test_vision_path_roman_urdu_latin_is_untouched(fake_classifier):
    fake_classifier()
    latin = "Yeh tasveer makki ke patton par Common Rust dikha rahi hai."
    client = _FakeClient(response=_FakeResponse(_vision_json(latin, diagnosis="Corn Common Rust")))
    provider = GeminiDiagnosisProvider(client=client)
    provider._retrieve_kb_entries = lambda *t: []

    result = provider.diagnose(_image(language="rom"))

    assert len(client.models.calls) == 1            # already Latin-only -> kept
    assert result["advice"] == latin


# --- Follow-up language enforcement (1G) --------------------------------------

def test_followup_rejects_wrong_script_and_retries():
    provider, client = _make_seq_provider(
        ["Water every two days.", "ہر دو دن بعد پانی دیں۔"]
    )
    answer = provider.answer_followup(
        "How often should I water?", context={"diagnosis": "Early Blight", "language": "ur"}
    )
    assert len(client.models.calls) == 2
    assert any("\u0600" <= ch <= "\u06FF" for ch in answer)


def _make_seq_provider(responses):
    client = _FakeClient(responses=responses)
    return GeminiDiagnosisProvider(client=client), client


# --- Language plumbing on the ML explanation call -----------------------------

def test_urdu_language_reaches_explanation_prompt(fake_classifier):
    fake_classifier(_ml_ok("Corn___Common_rust", 0.77))
    client = _FakeClient(response=_FakeResponse("زنگ کی uygun تدبیر"))
    provider = GeminiDiagnosisProvider(client=client)
    provider._verify_ml_crop = lambda *a, **k: "supported"  # in-domain crop
    provider._retrieve_kb_entries = lambda *t: []

    result = provider.diagnose(_image(language="ur"))

    prompt = client.models.calls[0]["contents"][0]
    assert "Urdu script" in prompt
    assert result["advice"] == "زنگ کی uygun تدبیر"


def test_roman_urdu_language_reaches_explanation_prompt(fake_classifier):
    fake_classifier(_ml_ok("Corn___Common_rust", 0.77))
    client = _FakeClient(response=_FakeResponse("Zadid fouwaron se bachain."))
    provider = GeminiDiagnosisProvider(client=client)
    provider._verify_ml_crop = lambda *a, **k: "supported"  # in-domain crop
    provider._retrieve_kb_entries = lambda *t: []

    provider.diagnose(_image(language="rom"))

    prompt = client.models.calls[0]["contents"][0]
    assert "Roman Urdu" in prompt


# --- Advisor failure keeps the ML diagnosis but stays conservative ------------

def test_explanation_failure_keeps_diagnosis_and_sets_error(fake_classifier):
    fake_classifier(_ml_ok("Potato___Late_blight", 0.88))
    client = _FakeClient(exc=RuntimeError("503 UNAVAILABLE"))
    provider = GeminiDiagnosisProvider(client=client)
    provider._verify_ml_crop = lambda *a, **k: "supported"  # in-domain crop
    provider._retrieve_kb_entries = lambda *t: []

    result = provider.diagnose(_image())

    assert result["diagnosis"] == "Potato Late Blight"
    assert result["needs_expert"] is True
    assert "Gemini could not generate" in result["error"]


# --- Contract compatibility ---------------------------------------------------

def test_ml_answer_matches_frontend_schema(fake_classifier):
    fake_classifier(_ml_ok("Tomato___healthy", 0.91))
    provider = GeminiDiagnosisProvider(client=_FakeClient())
    provider._verify_ml_crop = lambda *a, **k: "supported"  # in-domain crop
    provider._grounded_advice = lambda *a, **k: "Plant looks healthy; keep monitoring."

    result = provider.diagnose(_image())

    parsed = DiagnosisResponse(**result)  # schema validation, raises on drift
    assert parsed.diagnosis == "Tomato Healthy"
    assert 0 <= parsed.confidence <= 1


# --- Classifier unit behavior (no TF required) --------------------------------

def test_format_display_name():
    assert ml_classifier.format_display_name("Tomato___Early_blight") == "Tomato Early Blight"
    assert (
        ml_classifier.format_display_name("Tomato___Tomato_Yellow_Leaf_Curl_Virus")
        == "Tomato Yellow Leaf Curl Virus"
    )
    assert ml_classifier.format_display_name("Corn___Common_rust") == "Corn Common Rust"


# --- Structural invariants: EXACTLY 16 classes (single source of truth) -------

def test_class_mapping_has_exactly_16_contiguous_classes():
    """The Phase-2 requirement is EXACTLY 16 output classes. The mapping file
    is the single source of truth the runtime uses, so assert its shape here
    (no TensorFlow needed): 16 entries, contiguous string keys 0..15, unique
    non-empty class names."""
    import json

    with open(ml_classifier.CLASS_MAPPING_PATH, "r", encoding="utf-8") as fh:
        mapping = json.load(fh)
    assert len(mapping) == 16
    assert sorted(int(k) for k in mapping) == list(range(16))
    names = [mapping[str(i)] for i in range(16)]
    assert all(isinstance(n, str) and n.strip() for n in names)
    assert len(set(names)) == 16  # no duplicate labels


def test_runtime_class_order_matches_mapping_indices():
    """MLClassifier builds its ordered class list by sorting the mapping keys,
    so argmax index -> name must line up with 0..15 exactly."""
    import json

    with open(ml_classifier.CLASS_MAPPING_PATH, "r", encoding="utf-8") as fh:
        mapping = json.load(fh)
    ordered = [v for _, v in sorted(mapping.items(), key=lambda kv: int(kv[0]))]
    assert ordered == [mapping[str(i)] for i in range(16)]


def test_classifier_reports_unavailable_when_model_file_missing(tmp_path):
    classifier = ml_classifier.MLClassifier(
        model_path=str(tmp_path / "nope.keras"),
        mapping_path=str(tmp_path / "nope.json"),
    )
    result = classifier.predict(b"whatever")

    assert result["status"] == ml_classifier.STATUS_UNAVAILABLE
    assert result["error"]  # reason surfaced for the report, never raised


def test_kill_switch_bypasses_classifier(monkeypatch):
    monkeypatch.setenv("FASALDOC_ML_ENABLED", "0")
    result = ml_classifier.MLClassifier().predict(b"whatever")

    assert result["status"] == ml_classifier.STATUS_UNAVAILABLE
    assert "FASALDOC_ML_ENABLED" in result["error"]


# --- Real trained model (runs only where TensorFlow exists, e.g. ml-env) -----

@pytest.mark.skipif(not HAS_TF, reason="TensorFlow not installed in this environment")
class TestRealModel:
    @pytest.fixture(scope="class")
    def classifier(self):
        return ml_classifier.MLClassifier()  # module-level files, real load

    _TEST_ROOT = os.path.join(
        os.path.dirname(__file__), "..", "data", "ml_dataset", "test"
    )

    def _first_image(self, class_dir):
        matches = sorted(
            glob.glob(os.path.join(self._TEST_ROOT, class_dir, "*.[jJ][pP][gG]"))
        )
        assert matches, f"no test images under {class_dir}"
        return matches[0]

    def test_real_model_predicts_ok_on_test_images(self, classifier):
        for class_dir in ("Tomato___healthy", "Tomato___Early_blight"):
            path = self._first_image(class_dir)
            with open(path, "rb") as fh:
                result = classifier.predict(fh.read())
            assert result["status"] == ml_classifier.STATUS_OK, result["error"]
            assert 0.0 <= result["confidence"] <= 1.0
            assert result["class_name"] and result["display_name"]

    def test_real_model_maps_every_predicted_index(self, classifier):
        path = self._first_image("Potato___Late_blight")
        with open(path, "rb") as fh:
            result = classifier.predict(fh.read())
        assert result["status"] == ml_classifier.STATUS_OK
        assert result["class_name"]  # index -> mapping name succeeded

    def test_real_model_output_dimension_is_16(self, classifier):
        """Required invariant: the served model has exactly 16 outputs and its
        argmax maps back to one of the 16 class names, with confidence in [0,1]."""
        assert classifier._ensure_loaded()
        assert tuple(classifier._model.output.shape) == (None, 16)
        assert len(classifier._class_names) == 16
        path = self._first_image("Corn___healthy")
        with open(path, "rb") as fh:
            probs = classifier._predict_proba(fh.read())
        assert probs.shape == (16,)
        assert 0.999 <= float(probs.sum()) <= 1.001  # softmax over 16 classes
        assert classifier._class_names[int(probs.argmax())]
