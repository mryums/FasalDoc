"""Permanent AI-phase language regression tests (Gemini vision path only).

Guards the rules reproduced live in Urdu mode:

* `en`  -> everything system-generated is English.
* `ur`  -> every system-generated PROSE field is proper Urdu script; a Roman
  Urdu or English leak (advice, follow-up, fallbacks, diagnosis label) is a bug.
* `rom` -> zero Urdu/Arabic characters in system-generated prose.

The `diagnosis` field itself stays CANONICAL ENGLISH (it is the knowledge-base
matching key); the localized DISPLAY label travels in `diagnosis_localized`,
validated against the selected script before it can ever reach the farmer.

ML is disabled (FASALDOC_ML_ENABLED=0) so these tests exercise ONLY the
Gemini AI path, and every Gemini call is faked — no network.
"""
import json
import os
import re

import pytest

from backend.models import DiagnosisResponse
from backend.services.diagnosis_service import ImageInput
from backend.services import gemini_provider as gp
from backend.services.gemini_provider import (
    FALLBACK_ADVICE_BY_LANG,
    NOT_A_PLANT_ADVICE_BY_LANG,
    GeminiDiagnosisProvider,
)

URDU_RE = re.compile(r"[\u0600-\u06FF]")


def urdu_count(text):
    return len(URDU_RE.findall(text or ""))


@pytest.fixture(autouse=True)
def _ai_only(monkeypatch):
    """This phase: Gemini Vision is the diagnosis source. MobileNetV2 must not
    take part (and must never be blamed for these results)."""
    monkeypatch.setenv("FASALDOC_ML_ENABLED", "0")


class _FakeResponse:
    def __init__(self, text):
        self.text = text


class _FakeModels:
    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = []

    def generate_content(self, **kwargs):
        self.calls.append(kwargs)
        # Vision/rewrite calls after the scripted answers run out get ''
        # (treated as an invalid answer -> localized fallback), never crash.
        return _FakeResponse(self._responses.pop(0) if self._responses else "")


class _FakeClient:
    def __init__(self, *responses):
        self.models = _FakeModels(responses)


def _provider(*responses):
    client = _FakeClient(*responses)
    provider = GeminiDiagnosisProvider(client=client)
    # KB grounding is covered by its own test below; elsewhere keep the vision
    # path deterministic with a single call.
    provider._retrieve_kb_entries = lambda *t: []
    return provider, client


def _image(language):
    return ImageInput(
        filename="leaf.jpg",
        content_type="image/jpeg",
        data=b"fake-jpeg-bytes",
        question="What is wrong with my plant?",
        language=language,
    )


def _vision_json(diagnosis, advice, confidence=0.85, localized=None, is_plant=True):
    payload = {
        "is_plant_photo": is_plant,
        "diagnosis": diagnosis,
        "confidence": confidence,
        "advice": advice,
        "needs_expert": confidence < 0.6,
    }
    if localized is not None:
        payload["diagnosis_localized"] = localized
    return json.dumps(payload, ensure_ascii=False)


URDU_ADVICE = (
    "متاثرہ پتوں کو فوری طور پر ہٹا کر تلف کریں اور پودوں کے درمیان "
    "ہوا کی آمد و رفت بہتر بنائیں۔"
)
URDU_NAME = "ٹماٹر میں اربل بلائٹ"
ROM_ADVICE = (
    "Mutaasira patton ko foran hata dein aur paudon ke darmiyan hawa ki "
    "aamad-o-raft behtar banayein."
)
ROM_NAME = "Tamatar mein Early Blight"


# ---------------------------------------------------------------------------
# 1+2+14.1  Urdu + confident Gemini diagnosis: name localized, prose Urdu,
#           canonical English diagnosis preserved for KB matching.
# ---------------------------------------------------------------------------

def test_urdu_confident_diagnosis_localizes_name_and_advice():
    provider, client = _provider(
        _vision_json("Tomato Early Blight", URDU_ADVICE, localized=URDU_NAME)
    )

    result = provider.diagnose(_image("ur"))

    assert len(client.models.calls) == 1
    assert result["diagnosis"] == "Tomato Early Blight"      # canonical English key
    assert urdu_count(result["diagnosis_localized"]) >= 2    # Urdu display label
    assert urdu_count(result["advice"]) >= 8                  # Urdu prose
    assert isinstance(result["confidence"], float)            # not flattened


def test_prompt_keeps_diagnosis_canonical_english():
    provider, client = _provider(_vision_json("X", URDU_ADVICE, localized=URDU_NAME))

    provider.diagnose(_image("ur"))

    sys_instr = client.models.calls[0]["config"].system_instruction
    assert "diagnosis_localized" in sys_instr
    assert "STANDARD ENGLISH" in sys_instr
    assert "Keep the \"diagnosis\" value in the STANDARD ENGLISH" in sys_instr


# ---------------------------------------------------------------------------
# 6+14.2  Urdu + low-confidence / Unknown path: every fallback is Urdu script.
# ---------------------------------------------------------------------------

def test_urdu_low_confidence_fallback_is_urdu_script():
    # Gemini answers in English AND names an arbitrary KB-miss diagnosis
    # (reproduced live CASE 1: "Minor Leaf Spotting" + English advice).
    provider, _ = _provider(
        _vision_json(
            "Minor Leaf Spotting",
            "Some minor spotting is visible on the leaves.",
            confidence=0.3,
            localized="Minor Leaf Spotting",
        )
    )

    result = provider.diagnose(_image("ur"))

    assert result["needs_expert"] is True
    # English label ignored (wrong script) -> empty, frontend KB/Unknown chain.
    assert result["diagnosis_localized"] == ""
    # Low-confidence advice MUST be the Urdu safety net, never English.
    assert result["advice"] == FALLBACK_ADVICE_BY_LANG["ur"]
    assert urdu_count(result["advice"]) >= 8
    assert "confidently diagnose" not in result["advice"]


