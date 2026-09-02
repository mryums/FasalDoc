import { useState, type ReactNode } from 'react'
import { useLanguage } from '../i18n/LanguageContext'
import { MicIcon } from './icons'
import { VoiceInput } from './VoiceInput'

/**
 * Voice-ready input: text field with active microphone integration.
 * When the mic button is clicked, opens VoiceInput overlay for speech-to-text.
 * The transcribed text is passed back and populates the input field.
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
  const [showVoice, setShowVoice] = useState(false)
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

  function handleVoiceConfirm(text: string) {
    onChange(text)
    setShowVoice(false)
  }

  function handleMicClick() {
    // Check if speech recognition is available
    const w = window as any
    const hasSR = w.SpeechRecognition ?? w.webkitSpeechRecognition
    if (!hasSR) {
      // Show unsupported message briefly via alert
      alert(t.voice.unsupported)
      return
    }
    setShowVoice(true)
  }

  return (
    <>
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
              className="question-input__mic question-input__mic--active"
              onClick={handleMicClick}
              disabled={disabled}
              title={t.voice.speak}
              aria-label={t.voice.speak}
            >
              <MicIcon size={20} />
            </button>
          )}
          {lang !== 'en' && <span className="question-input__hint">{t.upload.questionHelp}</span>}
        </div>
      </div>

      {showVoice && (
        <VoiceInput
          onConfirm={handleVoiceConfirm}
          onClose={() => setShowVoice(false)}
        />
      )}
    </>
  )
}
