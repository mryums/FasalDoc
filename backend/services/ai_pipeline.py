"""
ai_pipeline.py
==============
FasalDoc (Crop Doctor) — AI Pipeline Module
Owner: Member 1 (AI / Prompting Lead)

This module wraps all calls to Alibaba Cloud Model Studio (Qwen family)
behind four simple, well-documented Python functions:

    1. analyze_photo(image_bytes)          -> Qwen-VL   (vision)
    2. generate_advice(...)                -> Qwen-Plus (text + confidence logic)
    3. speech_to_text(audio_bytes)         -> Qwen-ASR  (Urdu audio -> Urdu text)
    4. text_to_speech(urdu_text)           -> Qwen-TTS  (Urdu text -> audio)

Design notes (see hackathon blueprint):
- No custom model training. We use Model Studio's hosted Qwen models
  through the OpenAI-compatible endpoint (simplest, most beginner-friendly
  integration path).
- "RAG-lite" grounding: generate_advice() feeds a small, hand-curated
  knowledge_base.json into the prompt instead of doing real vector search.
  That's intentional — it's the simplest approach that still keeps the
  advice grounded in real, curated agronomy info instead of the model
  guessing.
- Confidence transparency is a first-class feature, not an afterthought.
  We NEVER let the model quietly present a guess as a fact. If the
  model's own confidence estimate is below CONFIDENCE_THRESHOLD, we
  override its advice with a friendly "please see a local expert"
  message in Urdu — enforced in Python, not just requested in the prompt.

Environment variables required:
    DASHSCOPE_API_KEY   -> your Alibaba Cloud Model Studio API key

Install dependencies:
    pip install openai
"""

import os
import json
import base64
import logging
from typing import Any, Dict, List, Optional

from openai import OpenAI

# --------------------------------------------------------------------------
# CONFIGURATION
# --------------------------------------------------------------------------

# Model Studio is available in several regions (Singapore, Beijing, US,
# Tokyo, Frankfurt). For a Pakistan-based team, the Singapore ("intl")
# endpoint gives the lowest latency. Change this if your team activated
# Model Studio in a different region — the API key and base_url must
# match the same region.
DASHSCOPE_BASE_URL = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"

# Model choices. Qwen-Plus is the recommended default for live demos:
# fast, cheap enough to rehearse many times, and good Urdu output.
# Swap to "qwen-vl-max" / "qwen-max" only if you specifically need the
# extra reasoning power and can tolerate more latency/cost.
VISION_MODEL = "qwen-vl-plus"      # image understanding (Qwen-VL)
TEXT_MODEL = "qwen-plus"           # advice generation + confidence scoring
ASR_MODEL = "qwen3-asr-flash"      # speech-to-text (Urdu)
TTS_MODEL = "qwen3-tts-flash"      # text-to-speech (Urdu)
TTS_VOICE = "Cherry"               # pick any voice supported by your TTS model

# Below this confidence (%), we never show a specific diagnosis — we
# recommend a human expert instead. This is a hackathon "wow" feature
# (Step 17/18 of the blueprint) and a genuine safety practice.
CONFIDENCE_THRESHOLD = 60

# NOTE: exact model IDs occasionally change as Alibaba Cloud ships new
# Qwen versions. If a call fails with a "model not found" style error,
# check the current model list in your Model Studio console and update
# the constants above — the rest of this file does not need to change.

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fasaldoc.ai_pipeline")


def _get_client() -> OpenAI:
    """
    Build an OpenAI-compatible client pointed at Model Studio.

    Always load the key from the environment — never hardcode it.
    Raises a clear error early if the key is missing, instead of failing
    deep inside a network call.
    """
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise RuntimeError(
            "DASHSCOPE_API_KEY environment variable is not set. "
            "Get a key from the Alibaba Cloud Model Studio console and "
            "export it before running the app."
        )
    return OpenAI(api_key=api_key, base_url=DASHSCOPE_BASE_URL)