def test_urdu_non_plant_message_is_urdu_script():
    wrong = "This does not look like a plant photo."
    provider, client = _provider(
        _vision_json("Unknown", wrong, confidence=0.0, is_plant=False),
        wrong,  # rewrite attempt 1: still English
        wrong,  # stronger retry: still English
    )

    result = provider.diagnose(_image("ur"))

    assert result["diagnosis"] == "Unknown"
    assert result["advice"] == NOT_A_PLANT_ADVICE_BY_LANG["ur"]
    assert urdu_count(result["advice"]) >= 8
    assert len(client.models.calls) == 3  # vision + rewrite + stronger retry


# ---------------------------------------------------------------------------
# 2  Diagnosis NAME localization sources.
# ---------------------------------------------------------------------------

def test_urdu_localized_name_backfilled_from_knowledge_base():
    from backend.services.ai_pipeline import load_knowledge_base

    kb = load_knowledge_base(gp._KB_PATH)
    assert kb, "knowledge base must be loadable for this test"
    entry = kb[0]
    provider, _ = _provider(
        # Gemini followed the English-name rule but skipped the localized one.
        _vision_json(
            entry["issue_name_english"], URDU_ADVICE, localized=None
        )
    )

    result = provider.diagnose(_image("ur"))

    assert result["diagnosis"] == entry["issue_name_english"]
    assert result["diagnosis_localized"] == entry["issue_name_urdu"]
    assert urdu_count(result["diagnosis_localized"]) >= 2


def test_urdu_roman_localized_name_is_rejected():
    provider, _ = _provider(
        _vision_json(
            "Minor Leaf Spotting", URDU_ADVICE,
            localized="Tamatar mein Bacterial Spot",
        )
    )

    result = provider.diagnose(_image("ur"))

    # A Roman-Urdu label must never be presented as the Urdu diagnosis, and
    # the KB has no name for this synthetic diagnosis -> stripped entirely.
    assert result["diagnosis_localized"] == ""


def test_urdu_kb_localized_name_wins_over_missing_gemini_label():
    """If Gemini's localized label is in the wrong script but the KB HAS a
    proper Urdu name for the disease, the KB name backfills (localized name
    exists -> must be used)."""
    provider, _ = _provider(
        _vision_json(
            "Northern Corn Leaf Blight", URDU_ADVICE,
            localized="Makki mein Corn Leaf Blight",  # wrong script -> rejected
        )
    )

    result = provider.diagnose(_image("ur"))

    assert result["diagnosis_localized"] != "Makki mein Corn Leaf Blight"
    assert urdu_count(result["diagnosis_localized"]) >= 2


def test_unknown_diagnosis_never_becomes_a_localized_label():
    provider, _ = _provider(
        _vision_json("Unknown", URDU_ADVICE, confidence=0.0, localized="Unknown")
    )
    result = provider.diagnose(_image("ur"))
    assert result["diagnosis_localized"] == ""


# ---------------------------------------------------------------------------
# 5+14.4  Vision advice initially in the wrong script -> retry -> fallback.
# ---------------------------------------------------------------------------

def test_urdu_vision_roman_advice_rewritten_to_urdu_when_model_cooperates():
    roman = "Patte hata dein aur phayl se bachayen."
    provider, client = _provider(
        _vision_json("Tomato Late Blight", roman, localized=URDU_NAME), URDU_ADVICE
    )

    result = provider.diagnose(_image("ur"))

    assert len(client.models.calls) == 2       # vision + rewrite
    assert result["advice"] == URDU_ADVICE     # rewrite kept, not the generic net
    assert urdu_count(result["advice"]) >= 8


def test_urdu_vision_roman_advice_falls_back_when_rewrite_also_fails():
    roman = "Patte hata dein aur phayl se bachayen."
    provider, client = _provider(
        _vision_json("Tomato Late Blight", roman, localized=URDU_NAME),
        roman,   # rewrite attempt still Roman
        roman,   # stronger retry still Roman
    )

    result = provider.diagnose(_image("ur"))

    assert len(client.models.calls) == 3
    assert roman not in result["advice"]        # NEVER return the wrong-language text
    # Deterministic chain: KB-localized prose for this diagnosis (validated);
    # the generic static net is only the last resort when the KB has no entry.
    assert gp._prose_matches_language(result["advice"], "ur")
    assert urdu_count(result["advice"]) >= 8


# ---------------------------------------------------------------------------
# 5+14.5  Roman Urdu: zero Urdu/Arabic characters anywhere in system prose.
# ---------------------------------------------------------------------------

def test_rom_advice_with_urdu_script_retries_then_latin_fallback():
    urdu_text = "متاثرہ پتوں کو ہٹا دیں اور سپرے کریں۔"
    provider, client = _provider(
        _vision_json("Corn Common Rust", urdu_text, localized="مکئی میں زنگ"),
        urdu_text,
        urdu_text,
    )

    result = provider.diagnose(_image("rom"))

    assert len(client.models.calls) == 3
    assert result["advice"] == FALLBACK_ADVICE_BY_LANG["rom"]
    assert urdu_count(result["advice"]) == 0
    assert urdu_count(result["diagnosis_localized"]) == 0  # Urdu label rejected


def test_rom_correct_answer_is_untouched_single_call():
    provider, client = _provider(
        _vision_json("Corn Common Rust", ROM_ADVICE, localized=ROM_NAME)
    )

    result = provider.diagnose(_image("rom"))

    assert len(client.models.calls) == 1
    assert result["advice"] == ROM_ADVICE
    assert result["diagnosis_localized"] == ROM_NAME
    assert urdu_count(result["advice"]) == 0
    assert urdu_count(result["diagnosis_localized"]) == 0


