'use client'

import { useRef, useEffect } from 'react'
import { ChatMessage, type ChatLog } from './ChatMessage'

interface ChatMessageListProps {
  logs: ChatLog[]
  autoScroll?: boolean
}

export function ChatMessageList({ logs, autoScroll = true }: ChatMessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (autoScroll && bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [logs.length, autoScroll])

  return (
    <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3">
      {logs.map((log) => (
        <ChatMessage key={log.id ?? log.no} log={log} />
      ))}
      <div ref={bottomRef} />
    </div>
  )
}
