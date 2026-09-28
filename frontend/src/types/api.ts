/**
 * Frontend mirrors of Member 2's backend Pydantic models (backend/models.py).
 * Keep these in sync with the FastAPI contract — do not invent extra fields.
 */

/** Response of POST /diagnose (backend/models.py :: DiagnosisResponse) */
export interface DiagnosisResponse {
  filename: string
  diagnosis: string
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
