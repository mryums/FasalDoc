import { useEffect, useState } from 'react'
import { useLanguage } from '../i18n/LanguageContext'
import { SpinnerIcon } from '../components/icons'

interface AnalyzingScreenProps {
  previewUrl: string | null
}

export function AnalyzingScreen({ previewUrl }: AnalyzingScreenProps) {
  const { t } = useLanguage()
  const [step, setStep] = useState(0)

  useEffect(() => {
    const timer = setInterval(() => {
      setStep((s) => (s + 1) % t.analyzing.messages.length)
    }, 2400)
    return () => clearInterval(timer)
  }, [t.analyzing.messages.length])

  return (
    <div className="screen analyzing" role="status" aria-live="polite">
      {previewUrl && (
        <img src={previewUrl} alt={t.result.imageLabel} className="analyzing__image" />
      )}
      <div className="analyzing__status">
        <SpinnerIcon size={30} className="analyzing__spinner" />
        <h1 className="analyzing__title">{t.analyzing.title}</h1>
        <p className="analyzing__message" key={step}>
          {t.analyzing.messages[step]}
        </p>
        <p className="analyzing__note">{t.analyzing.note}</p>
      </div>
    </div>
  )
}
