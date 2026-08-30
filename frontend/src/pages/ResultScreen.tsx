import { useLanguage } from '../i18n/LanguageContext'
import type { DiagnosisResponse } from '../types/api'
import { ConfidenceIndicator, confidenceBand } from '../components/ConfidenceIndicator'
import { Button } from '../components/Button'
import { ErrorMessage } from '../components/ErrorMessage'
import { AlertIcon, RefreshIcon } from '../components/icons'

interface ResultScreenProps {
  diagnosis: DiagnosisResponse | null
  error: string | null
  previewUrl: string | null
  onAskFollowup: () => void
  onNewDiagnosis: () => void
  onRetry: () => void
}

export function ResultScreen({
  diagnosis,
  error,
  previewUrl,
  onAskFollowup,
  onNewDiagnosis,
  onRetry,
}: ResultScreenProps) {
  const { t } = useLanguage()

  if (error || !diagnosis) {
    return (
      <div className="screen result">
        <h1 className="screen__title">{t.result.title}</h1>
        <ErrorMessage message={error ?? t.errors.server} onRetry={onRetry} />
        <Button variant="secondary" onClick={onNewDiagnosis}>
          <RefreshIcon size={18} />
          {t.result.newDiagnosis}
        </Button>
      </div>
    )
  }

  const band = confidenceBand(diagnosis.confidence)

  return (
    <div className="screen result">
      <h1 className="screen__title">{t.result.title}</h1>

      {previewUrl && (
        <div className="result__image-card">
          <img src={previewUrl} alt={t.result.imageLabel} className="result__image" />
          <span className="result__filename">{diagnosis.filename}</span>
        </div>
      )}

      <section className="card diagnosis-card" aria-labelledby="diagnosis-heading">
        <p className="card__eyebrow">{t.result.possibleProblem}</p>
        <h2 id="diagnosis-heading" className="diagnosis-card__name">
          {diagnosis.diagnosis}
        </h2>
        {band !== 'high' && (
          <p className="diagnosis-card__caution">
            <AlertIcon size={16} />
            {t.result.confidenceLow}
          </p>
        )}
      </section>

      <section className="card" aria-label={t.result.confidenceLabel}>
        <ConfidenceIndicator confidence={diagnosis.confidence} />
      </section>

      <section className="card advice-card" aria-labelledby="advice-heading">
        <h2 id="advice-heading" className="advice-card__title">
          {t.result.adviceTitle}
        </h2>
        <p className="advice-card__text">{diagnosis.advice}</p>
        {diagnosis.needs_expert && (
          <p className="advice-card__expert">
            <AlertIcon size={18} />
            {t.result.needsExpert}
          </p>
        )}
      </section>

      <div className="result__actions">
        <Button onClick={onAskFollowup}>{t.result.followupCta}</Button>
        <Button variant="secondary" onClick={onNewDiagnosis}>
          <RefreshIcon size={18} />
          {t.result.newDiagnosis}
        </Button>
      </div>
    </div>
  )
}
