'use client'

import { AuthGuard } from '@/components/auth/AuthGuard'
import {
  SystemContextBar,
  SystemContextProvider,
} from '@/components/workflow/SystemContext'
import { OrgProvider } from '@/context/OrgContext'
import { OrgSwitcher } from '@/components/OrgSwitcher'

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <AuthGuard>
      <OrgProvider>
        <SystemContextProvider>
          <div className="space-y-0">
            <OrgSwitcher />
            <SystemContextBar />
            {children}
          </div>
        </SystemContextProvider>
      </OrgProvider>
    </AuthGuard>
  )
}
