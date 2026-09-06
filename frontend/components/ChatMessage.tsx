import { LeafIcon } from './icons'

export interface ChatMessageData {
  id: number
  role: 'farmer' | 'fasaldoc'
  text: string
}

export function ChatMessage({ message }: { message: ChatMessageData }) {
  const isFarmer = message.role === 'farmer'
  return (
    <div className={`chat-msg ${isFarmer ? 'chat-msg--farmer' : 'chat-msg--fasaldoc'}`}>
      {!isFarmer && (
        <span className="chat-msg__avatar" aria-hidden>
          <LeafIcon size={15} />
        </span>
      )}
      <div className="chat-msg__bubble">{message.text}</div>
    </div>
  )
}
