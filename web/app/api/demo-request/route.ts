import { appendDemoRequest, listDemoRequests } from '@/lib/demo-request-store'

export async function POST(request: Request) {
  try {
    const data = await request.json()
    const record = await appendDemoRequest({
      company: data.company,
      email: data.email,
      industry: data.industry,
      teamSize: data.teamSize,
      painPoints: data.painPoints,
      cloudPlatforms: data.cloudPlatforms,
      governanceSteps: data.governanceSteps,
      integrations: data.integrations,
      useCase: data.useCase,
      complexity: data.complexity,
      budget: data.budget,
      timeline: data.timeline,
      source: 'web-demo-form',
    })
    return Response.json({
      success: true,
      message: 'Demo request submitted successfully',
      requestId: record.id,
      timestamp: record.created_at,
    })
  } catch (error) {
    console.error('Error processing demo request:', error)
    return Response.json(
      { error: 'Failed to process demo request' },
      { status: 500 }
    )
  }
}

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url)
    const limitParam = Number(searchParams.get('limit') ?? '25')
    const limit = Number.isFinite(limitParam) ? Math.max(1, Math.min(100, limitParam)) : 25

    const rows = await listDemoRequests(limit)
    return Response.json({
      success: true,
      count: rows.length,
      requests: rows,
    })
  } catch (error) {
    console.error('Error listing demo requests:', error)
    return Response.json(
      { error: 'Failed to list demo requests' },
      { status: 500 }
    )
  }
}
