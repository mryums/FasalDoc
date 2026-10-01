import { useLanguage } from '../i18n/LanguageContext'
import type { DiagnosisResponse } from '../types/api'
import { ConfidenceIndicator, confidenceBand } from '../components/ConfidenceIndicator'
import { Button } from '../components/Button'
import { ErrorMessage } from '../components/ErrorMessage'
import { AlertIcon, RefreshIcon } from '../components/icons'
import { localizedDiseaseForDiagnosis } from '../data/agriculture'

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
  const { t, lang } = useLanguage()

  // A provider-level error (e.g. Gemini quota outage) must NOT render as a
  // normal "Unknown" diagnosis — show the clean retry/error screen instead.
  // The raw backend error string is intentionally never displayed.
  if (error || !diagnosis || diagnosis.error) {
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

  // Localize the diagnosis heading + Symptoms/Treatment/Prevention content to
  // the ACTIVE language (Member 4 data). null when no KB entry matches.
  const enrichedInfo = localizedDiseaseForDiagnosis(diagnosis.diagnosis, lang)

  // "Unknown" is a backend sentinel, not translatable content — render it with
  // the localized label so Urdu / Roman Urdu mode never shows the English word.
  // Non-English diagnoses with no KB entry fall back to the AI-provided
  // localized label, so ur/rom modes never surface a raw English name.
  const displayDiagnosis =
    enrichedInfo?.displayName ??
    (diagnosis.diagnosis === 'Unknown'
      ? t.result.unknown
      : (lang !== 'en' && diagnosis.diagnosis_localized) || diagnosis.diagnosis)

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
        {/* Exact ee6e5b5 markup: no per-element `dir`. Urdu RTL comes from the
            global html dir set in LanguageContext, so rendering is unchanged. */}
        <h2 id="diagnosis-heading" className="diagnosis-card__name">
          {displayDiagnosis}
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

      {/* Member 4 enriched data - only shown when a match is found */}
      {enrichedInfo && (
        <>
          {enrichedInfo.symptoms && enrichedInfo.symptoms.length > 0 && (
            <section className="card result__detail" aria-labelledby="symptoms-heading">
              <h2 id="symptoms-heading" className="result__detail-title">
                {t.result.symptomsTitle}
              </h2>
              <ul className="result__detail-list">
                {enrichedInfo.symptoms.map((s, i) => (
                  <li key={i}>{s}</li>
                ))}
              </ul>
            </section>
          )}

          {enrichedInfo.treatment && enrichedInfo.treatment.length > 0 && (
            <section className="card result__detail" aria-labelledby="treatment-heading">
              <h2 id="treatment-heading" className="result__detail-title">
                {t.result.treatmentTitle}
              </h2>
              <ol className="result__detail-list result__detail-list--ordered">
                {enrichedInfo.treatment.map((tr, i) => (
                  <li key={i}>{tr}</li>
                ))}
              </ol>
            </section>
          )}

          {enrichedInfo.prevention && enrichedInfo.prevention.length > 0 && (
            <section className="card result__detail" aria-labelledby="prevention-heading">
              <h2 id="prevention-heading" className="result__detail-title">
                {t.result.preventionTitle}
              </h2>
              <ul className="result__detail-list">
                {enrichedInfo.prevention.map((p, i) => (
                  <li key={i}>{p}</li>
                ))}
              </ul>
            </section>
          )}
        </>
      )}

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
