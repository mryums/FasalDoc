"""gemini_provider.py
===================
Real AI-powered DiagnosisProvider backed by Google's Gemini 2.5 Flash
(vision + text in a single multimodal call).

This provider is second in the fallback chain used by
``diagnosis_service._build_provider()``:

    Qwen (Member 1)  ->  Gemini (this module)  ->  Mock (offline)

It is only ever constructed when:
    * ``DASHSCOPE_API_KEY`` (Qwen) is missing/placeholder, AND
    * ``GEMINI_API_KEY`` looks like a real, non-placeholder key.

If Gemini itself is unreachable/misconfigured, ``diagnosis_service`` catches
the resulting exception and falls back to the offline mock, so the app never
hard-crashes just because a cloud AI provider is having a bad day.

Environment variables:
    GEMINI_API_KEY   -> your Google AI Studio / Gemini API key (required)
    GEMINI_MODEL     -> optional override, defaults to "gemini-3.6-flash"

Install dependencies:
    pip install google-genai
"""
from __future__ import annotations

import json
import logging
import os
import re
from typing import Any, Dict, List, Optional

from backend.services.diagnosis_service import DiagnosisProvider, ImageInput

logger = logging.getLogger("fasaldoc.gemini_provider")

DEFAULT_MODEL = "gemini-3.6-flash"

# Local knowledge base (same file/idea the Qwen pipeline uses). Loaded once,
# lazily, on the first confident diagnosis.
_KB_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "knowledge_base.json"
)
KB_MAX_ENTRIES = 3  # shortlist size fed to the grounding call (keeps prompts cheap)

# Below this confidence (0..1), we never show a specific diagnosis to the
# farmer — we recommend a human expert instead. Mirrors the safety net used
# by Member 1's Qwen pipeline (ai_pipeline.CONFIDENCE_THRESHOLD = 60/100).
CONFIDENCE_THRESHOLD = 0.60

FALLBACK_ADVICE = (
    "We could not confidently diagnose this from the photo and question "
    "provided. To avoid giving potentially wrong advice, please consult a "
    "local agriculture expert or extension officer for an in-person "
    "assessment."
)

NOT_A_PLANT_ADVICE = (
    "This image does not appear to show a plant or crop. Please upload a "
    "clear photo of the affected leaf, stem, or plant so we can help "
    "diagnose the issue."
)

# Localized variants of the two safety-net texts, keyed by the UI language
# code sent from the frontend. The Python-side safety logic (threshold,
# needs_expert) is identical for every language — only the wording changes.
FALLBACK_ADVICE_BY_LANG = {
    "en": FALLBACK_ADVICE,
    "ur": (
        "ہم اس تصویر اور سوال سے یقینی تشخیص نہیں کر سکے۔ غلط مشورے سے "
        "بچنے کے لیے براہ کرم کسی مقامی زرعی ماہر یا ایکسٹینشن آفیسر سے "
        "ذاتی طور پر معائنہ کروائیں۔"
    ),
    "rom": (
        "Hum is tasveer aur sawal se yaqeeni tashkhees nahi kar sakay. "
        "Ghalat mashwaray se bachne ke liye, barah-e-karam kisi maqami "
        "zaraat expert ya extension officer se shakhsiyat mein muaina "
        "karwayen."
    ),
}

NOT_A_PLANT_ADVICE_BY_LANG = {
    "en": NOT_A_PLANT_ADVICE,
    "ur": (
        "اس تصویر میں کوئی پودا یا فصل نظر نہیں آ رہی۔ براہ کرم متاثرہ "
        "پتے، تنے یا پودے کی واضح تصویر اپ لوڈ کریں تاکہ ہم مسئلے کی "
        "تشخیص میں مدد کر سکیں۔"
    ),
    "rom": (
        "Is tasveer mein koi pauda ya fasal nazar nahi aa rahi. Barah-e-"
        "karam mutassir patta, tana ya pauday ki saaf tasveer upload "
        "karein taake hum maslay ki tashkhees mein madad kar sakein."
    ),
}


def _localized(text_map: Dict[str, str], language: Optional[str]) -> str:
    """Pick the safety-net text matching the UI language; English default."""
    key = (language or "en").strip().lower()
    return text_map.get(key, text_map["en"])

