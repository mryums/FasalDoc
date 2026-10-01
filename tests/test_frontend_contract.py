"""Frontend <-> backend advice data-flow contract (AI phase).

Guards the invariant proven broken in the field: the ResultScreen "Recommended
Action" MUST be the exact `advice` string carried by the backend
`DiagnosisResponse` for the SAME request. The frontend may localize static
labels and enrich Symptoms/Treatment/Prevention from `agriculture.ts`, but it
must NEVER replace, regenerate or drop the Gemini advice — and it must send the
selected `language` with the request, or the backend legitimately answers in
English and the farmer sees the wrong language (the reproduced stale-bundle
symptom: Urdu UI showing "Your tomato plant currently looks healthy...").

These are source-contract tests (the frontend has no JS test runner) plus one
route-level test that the /diagnose response carries the provider's advice
verbatim with the request's language threaded through.
"""
import os
import re

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FE = os.path.join(ROOT, "frontend", "src")


def _read(*parts):
    with open(os.path.join(FE, *parts), encoding="utf-8") as fh:
        return fh.read()


# ---------------------------------------------------------------------------
# 1. ResultScreen binds the advice card to the API response — nothing else.
# ---------------------------------------------------------------------------

def test_result_screen_renders_backend_advice_verbatim():
    src = _read("pages", "ResultScreen.tsx")
    # Exactly one advice paragraph, bound straight to diagnosis.advice.
    advice_paragraphs = re.findall(
        r'<p className="advice-card__text">\{([^}]+)\}</p>', src
    )
    assert advice_paragraphs == ["diagnosis.advice"], (
        "Recommended Action must render the backend DiagnosisResponse.advice "
        f"directly, found: {advice_paragraphs}"
    )


def test_result_screen_never_uses_kb_content_as_advice():
    src = _read("pages", "ResultScreen.tsx")
    # agriculture.ts may enrich headings/symptoms/treatment/prevention, but no
    # enriched/KB-derived value may flow into the advice slot.
    assert "enrichedInfo.description" not in src
    assert re.search(r"advice-card__text\">\{diagnosis\.advice\}", src)
    # No local advice generation surfaces: only the API field is displayed.
    assert src.count("advice") and "adviceTitle" in src


def test_no_frontend_module_overwrites_advice():
    """No `.advice =` assignment, no spread that replaces advice, no local
    advice field anywhere in the frontend source."""
    offenders = []
    for dirpath, _dirs, files in os.walk(FE):
        for fn in files:
            if not fn.endswith((".ts", ".tsx")):
                continue
            path = os.path.join(dirpath, fn)
            text = open(path, encoding="utf-8").read()
            for pattern in (r"\.advice\s*=", r"\.\.\.\w+,\s*advice\s*:",
                            r"\badvice\s*:\s*(?!string)"):
                for m in re.finditer(pattern, text):
                    # DiagnosisResponse TYPE declaration (`advice: string`) is
                    # the contract itself, not an overwrite.
                    snippet = text[max(0, m.start() - 60): m.end() + 60]
                    if re.search(r"advice\s*:\s*string", snippet):
                        continue
                    offenders.append((os.path.relpath(path, FE), snippet))
    assert not offenders, f"frontend mutates/derives `advice`: {offenders}"


# ---------------------------------------------------------------------------
# 2. The request must carry the selected language — without it the backend
#    legitimately answers in English (the reproduced symptom's real trigger).
# ---------------------------------------------------------------------------

def test_api_sends_language_on_diagnose_and_followup():
    src = _read("services", "api.ts")
    assert re.search(r"form\.append\(\s*'language'\s*,\s*language\s*\)", src)
    # The follow-up JSON body must carry `language` too.
    body = re.search(r"body: JSON\.stringify\(\{[^)]*\)", src)
    assert body and "language" in body.group(0)


def test_app_threads_active_language_into_diagnose_image():
    src = _read("App.tsx")
    assert re.search(r"diagnoseImage\(file,\s*question,\s*lang\)", src)
    assert re.search(r"askFollowup\(question,\s*lang\)", src)
    # The reducer stores the API response untouched — no advice rewrite.
    assert re.search(
        r"case 'diagnosis-success':\s*\n\s*return \{ \.\.\.state[^}]*diagnosis: action\.diagnosis",
        src,
    )


# ---------------------------------------------------------------------------
# 3. Route level: /diagnose returns the provider's FINAL advice verbatim for
#    the request language (nothing between provider and JSON may edit it).
# ---------------------------------------------------------------------------

def test_diagnose_route_returns_provider_advice_unchanged(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient

    from backend.services import diagnosis_service

    expected_advice = (
        "متاثرہ پتوں کو فوری طور پر ہٹا کر تلف کریں اور پودوں کے درمیان "
        "ہوا کی آمد و رفت بہتر بنائیں۔"
    )
    seen = {}

    class _StubProvider:
        def diagnose(self, image):
            seen["language"] = image.language
            return {
                "filename": image.filename,
                "diagnosis": "Tomato Yellow Leaf Curl Virus",
                "diagnosis_localized": "ٹماٹر زرد پتی کرل وائرس",
                "confidence": 0.85,
                "advice": expected_advice,
                "needs_expert": True,
            }

        def answer_followup(self, question, context=None):
            return "x"

    monkeypatch.setattr(diagnosis_service, "_provider", _StubProvider())
    monkeypatch.setattr(diagnosis_service, "_latest_context", None)

    from backend.main import app

    client = TestClient(app)
    png = tmp_path / "leaf.png"
    png.write_bytes(b"fake-png-bytes")
    with open(png, "rb") as fh:
        res = client.post(
            "/diagnose",
            files={"image": ("leaf.png", fh.read(), "image/png")},
            data={"question": "کیا بات ہے؟", "language": "ur"},
        )
    assert res.status_code == 200
    body = res.json()
    # Exactly the provider's final advice reaches the client — and the
    # selected language reached the provider.
    assert body["advice"] == expected_advice
    assert seen["language"] == "ur"
    assert body["diagnosis_localized"] == "ٹماٹر زرد پتی کرل وائرس"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
