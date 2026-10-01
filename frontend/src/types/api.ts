/**
 * Frontend mirrors of Member 2's backend Pydantic models (backend/models.py).
 * Keep these in sync with the FastAPI contract — do not invent extra fields.
 */

/** Response of POST /diagnose (backend/models.py :: DiagnosisResponse) */
export interface DiagnosisResponse {
  filename: string
  /** Canonical English label — the KB-matching key (never shown raw in ur/rom). */
  diagnosis: string
  /**
   * Diagnosis label already localized to the selected UI language (Urdu script
   * for 'ur', Latin-only Roman Urdu for 'rom'). Null/empty when the provider
   * produced none — screens then fall back to KB localization or the English
   * label (mirrors backend/models.py :: diagnosis_localized).
   */
  diagnosis_localized?: string | null
  /** 0..1 — backend guarantees Field(ge=0, le=1) */
  confidence: number
  advice: string
  needs_expert: boolean
  /** Non-null only when the AI provider failed (fallback response in use) */
  error?: string | null
}

/** Request body of POST /ask-followup (backend/models.py :: FollowupRequest) */
export interface FollowupRequest {
  question: string
}

/** Response of POST /ask-followup (backend/models.py :: FollowupResponse) */
export interface FollowupResponse {
  question: string
  answer: string
}