GEMINI_SYSTEM_PROMPT = """You are "FasalDoc", an agricultural vision-and-advisory \
assistant that helps farmers diagnose crop health issues from a photo and an \
optional question. You are NOT a certain diagnosis tool -- you combine what is \
visually observable in the image with the farmer's question to give honest, \
conservative guidance.

Respond with ONLY a JSON object (no extra text, no markdown code fences) with \
exactly this structure:

{
  "is_plant_photo": true or false,
  "diagnosis": "canonical diagnosis label in ENGLISH (standard disease name), or 'Unknown' if unclear",
  "diagnosis_localized": "the same 'diagnosis' label expressed in the farmer's answer language (see the LANGUAGE rule); repeat the English label when answering in English",
  "confidence": 0.0-1.0 number,
  "advice": "clear, farmer-friendly advice text, 2-5 sentences",
  "needs_expert": true or false
}

Rules:
- ALWAYS keep "diagnosis" in the standard ENGLISH disease name -- the app
  matches it against a knowledge base, so translating it breaks enrichment.
  Only "diagnosis_localized" and "advice" follow the answer language.
- If the image does NOT show a plant/crop at all (e.g. a person, an animal, a \
random object, a blank/corrupted image), set "is_plant_photo" to false, \
"diagnosis" to "Unknown", "confidence" to 0.0, "needs_expert" to true, and \
"advice" to a short note asking the farmer to upload a clear plant photo. Do \
NOT invent crop symptoms for a non-plant photo.
- Set "confidence" honestly: high (0.7-1.0) only when symptoms in the image \
clearly match one specific diagnosis; medium (0.4-0.69) when partially clear; \
low (0.0-0.39) when the photo is blurry, ambiguous, or symptoms don't match \
anything specific.
- Set "needs_expert" to true whenever confidence is below 0.6, or the case \
looks severe, or you are not confident in a specific diagnosis.
- Be conservative -- it is much better to admit uncertainty than to \
confidently give wrong advice to a farmer who may act on it immediately.
- Use the farmer's question (if provided) to focus the advice, but never let \
it override what is actually visible in the image.
"""

# Mapping of the frontend UI language codes to an explicit answer-language
# instruction appended to the prompts. Anything unknown/missing stays English
# so the existing English behavior is preserved.
_LANGUAGE_INSTRUCTIONS = {
    "en": None,  # English is the prompt's default — no extra instruction.
    "ur": (
        'LANGUAGE: Keep the "diagnosis" value in the STANDARD ENGLISH '
        'disease name (it is matched against a knowledge base -- '
        'translating it breaks the app). Write the "diagnosis_localized" '
        'and "advice" values ENTIRELY in proper Urdu script (نستعلیق). '
        "Do NOT use Roman Urdu (Urdu written "\
        "with Latin letters) and do NOT answer in English. Answer in Urdu "
        "script EVEN IF the farmer's question was typed in Roman Urdu or "
        "English — ignore the question's script. Only standard disease/"
        "chemical names may stay in English inside the Urdu sentences.\n"
    ),
    "rom": (
        'LANGUAGE: Keep the "diagnosis" value in the STANDARD ENGLISH '
        "disease name (it is matched against a knowledge base). Write the "
        '"diagnosis_localized" and "advice" values in Roman Urdu — Urdu '
        "words spelled with Latin/English letters (e.g. diagnosis_localized "
        "'Tamatar mein Early Blight'). NEVER use Urdu/Arabic script; do NOT "
        "answer in English only.\n"
    ),
}

_DISEASE_NAME_RULE = (
    "DISEASE NAMES: Keep the diagnosis medically meaningful. If the disease "
    "has a widely understood local name, use it; otherwise keep the standard "
    "English disease name (e.g. 'Early Blight', 'Tomato Yellow Leaf Curl "
    "Virus') and describe it in the requested language. Never invent a "
    "literal translation that changes the medical meaning. JSON keys and "
    "boolean/number values must always stay exactly as specified.\n"
)


def _language_directive(language: Optional[str]) -> str:
    """Prompt fragment forcing the answer language; '' for English/default."""
    key = (language or "en").strip().lower()
    instruction = _LANGUAGE_INSTRUCTIONS.get(key)
    if not instruction:
        return ""
    return "\n" + instruction + _DISEASE_NAME_RULE


# Wording for the plain-text (advice-only) KB-grounding call, keyed by the
# UI language code. English is the default for unknown/missing values.
_ADVICE_LANGUAGE = {
    "ur": (
        "Urdu, written ENTIRELY in proper Urdu script (نستعلیق) — NEVER "
        "Roman Urdu (Latin-letter Urdu) and never English sentences, even "
        "if the farmer's question is typed in Roman Urdu or English. "
        "Standard disease/chemical names may remain in English inside the "
        "Urdu sentence"
    ),
    "rom": (
        "Roman Urdu — Urdu spelled with Latin/English letters only. NEVER "
        "use Urdu/Arabic script, and do not answer in English only"
    ),
}


