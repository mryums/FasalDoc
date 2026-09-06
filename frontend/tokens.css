import { useLanguage } from '../i18n/LanguageContext'
import type { DiagnosisResponse } from '../types/api'
import { FollowUpChat } from '../components/FollowUpChat'
import type { ChatMessageData } from '../components/ChatMessage'

interface FollowUpScreenProps {
  diagnosis: DiagnosisResponse
  previewUrl: string | null
  messages: ChatMessageData[]
  sending: boolean
  sendError: string | null
  initialDraft: string
  onSend: (question: string) => void
}

export function FollowUpScreen({
  diagnosis,
  previewUrl,
  messages,
  sending,
  sendError,
  initialDraft,
  onSend,
}: FollowUpScreenProps) {
  const { t } = useLanguage()

  return (
    <div className="screen followup-screen">
      <h1 className="screen__title">{t.followup.title}</h1>

      <div className="followup-context">
        {previewUrl && (
          <img src={previewUrl} alt="" className="followup-context__thumb" aria-hidden />
        )}
        <div className="followup-context__text">
          <span className="followup-context__label">{t.followup.aboutLabel}</span>
          <strong className="followup-context__diagnosis">{diagnosis.diagnosis}</strong>
          <span className="followup-context__confidence">
            {t.result.confidenceLabel}: {Math.round(diagnosis.confidence * 100)}%
          </span>
        </div>
      </div>

      <FollowUpChat
        messages={messages}
        sending={sending}
        sendError={sendError}
        initialDraft={initialDraft}
        onSend={onSend}
      />
    </div>
  )
}
