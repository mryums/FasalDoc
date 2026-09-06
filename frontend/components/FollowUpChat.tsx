import { useEffect, useRef, useState } from 'react'
import { ChatMessage, type ChatMessageData } from './ChatMessage'
import { QuestionInput } from './QuestionInput'
import { Button } from './Button'
import { SendIcon } from './icons'
import { useLanguage } from '../i18n/LanguageContext'

interface FollowUpChatProps {
  messages: ChatMessageData[]
  sending: boolean
  sendError: string | null
  initialDraft?: string
  onSend: (question: string) => void
}

export function FollowUpChat({
  messages,
  sending,
  sendError,
  initialDraft = '',
  onSend,
}: FollowUpChatProps) {
  const { t } = useLanguage()
  const [draft, setDraft] = useState(initialDraft)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [messages, sending])

  function submit() {
    const question = draft.trim()
    if (!question || sending) return
    onSend(question)
    setDraft('')
  }

  return (
    <div className="chat">
      <div className="chat__messages" aria-live="polite">
        <div className="chat-msg chat-msg--fasaldoc">
          <span className="chat-msg__avatar" aria-hidden />
          <div className="chat-msg__bubble chat-msg__bubble--soft">{t.followup.greeting}</div>
        </div>
        {messages.map((m) => (
          <ChatMessage key={m.id} message={m} />
        ))}
        {sending && (
          <div className="chat-msg chat-msg--fasaldoc">
            <span className="chat-msg__avatar" aria-hidden />
            <div
              className="chat-msg__bubble chat-msg__bubble--typing"
              aria-label={t.followup.sending}
            >
              <span className="typing-dot" />
              <span className="typing-dot" />
              <span className="typing-dot" />
            </div>
          </div>
        )}
        {sendError && (
          <div className="chat__error" role="alert">
            {sendError}
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <form
        className="chat__composer"
        onSubmit={(e) => {
          e.preventDefault()
          submit()
        }}
      >
        <QuestionInput
          id="followup-question"
          value={draft}
          singleLine
          placeholder={t.followup.placeholder}
          disabled={sending}
          onChange={setDraft}
        />
        <Button type="submit" loading={sending} aria-label={t.followup.send}>
          <SendIcon size={18} />
          <span className="chat__send-label">{t.followup.send}</span>
        </Button>
      </form>
    </div>
  )
}