# ---------------------------------------------------------------------------
# 6+14.1  English: pure English passthrough, no extra enforcement calls.
# ---------------------------------------------------------------------------

def test_en_confident_result_is_english_only():
    provider, client = _provider(
        _vision_json("Tomato Early Blight", "Remove affected leaves now.")
    )

    result = provider.diagnose(_image("en"))

    assert len(client.models.calls) == 1
    assert result["diagnosis"] == "Tomato Early Blight"
    assert result["advice"] == "Remove affected leaves now."
    assert result["diagnosis_localized"] == ""  # frontend renders English directly
    assert urdu_count(json.dumps(result, ensure_ascii=False)) == 0


# ---------------------------------------------------------------------------
# 7  RAG grounding must not force English onto an Urdu result.
# ---------------------------------------------------------------------------

def test_urdu_rag_grounding_final_advice_is_urdu():
    english_vision = "Remove affected leaves and improve airflow."
    provider, client = _provider(
        _vision_json("Tomato Early Blight", english_vision, localized=URDU_NAME),
        URDU_ADVICE,  # the RAG-grounded rewrite answer
    )
    kb_entry = {"issue_name_english": "Tomato Early Blight", "symptom_keywords": ["blight"]}
    provider._retrieve_kb_entries = lambda *t: [kb_entry]

    result = provider.diagnose(_image("ur"))

    # 1 vision call + 1 grounded rewrite; the FINAL (post-RAG) text is Urdu.
    assert len(client.models.calls) == 2
    assert result["advice"] == URDU_ADVICE
    assert urdu_count(result["advice"]) >= 8


def test_urdu_rag_grounding_wrong_script_is_revalidated():
    english_vision = "Remove affected leaves and improve airflow."
    roman_rewrite = "Patte hata dein aur airflow behtar karein."
    provider, client = _provider(
        _vision_json("Tomato Early Blight", english_vision, localized=URDU_NAME),
        roman_rewrite,  # RAG rewrite ignores the script
        roman_rewrite,  # stronger retry inside _generate_advice also ignores it
    )
    kb_entry = {"issue_name_english": "Tomato Early Blight", "symptom_keywords": ["blight"]}
    provider._retrieve_kb_entries = lambda *t: [kb_entry]

    result = provider.diagnose(_image("ur"))

    # The wrong-script RAG output must NEVER reach the farmer.
    assert roman_rewrite not in result["advice"]
    assert urdu_count(result["advice"]) >= 8


# ---------------------------------------------------------------------------
# 5+14.7  Follow-up: final answer is script-checked, then localized fallback.
# ---------------------------------------------------------------------------

def test_followup_ur_returns_urdu_fallback_when_both_attempts_are_roman():
    roman1 = "Patton mein daaghen hain, paani kam dein."
    roman2 = "Yeh dekhne jaisi baat nahi, expert ko dikhayen."
    provider, client = _provider(roman1, roman2)

    answer = provider.answer_followup(
        "Mera kya karein?", context={"diagnosis": "Leaf Spot", "language": "ur"}
    )

    assert len(client.models.calls) == 2
    assert answer not in (roman1, roman2)          # never ship the wrong-language text
    assert urdu_count(answer) >= 8
    assert answer == FALLBACK_ADVICE_BY_LANG["ur"]


def test_followup_rom_never_returns_urdu_script():
    urdu1 = "پتوں کے داغ ہیں، پانی کم دیں۔"
    urdu2 = "ماہر کو دکھائیں۔"
    provider, client = _provider(urdu1, urdu2)

    answer = provider.answer_followup(
        "Kya karun?", context={"diagnosis": "Leaf Spot", "language": "rom"}
    )

    assert len(client.models.calls) == 2
    assert urdu_count(answer) == 0
    assert answer == FALLBACK_ADVICE_BY_LANG["rom"]


def test_followup_ur_correct_first_answer_kept():
    provider, client = _provider(URDU_ADVICE)

    answer = provider.answer_followup(
        "Mera kya karein?", context={"diagnosis": "X", "language": "ur"}
    )

    assert len(client.models.calls) == 1
    assert answer == URDU_ADVICE


def test_followup_en_passthrough():
    provider, client = _provider("Water every two days after treatment.")

    answer = provider.answer_followup(
        "How often should I water?", context={"diagnosis": "X", "language": "en"}
    )

    assert len(client.models.calls) == 1
    assert answer == "Water every two days after treatment."


# ---------------------------------------------------------------------------
# 13  Static language matrix over every hardcoded safety-net string.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("mapping", [FALLBACK_ADVICE_BY_LANG, NOT_A_PLANT_ADVICE_BY_LANG])
def test_localized_safety_nets_matrix(mapping):
    assert urdu_count(mapping["en"]) == 0
    assert mapping["en"].isascii()
    assert urdu_count(mapping["ur"]) >= 8       # real Urdu script, not Roman
    assert urdu_count(mapping["rom"]) == 0      # Latin only
    assert any(w in mapping["rom"].lower() for w in ("tasveer", "barah-e-karam", "karam"))


# ---------------------------------------------------------------------------
# 13+3  Devanagari pollution (पत्तों-style leak observed live) in any mode.
# ---------------------------------------------------------------------------

