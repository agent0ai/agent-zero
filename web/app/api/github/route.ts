import { getRepoStats, getLatestRelease } from '@/lib/github'
import { NextRequest, NextResponse } from 'next/server'

export async function GET(request: NextRequest) {
  try {
    const [stats, release] = await Promise.all([
      getRepoStats(),
      getLatestRelease(),
    ])

    return NextResponse.json({
      stats,
      release,
      timestamp: new Date().toISOString(),
    })
  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to fetch GitHub data' },
      { status: 500 }
    )
  }
}
