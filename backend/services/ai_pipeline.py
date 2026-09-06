import base64
import json
import logging
from pathlib import Path
from typing import Any

from openai import OpenAI

from backend.services.ai_config import PROJECT_ROOT, get_settings
from backend.services.ai_errors import (
    AIConfigurationError,
    AIInvalidModelOutputError,
    AIServiceError,
    AIUpstreamError,
    translate_provider_error,
)


logger = logging.getLogger("fasaldoc.ai")
DEFAULT_KNOWLEDGE_BASE_PATH = PROJECT_ROOT / "data" / "knowledge_base.json"

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


def _get_client() -> OpenAI:
    settings = get_settings()
    if not settings.api_key:
        raise AIConfigurationError()
    return OpenAI(
        api_key=settings.api_key,
        base_url=settings.base_url,
        timeout=settings.timeout_seconds,
        max_retries=settings.max_retries,
    )


def _run_provider_call(operation: str, callback):
    try:
        return callback()
    except AIServiceError:
        raise
    except Exception as error:
        logger.error(
            "Qwen %s failed: type=%s status=%s",
            operation,
            type(error).__name__,
            getattr(error, "status_code", "unknown"),
        )
        raise translate_provider_error(error) from error


def _extract_json(raw_text: str) -> dict[str, Any] | None:
    if not isinstance(raw_text, str) or not raw_text.strip():
        return None

    candidate = raw_text.strip()
    if candidate.startswith("```"):
        candidate = candidate.split("\n", 1)[1] if "\n" in candidate else ""
        if candidate.endswith("```"):
            candidate = candidate[:-3]
        candidate = candidate.strip()

    for value in (candidate, candidate[candidate.find("{") : candidate.rfind("}") + 1]):
        if not value:
            continue
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed
    return None


def _response_content(response: Any) -> str:
    try:
        content = response.choices[0].message.content
    except (AttributeError, IndexError, TypeError) as error:
        raise AIInvalidModelOutputError() from error
    if not isinstance(content, str):
        raise AIInvalidModelOutputError()
    return content


def _vision_defaults() -> dict[str, Any]:
    return {
        "is_plant_photo": False,
        "crop_type_guess": "unknown",
        "affected_part": "unknown",
        "visible_symptoms": [],
        "severity_estimate": "unclear",
        "visual_notes": "",
    }


def analyze_photo(image_bytes: bytes, image_format: str = "jpeg") -> dict[str, Any]:
    if not image_bytes:
        raise AIInvalidModelOutputError()

    client = _get_client()
    encoded_image = base64.b64encode(image_bytes).decode("ascii")
    response = _run_provider_call(
        "vision",
        lambda: client.chat.completions.create(
            model=get_settings().vision_model,
            messages=[
                {"role": "system", "content": VISION_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": f"data:image/{image_format};base64,{encoded_image}"}},
                        {"type": "text", "text": "Analyze this crop photo and return the JSON described."},
                    ],
                },
            ],
            temperature=0.2,
        ),
    )
    parsed = _extract_json(_response_content(response))
    if parsed is None or not isinstance(parsed.get("is_plant_photo"), bool):
        raise AIInvalidModelOutputError()

    findings = _vision_defaults()
    findings.update(parsed)
    if not isinstance(findings.get("visible_symptoms"), list):
        findings["visible_symptoms"] = []
    return findings


def _shortlist_knowledge_base(
    visual_findings: dict[str, Any], knowledge_base_data: list[dict[str, Any]], max_entries: int = 6
) -> list[dict[str, Any]]:
    symptoms_text = " ".join(str(item) for item in visual_findings.get("visible_symptoms", [])).lower()
    crop_guess = str(visual_findings.get("crop_type_guess", "")).lower()
    scored: list[tuple[int, dict[str, Any]]] = []

    for entry in knowledge_base_data:
        keywords = [str(keyword).lower() for keyword in entry.get("symptom_keywords", [])]
        score = sum(1 for keyword in keywords if keyword and keyword in symptoms_text)
        if crop_guess and crop_guess in str(entry.get("crop", "")).lower():
            score += 1
        scored.append((score, entry))

    scored.sort(key=lambda pair: pair[0], reverse=True)
    shortlisted = [entry for score, entry in scored if score > 0][:max_entries]
    return shortlisted or knowledge_base_data[:max_entries]


def _non_plant_advice() -> dict[str, Any]:
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