def test_urdu_advice_with_devanagari_is_rejected_and_rewritten():
    # Reproduced live: Urdu-script advice polluted by one Devanagari token.
    polluted = (
        "آپ کے ٹماٹر کے पت्तों پر جو भूरे داغ نظر آ रहे हैं، یہ ارلی بلائٹ ہے۔"
    )
    provider, client = _provider(
        _vision_json("Tomato Early Blight", polluted, localized=URDU_NAME),
        URDU_ADVICE,  # rewrite returns clean Urdu -> accepted
    )

    result = provider.diagnose(_image("ur"))

    assert len(client.models.calls) == 2
    assert result["advice"] == URDU_ADVICE
    assert urdu_count(result["advice"]) >= 8
    assert not re.search(r"[\u0900-\u097F]", result["advice"])


def test_urdu_devanagari_never_shipped_even_after_failed_rewrites():
    polluted = "یہ पत्तों کی بات ہے، ذرا دیکھیں۔"
    provider, _ = _provider(
        _vision_json("Tomato Early Blight", polluted, localized=URDU_NAME),
        polluted, polluted,  # rewrite + stronger retry stay polluted
    )

    result = provider.diagnose(_image("ur"))

    assert polluted not in result["advice"]
    assert gp._prose_matches_language(result["advice"], "ur")
    assert not re.search(r"[\u0900-\u097F]", result["advice"])


def test_rom_and_en_reject_devanagari_pollution():
    for lang in ("rom", "en"):
        dirty = (
            "Patton par daag hain, foran spray karein पत्तों।"
            if lang == "rom"
            else "Remove the affected पत्तों leaves now."
        )
        provider, _ = _provider(_vision_json("Tomato Early Blight", dirty))
        result = provider.diagnose(_image(lang))
        assert not re.search(r"[\u0900-\u097F]", result["advice"]), lang
        assert result["advice"] != dirty


# ---------------------------------------------------------------------------
# 3+14  Spider Mites KB matching: variants resolve to the same agriculture
#       entry so Symptoms/Treatment/Prevention stop disappearing.
# ---------------------------------------------------------------------------

_CROP_KB_PATH = os.path.join(
    os.path.dirname(__file__), "..", "data", "plant_disease_dataset",
    "crop_knowledge.json",
)

SPIDER_MITE_VARIANTS = [
    "Spider Mites",
    "Two-spotted Spider Mite",
    "Tomato Spider Mites Two-spotted Spider Mite",
    "spider mites (two spotted spider mite)",
]


def _kb_matching_tokens(text):
    return gp._name_tokens(text)


def _tomato_diseases():
    with open(_CROP_KB_PATH, encoding="utf-8") as fh:
        ck = json.load(fh)
    tomato = [p for p in ck["plants"] if p["name"]["en"].lower() == "tomato"][0]
    return ck, tomato["diseases"]


def test_spider_mites_kb_entry_has_full_localized_content():
    _, diseases = _tomato_diseases()
    entry = [d for d in diseases if "spider mite" in d["name"]["en"].lower()]
    assert entry, "crop_knowledge.json must contain a Spider Mites tomato entry"
    d = entry[0]
    for field in ("name", "description", "symptoms", "treatment", "prevention"):
        assert d[field]["en"], f"{field} missing English content"
        assert d[field].get("ur"), f"{field} missing Urdu content (ur mode would fall back to English)"
    # Urdu lists must actually be Urdu script.
    for s in d["symptoms"]["ur"]:
        assert urdu_count(s) >= 4, s
    assert "spider mites" in [a.lower() for a in d.get("aliases", [])]


def test_spider_mites_variants_resolve_to_one_entry_like_the_frontend():
    """Mirror frontend matchScore token logic: every label variant must reach
    the SAME Spider Mites entry (aliases or full-token containment)."""
    _, diseases = _tomato_diseases()
    entry = [d for d in diseases if "spider mite" in d["name"]["en"].lower()][0]
    label_tokens = _kb_matching_tokens(entry["name"]["en"])
    aliases = [a.lower() for a in entry.get("aliases", [])]
    for variant in SPIDER_MITE_VARIANTS:
        vt = _kb_matching_tokens(variant)
        matched = (
            any(a in variant.lower() for a in aliases)
            or label_tokens <= vt
            or vt <= label_tokens
        )
        assert matched, f"variant {variant!r} does not resolve to the KB entry"


def test_rom_overlay_exists_for_spider_mites_entry():
    """The frontend Roman Urdu transliteration layer must cover the Spider
    Mites disease id, Latin-only (no Urdu script in rom strings)."""
    _, diseases = _tomato_diseases()
    disease_id = [d for d in diseases if "spider mite" in d["name"]["en"].lower()][0][
        "disease_id"
    ]
    ts_path = os.path.join(
        os.path.dirname(__file__), "..", "frontend", "src", "data", "agriculture.ts"
    )
    src = open(ts_path, encoding="utf-8").read()
    assert f"{disease_id}: {{" in src, f"ROMAN_URDU missing {disease_id}"
    block = src.split(f"{disease_id}: {{", 1)[1].split("\n  },", 1)[0]
    assert urdu_count(block) == 0, "rom overlay block must be Latin-only"
    assert "symptoms" in block and "treatment" in block and "prevention" in block


def test_urdu_spider_mites_diagnosis_backfills_urdu_name():
    """Backend gate: even when Gemini omits diagnosis_localized, the KB Urdu
    name for the same disease (variant-tolerant token match) is filled in."""
    provider, _ = _provider(
        _vision_json(
            "Tomato Spider Mites Two-spotted Spider Mite",
            URDU_ADVICE,
            localized=None,
        )
    )

    result = provider.diagnose(_image("ur"))

    assert result["diagnosis"] == "Tomato Spider Mites Two-spotted Spider Mite"
    assert urdu_count(result["diagnosis_localized"]) >= 2


# ---------------------------------------------------------------------------
# 9+14.9  Contract stays structured: no field flattening / heading concat.
# ---------------------------------------------------------------------------

