import type { ReactNode } from 'react'
import { useLanguage } from '../i18n/LanguageContext'
import { MicIcon } from './icons'

/**
 * Voice-ready input: text today, microphone later.
 * A future VoiceInput can replace/extend `trailing` without touching
 * the diagnosis flow — the component contract stays the same.
 */
interface QuestionInputProps {
  id: string
  value: string
  placeholder?: string
  disabled?: boolean
  singleLine?: boolean
  onChange: (value: string) => void
  trailing?: ReactNode
}

const MAX_LENGTH = 1000

export function QuestionInput({
  id,
  value,
  placeholder,
  disabled,
  singleLine = false,
  onChange,
  trailing,
}: QuestionInputProps) {
  const { t, lang } = useLanguage()
  const shared = {
    id,
    value,
    maxLength: MAX_LENGTH,
    disabled,
    placeholder: placeholder ?? t.upload.questionPlaceholder,
    onChange: (
      e: React.ChangeEvent<HTMLInputElement> | React.ChangeEvent<HTMLTextAreaElement>,
    ) => onChange(e.target.value),
  }

  return (
    <div className="question-input">
      {singleLine ? (
        <input type="text" className="question-input__field" {...shared} />
      ) : (
        <textarea className="question-input__field" rows={3} {...shared} />
      )}
      <div className="question-input__trailing">
        {trailing ?? (
          <button
            type="button"
            className="question-input__mic"
            disabled
            title={t.upload.micComingSoon}
            aria-label={t.upload.micComingSoon}
          >
            <MicIcon size={20} />
          </button>
        )}
        {lang !== 'en' && <span className="question-input__hint">{t.upload.questionHelp}</span>}
      </div>
    </div>
  )
}
