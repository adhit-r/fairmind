import type { Metadata } from 'next'
import { JetBrains_Mono } from 'next/font/google'
import './globals.css'

const jetbrains = JetBrains_Mono({
  subsets: ['latin'],
  weight: ['300', '400', '500', '600', '700'],
  variable: '--font-jetbrains',
})

export const metadata: Metadata = {
  title: 'FairMind - AI Governance Platform',
  description: 'Comprehensive AI governance, bias detection, and compliance platform',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={`${jetbrains.className} font-mono bg-background text-foreground`}>
        <div className="flex h-screen">
          {/* Sidebar */}
          <div className="w-64 bg-sidebar border-r border-sidebar-border flex flex-col">
            {/* Header */}
            <div className="p-4 border-b border-sidebar-border">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded bg-gold text-gold-foreground font-bold">
                  <span className="text-sm">FM</span>
                </div>
                <div className="flex flex-col">
                  <span className="text-lg font-bold tracking-wider">FAIRMIND</span>
                  <span className="text-xs text-muted-foreground tracking-wide">AI.GOVERNANCE.PLATFORM</span>
                </div>
              </div>
            </div>

            {/* Navigation */}
            <nav className="flex-1 p-4 space-y-6">
              {/* Discover Section */}
              <div className="space-y-2">
                <h3 className="text-xs font-bold tracking-wider text-muted-foreground">DISCOVER</h3>
                <div className="space-y-1">
                  <a href="/" className="flex items-center gap-3 px-3 py-2 rounded-md bg-gold text-gold-foreground font-mono text-sm">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2H5a2 2 0 00-2-2z" />
                    </svg>
                    <span className="tracking-wide">DASHBOARD</span>
                  </a>
                  <a href="/model-registry" className="flex items-center gap-3 px-3 py-2 rounded-md text-muted-foreground hover:bg-accent hover:text-accent-foreground font-mono text-sm">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                    </svg>
                    <span className="tracking-wide">MODEL_REGISTRY</span>
                  </a>
                </div>
              </div>

              {/* Upload Section */}
              <div className="space-y-2">
                <h3 className="text-xs font-bold tracking-wider text-muted-foreground">UPLOAD</h3>
                <div className="space-y-1">
                  <a href="/model-upload" className="flex items-center gap-3 px-3 py-2 rounded-md text-muted-foreground hover:bg-accent hover:text-accent-foreground font-mono text-sm">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                    </svg>
                    <span className="tracking-wide">NEW_MODEL</span>
                  </a>
                  <a href="/batch-upload" className="flex items-center gap-3 px-3 py-2 rounded-md text-muted-foreground hover:bg-accent hover:text-accent-foreground font-mono text-sm">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                    </svg>
                    <span className="tracking-wide">BATCH_UPLOAD</span>
                  </a>
                </div>
              </div>

              {/* Test Section */}
              <div className="space-y-2">
                <h3 className="text-xs font-bold tracking-wider text-muted-foreground">TEST</h3>
                <div className="space-y-1">
                  <a href="/bias-detection" className="flex items-center gap-3 px-3 py-2 rounded-md text-muted-foreground hover:bg-accent hover:text-accent-foreground font-mono text-sm">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                    </svg>
                    <span className="tracking-wide">BIAS_DETECTION</span>
                  </a>
                  <a href="/security-testing" className="flex items-center gap-3 px-3 py-2 rounded-md text-muted-foreground hover:bg-accent hover:text-accent-foreground font-mono text-sm">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                    </svg>
                    <span className="tracking-wide">SECURITY_TESTING</span>
                  </a>
                  <a href="/model-testing" className="flex items-center gap-3 px-3 py-2 rounded-md text-muted-foreground hover:bg-accent hover:text-accent-foreground font-mono text-sm">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.828 14.828a4 4 0 01-5.656 0M9 10h1m4 0h1m-6 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <span className="tracking-wide">MODEL_TESTING</span>
                  </a>
                </div>
              </div>

              {/* Monitor Section */}
              <div className="space-y-2">
                <h3 className="text-xs font-bold tracking-wider text-muted-foreground">MONITOR</h3>
                <div className="space-y-1">
                  <a href="/model-monitoring" className="flex items-center gap-3 px-3 py-2 rounded-md text-muted-foreground hover:bg-accent hover:text-accent-foreground font-mono text-sm">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                    </svg>
                    <span className="tracking-wide">MODEL_MONITORING</span>
                  </a>
                  <a href="/drift-detection" className="flex items-center gap-3 px-3 py-2 rounded-md text-muted-foreground hover:bg-accent hover:text-accent-foreground font-mono text-sm">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                    <span className="tracking-wide">DRIFT_DETECTION</span>
                  </a>
                  <a href="/performance-tracking" className="flex items-center gap-3 px-3 py-2 rounded-md text-muted-foreground hover:bg-accent hover:text-accent-foreground font-mono text-sm">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 8v8m-4-5v5m-4-2v2m-2 4h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                    <span className="tracking-wide">PERFORMANCE</span>
                  </a>
                </div>
              </div>

              {/* Govern Section */}
              <div className="space-y-2">
                <h3 className="text-xs font-bold tracking-wider text-muted-foreground">GOVERN</h3>
                <div className="space-y-1">
                  <a href="/compliance" className="flex items-center gap-3 px-3 py-2 rounded-md text-muted-foreground hover:bg-accent hover:text-accent-foreground font-mono text-sm">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                    </svg>
                    <span className="tracking-wide">COMPLIANCE</span>
                  </a>
                  <a href="/ai-bom" className="flex items-center gap-3 px-3 py-2 rounded-md text-muted-foreground hover:bg-accent hover:text-accent-foreground font-mono text-sm">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                    </svg>
                    <span className="tracking-wide">AI_BOM</span>
                  </a>
                  <a href="/provenance" className="flex items-center gap-3 px-3 py-2 rounded-md text-muted-foreground hover:bg-accent hover:text-accent-foreground font-mono text-sm">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    <span className="tracking-wide">PROVENANCE</span>
                  </a>
                </div>
              </div>

              {/* Analyze Section */}
              <div className="space-y-2">
                <h3 className="text-xs font-bold tracking-wider text-muted-foreground">ANALYZE</h3>
                <div className="space-y-1">
                  <a href="/analytics" className="flex items-center gap-3 px-3 py-2 rounded-md text-muted-foreground hover:bg-accent hover:text-accent-foreground font-mono text-sm">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 8v8m-4-5v5m-4-2v2m-2 4h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                    <span className="tracking-wide">ANALYTICS</span>
                  </a>
                  <a href="/reports" className="flex items-center gap-3 px-3 py-2 rounded-md text-muted-foreground hover:bg-accent hover:text-accent-foreground font-mono text-sm">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    <span className="tracking-wide">REPORTS</span>
                  </a>
                </div>
              </div>
            </nav>

            {/* Footer */}
            <div className="p-4 border-t border-sidebar-border">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 bg-accent rounded-full flex items-center justify-center">
                  <span className="text-xs font-bold">JD</span>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">JOHN.DOE</p>
                  <p className="text-xs text-muted-foreground truncate">ADMIN</p>
                </div>
              </div>
            </div>
          </div>

          {/* Main Content */}
          <div className="flex-1 flex flex-col">
            {/* Header */}
            <header className="flex h-16 shrink-0 items-center gap-2 border-b border-border">
              <div className="flex items-center gap-2 px-4">
                <div className="w-px h-4 bg-border"></div>
                <div className="text-sm font-mono">
                  <span className="text-muted-foreground">HOME</span>
                  <span className="text-muted-foreground mx-2">/</span>
                  <span>AI_GOVERNANCE_DASHBOARD</span>
                </div>
              </div>
            </header>

            {/* Content */}
            <div className="flex-1 overflow-auto">
        {children}
            </div>
          </div>
        </div>
      </body>
    </html>
  )
}
