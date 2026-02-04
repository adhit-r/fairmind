'use client'

import React from 'react'
import { usePathname } from 'next/navigation'
import { SidebarProvider } from '@/components/ui/sidebar'
import { Header } from './Header'
import { AppSidebar } from './Sidebar'

interface NavigationProps {
  children: React.ReactNode
}

export function Navigation({ children }: NavigationProps) {
  const pathname = usePathname()
  const isAuthRoute = pathname?.startsWith('/login') || pathname?.startsWith('/register')
  const [mobileMenuOpen, setMobileMenuOpen] = React.useState(false)

  // Don't show sidebar/header on auth pages
  if (isAuthRoute) {
    return <>{children}</>
  }

  return (
    <SidebarProvider>
      <div className="flex min-h-screen w-full">
        <AppSidebar />
        <div className="flex flex-1 flex-col min-w-0">
          <Header onMenuToggle={() => setMobileMenuOpen(!mobileMenuOpen)} />
          <main className="flex-1 p-3 sm:p-4 md:p-6 bg-gray-50 overflow-x-hidden">
            {children}
          </main>
        </div>
      </div>
    </SidebarProvider>
  )
}

