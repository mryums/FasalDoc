import { useLanguage } from '../i18n/LanguageContext'
import type { DiagnosisResponse } from '../types/api'
import { ConfidenceIndicator, confidenceBand } from '../components/ConfidenceIndicator'
import { Button } from '../components/Button'
import { ErrorMessage } from '../components/ErrorMessage'
import { AlertIcon, RefreshIcon } from '../components/icons'
import { agricultureData } from '../data/agriculture'

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

  // Try to enrich with Member 4 data
  const enrichedInfo = diseaseLookupFromDiagnosis(diagnosis.diagnosis)

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

/**
 * Try to extract disease info from the diagnosis string.
 * The backend returns diagnosis like "Early Blight" — we match against
 * Member 4's disease names using fuzzy matching.
 */
function diseaseLookupFromDiagnosis(
  diagnosisText: string,
): { symptoms: string[]; treatment: string[]; prevention: string[] } | null {
  const diagLower = diagnosisText.toLowerCase().trim()

  for (const plant of agricultureData.plants) {
    for (const disease of plant.diseases) {
      const nameLower = disease.name.en.toLowerCase()
      if (
        nameLower === diagLower ||
        diagLower.includes(nameLower) ||
        nameLower.includes(diagLower)
      ) {
        return {
          symptoms: disease.symptoms?.en ?? [],
          treatment: disease.treatment?.en ?? [],
          prevention: disease.prevention?.en ?? [],
        }
      }
    }
  }
  return null
}