def _extract_json(raw_text: str) -> Optional[Dict[str, Any]]:
    """
    Best-effort helper to pull a JSON object out of a model response.

    Even when we ask the model to "reply with ONLY JSON", it sometimes
    wraps the JSON in ```json fences or adds a sentence before/after.
    This helper tries a direct parse first, then falls back to slicing
    out the {...} substring.
    """
    if not raw_text:
        return None
    raw_text = raw_text.strip()
    # Strip common markdown code fences.
    if raw_text.startswith("```"):
        raw_text = raw_text.strip("`")
        raw_text = raw_text.replace("json\n", "", 1).replace("json", "", 1)
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        pass
    start = raw_text.find("{")
    end = raw_text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(raw_text[start:end + 1])
        except json.JSONDecodeError:
            logger.warning("Could not parse JSON from model output: %s", raw_text[:300])
    return None


# --------------------------------------------------------------------------
# 1. VISION — analyze_photo()
# --------------------------------------------------------------------------

VISION_SYSTEM_PROMPT = """You are an agricultural vision assistant helping diagnose \
crop health from a farmer-submitted photo. You are NOT a certain diagnosis tool — \
you only describe what is visually observable.

Look carefully at the image and respond with ONLY a JSON object (no extra text, \
no markdown fences) with this exact structure:

{
  "is_plant_photo": true or false,
  "crop_type_guess": "best guess of the plant/crop, or 'unknown'",
  "affected_part": "e.g. leaves, stem, fruit, roots, whole plant",
  "visible_symptoms": ["short phrase", "short phrase", ...],
  "severity_estimate": "mild" | "moderate" | "severe" | "unclear",
  "visual_notes": "one short sentence with anything else useful for a diagnosis"
}

Rules:
- If the photo does NOT show a plant/crop at all (e.g. a person, an animal, a \
random object), set "is_plant_photo" to false and leave the other fields as \
best-effort empty/"unknown" values. Do NOT invent crop symptoms for a non-plant photo.
- List only symptoms you can actually see (spots, discoloration, wilting, holes, \
curling, pest insects, mold, etc.). Do not guess a disease name here — that \
happens in a later step.
"""


def analyze_photo(image_bytes: bytes, image_format: str = "jpeg") -> Dict[str, Any]:
    """
    Send a crop photo to Qwen-VL and get back structured visual findings.

    Args:
        image_bytes: Raw bytes of the uploaded photo (e.g. from FastAPI's
                      `UploadFile.read()`).
        image_format: "jpeg", "png", etc. — used to build the data URL.

    Returns:
        A dict shaped like:
        {
            "is_plant_photo": bool,
            "crop_type_guess": str,
            "affected_part": str,
            "visible_symptoms": [str, ...],
            "severity_estimate": str,
            "visual_notes": str,
            "error": str  # only present if something went wrong
        }
    """
    fallback_result = {
        "is_plant_photo": False,
        "crop_type_guess": "unknown",
        "affected_part": "unknown",
        "visible_symptoms": [],
        "severity_estimate": "unclear",
        "visual_notes": "",
    }

    try:
        client = _get_client()
        b64_image = base64.b64encode(image_bytes).decode("utf-8")
        data_url = f"data:image/{image_format};base64,{b64_image}"

        response = client.chat.completions.create(
            model=VISION_MODEL,
            messages=[
                {"role": "system", "content": VISION_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": data_url}},
                        {
                            "type": "text",
                            "text": "Analyze this crop photo and return the JSON described.",
                        },
                    ],
                },
            ],
            temperature=0.2,  # low temperature: we want consistent, factual descriptions
        )

        raw_text = response.choices[0].message.content
        parsed = _extract_json(raw_text)

        if parsed is None:
            logger.error("analyze_photo: failed to parse model output: %s", raw_text)
            fallback_result["error"] = "Could not parse vision model response."
            return fallback_result

        # Merge with fallback defaults so missing keys never crash the caller.
        fallback_result.update(parsed)
        return fallback_result

    except Exception as exc:  # noqa: BLE001 — we want to catch and report any SDK/network error
        logger.exception("analyze_photo failed")
        fallback_result["error"] = f"Vision analysis failed: {exc}"
        return fallback_result


# --------------------------------------------------------------------------
# 2. ADVICE + CONFIDENCE — generate_advice()
# --------------------------------------------------------------------------