def test_result_contract_is_not_flattened():
    provider, _ = _provider(
        _vision_json("Tomato Early Blight", URDU_ADVICE, localized=URDU_NAME)
    )

    result = provider.diagnose(_image("ur"))

    parsed = DiagnosisResponse(**result)  # schema validation, raises on drift
    assert parsed.diagnosis == "Tomato Early Blight"
    assert isinstance(parsed.confidence, float)
    # Advice is its own prose block — never merged with the label/confidence.
    assert parsed.diagnosis not in parsed.advice
    assert "confidence" not in parsed.advice.lower()


# ---------------------------------------------------------------------------
# 15  Hard final-language guarantee (reproduced live: language=ur shipped
#     "Aap ke tamatar ke podon par Early Blight ke asraat hain...").
#     Roman-dominant prose is NEVER valid Urdu, and the FINAL gate at
#     diagnose()'s return boundary funnels every path through a
#     deterministic validate -> restate -> KB-fallback -> static-fallback
#     chain that validates each candidate before returning.
# ---------------------------------------------------------------------------

# Verbatim shape of the shipped bug: pure Roman Urdu.
PURE_ROMAN_ADVICE = (
    "Aap ke tamatar ke podon par Early Blight ke asraat hain. Mutaassir "
    "patton ko foran hata dein aur ache fungicide ka spray karein."
)
# The sneakier variant: Roman prose with a few Urdu-script words pasted in —
# enough Urdu CHARACTERS to fool the old presence-only checker.
MIXED_ADVICE = (
    "Is tasweer mein makai ke patton par lambay bhore dhabbe نظر آ رہے ہیں، "
    "yeh Northern Leaf Blight hai۔"
)


def test_ur_rule_rejects_roman_and_latin_dominant_mix():
    assert not gp._prose_matches_language(PURE_ROMAN_ADVICE, "ur")
    assert urdu_count(MIXED_ADVICE) >= 8          # would pass the OLD rule
    assert gp._latin_script_dominant(MIXED_ADVICE)
    assert not gp._prose_matches_language(MIXED_ADVICE, "ur")

    legit = (
        "ٹماٹر کے پتوں پر Early Blight کی علامات نظر آتی ہیں۔ متاثرہ پتے "
        "ہٹا کر copper oxychloride کا سپرے کریں۔"
    )
    assert gp._prose_matches_language(legit, "ur")  # English names stay allowed


def test_pure_roman_advice_in_ur_is_never_returned():
    """The exact reproduced bug: tomato, language=ur, Roman advice."""
    provider, _ = _provider(
        _vision_json("Tomato Early Blight", PURE_ROMAN_ADVICE, localized=URDU_NAME),
        PURE_ROMAN_ADVICE,  # rewrite attempt: still Roman
        PURE_ROMAN_ADVICE,  # stronger retry: still Roman
    )

    result = provider.diagnose(_image("ur"))

    assert result["advice"] != PURE_ROMAN_ADVICE
    assert PURE_ROMAN_ADVICE not in result["advice"]
    assert gp._prose_matches_language(result["advice"], "ur")
    assert not gp._latin_script_dominant(result["advice"])
    assert urdu_count(result["advice"]) >= 8


# ---------------------------------------------------------------------------
# 18  English must be ENGLISH, not Roman Urdu. Both are pure Latin script, so
#     the old script-only `en` rule accepted Roman-Urdu advice verbatim; the
#     word-level Roman-Urdu detector is what closes that gap.
# ---------------------------------------------------------------------------

ENGLISH_REWRITE = (
    "Remove the affected leaves immediately and improve airflow around the "
    "plant so the foliage dries quickly."
)


def test_en_rule_rejects_roman_urdu_but_keeps_english():
    # Roman Urdu is Latin-only, so the pure script check used to pass it.
    assert gp._looks_like_roman_urdu(PURE_ROMAN_ADVICE)
    assert not gp._prose_matches_language(PURE_ROMAN_ADVICE, "en")
    # Genuine English (incl. a standard disease/chemical name) stays valid.
    assert not gp._looks_like_roman_urdu(ENGLISH_REWRITE)
    assert gp._prose_matches_language(ENGLISH_REWRITE, "en")
    assert gp._prose_matches_language(
        "Apply Mancozeb after confirming the dose with a local expert.", "en"
    )


def test_roman_advice_in_en_is_rewritten_to_english():
    """Vision drifts to Roman Urdu for an English request; the gate must
    reject it and return the English rewrite, never the Roman original."""
    provider, _ = _provider(
        _vision_json("Tomato Early Blight", PURE_ROMAN_ADVICE),
        ENGLISH_REWRITE,  # the English rewrite answer
    )

    result = provider.diagnose(_image("en"))

    assert result["advice"] == ENGLISH_REWRITE
    assert PURE_ROMAN_ADVICE not in result["advice"]
    assert gp._prose_matches_language(result["advice"], "en")
    assert not gp._looks_like_roman_urdu(result["advice"])
    assert urdu_count(result["advice"]) == 0


def test_en_never_ships_roman_urdu_even_when_every_rewrite_stays_roman():
    """Stubborn Roman output through rewrite + retry must collapse to the
    validated English static fallback — the invalid original is unreachable."""
    provider, _ = _provider(
        _vision_json("Tomato Early Blight", PURE_ROMAN_ADVICE),
        PURE_ROMAN_ADVICE,  # rewrite attempt: still Roman
        PURE_ROMAN_ADVICE,  # stronger retry: still Roman
    )

    result = provider.diagnose(_image("en"))

    assert PURE_ROMAN_ADVICE not in result["advice"]
    assert gp._prose_matches_language(result["advice"], "en")
    assert not gp._looks_like_roman_urdu(result["advice"])
    assert urdu_count(result["advice"]) == 0


