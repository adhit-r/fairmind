import type { Metadata, Viewport } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import '@mantine/core/styles.css'
import '@mantine/notifications/styles.css'
import '@mantine/spotlight/styles.css'
import '@mantine/nprogress/styles.css'
import '@mantine/charts/styles.css'
import '../styles/brutalist.css'
import { GlassmorphicThemeProvider } from '@/providers/glassmorphic-theme-provider'
import { Navigation } from '@/components/Navigation'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'FairMind - Advanced AI Governance Platform',
  description: 'Next-generation AI governance, bias detection, and ethical AI compliance platform with modern glassmorphic design',
  keywords: 'AI governance, ethical AI, bias detection, fairness, machine learning, glassmorphic design, responsible AI',
  authors: [{ name: 'FairMind Team' }],
  openGraph: {
    title: 'FairMind - Advanced AI Governance Platform',
    description: 'Next-generation AI governance, bias detection, and ethical AI compliance platform',
    type: 'website',
  },
}

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
  themeColor: '#3b82f6',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <GlassmorphicThemeProvider>
          <Navigation>
            {children}
          </Navigation>
        </GlassmorphicThemeProvider>
      </body>
    </html>
  )
}