def _advice_language_instruction(language: Optional[str]) -> str:
    key = (language or "en").strip().lower()
    return "Reply in " + _ADVICE_LANGUAGE.get(key, "English") + "."


# Urdu / Arabic script block (covers the extended letters Urdu adds: ٹ ڈ ں ے …).
_URDU_SCRIPT_RE = re.compile(r"[\u0600-\u06FF]")

# Devanagari (Hindi/Marathi) block — Gemini occasionally answers "Urdu" prose
# with Devanagari characters (पत्तों instead of پتوں). That is a different
# script entirely and must never reach the farmer in any of the 3 modes.
_DEVANAGARI_RE = re.compile(r"[\u0900-\u097F]")

# Latin letters — used to detect Roman Urdu masquerading as Urdu script.
_LATIN_LETTER_RE = re.compile(r"[A-Za-z]")


def _has_devanagari(text: Optional[str]) -> bool:
    return bool(_DEVANAGARI_RE.search(text or ""))


def _urdu_script_count(text: Optional[str]) -> int:
    return len(_URDU_SCRIPT_RE.findall(text or ""))


def _latin_script_dominant(text: Optional[str]) -> bool:
    """True when Latin-letter WORDS make up the bulk of the text.

    This is the shape of the reproduced bug: Roman-Urdu prose (`Aap ke
    tamatar ke podon par Early Blight ke asraat hain...`) with a few
    Urdu-script words pasted in — enough Urdu CHARACTERS to fool a simple
    presence check while the language of the sentence is still Roman Urdu.
    Counting whole words keeps legitimate Urdu prose that mentions one or
    two standard English disease/chemical names valid.
    """
    urdu_words = latin_words = 0
    for word in re.split(r"\s+", text or ""):
        if _URDU_SCRIPT_RE.search(word):
            urdu_words += 1
        elif _LATIN_LETTER_RE.search(word):
            latin_words += 1
    return latin_words > urdu_words


def _prose_matches_language(text: str, language: Optional[str]) -> bool:
    """Script-level language check for generated advice/follow-up prose.

    en  -> English: no Urdu/Arabic and no Devanagari characters.
    ur  -> must contain meaningful Urdu-script prose (not Roman Urdu/English)
           and must NOT be polluted with Devanagari (a different script).
           A Latin-word-dominant paragraph is Roman Urdu even when it holds
           a handful of Urdu characters, so dominance is rejected explicitly.
    rom -> must be Latin-only, i.e. ZERO Urdu/Arabic-script characters and
           zero Devanagari characters.
    """
    key = (language or "en").strip().lower()
    if key == "ur":
        return (
            _urdu_script_count(text) >= 8
            and not _has_devanagari(text)
            and not _latin_script_dominant(text)
        )
    if key == "rom":
        return _urdu_script_count(text) == 0 and not _has_devanagari(text)
    if key == "en":
        return _urdu_script_count(text) == 0 and not _has_devanagari(text)
    return True


def _localized_name_matches(name: str, language: Optional[str]) -> bool:
    """Script check for a short localized DIAGNOSIS label (not full prose).

    ur  -> must actually be Urdu script (a Roman/English label would leak).
    rom -> must be Latin-only (zero Urdu/Arabic characters).
    en  -> no separate localized label is needed.
    """
    key = (language or "en").strip().lower()
    cleaned = (name or "").strip()
    if not cleaned or cleaned.strip().lower() == "unknown":
        return False
    if _has_devanagari(cleaned):
        return False  # Devanagari is never a valid label in any mode.
    if key == "ur":
        # Urdu script AND not Latin-word-dominant (a Roman label with two
        # Urdu words pasted in is still Roman Urdu and must not display).
        return _urdu_script_count(cleaned) >= 2 and not _latin_script_dominant(cleaned)
    if key == "rom":
        return _urdu_script_count(cleaned) == 0
    return False


# Appended to the prompt on the single retry when the first answer ignored the
# requested script. Kept terse and unambiguous about the failure.
_STRONGER_LANGUAGE = {
    "en": (
        "CRITICAL SCRIPT REQUIREMENT: answer ONLY in English using Latin "
        "letters. Any Urdu/Arabic-script or Devanagari (Hindi) characters "
        "are invalid and will be rejected. "
    ),
    "ur": (
        "CRITICAL SCRIPT REQUIREMENT: answer ONLY in Urdu script (نستعلیق). "
        "Any Roman Urdu (Latin-letter Urdu) or full English sentence is "
        "invalid and will be rejected. "
    ),
    "rom": (
        "CRITICAL SCRIPT REQUIREMENT: answer ONLY in Roman Urdu — Urdu spelled "
        "with Latin letters. Any Urdu/Arabic-script character is invalid, and "
        "an English-only answer is invalid. "
    ),
}