def generate_advice(
    visual_findings: dict[str, Any], user_urdu_query: str, knowledge_base_data: list[dict[str, Any]]
) -> dict[str, Any]:
    if visual_findings.get("is_plant_photo") is False:
        return _non_plant_advice()

    client = _get_client()
    relevant_knowledge_base = _shortlist_knowledge_base(visual_findings, knowledge_base_data)
    user_content = {
        "visual_findings": visual_findings,
        "farmer_question_urdu": user_urdu_query or "(no spoken question provided)",
        "reference_knowledge_base": relevant_knowledge_base,
    }
    response = _run_provider_call(
        "advice",
        lambda: client.chat.completions.create(
            model=get_settings().text_model,
            messages=[
                {"role": "system", "content": ADVICE_SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(user_content, ensure_ascii=False)},
            ],
            temperature=0.3,
        ),
    )
    parsed = _extract_json(_response_content(response))
    if parsed is None:
        raise AIInvalidModelOutputError()

    try:
        confidence = int(parsed.get("confidence_score", 0))
    except (TypeError, ValueError) as error:
        raise AIInvalidModelOutputError() from error
    confidence = max(0, min(100, confidence))
    parsed["confidence_score"] = confidence
    parsed.setdefault("diagnosis_english", None)
    parsed.setdefault("diagnosis_urdu", None)
    parsed.setdefault("matched_knowledge_base_id", None)
    parsed.setdefault("treatment_steps_urdu", [])
    parsed.setdefault("low_cost_tips_urdu", [])

    if confidence < get_settings().confidence_threshold:
        parsed["advice_urdu"] = FALLBACK_ADVICE_URDU
        parsed["treatment_steps_urdu"] = []
        parsed["low_cost_tips_urdu"] = []
        parsed["is_fallback"] = True
        return parsed

    if not isinstance(parsed.get("advice_urdu"), str) or not parsed["advice_urdu"].strip():
        raise AIInvalidModelOutputError()
    parsed["is_fallback"] = False
    return parsed


def speech_to_text(audio_bytes: bytes, audio_format: str = "wav") -> dict[str, str]:
    if not audio_bytes:
        raise AIInvalidModelOutputError()

    client = _get_client()
    encoded_audio = base64.b64encode(audio_bytes).decode("ascii")
    response = _run_provider_call(
        "speech-to-text",
        lambda: client.chat.completions.create(
            model=get_settings().asr_model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "input_audio", "input_audio": {"data": encoded_audio, "format": audio_format}},
                        {
                            "type": "text",
                            "text": "Transcribe this audio exactly as spoken, in Urdu script. Reply with ONLY the transcription text, nothing else.",
                        },
                    ],
                }
            ],
        ),
    )
    transcript = " ".join(_response_content(response).split())
    if not transcript:
        raise AIInvalidModelOutputError()
    return {"transcript_urdu": transcript}


def text_to_speech(urdu_text: str) -> dict[str, Any]:
    if not urdu_text.strip():
        raise AIInvalidModelOutputError()

    client = _get_client()
    response = _run_provider_call(
        "text-to-speech",
        lambda: client.chat.completions.create(
            model=get_settings().tts_model,
            messages=[{"role": "user", "content": urdu_text}],
            modalities=["text", "audio"],
            audio={"voice": get_settings().tts_voice, "format": "wav"},
        ),
    )
    try:
        audio_data = response.choices[0].message.audio.data
        audio_bytes = base64.b64decode(audio_data, validate=True)
    except (AttributeError, IndexError, TypeError, ValueError) as error:
        raise AIInvalidModelOutputError() from error
    if not audio_bytes:
        raise AIInvalidModelOutputError()
    return {"audio_bytes": audio_bytes, "audio_format": "wav"}


def load_knowledge_base(path: str | Path | None = None) -> list[dict[str, Any]]:
    knowledge_base_path = Path(path) if path is not None else DEFAULT_KNOWLEDGE_BASE_PATH
    try:
        payload = json.loads(knowledge_base_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        logger.error("Knowledge base load failed: type=%s", type(error).__name__)
        raise AIUpstreamError() from error

    if not isinstance(payload, list) or not payload:
        raise AIInvalidModelOutputError()
    for entry in payload:
        if not isinstance(entry, dict) or not {"id", "crop", "symptom_keywords"}.issubset(entry):
            raise AIInvalidModelOutputError()
        if not isinstance(entry["symptom_keywords"], list):
            raise AIInvalidModelOutputError()
    return payload
