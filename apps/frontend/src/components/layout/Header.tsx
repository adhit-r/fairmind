'use client'

import React from 'react'
import Link from 'next/link'
import { IconBell, IconLogout, IconMenu2, IconSettings } from '@tabler/icons-react'

import { OrangeLogo } from '@/components/OrangeLogo'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { useSidebar } from '@/components/ui/sidebar'
import { FramedIcon } from '@/components/ui/FramedIcon'
import { FramedIdentity } from '@/components/ui/FramedIdentity'
import { ThemeToggle } from '@/components/theme/ThemeToggle'
import { useSession } from '@/context/SessionContext'
import { QuickJump } from './QuickJump'

interface HeaderProps {
  onMenuToggle?: () => void
}

export function Header({ onMenuToggle }: HeaderProps) {
  const { toggleSidebar } = useSidebar()
  const { user, loading: sessionLoading, logout } = useSession()

  const handleNavigationToggle = () => {
    onMenuToggle?.()
    toggleSidebar()
  }

  return (
    <header className="sticky top-0 z-30 flex h-[var(--header-height)] w-full items-center border-b border-border bg-background">
      <div className="flex w-full items-center justify-between gap-2 px-3 sm:gap-4 sm:px-4">
        <div className="flex flex-shrink-0 items-center gap-1 sm:gap-3">
          <FramedIcon icon={IconMenu2} label="Toggle navigation" onClick={handleNavigationToggle} />
          <Link
            href="/dashboard"
            aria-label="FairMind home"
            className="rounded-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
          >
            <OrangeLogo size="sm" showText />
          </Link>
        </div>

        <div className="flex min-w-0 items-center gap-1 sm:gap-2">
          <QuickJump />
          <ThemeToggle />
          <Link
            href="/monitoring?tab=alerts"
            aria-label="Alerts"
            className="inline-flex h-11 w-11 items-center justify-center rounded-md text-foreground transition-colors hover:bg-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
          >
            <IconBell className="h-5 w-5" aria-hidden="true" />
          </Link>

          {user ? (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <FramedIdentity
                  name={user.username}
                  collapsed
                  label={`Open user menu for ${user.username}`}
                />
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-64">
                <DropdownMenuLabel className="space-y-0.5 font-normal">
                  <span className="block truncate text-sm font-semibold">{user.username}</span>
                  <span className="block truncate text-xs text-muted-foreground">{user.email}</span>
                </DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem asChild>
                  <Link href="/settings">
                    <IconSettings aria-hidden="true" />
                    Settings
                  </Link>
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onSelect={() => void logout()} className="text-destructive-strong focus:text-destructive-strong">
                  <IconLogout aria-hidden="true" />
                  Sign out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          ) : (
            <span aria-live="polite" className="hidden text-xs text-muted-foreground sm:inline">
              {sessionLoading ? 'Loading session' : 'Session unavailable'}
            </span>
          )}
        </div>
      </div>
    </header>
  )
}