def _stronger_language_block(language: Optional[str]) -> str:
    key = (language or "en").strip().lower()
    return _STRONGER_LANGUAGE.get(key, "")


def _is_plain_prose(text: str) -> bool:
    """Reject JSON blobs / markdown / over-long output — reused by every advice
    generation step so a bad answer never reaches the farmer as-is."""
    return bool(text) and not text.startswith(("{", "```")) and '"diagnosis"' not in text and len(text) <= 2000


def _extract_json(raw_text: Optional[str]) -> Optional[Dict[str, Any]]:
    """Best-effort JSON extraction from a Gemini text response.

    Mirrors ai_pipeline._extract_json's tolerance for markdown fences / extra
    prose, since LLMs occasionally ignore "JSON only" instructions.
    """
    if not raw_text:
        return None
    text = raw_text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = re.sub(r"^json\s*", "", text, count=1, flags=re.IGNORECASE)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            logger.warning("Could not parse JSON from Gemini output: %s", text[:300])
    return None


def _guess_mime_type(content_type: Optional[str], filename: str) -> str:
    """Pick a safe image mime type for the Gemini API."""
    allowed = {"image/jpeg", "image/png", "image/webp"}
    if content_type in allowed:
        return content_type
    lower_name = (filename or "").lower()
    if lower_name.endswith(".png"):
        return "image/png"
    if lower_name.endswith(".webp"):
        return "image/webp"
    return "image/jpeg"


def _name_tokens(text: str) -> set:
    """Normalized comparison tokens for a disease label: lowercase, no
    punctuation/parentheses, e.g. 'Spider Mites (Two-Spotted Spider Mite)' ->
    {spider, mites, two, spotted, mite}."""
    cleaned = re.sub(r"[^a-z0-9 ]+", " ", (text or "").lower())
    return {t for t in cleaned.split() if t}


