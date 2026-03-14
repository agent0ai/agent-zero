'use client'

import { ChatMessageList } from './ChatMessageList'
import { ChatInput } from './ChatInput'
import { ChatProgress } from './ChatProgress'
import { EmptyState } from '@/components/ui/EmptyState'
import { MessageSquare } from 'lucide-react'
import type { ChatLog } from './ChatMessage'

interface ChatViewProps {
  logs: ChatLog[]
  progress?: string
  progressActive?: boolean
  onSend: (text: string) => void
  sending?: boolean
}

export function ChatView({ logs, progress, progressActive, onSend, sending }: ChatViewProps) {
  return (
    <div className="flex h-full flex-col">
      {logs.length > 0 ? (
        <ChatMessageList logs={logs} />
      ) : (
        <div className="flex-1 flex items-center justify-center">
          <EmptyState
            icon={<MessageSquare className="h-12 w-12" />}
            title="Start a conversation"
            description="Send a message to begin interacting with Agent Jumbo"
          />
        </div>
      )}

      <ChatProgress message={progress} active={progressActive} />
      <ChatInput onSend={onSend} disabled={sending} />
    </div>
  )
}