def test_roman_rewrite_recovers_when_model_complies():
    provider, client = _provider(
        _vision_json("Tomato Early Blight", MIXED_ADVICE, localized=URDU_NAME),
        URDU_ADVICE,
    )

    result = provider.diagnose(_image("ur"))

    assert result["advice"] == URDU_ADVICE
    assert len(client.models.calls) == 2  # vision + one enforced rewrite


def test_kb_derived_fallback_is_used_when_rewrites_keep_failing():
    """Deterministic step 5: model uncooperative -> diagnosis-specific KB
    Urdu prose (validated), NOT the invalid original, NOT necessarily the
    generic static net."""
    provider, _ = _provider(
        _vision_json(
            "Tomato Yellow Leaf Curl Virus", MIXED_ADVICE, localized=URDU_NAME
        ),
        MIXED_ADVICE,
        MIXED_ADVICE,
    )

    result = provider.diagnose(_image("ur"))

    kb_text = provider._kb_localized_advice("Tomato Yellow Leaf Curl Virus", "ur")
    assert kb_text and gp._prose_matches_language(kb_text, "ur")
    assert result["advice"] == kb_text
    assert result["advice"] != FALLBACK_ADVICE_BY_LANG["ur"]


def test_static_fallback_when_kb_has_no_entry_for_diagnosis():
    provider, _ = _provider(
        _vision_json("Minor Leaf Spotting", MIXED_ADVICE, localized=URDU_NAME),
        MIXED_ADVICE,
        MIXED_ADVICE,
    )

    result = provider.diagnose(_image("ur"))

    assert result["advice"] == FALLBACK_ADVICE_BY_LANG["ur"]
    assert gp._prose_matches_language(result["advice"], "ur")


def test_fallback_chain_validates_candidates_never_ships_invalid():
    """Even a corrupted/garbage `fallback` argument cannot make
    _ensure_script return invalid text: the KB candidate is validated and
    wins, and an invalid static fallback is never chosen over it."""
    provider, _ = _provider(MIXED_ADVICE, MIXED_ADVICE)  # rewrites keep failing

    out = provider._ensure_script(
        PURE_ROMAN_ADVICE,                      # invalid original
        "Tomato Yellow Leaf Curl Virus",
        "", "ur",
        "Yeh bhi Roman Urdu fallback hai۔",  # deliberately invalid fallback
    )

    assert gp._prose_matches_language(out, "ur")
    assert out not in (PURE_ROMAN_ADVICE, "Yeh bhi Roman Urdu fallback hai۔")


def test_final_gate_at_diagnose_boundary_fixes_post_vision_leaks(monkeypatch):
    """Prove the gate validates the ACTUAL final value even if something
    AFTER _vision_diagnose replaced the advice."""
    provider, client = _provider(URDU_ADVICE)  # one scripted rewrite

    def fake_vision(img):
        return {
            "filename": img.filename,
            "diagnosis": "Corn Northern Leaf Blight",
            "diagnosis_localized": "مکئی میں Northern Leaf Blight ka telaa",
            "confidence": 0.85,
            "advice": MIXED_ADVICE,
            "needs_expert": False,
        }

    monkeypatch.setattr(provider, "_vision_diagnose", fake_vision)

    result = provider.diagnose(_image("ur"))

    assert len(client.models.calls) == 1           # boundary rewrite only
    assert result["advice"] == URDU_ADVICE         # never the mixed original
    # Roman-dominant localized label is stripped -> frontend KB/Unknown chain.
    assert result["diagnosis_localized"] == ""
    assert result["diagnosis"] == "Corn Northern Leaf Blight"  # canonical kept


def test_final_gate_is_noop_without_language(monkeypatch):
    provider, client = _provider()

    def fake_vision(img):
        return {
            "filename": img.filename,
            "diagnosis": "Corn Northern Leaf Blight",
            "diagnosis_localized": "",
            "confidence": 0.85,
            "advice": "Remove affected leaves now.",
            "needs_expert": False,
        }

    monkeypatch.setattr(provider, "_vision_diagnose", fake_vision)

    result = provider.diagnose(_image(None))  # legacy no-language contract shape

    assert result["advice"] == "Remove affected leaves now."
    assert len(client.models.calls) == 0  # gate never fires without a language


def test_confidence_fields_stay_separate_in_the_contract():
    """Bug 2 guard (backend side): confidence stays a numeric field and the
    heading/caption live in the frontend translations — no code path may
    concatenate label + caption into advice or a single string."""
    provider, _ = _provider(
        _vision_json("Tomato Early Blight", URDU_ADVICE, localized=URDU_NAME)
    )
    result = provider.diagnose(_image("ur"))

    assert isinstance(result["confidence"], float)
    assert "یقین کی سطح" not in result["advice"]
    assert not any(v in result["advice"] for v in ("confidence", "Confidence"))


# ---------------------------------------------------------------------------
# 16  Localized DIAGNOSIS-LABEL validation must reject every non-Urdu script.
#     Reproduced live with language=ur:
#         diagnosis_localized: "ٹमेटو یلو লিफ ಕরल وाइرس"
#     Gemini spelled "Tomato Yellow Leaf Curl Virus" with lookalike letters
#     from several Indic scripts at once. The old rule only screened for
#     Devanagari, so a Bengali/Kannada/Telugu/… mix carrying enough real Urdu
#     characters was certified as a valid Urdu label.
# ---------------------------------------------------------------------------

# Verbatim live leak (Devanagari + Bengali + Kannada inside an Urdu frame).
MIXED_TYLCV_LABEL = "ٹमেটو یلو লিফ ಕर्ल وाइرس"
# Same failure mode WITHOUT any Devanagari — this is the shape the old
# Devanagari-only screen could not see (11 genuine Urdu characters, so the
# Urdu minimum and the Latin-dominance rule both pass it).
MIXED_NO_DEVANAGARI_LABEL = "ٹماٹر লিফ ಕರ್ಲ ವೈರಸ್"

