'use client'

import { useCallback } from 'react'
import { Card } from '@/components/ui/Card'
import { ChatView } from '@/components/chat/ChatView'
import { ModelSelector } from '@/components/chat/ModelSelector'
import { useRealtime } from '@/hooks/useRealtime'
import { useSendMessage } from '@/hooks/useChat'

export default function ChatContextPage({ params }: { params: { contextId: string } }) {
  const { contextId } = params
  const realtime = useRealtime(contextId)
  const sendMutation = useSendMessage(contextId)

  const handleSend = useCallback(
    (text: string) => {
      sendMutation.mutate(text)
    },
    [sendMutation],
  )

  return (
    <div className="h-[calc(100vh-var(--topbar-height)-2rem)]">
      <Card className="h-full flex flex-col overflow-hidden">
        <div className="flex items-center justify-between px-4 py-2 border-b border-[var(--border-default)]">
          <div className="flex items-center gap-2">
            <h2 className="text-sm font-semibold text-[var(--text-primary)]">Chat</h2>
            {realtime.connected && (
              <span className="inline-flex h-2 w-2 rounded-full bg-success" title="Connected" />
            )}
          </div>
          <ModelSelector />
        </div>

        <ChatView
          logs={realtime.logs}
          progress={realtime.progress}
          progressActive={realtime.progressActive}
          onSend={handleSend}
          sending={sendMutation.isPending}
        />
      </Card>
    </div>
  )
}