ADVICE_SYSTEM_PROMPT = """You are "FasalDoc", a friendly agricultural advisor for \
small and mid-scale crop farmers in Pakistan (Punjab and Sindh). Farmers will \
describe their problem in Urdu and you have visual symptom findings from a photo. \
You must ground your answer in the provided reference knowledge base — do not \
invent treatments that aren't grounded in it or in well-established agronomy.

Respond with ONLY a JSON object (no extra text, no markdown fences) in this \
exact structure:

{
  "diagnosis_english": "short diagnosis label in English",
  "diagnosis_urdu": "short diagnosis label in Urdu",
  "confidence_score": 0-100 integer,
  "matched_knowledge_base_id": "id of the closest matching knowledge base entry, or null",
  "advice_urdu": "clear, farmer-friendly advisory text in Urdu, 3-5 sentences",
  "treatment_steps_urdu": ["step 1 in Urdu", "step 2 in Urdu", ...],
  "low_cost_tips_urdu": ["cheap/local remedy in Urdu", ...]
}

How to set confidence_score:
- High (70-100): visual symptoms and farmer's description clearly match ONE \
knowledge base entry, with no major contradictions.
- Medium (40-69): symptoms partially match, photo is unclear/incomplete, or \
multiple issues look equally likely.
- Low (0-39): photo doesn't look like a plant, symptoms don't match anything in \
the knowledge base, or the description is too vague to say anything useful.

Be honest and conservative — it is much better to admit uncertainty than to \
confidently give wrong advice to a farmer who may act on it immediately.
"""

FALLBACK_ADVICE_URDU = (
    "معاف کیجیے، تصویر اور آپ کی بتائی گئی علامات سے ہم پورے یقین کے ساتھ "
    "بیماری کی تشخیص نہیں کر سکے۔ غلط اندازے سے نقصان ہو سکتا ہے، اس لیے براہِ "
    "کرم اپنے قریبی زرعی ماہر (Agriculture Extension Officer) یا مستند کسان "
    "مرکز سے رجوع کریں تاکہ فصل کا صحیح معائنہ ہو سکے۔"
)

NOT_A_PLANT_ADVICE_URDU = (
    "معاف کیجیے، اپلوڈ کی گئی تصویر میں کوئی فصل یا پودا واضح طور پر نظر نہیں "
    "آ رہا۔ براہِ کرم متاثرہ پتے یا پودے کی صاف تصویر دوبارہ بھیجیں تاکہ ہم "
    "بہتر رہنمائی دے سکیں۔"
)


def _shortlist_knowledge_base(
    visual_findings: Dict[str, Any],
    knowledge_base_data: List[Dict[str, Any]],
    max_entries: int = 6,
) -> List[Dict[str, Any]]:
    """
    "RAG-lite" step: instead of a real vector database, do a cheap keyword
    overlap score between the visible symptoms and each knowledge base
    entry's symptom_keywords, and keep only the most relevant handful.

    This keeps the prompt short (cheaper, faster, less distracting for the
    model) while still grounding the answer in curated data. If nothing
    matches well, we just fall back to sending the whole (small) knowledge
    base, since it's only ~20-30 entries.
    """
    symptoms_text = " ".join(visual_findings.get("visible_symptoms", [])).lower()
    crop_guess = str(visual_findings.get("crop_type_guess", "")).lower()

    scored = []
    for entry in knowledge_base_data:
        keywords = [k.lower() for k in entry.get("symptom_keywords", [])]
        score = sum(1 for k in keywords if k in symptoms_text)
        if crop_guess and crop_guess in str(entry.get("crop", "")).lower():
            score += 1
        scored.append((score, entry))

    scored.sort(key=lambda pair: pair[0], reverse=True)
    top = [entry for score, entry in scored if score > 0][:max_entries]

    return top if top else knowledge_base_data[:max_entries]


