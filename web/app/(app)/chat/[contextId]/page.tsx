'use client'

import { Card, CardBody } from '@/components/ui/Card'
import { Spinner } from '@/components/ui/Spinner'

export default function ChatContextPage({ params }: { params: { contextId: string } }) {
  return (
    <div className="h-[calc(100vh-var(--topbar-height)-2rem)]">
      <Card className="h-full flex flex-col">
        <CardBody className="flex-1 flex items-center justify-center">
          <div className="text-center space-y-3">
            <Spinner size="lg" />
            <p className="text-sm text-[var(--text-secondary)]">
              Loading context {params.contextId}...
            </p>
          </div>
        </CardBody>
      </Card>
    </div>
  )
}
