export async function POST(request: Request) {
  try {
    const data = await request.json()

    // Log demo request
    console.log('Demo request received:', {
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
      timestamp: new Date().toISOString(),
    })

    // In production, you would:
    // 1. Send email to sales team
    // 2. Create record in CRM
    // 3. Add to mailing list
    // 4. Trigger follow-up workflow

    // For now, just return success
    return Response.json({
      success: true,
      message: 'Demo request submitted successfully',
      timestamp: new Date().toISOString(),
    })
  } catch (error) {
    console.error('Error processing demo request:', error)
    return Response.json(
      { error: 'Failed to process demo request' },
      { status: 500 }
    )
  }
}