# One foreign-script word pasted into an otherwise-correct Urdu label.
FOREIGN_SCRIPT_WORDS = [
    ("Bengali", "লিফ"),
    ("Devanagari", "पति"),
    ("Gurmukhi", "ਪਤੀ"),
    ("Gujarati", "પતી"),
    ("Oriya", "ପତ୍ର"),
    ("Tamil", "இலை"),
    ("Telugu", "ఆకు"),
    ("Kannada", "ಕರ್ಲ"),
    ("Malayalam", "ഇല"),
    ("Sinhala", "පත"),
]


def test_live_mixed_script_label_is_rejected():
    assert gp._localized_name_matches(MIXED_TYLCV_LABEL, "ur") is False


def test_mixed_label_without_devanagari_is_rejected():
    """The exact hole: no Devanagari at all, plenty of Urdu characters."""
    assert urdu_count(MIXED_NO_DEVANAGARI_LABEL) >= 2
    assert not re.search(r"[\u0900-\u097F]", MIXED_NO_DEVANAGARI_LABEL)
    assert gp._localized_name_matches(MIXED_NO_DEVANAGARI_LABEL, "ur") is False


@pytest.mark.parametrize("script,word", FOREIGN_SCRIPT_WORDS)
def test_every_non_urdu_script_mix_is_rejected_in_ur(script, word):
    label = f"ٹماٹر {word} وائرس"
    assert gp._localized_name_matches(label, "ur") is False, script


def test_genuine_urdu_labels_stay_valid():
    assert gp._localized_name_matches("ٹماٹر زرد پتی کرل وائرس", "ur") is True
    assert gp._localized_name_matches(URDU_NAME, "ur") is True


def test_english_disease_name_inside_an_urdu_label_is_not_over_restricted():
    """Standard English/chemical names are allowed inside Urdu labels, and
    acronyms too — only a THIRD SCRIPT is a problem."""
    assert gp._localized_name_matches("ٹماٹر میں Early Blight ہے", "ur") is True
    assert gp._localized_name_matches("ٹماٹر TYLCV وائرس", "ur") is True


@pytest.mark.parametrize("language", ["rom", "en"])
def test_latin_only_modes_reject_every_non_latin_script(language):
    """rom accepts Latin-only labels; en never needs a localized label at all.
    Both must reject every other script, whichever word it appears in."""
    assert gp._localized_name_matches(ROM_NAME, "rom") is True
    assert gp._localized_name_matches(ROM_NAME, "en") is False
    for _script, word in FOREIGN_SCRIPT_WORDS:
        assert gp._localized_name_matches(f"Tamatar {word} Virus", language) is False
    assert gp._localized_name_matches("ٹماٹر وائرس", language) is False


def test_mixed_script_label_never_reaches_the_response():
    """End-to-end: Gemini shipping the leaked label must NOT surface it — the
    final gate either backfills the KB Urdu name or clears the field so the
    frontend's own localization chain takes over."""
    provider, _ = _provider(
        _vision_json(
            "Tomato Yellow Leaf Curl Virus",
            URDU_ADVICE,
            localized=MIXED_TYLCV_LABEL,
        )
    )

    result = provider.diagnose(_image("ur"))

    label = result["diagnosis_localized"]
    assert label != MIXED_TYLCV_LABEL
    assert label == "" or gp._localized_name_matches(label, "ur")
    assert result["diagnosis"] == "Tomato Yellow Leaf Curl Virus"  # KB key intact


# ---------------------------------------------------------------------------
# 17  Advice prose: the SAME character-level allowlist as the labels.
#     `_prose_matches_language("ur")` used to screen only for Devanagari, so
#     Urdu advice polluted with Bengali/Kannada/Telugu/Cyrillic/… lookalikes
#     passed as long as it held 8+ Urdu characters. Requirement: `language=ur`
#     advice is proper Urdu script, with only legitimate Latin disease/chemical
#     names mixed in.
# ---------------------------------------------------------------------------

CLEAN_URDU_ADVICE = (
    "متاثرہ پتوں کو فوری طور پر ہٹا کر تلف کریں اور پودوں کے درمیان ہوا کی "
    "آمد و رفت بہتر بنائیں۔"
)

# Urdu prose with ONE word written in another script (each keeps 8+ Urdu
# characters, so the old rule could not see them).
FOREIGN_SCRIPT_ADVICE = [
    ("Bengali", "متاثرہ পতوں को فوری طور پر ہٹا کر تلف کریں اور پودوں کے درمیان ہوا بہتر رکھیں۔"),
    ("Devanagari", "متाثرہ پتوں کو فوری طور پر ہٹا کر تلف करें اور پودوں کے درمیان ہوا بہتر رکھیں۔"),
    ("Gurmukhi", "متاثرہ ਪਤوں کو فوری طور پر ہٹا کر تلف کریں اور پودوں کے درمیان ہوا بہتر رکھیں۔"),
    ("Gujarati", "متાથેਰہ پتوں کو فوری طور پر ہٹا کر تلف کریں اور پودوں کے درمیان ہوا بہتر رکھیں۔"),
    ("Oriya", "متାଥେରহ পتوں को فوری طور پر हटा कर تلف کریں اور پودوں के درमियान हوا बेহतर ਰੱਖିଁ।"),
    ("Tamil", "மதா்ہ பதோன کو فوری طور پر ہٹا کر تلف کریں اور پودوں کے درمیان ہوا بہتر رکھیں۔"),
    ("Telugu", "మతాథేరह పతోన کو فوری طور پر ہٹا کر تلف کریں اور پودوں کے درمیان ہوا بہتر رکھیں۔"),
    ("Kannada", "متಾಥೇರಹ ಪತೋನ को فوری طور पर हटā कर तલफ़ क্রिं और पودوں के दरमियान हवā बेहतर रkھيं।"),
    ("Malayalam", "മതാഥേരഹ പതോന کو فوری طور پر ہٹا کر تلف کریں اور پودوں کے درمیان ہوا بہتر رکھیں۔"),
    ("Sinhala", "මතාඨේරහ පතෝන को فوری طور पर हटा कर تلف کریں اور پودوں کے درمیان ہوا بہتر رکھیں۔"),
    ("CJK", "متاثرہ 病叶 को فوری طور पर हटा कर تلف کریں اور پودوں के درमियान हوا बेहतर রাখيं।"),
    ("Cyrillic", "метاثرہ پتوں کو فوری طور पर हटा कर تлф़ کریं और पौदोں के दरमियान हवā बेहतर रkھيं।"),
]