def generate_advice(
    visual_findings: Dict[str, Any],
    user_urdu_query: str,
    knowledge_base_data: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Turn vision findings + the farmer's spoken (transcribed) Urdu question
    into a confidence-scored Urdu advisory, grounded in a local knowledge
    base file.

    Args:
        visual_findings: The dict returned by analyze_photo().
        user_urdu_query: Urdu text (already transcribed via speech_to_text,
                          or typed directly).
        knowledge_base_data: The loaded contents of knowledge_base.json
                              (a list of dicts — see sample file).

    Returns:
        {
            "diagnosis_english": str,
            "diagnosis_urdu": str,
            "confidence_score": int,
            "matched_knowledge_base_id": str | None,
            "advice_urdu": str,
            "treatment_steps_urdu": [str, ...],
            "low_cost_tips_urdu": [str, ...],
            "is_fallback": bool,   # True if we recommend a human expert instead
            "error": str           # only present if something went wrong
        }
    """
    # Guard clause: if the photo clearly wasn't a plant, don't even call the
    # LLM for a "diagnosis" — go straight to the honest fallback message.
    if visual_findings.get("is_plant_photo") is False:
        return {
            "diagnosis_english": None,
            "diagnosis_urdu": None,
            "confidence_score": 0,
            "matched_knowledge_base_id": None,
            "advice_urdu": NOT_A_PLANT_ADVICE_URDU,
            "treatment_steps_urdu": [],
            "low_cost_tips_urdu": [],
            "is_fallback": True,
        }

    try:
        client = _get_client()

        relevant_kb = _shortlist_knowledge_base(visual_findings, knowledge_base_data)

        user_content = {
            "visual_findings": visual_findings,
            "farmer_question_urdu": user_urdu_query or "(no spoken question provided)",
            "reference_knowledge_base": relevant_kb,
        }

        response = client.chat.completions.create(
            model=TEXT_MODEL,
            messages=[
                {"role": "system", "content": ADVICE_SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(user_content, ensure_ascii=False)},
            ],
            temperature=0.3,
        )

        raw_text = response.choices[0].message.content
        parsed = _extract_json(raw_text)

        if parsed is None:
            logger.error("generate_advice: failed to parse model output: %s", raw_text)
            return {
                "diagnosis_english": None,
                "diagnosis_urdu": None,
                "confidence_score": 0,
                "matched_knowledge_base_id": None,
                "advice_urdu": FALLBACK_ADVICE_URDU,
                "treatment_steps_urdu": [],
                "low_cost_tips_urdu": [],
                "is_fallback": True,
                "error": "Could not parse advisory model response.",
            }

        confidence = int(parsed.get("confidence_score", 0) or 0)
        confidence = max(0, min(100, confidence))  # clamp to a sane 0-100 range
        parsed["confidence_score"] = confidence

        # This is the core "safety net": we NEVER trust the model to police
        # its own threshold. Python enforces it, every time.
        if confidence < CONFIDENCE_THRESHOLD:
            parsed["advice_urdu"] = FALLBACK_ADVICE_URDU
            parsed["treatment_steps_urdu"] = []
            parsed["low_cost_tips_urdu"] = []
            parsed["is_fallback"] = True
        else:
            parsed["is_fallback"] = False

        # Make sure every expected key exists even if the model omitted one.
        parsed.setdefault("diagnosis_english", None)
        parsed.setdefault("diagnosis_urdu", None)
        parsed.setdefault("matched_knowledge_base_id", None)
        parsed.setdefault("treatment_steps_urdu", [])
        parsed.setdefault("low_cost_tips_urdu", [])

        return parsed

    except Exception as exc:  # noqa: BLE001
        logger.exception("generate_advice failed")
        return {
            "diagnosis_english": None,
            "diagnosis_urdu": None,
            "confidence_score": 0,
            "matched_knowledge_base_id": None,
            "advice_urdu": FALLBACK_ADVICE_URDU,
            "treatment_steps_urdu": [],
            "low_cost_tips_urdu": [],
            "is_fallback": True,
            "error": f"Advice generation failed: {exc}",
        }


# --------------------------------------------------------------------------
# 3. SPEECH-TO-TEXT — speech_to_text()
# --------------------------------------------------------------------------

def speech_to_text(audio_bytes: bytes, audio_format: str = "wav") -> Dict[str, Any]:
    """
    Transcribe a farmer's spoken Urdu voice note into Urdu text using
    Qwen-ASR (called through the OpenAI-compatible endpoint).

    Args:
        audio_bytes: Raw audio bytes (e.g. from an uploaded .wav/.mp3 file).
        audio_format: "wav", "mp3", "m4a", etc.

    Returns:
        {
            "transcript_urdu": str,
            "error": str  # only present if something went wrong
        }
    """
    try:
        client = _get_client()
        b64_audio = base64.b64encode(audio_bytes).decode("utf-8")

        response = client.chat.completions.create(
            model=ASR_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_audio",
                            "input_audio": {"data": b64_audio, "format": audio_format},
                        },
                        {
                            "type": "text",
                            "text": (
                                "Transcribe this audio exactly as spoken, in Urdu script. "
                                "Reply with ONLY the transcription text, nothing else."
                            ),
                        },
                    ],
                }
            ],
        )

        transcript = (response.choices[0].message.content or "").strip()
        return {"transcript_urdu": transcript}

    except Exception as exc:  # noqa: BLE001
        logger.exception("speech_to_text failed")
        return {"transcript_urdu": "", "error": f"Speech-to-text failed: {exc}"}


# --------------------------------------------------------------------------
# 4. TEXT-TO-SPEECH — text_to_speech()
# --------------------------------------------------------------------------

def text_to_speech(urdu_text: str) -> Dict[str, Any]:
    """
    Convert generated Urdu advisory text into a spoken audio response
    using Qwen-TTS (called through the OpenAI-compatible endpoint).

    Args:
        urdu_text: The Urdu text to speak aloud (e.g. advice_urdu from
                    generate_advice()).

    Returns:
        {
            "audio_bytes": bytes | None,   # raw audio, ready to save/stream
            "audio_format": "wav",
            "error": str  # only present if something went wrong
        }
    """
    if not urdu_text:
        return {"audio_bytes": None, "audio_format": "wav", "error": "No text provided."}

    try:
        client = _get_client()

        response = client.chat.completions.create(
            model=TTS_MODEL,
            messages=[{"role": "user", "content": urdu_text}],
            modalities=["text", "audio"],
            audio={"voice": TTS_VOICE, "format": "wav"},
        )

        message = response.choices[0].message
        audio_block = getattr(message, "audio", None)

        if not audio_block or not getattr(audio_block, "data", None):
            return {
                "audio_bytes": None,
                "audio_format": "wav",
                "error": "TTS model did not return audio data.",
            }

        audio_bytes = base64.b64decode(audio_block.data)
        return {"audio_bytes": audio_bytes, "audio_format": "wav"}

    except Exception as exc:  # noqa: BLE001
        logger.exception("text_to_speech failed")
        return {"audio_bytes": None, "audio_format": "wav", "error": f"Text-to-speech failed: {exc}"}


# --------------------------------------------------------------------------
# HELPER — loading the local knowledge base
# --------------------------------------------------------------------------

def load_knowledge_base(path: str = "data/knowledge_base.json") -> List[Dict[str, Any]]:
    """
    Load the curated crop-issue knowledge base from disk.

    Kept as a tiny separate function so Member 2 (backend) can call it once
    at server startup and pass the result into generate_advice() on every
    request, instead of re-reading the file each time.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to load knowledge base from %s", path)
        raise RuntimeError(f"Could not load knowledge base at '{path}': {exc}") from exc


# --------------------------------------------------------------------------
# QUICK MANUAL TEST (run this file directly to sanity-check your API key)
# --------------------------------------------------------------------------

if __name__ == "__main__":
    # This block is only for local debugging — it is NOT called by FastAPI.
    # Example: python ai_pipeline.py path/to/test_photo.jpg
    import sys

    if len(sys.argv) < 2:
        print("Usage: python ai_pipeline.py <path_to_test_photo.jpg>")
        sys.exit(0)

    with open(sys.argv[1], "rb") as f:
        photo_bytes = f.read()

    print("Analyzing photo...")
    findings = analyze_photo(photo_bytes)
    print(json.dumps(findings, ensure_ascii=False, indent=2))

    kb = load_knowledge_base(os.path.join(os.path.dirname(__file__), "knowledge_base.json"))

    print("\nGenerating advice...")
    advice = generate_advice(findings, "میرے پودے کے پتے پیلے ہو رہے ہیں", kb)
    print(json.dumps(advice, ensure_ascii=False, indent=2))
