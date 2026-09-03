import { useLanguage } from '../i18n/LanguageContext'

export type ConfidenceBand = 'high' | 'medium' | 'low'

export function confidenceBand(confidence: number): ConfidenceBand {
  if (confidence >= 0.75) return 'high'
  if (confidence >= 0.5) return 'medium'
  return 'low'
}

interface ConfidenceIndicatorProps {
  /** 0..1 as returned by the backend */
  confidence: number
}

export function ConfidenceIndicator({ confidence }: ConfidenceIndicatorProps) {
  const { t } = useLanguage()
  const pct = Math.round(Math.min(Math.max(confidence, 0), 1) * 100)
  const band = confidenceBand(confidence)

  const radius = 44
  const circumference = 2 * Math.PI * radius
  const filled = (pct / 100) * circumference

  const caption =
    band === 'high'
      ? t.result.confidenceHigh
      : band === 'medium'
        ? t.result.confidenceMedium
        : t.result.confidenceLow

  return (
    <div className={`confidence confidence--${band}`}>
      <div
        className="confidence__ring"
        role="img"
        aria-label={`${t.result.confidenceLabel}: ${pct}%`}
      >
        <svg viewBox="0 0 100 100" width="110" height="110" aria-hidden>
          <circle cx="50" cy="50" r={radius} className="confidence__track" />
          <circle
            cx="50"
            cy="50"
            r={radius}
            className="confidence__fill"
            strokeDasharray={`${filled} ${circumference}`}
            transform="rotate(-90 50 50)"
          />
        </svg>
        <span className="confidence__pct" aria-hidden>
          {pct}%
        </span>
      </div>
      <div className="confidence__text">
        <span className="confidence__label">{t.result.confidenceLabel}</span>
        <span className="confidence__caption">{caption}</span>
        {band !== 'high' && (
          <span className="confidence__tip">{t.result.lowConfidenceAdvice}</span>
        )}
      </div>
    </div>
  )
}
