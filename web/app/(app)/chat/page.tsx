'use client'

import { useState, useCallback } from 'react'
import { Card } from '@/components/ui/Card'
import { ChatView } from '@/components/chat/ChatView'
import { ChatSidebar } from '@/components/chat/ChatSidebar'
import { ModelSelector } from '@/components/chat/ModelSelector'
import { useRealtime } from '@/hooks/useRealtime'
import { useSendMessage, useCreateChat } from '@/hooks/useChat'
import { deleteChat } from '@/lib/api/endpoints/chat'

export default function ChatPage() {
  const [contextId, setContextId] = useState<string | null>(null)

  const realtime = useRealtime(contextId)
  const sendMutation = useSendMessage(contextId)
  const createMutation = useCreateChat()

  const handleSend = useCallback(
    (text: string) => {
      sendMutation.mutate(text)
    },
    [sendMutation],
  )

  const handleCreate = useCallback(async () => {
    const result = await createMutation.mutateAsync()
    if (result.context) {
      setContextId(result.context)
    }
  }, [createMutation])

  const handleSelect = useCallback((id: string) => {
    setContextId(id)
  }, [])

  const handleDelete = useCallback(
    async (id: string) => {
      await deleteChat(id)
      if (contextId === id) {
        setContextId(null)
      }
    },
    [contextId],
  )

  return (
    <div className="h-[calc(100vh-var(--topbar-height)-2rem)]">
      <Card className="h-full flex overflow-hidden">
        {/* Chat sidebar */}
        <div className="hidden lg:block">
          <ChatSidebar
            contexts={realtime.contexts}
            activeContextId={contextId}
            onSelect={handleSelect}
            onCreate={handleCreate}
            onDelete={handleDelete}
          />
        </div>

        {/* Chat main area */}
        <div className="flex-1 flex flex-col min-w-0">
          {/* Top bar with model selector */}
          <div className="flex items-center justify-between px-4 py-2 border-b border-[var(--border-default)]">
            <div className="flex items-center gap-2">
              <h2 className="text-sm font-semibold text-[var(--text-primary)]">
                {contextId ? `Chat` : 'Agent Jumbo'}
              </h2>
              {realtime.connected && (
                <span className="inline-flex h-2 w-2 rounded-full bg-success" title="Connected" />
              )}
            </div>
            <ModelSelector />
          </div>

          {/* Chat view */}
          <ChatView
            logs={realtime.logs}
            progress={realtime.progress}
            progressActive={realtime.progressActive}
            onSend={handleSend}
            sending={sendMutation.isPending}
          />
        </div>
      </Card>
    </div>
  )
}
