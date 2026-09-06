export interface DiagnosisResponse {
  filename: string
  diagnosis: string
  /** 0..1 confidence score from the backend */
  confidence: number
  advice: string
  needs_expert: boolean
}

export interface FollowupResponse {
  question: string
  answer: string
}