class GeminiDiagnosisProvider(DiagnosisProvider):
    """DiagnosisProvider backed by Gemini 2.5 Flash (vision + text)."""

    def __init__(self, client: Optional[Any] = None, model: Optional[str] = None):
        """Create the provider.

        Args:
            client: Optional pre-built ``google.genai.Client``. Tests inject
                a fake client here to avoid any live API calls. When omitted,
                a real client is built from ``GEMINI_API_KEY``.
            model: Optional model name override; defaults to
                ``GEMINI_MODEL`` env var or ``gemini-3.6-flash``.
        """
        self.model = model or os.getenv("GEMINI_MODEL") or DEFAULT_MODEL
        self._client = client if client is not None else self._build_client()
        # Lazy-loaded local KB (RAG-lite grounding), shared with the Qwen
        # pipeline's loader — see _get_knowledge_base().
        self._knowledge_base: Optional[List[Dict[str, Any]]] = None

    @staticmethod
    def _build_client() -> Any:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key or api_key.strip().lower() in {"", "your_key_here"}:
            raise RuntimeError(
                "GEMINI_API_KEY environment variable is not set. Get a key "
                "from Google AI Studio and export it before running the app."
            )
        # Imported lazily so the whole backend doesn't hard-depend on
        # google-genai being installed unless Gemini is actually used.
        from google import genai  # type: ignore

        return genai.Client(api_key=api_key)

    # -- Local knowledge base (RAG-lite grounding) ----------------------

    def _get_knowledge_base(self) -> List[Dict[str, Any]]:
        """Load data/knowledge_base.json once, reusing the Qwen pipeline's
        loader (no second RAG implementation). Degrades to "no grounding"
        if the file or the shared module is unavailable."""
        if self._knowledge_base is None:
            try:
                from backend.services.ai_pipeline import load_knowledge_base

                self._knowledge_base = load_knowledge_base(_KB_PATH)
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "Knowledge base unavailable (%s); advice will not be KB-grounded.", exc
                )
                self._knowledge_base = []
        return self._knowledge_base

    def _retrieve_kb_entries(self, *texts: Optional[str]) -> List[Dict[str, Any]]:
        """Shortlist the most relevant KB entries for the given text, reusing
        ai_pipeline's keyword scorer. Returns [] when nothing actually
        matches — we never ground advice on unrelated entries (the shared
        helper's "first N entries" fallback is deliberately rejected here).
        """
        kb = self._get_knowledge_base()
        if not kb:
            return []
        from backend.services.ai_pipeline import _shortlist_knowledge_base

        search_text = " ".join(t for t in texts if t).lower()
        findings = {"visible_symptoms": [search_text], "crop_type_guess": ""}
        shortlist = _shortlist_knowledge_base(
            findings, kb, max_entries=KB_MAX_ENTRIES
        )
        return [
            entry
            for entry in shortlist
            if any(
                str(kw).lower() in search_text
                for kw in entry.get("symptom_keywords", [])
            )
        ]

    def _call_text(self, prompt: str) -> Optional[str]:
        """Single cheap text-only Gemini call. Returns the raw stripped text, or
        None when the call itself fails (network/auth/etc.)."""
        try:
            from google.genai import types  # type: ignore

            response = self._client.models.generate_content(
                model=self.model,
                contents=[prompt],
                config=types.GenerateContentConfig(temperature=0.2),
            )
        except Exception:  # noqa: BLE001 - callers fall back conservatively
            logger.exception("Gemini text call failed")
            return None
        return (getattr(response, "text", None) or "").strip()

    def _generate_advice(self, prompt: str, language: Optional[str]) -> Optional[str]:
        """Generate localized advice prose, enforcing the requested SCRIPT.

        Accepts a first answer only when it is plain prose AND matches the
        language's script requirement (Urdu script for 'ur', Latin-only for
        'rom'). On a script mismatch it retries exactly once with a stronger
        instruction, then returns None so the caller uses the localized
        fallback. Returns None on any call/prose failure too.
        """
        text = self._call_text(prompt)
        if text is not None and _is_plain_prose(text) and _prose_matches_language(
            text, language
        ):
            return text

        stronger = _stronger_language_block(language)
        if stronger:
            logger.info(
                "Gemini advice did not match the '%s' script; retrying once",
                (language or "en"),
            )
            retry = self._call_text(stronger + "\n" + prompt)
            if retry is not None and _is_plain_prose(retry) and _prose_matches_language(
                retry, language
            ):
                return retry
        return None

    def _restate_in_script(
        self, advice: str, diagnosis: str, question_text: str, language: Optional[str]
    ) -> Optional[str]:
        """Rewrite EXISTING advice into the requested script, preserving its
        full meaning and length (never shorten/remove). Retries once inside
        :meth:`_generate_advice`; returns None if the script still fails."""
        stronger = _stronger_language_block(language)
        if not stronger:  # unknown/missing language -> nothing to enforce.
            return None
        prompt = (
            "You are FasalDoc, an agricultural advisor for farmers in Pakistan.\n"
            + _advice_language_instruction(language)
            + " "
            + stronger
            + " Rewrite the advice below for the SAME diagnosis with the EXACT "
            "same meaning and the SAME number of sentences. Do NOT shorten, "
            "summarize, drop steps, or change the diagnosis. Standard disease "
            "or chemical names may stay in English inside the sentence, but all "
            "surrounding prose MUST use the required script.\n\n"
            f"Diagnosis: {diagnosis}\n"
            f"Farmer's question: {question_text or '(none)'}\n\n"
            f"Advice to rewrite: {advice}\n\n"
            "Return ONLY the rewritten advice text — no JSON, no labels, no "
            "markdown."
        )
        return self._generate_advice(prompt, language)

    def _ensure_script(
        self,
        advice: str,
        diagnosis: str,
        question_text: str,
        language: Optional[str],
        fallback: str,
    ) -> str:
        """Deterministic guarantee that the user-visible advice matches the
        selected LANGUAGE's script. Steps:

          1. accept advice that already validates (clean output passes on
             the first check — no extra calls);
          2. on a mismatch, regenerate ONCE via :meth:`_restate_in_script`
             (which itself retries with a stronger instruction);
          3. validate every candidate — rewrite, KB-derived localized text,
             static fallback — and return the FIRST that passes;
          4. never return the invalid original: for the three enforced
             languages the static fallback is script-valid (guarded by the
             matrix regression test), so the chain always terminates in a
             valid string.
        """
        if _prose_matches_language(advice, language):
            return advice
        logger.info(
            "Gemini advice ignored the '%s' script; enforcing it",
            (language or "en"),
        )
        corrected = self._restate_in_script(advice, diagnosis, question_text, language)
        # Deterministic, Gemini-free fallback chain: diagnosis-specific KB
        # localized content first, then the static localized safety net —
        # each candidate validated before it can be returned.
        for candidate in (corrected, self._kb_localized_advice(diagnosis, language), fallback):
            if candidate and _prose_matches_language(candidate, language):
                return candidate
        # Unreachable for en/ur/rom (static fallback validates); still prefer
        # the known-good static text over any invalid generated string.
        return fallback

    def _match_kb_entry(self, diagnosis: str) -> Optional[Dict[str, Any]]:
        """Variant-tolerant lookup in the local knowledge base: substring
        either way, or one label's tokens fully containing the other's
        (handles word order and crop prefixes: 'Tomato Spider Mites Two-
        spotted Spider Mite' -> 'Spider Mites (Two-Spotted Spider Mite)')."""
        target = (diagnosis or "").strip().lower()
        if not target or target == "unknown":
            return None
        target_tokens = _name_tokens(target)
        for entry in self._get_knowledge_base():
            en_name = str(entry.get("issue_name_english", "")).strip()
            if not en_name:
                continue
            en_lower = en_name.lower()
            en_tokens = _name_tokens(en_name)
            if (
                en_lower == target
                or en_lower in target
                or target in en_lower
                or bool(en_tokens) and bool(target_tokens)
                and (en_tokens <= target_tokens or target_tokens <= en_tokens)
            ):
                return entry
        return None

    def _kb_localized_advice(self, diagnosis: str, language: Optional[str]) -> str:
        """Deterministic, model-free fallback prose built from the local
        knowledge base (Member 1's curated Urdu treatment/prevention steps
        for the SAME diagnosis). Only Urdu mode has localized KB prose;
        en/rom rely on their validated static fallbacks. The built text is
        script-validated here — an invalid candidate is never returned."""
        key = (language or "en").strip().lower()
        if key != "ur":
            return ""
        entry = self._match_kb_entry(diagnosis)
        if not entry:
            return ""
        parts: list = []
        for field in ("low_cost_treatment_urdu", "prevention_tips_urdu"):
            values = entry.get(field) or []
            if isinstance(values, str):
                values = [values]
            parts.extend(str(v).strip() for v in values if str(v).strip())
        if not parts:
            return ""
        text = " ".join(parts[:3])
        return text if _prose_matches_language(text, "ur") else ""

    def _localized_diagnosis_name(
        self, raw_localized: Optional[str], diagnosis: str, language: Optional[str]
    ) -> str:
        """Return a SAFE localized display label for the diagnosis ("" when no
        correct-script label is available — the frontend then falls back to its
        own KB localization). The canonical `diagnosis` itself always stays
        English so knowledge-base enrichment keeps matching. Gemini's label is
        accepted only when its script actually matches the selected language
        (this is what stops 'Minor Leaf Spotting' or a Roman-Urdu label from
        surfacing in Urdu mode); on a miss in Urdu mode we fall back to the
        local KB's `issue_name_urdu` for the same disease.
        """
        name = (raw_localized or "").strip()
        if _localized_name_matches(name, language):
            return name
        key = (language or "en").strip().lower()
        if key == "ur":
            entry = self._match_kb_entry(diagnosis)
            if entry:
                urdu = str(entry.get("issue_name_urdu", "")).strip()
                if _localized_name_matches(urdu, "ur"):
                    return urdu
        return ""

    def _grounded_advice(
        self,
        diagnosis: str,
        visual_advice: str,
        question_text: str,
        language: Optional[str],
    ) -> Optional[str]:
        """Second, cheap text-only Gemini call: rewrite the advice using the
        retrieved local KB entries as grounded context. The vision diagnosis
        is never overridden; on any failure we return None and keep the
        original advice (conservative behavior unchanged).
        """
        entries = self._retrieve_kb_entries(diagnosis, visual_advice, question_text)
        if not entries:
            return None

        kb_payload = json.dumps(
            [
                {
                    k: e.get(k)
                    for k in (
                        "issue_name_english",
                        "crop",
                        "symptom_keywords",
                        "likely_causes_urdu",
                        "low_cost_treatment_urdu",
                        "prevention_tips_urdu",
                        "when_to_seek_expert_urdu",
                    )
                    if e.get(k)
                }
                for e in entries
            ],
            ensure_ascii=False,
        )
        prompt = (
            "You are FasalDoc, an agricultural advisor writing the final advice "
            "for a farmer, grounded in a curated local knowledge base.\n"
            + _advice_language_instruction(language)
            + " Keep disease names medically meaningful (the standard English "
            "disease name may stay inside a local-language sentence). Do NOT "
            "copy Urdu-script text from the knowledge base verbatim — restate "
            "its meaning in the required language.\n\n"
            f"Visual diagnosis (already decided — do NOT change it, swap it, "
            f"or second-guess it): {diagnosis}\n"
            f"What the photo analysis observed: {visual_advice}\n"
            f"Farmer's question: {question_text or '(none)'}\n\n"
            "Curated local knowledge base entries (grounded reference for "
            "causes, treatment, prevention, and when to seek an expert):\n"
            f"{kb_payload}\n\n"
            "Write the final advice, 2-5 sentences, clear and actionable. "
            "Build on the visual diagnosis and incorporate the relevant "
            "treatment/management steps, prevention tips, and when-to-seek-"
            "expert guidance from the knowledge entries above. For any "
            "pesticide/fungicide mention, tell the farmer to confirm the "
            "dose with a local agriculture expert or dealer. "
            "Return ONLY the advice text — no JSON, no labels, no markdown."
        )

        return self._generate_advice(prompt, language)

    # -- DiagnosisProvider interface -----------------------------------

    def diagnose(self, image: ImageInput) -> dict:
        result = self._vision_diagnose(image)
        return self._finalize_result(result, image)

    def _finalize_result(self, result: Dict[str, Any], image: ImageInput) -> Dict[str, Any]:
        """ONE central final validation of the final `advice` and
        `diagnosis_localized`, AFTER every Vision / RAG / grounding / rewrite
        / retry / fallback step on every provider path.

        * `advice` goes through :meth:`_ensure_script` as the very last
          operation: invalid text gets one stronger rewrite and then the
          deterministic KB / static fallback chain — each candidate validated
          — so a Roman-Urdu or English string can never be returned for an
          Urdu request (and symmetrically for rom/en). The invalid original
          is NEVER returned.
        * `diagnosis_localized` is re-validated against the selected script
          (Roman-dominant / English / Devanagari labels collapse to "" so the
          frontend's KB + Unknown chain takes over).
        * A request without a language stays a no-op (legacy contract).
        """
        language = image.language
        if language is None or "advice" not in result:
            return result
        result = dict(result)
        question_text = (image.question or "").strip()
        fallback_advice = _localized(FALLBACK_ADVICE_BY_LANG, language)
        final_advice = result.get("advice") or fallback_advice
        result["advice"] = self._ensure_script(
            final_advice, result.get("diagnosis") or "", question_text,
            language, fallback_advice,
        )
        if result.get("diagnosis") == "Unknown" or not _localized_name_matches(
            result.get("diagnosis_localized") or "", language
        ):
            result["diagnosis_localized"] = ""
        return result

    def _vision_diagnose(self, image: ImageInput) -> dict:
        """Gemini vision diagnosis flow: build the prompt, parse the model
        response, apply the confidence safety net, and ground the advice in
        the local knowledge base."""
        filename = image.filename
        question_text = (image.question or "").strip()
        # Language-aware safety-net texts; threshold logic stays unchanged.
        fallback_advice = _localized(FALLBACK_ADVICE_BY_LANG, image.language)
        not_a_plant_advice = _localized(NOT_A_PLANT_ADVICE_BY_LANG, image.language)

        try:
            from google.genai import types  # type: ignore

            mime_type = _guess_mime_type(image.content_type, filename)
            prompt_text = (
                f"Farmer's question: {question_text}"
                if question_text
                else "The farmer did not provide a written question. "
                "Diagnose the crop issue from the photo alone."
            )

            response = self._client.models.generate_content(
                model=self.model,
                contents=[
                    types.Part.from_bytes(data=image.data, mime_type=mime_type),
                    prompt_text,
                ],
                config=types.GenerateContentConfig(
                    system_instruction=GEMINI_SYSTEM_PROMPT
                    + _language_directive(image.language),
                    temperature=0.2,
                ),
            )
        except Exception as exc:  # noqa: BLE001 - network/SDK/auth errors, etc.
            logger.exception("Gemini diagnose() call failed")
            return {
                "filename": filename,
                "diagnosis": "Unknown",
                "confidence": 0.0,
                "advice": fallback_advice,
                "needs_expert": True,
                "error": f"Gemini request failed: {exc}",
            }

        raw_text = getattr(response, "text", None)
        parsed = _extract_json(raw_text)

        if parsed is None:
            logger.error("Gemini diagnose(): could not parse response: %s", raw_text)
            return {
                "filename": filename,
                "diagnosis": "Unknown",
                "confidence": 0.0,
                "advice": fallback_advice,
                "needs_expert": True,
                "error": "Could not parse Gemini response.",
            }

        # Non-plant photo: short-circuit with the dedicated message, ignoring
        # whatever else the model may have filled in. The model can still return
        # this note in the wrong script, so enforce the language first.
        if parsed.get("is_plant_photo") is False:
            np_advice = parsed.get("advice") or not_a_plant_advice
            np_advice = self._ensure_script(
                np_advice, "Unknown", question_text, image.language, not_a_plant_advice
            )
            return {
                "filename": filename,
                "diagnosis": "Unknown",
                "confidence": 0.0,
                "advice": np_advice,
                "needs_expert": True,
            }

        try:
            confidence = float(parsed.get("confidence", 0) or 0)
        except (TypeError, ValueError):
            confidence = 0.0
        confidence = max(0.0, min(1.0, confidence))

        diagnosis = parsed.get("diagnosis") or "Unknown"
        advice = parsed.get("advice") or ""
        needs_expert = bool(parsed.get("needs_expert", False))
        # Localized DISPLAY label (script-validated, KB-backed). The `diagnosis`
        # itself stays canonical English for KB matching + session context.
        diagnosis_localized = self._localized_diagnosis_name(
            parsed.get("diagnosis_localized"), diagnosis, image.language
        )

        # Python enforces the safety net -- never trust the model to police
        # its own threshold, same principle as ai_pipeline.CONFIDENCE_THRESHOLD.
        if confidence < CONFIDENCE_THRESHOLD:
            needs_expert = True
            advice = fallback_advice

        final_advice = advice or fallback_advice

        # Ground the advice in the local knowledge base (RAG-lite), only for
        # confident, specific diagnoses — the low-confidence safety net above
        # (threshold, needs_expert, fallback text) is untouched.
        if confidence >= CONFIDENCE_THRESHOLD and diagnosis != "Unknown":
            grounded = self._grounded_advice(
                diagnosis, final_advice, question_text, image.language
            )
            if grounded:
                final_advice = grounded

        # ---- CENTRAL FINAL LANGUAGE GATE ---------------------------------
        # Every transformation above (raw Vision JSON -> RAG grounding ->
        # rewrite -> retry -> fallback) funnels through this ONE last-step
        # validation of exactly the values that reach /diagnose:
        #   * the FINAL advice is script-checked AFTER the final rewrite, and
        #     can only leave as correct-script text or the localized fallback;
        #   * the localized display label is re-validated against the selected
        #     script (English/Devanagari never surfaces in Urdu mode, Urdu
        #     never surfaces in Roman mode); Unknown stays a sentinel handled
        #     by the frontend.
        # A wrong-language string can therefore never be returned.
        final_advice = self._ensure_script(
            final_advice, diagnosis, question_text, image.language, fallback_advice
        )
        if diagnosis == "Unknown" or not _localized_name_matches(
            diagnosis_localized, image.language
        ):
            diagnosis_localized = ""

        return {
            "filename": filename,
            "diagnosis": diagnosis,
            "diagnosis_localized": diagnosis_localized,
            "confidence": confidence,
            "advice": final_advice,
            "needs_expert": needs_expert,
        }

    def _followup_generate(self, prompt: str) -> str:
        """One follow-up text call. Re-raises on transport failure so the route
        returns a clean 500 rather than dressing an outage up as an answer."""
        try:
            response = self._client.models.generate_content(
                model=self.model,
                contents=[prompt],
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("Gemini answer_followup() call failed")
            raise RuntimeError(f"Gemini follow-up failed: {exc}") from exc
        return (getattr(response, "text", None) or "").strip()

    def answer_followup(self, question: str, context: Optional[dict] = None) -> str:
        language = (context or {}).get("language")
        context_note = ""
        if context and context.get("diagnosis"):
            context_note = (
                f"Earlier diagnosis for this session: {context.get('diagnosis')} "
                f"(confidence {context.get('confidence')}). "
            )
        base_prompt = (
            "You are FasalDoc, an agricultural advisor answering a farmer's "
            "follow-up question. Reply in plain text (no JSON), 2-4 sentences, "
            "clear and actionable.\n"
            + _advice_language_instruction(language)
            + " Standard disease/chemical names may stay in English inside "
            "local-language sentences.\n\n"
            + f"{context_note}Follow-up question: {question}"
        )

        # Enforce the requested SCRIPT (Urdu vs Roman vs English), retry once
        # with a stronger instruction on a mismatch, then fall back locally.
        text = self._followup_generate(base_prompt)
        if text and _prose_matches_language(text, language):
            return text

        stronger = _stronger_language_block(language)
        if stronger:
            logger.info(
                "Gemini follow-up did not match the '%s' script; retrying once",
                (language or "en"),
            )
            retry = self._followup_generate(stronger + "\n" + base_prompt)
            if retry and _prose_matches_language(retry, language):
                return retry

        # Both attempts ignored the script (or came back empty): NEVER ship the
        # wrong-language text — the localized fallback is always correct-script.
        return _localized(FALLBACK_ADVICE_BY_LANG, language)


def create_provider() -> DiagnosisProvider:
    """Factory function expected by diagnosis_service._build_provider()."""
    return GeminiDiagnosisProvider()
