'use client'

import { Card, CardBody } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { EmptyState } from '@/components/ui/EmptyState'
import { MessageSquare, Plus } from 'lucide-react'

export default function ChatPage() {
  return (
    <div className="h-[calc(100vh-var(--topbar-height)-2rem)]">
      <Card className="h-full flex flex-col">
        <CardBody className="flex-1 flex items-center justify-center">
          <EmptyState
            icon={<MessageSquare className="h-12 w-12" />}
            title="Start a conversation"
            description="Create a new chat to interact with Agent Zero"
            action={
              <Button size="md">
                <Plus className="h-4 w-4" />
                New Chat
              </Button>
            }
          />
        </CardBody>
      </Card>
    </div>
  )
}
