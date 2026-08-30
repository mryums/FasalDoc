import { AlertIcon } from './icons'
import { Button } from './Button'
import { useLanguage } from '../i18n/LanguageContext'

interface ErrorMessageProps {
  message: string
  onRetry?: () => void
}

export function ErrorMessage({ message, onRetry }: ErrorMessageProps) {
  const { t } = useLanguage()
  if (!message) return null
  return (
    <div className="error-box" role="alert">
      <AlertIcon size={20} className="error-box__icon" />
      <p className="error-box__text">{message}</p>
      {onRetry && (
        <Button variant="secondary" onClick={onRetry} className="error-box__retry">
          {t.errors.retry}
        </Button>
      )}
    </div>
  )
}
