import type { DiagnosisResponse, FollowupResponse } from '../types/api'

/**
 * Centralized API service for the FasalDoc FastAPI backend (Member 2).
 * Components never call fetch directly — everything goes through here.
 *
 * Architecture: Frontend -> FastAPI -> AI service.
 * No AI/cloud credentials ever reach the browser.
 */

const API_BASE = (
  import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'
).replace(/\/+$/, '')

export type ApiErrorKind = 'validation' | 'network' | 'server'

export class ApiError extends Error {
  constructor(
    message: string,
    public kind: ApiErrorKind,
    public status?: number,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

/** Mirrors backend/utils/validators.py — same limits, checked early for UX. */
export const ALLOWED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/webp']
export const MAX_IMAGE_SIZE = 10 * 1024 * 1024 // 10 MB

export type ImageValidationError = 'no-image' | 'invalid-type' | 'too-large'

export function validateImageFile(file: File | null): ImageValidationError | null {
  if (!file) return 'no-image'
  if (!ALLOWED_IMAGE_TYPES.includes(file.type)) return 'invalid-type'
  if (file.size > MAX_IMAGE_SIZE) return 'too-large'
  return null
}

/** Mirrors backend validate_question: non-empty after trimming. */
export function validateQuestion(question: string): boolean {
  return Boolean(question && question.trim())
}

async function parseBackendError(res: Response): Promise<ApiError> {
  let detail = ''
  try {
    const body = (await res.json()) as { detail?: unknown }
    if (typeof body.detail === 'string') detail = body.detail
  } catch {
    // non-JSON error body — keep generic message, never expose internals
  }
  if (res.status === 400 || res.status === 422) {
    return new ApiError(detail || 'The request was rejected.', 'validation', res.status)
  }
  return new ApiError(detail, 'server', res.status)
}

/**
 * POST /diagnose — multipart upload, field name must be "image"
 * (backend/routes/diagnose.py :: image: UploadFile = File(...)).
 */
export async function diagnoseImage(file: File): Promise<DiagnosisResponse> {
  const form = new FormData()
  form.append('image', file)

  let res: Response
  try {
    res = await fetch(`${API_BASE}/diagnose`, { method: 'POST', body: form })
  } catch {
    throw new ApiError('', 'network')
  }

  if (!res.ok) throw await parseBackendError(res)
  return (await res.json()) as DiagnosisResponse
}

/**
 * POST /ask-followup — JSON body { question } per FollowupRequest.
 * The current backend schema only carries the question; the diagnosis
 * context is kept in frontend state and shown in the chat header.
 */
export async function askFollowup(question: string): Promise<FollowupResponse> {
  let res: Response
  try {
    res = await fetch(`${API_BASE}/ask-followup`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question }),
    })
  } catch {
    throw new ApiError('', 'network')
  }

  if (!res.ok) throw await parseBackendError(res)
  return (await res.json()) as FollowupResponse
}
