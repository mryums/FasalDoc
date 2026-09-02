import { useCallback, useEffect, useRef, useState } from 'react'
import { useLanguage } from '../i18n/LanguageContext'
import { Button } from './Button'
import { MicIcon, StopIcon, XIcon, CheckIcon } from './icons'

interface VoiceInputProps {
  onConfirm: (text: string) => void
  onClose: () => void
}

type VoiceState = 'idle' | 'listening' | 'transcribed' | 'unsupported' | 'error'

/* eslint-disable @typescript-eslint/no-explicit-any */
interface SpeechRecognitionLike {
  continuous: boolean
  interimResults: boolean
  lang: string
  onresult: ((event: any) => void) | null
  onerror: ((event: any) => void) | null
  onend: (() => void) | null
  start(): void
  stop(): void
  abort(): void
}
/* eslint-enable @typescript-eslint/no-explicit-any */

function getSpeechRecognition(): (new () => SpeechRecognitionLike) | null {
  const w = window as any
  return w.SpeechRecognition ?? w.webkitSpeechRecognition ?? null
}

export function VoiceInput({ onConfirm, onClose }: VoiceInputProps) {
  const { t, lang } = useLanguage()
  const [state, setState] = useState<VoiceState>('idle')
  const [transcript, setTranscript] = useState('')
  const recognitionRef = useRef<SpeechRecognitionLike | null>(null)

  const SpeechRecognitionCtor = getSpeechRecognition()

  const startListening = useCallback(() => {
    if (!SpeechRecognitionCtor) {
      setState('unsupported')
      return
    }

    const recognition = new SpeechRecognitionCtor()
    recognition.continuous = false
    recognition.interimResults = true
    recognition.lang = lang === 'ur' ? 'ur-PK' : lang === 'rom' ? 'ur-PK' : 'en-US'

    recognition.onresult = (event: any) => {
      let finalTranscript = ''
      let interimTranscript = ''
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i]
        if (result.isFinal) {
          finalTranscript += result[0].transcript
        } else {
          interimTranscript += result[0].transcript
        }
      }
      const text = finalTranscript || interimTranscript
      if (text.trim()) {
        setTranscript(text.trim())
      }
    }

    recognition.onerror = () => {
      setState('error')
    }

    recognition.onend = () => {
      setTranscript((prev: string) => {
        if (prev.trim()) {
          setState('transcribed')
        } else {
          setState('idle')
        }
        return prev
      })
    }

    recognitionRef.current = recognition
    recognition.start()
    setState('listening')
  }, [SpeechRecognitionCtor, lang])

  function stopListening() {
    recognitionRef.current?.stop()
  }

  function handleCancel() {
    recognitionRef.current?.abort()
    setTranscript('')
    onClose()
  }

  function handleConfirm() {
    if (transcript.trim()) {
      onConfirm(transcript.trim())
    }
    onClose()
  }

  function handleRetry() {
    setTranscript('')
    setState('idle')
    startListening()
  }

  useEffect(() => {
    return () => {
      recognitionRef.current?.abort()
    }
  }, [])

  // Auto-start on mount
  useEffect(() => {
    if (state === 'idle' && !transcript) {
      startListening()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return (
    <div className="voice-overlay" role="dialog" aria-label={t.voice.speak}>
      <div className="voice-overlay__header">
        <span>{t.voice.speak}</span>
        <button
          type="button"
          className="voice-overlay__close"
          onClick={handleCancel}
          aria-label={t.voice.cancel}
        >
          <XIcon size={20} />
        </button>
      </div>

      <div className="voice-overlay__body">
        {state === 'unsupported' && (
          <p className="voice-overlay__message">{t.voice.unsupported}</p>
        )}

        {state === 'error' && (
          <div className="voice-overlay__message">
            <p>{t.voice.unsupported}</p>
            <Button variant="secondary" onClick={handleRetry}>
              {t.voice.speak}
            </Button>
          </div>
        )}

        {(state === 'idle' || state === 'listening') && (
          <div className="voice-overlay__mic-area">
            <button
              type="button"
              className={`voice-overlay__mic-btn ${state === 'listening' ? 'voice-overlay__mic-btn--pulse' : ''}`}
              onClick={state === 'listening' ? stopListening : startListening}
              aria-label={state === 'listening' ? t.voice.stop : t.voice.speak}
            >
              {state === 'listening' ? <StopIcon size={28} /> : <MicIcon size={28} />}
            </button>
            {state === 'listening' && (
              <p className="voice-overlay__status">{t.voice.listening}</p>
            )}
            {state === 'idle' && !transcript && (
              <p className="voice-overlay__status">{t.voice.speak}</p>
            )}
          </div>
        )}

        {state === 'transcribed' && (
          <div className="voice-overlay__transcript">
            <label className="voice-overlay__transcript-label">{t.voice.transcript}</label>
            <textarea
              className="voice-overlay__transcript-text"
              value={transcript}
              onChange={(e) => setTranscript(e.target.value)}
              rows={3}
            />
            <p className="voice-overlay__hint">{t.voice.editHint}</p>
            <div className="voice-overlay__actions">
              <Button variant="secondary" onClick={handleCancel}>
                {t.voice.cancel}
              </Button>
              <Button onClick={handleConfirm}>
                <CheckIcon size={16} />
                {t.voice.confirm}
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
