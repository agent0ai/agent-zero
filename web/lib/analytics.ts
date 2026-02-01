export function initializeAnalytics(gaId: string) {
  if (!gaId || gaId === 'YOUR_GA_ID') {
    console.warn('Google Analytics not configured')
    return
  }

  const script = document.createElement('script')
  script.async = true
  script.src = `https://www.googletagmanager.com/gtag/js?id=${gaId}`
  document.head.appendChild(script)

  window.dataLayer = window.dataLayer || []
  function gtag(..._args: any[]) {
    window.dataLayer.push(arguments)
  }
  gtag('js', new Date())
  gtag('config', gaId, {
    page_path: typeof window !== 'undefined' ? window.location.pathname : '',
  })
  window.gtag = gtag
}

export function trackPageView(path: string) {
  if (typeof window !== 'undefined' && window.gtag) {
    window.gtag('config', (window as any).GA_ID || '', {
      page_path: path,
    })
  }
}

declare global {
  interface Window {
    dataLayer: any[]
    gtag: (...args: any[]) => void
    GA_ID?: string
  }
}
