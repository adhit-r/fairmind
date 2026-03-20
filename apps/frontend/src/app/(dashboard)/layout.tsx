'use client'

import { AuthGuard } from '@/components/auth/AuthGuard'
import {
  SystemContextBar,
  SystemContextProvider,
} from '@/components/workflow/SystemContext'

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <AuthGuard>
      <SystemContextProvider>
        <div className="space-y-0">
          <SystemContextBar />
          {children}
        </div>
      </SystemContextProvider>
    </AuthGuard>
  )
}