def test_valid_urdu_advice_is_accepted():
    assert gp._prose_matches_language(CLEAN_URDU_ADVICE, "ur") is True


def test_urdu_advice_with_english_disease_or_chemical_names_is_accepted():
    """Legitimate technical names stay allowed — the allowlist permits Latin."""
    with_disease = (
        "یہ ٹماٹر میں Early Blight کی بیماری ہے، متاثرہ پتے ہٹا دیں اور باقی "
        "پودوں پر مناسب فیصلہ کریں۔"
    )
    with_chemical = (
        "Mancozeb 75% WP کو دو ہفتے کے وقفے سے چھڑکائیں اور پودوں کے درمیان "
        "ہوا کی آمد و رفت کو بہتر بنائیں۔"
    )
    assert gp._prose_matches_language(with_disease, "ur") is True
    assert gp._prose_matches_language(with_chemical, "ur") is True


def test_urdu_advice_with_digits_and_punctuation_is_accepted():
    """Digits, symbols and Latin/Urdu punctuation are script-neutral."""
    text = (
        "زائد نمی سے بچنے کے لیے 2 ہفتے کے وقفے سے 0.5٪ محلول (75% WP) — "
        "چھڑکاو جاری رکھیں؛ پتوں کی نگرانی کرتے رہیں۔"
    )
    assert gp._prose_matches_language(text, "ur") is True


@pytest.mark.parametrize("script,text", FOREIGN_SCRIPT_ADVICE)
def test_foreign_script_in_urdu_advice_is_rejected(script, text):
    assert urdu_count(text) >= 8, f"{script} fixture must keep the old rule fooled"
    assert gp._prose_matches_language(text, "ur") is False, script


def test_roman_urdu_and_english_advice_stay_rejected():
    """The pre-existing rejections are not weakened by the new allowlist."""
    assert gp._prose_matches_language(PURE_ROMAN_ADVICE, "ur") is False
    assert gp._prose_matches_language(ROM_ADVICE, "ur") is False
    assert (
        gp._prose_matches_language(
            "Remove affected leaves immediately and improve air circulation "
            "between the plants to reduce humidity around the canopy.", "ur"
        )
        is False
    )
    # ...and each mode still accepts its own script.
    assert gp._prose_matches_language(ROM_ADVICE, "rom") is True
    assert gp._prose_matches_language(
        "Remove affected leaves immediately and improve air circulation.", "en"
    ) is True


def test_latin_only_modes_reject_foreign_script_prose():
    polluted = "Mutaasira पतton ko foran hata dein aur paudon ke darmiyan hawa behtar banayein."
    assert gp._prose_matches_language(polluted, "rom") is False
    assert gp._prose_matches_language(polluted, "en") is False


def test_foreign_script_advice_never_ships_from_diagnose():
    """End-to-end: Kannada-polluted Urdu advice from Gemini must be replaced by
    the deterministic chain (restate -> KB -> static), never returned as-is."""
    polluted = next(text for name, text in FOREIGN_SCRIPT_ADVICE if name == "Kannada")
    provider, _ = _provider(
        _vision_json("Tomato Early Blight", polluted, localized=URDU_NAME)
    )

    result = provider.diagnose(_image("ur"))

    advice = result["advice"]
    assert polluted not in advice
    assert gp._prose_matches_language(advice, "ur") is True
    assert gp._has_foreign_script_letters(advice, urdu_allowed=True) is False


def test_clean_restate_of_polluted_advice_is_used_when_it_complies():
    """The chain still prefers the rewritten advice over the local fallback."""
    polluted = next(text for name, text in FOREIGN_SCRIPT_ADVICE if name == "Bengali")
    provider, client = _provider(
        _vision_json("Tomato Early Blight", polluted, localized=URDU_NAME),
        CLEAN_URDU_ADVICE,  # the stronger rewrite instruction complies
    )

    result = provider.diagnose(_image("ur"))

    assert result["advice"] == CLEAN_URDU_ADVICE
    assert len(client.models.calls) == 2


def test_kb_fallback_skips_a_foreign_script_line_but_keeps_the_entry():
    """data/knowledge_base.json ships at least one Urdu line typed with
    Cyrillic lookalikes. The RAG data is never rewritten — the dirty line is
    skipped so the diagnosis-specific fallback tier survives for that disease."""
    provider, _ = _provider(_vision_json("Tomato Septoria Leaf Spot", URDU_ADVICE))

    text = provider._kb_localized_advice("Tomato Septoria Leaf Spot", "ur")

    assert text
    assert "спорے" not in text  # the Cyrillic-typed tip was filtered out
    assert gp._prose_matches_language(text, "ur") is True
