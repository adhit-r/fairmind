'use client'

// Temporarily disable AuthGuard for testing
// import { AuthGuard } from '@/components/auth/AuthGuard'

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  // Temporarily return children directly for testing
  return <>{children}</>
  // return <AuthGuard>{children}</AuthGuard>
}

