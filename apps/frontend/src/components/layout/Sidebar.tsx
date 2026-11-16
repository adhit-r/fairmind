'use client'

import React from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { IconLogout } from '@tabler/icons-react'

import { Sidebar, SidebarContent, useSidebar } from '@/components/ui/sidebar'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'
import { FramedIdentity } from '@/components/ui/FramedIdentity'
import { useSession } from '@/context/SessionContext'
import { useOptionalOrg } from '@/context/OrgContext'
import {
  NAVIGATION_ITEMS,
  SETTINGS_NAV_ITEM,
  isNavigationItemActive,
  resolveAdminAccess,
  type NavigationItem,
} from '@/lib/constants/navigation'
import { cn } from '@/lib/utils'

interface AppSidebarProps {
  className?: string
}

function NavLink({
  item,
  pathname,
  collapsed,
  onNavigate,
}: {
  item: NavigationItem
  pathname: string
  collapsed: boolean
  onNavigate?: () => void
}) {
  const Icon = item.icon
  const active = isNavigationItemActive(pathname, item)
  const link = (
    <Link
      href={item.href}
      aria-current={active ? 'page' : undefined}
      aria-label={collapsed ? item.title : undefined}
      onClick={onNavigate}
      className={cn(
        'flex min-h-11 items-center gap-3 rounded-md px-3 text-sm font-medium text-sidebar-foreground transition-colors motion-reduce:transition-none',
        'hover:bg-sidebar-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sidebar-ring',
        active && 'bg-sidebar-accent font-semibold',
        collapsed && 'justify-center px-0',
      )}
    >
      <Icon
        aria-hidden="true"
        className={cn('h-5 w-5 shrink-0', active ? 'text-primary-strong' : 'text-muted-foreground')}
      />
      {!collapsed && <span className="min-w-0 flex-1 truncate">{item.title}</span>}
    </Link>
  )

  if (!collapsed) return link
  return (
    <Tooltip>
      <TooltipTrigger asChild>{link}</TooltipTrigger>
      <TooltipContent side="right">{item.title}</TooltipContent>
    </Tooltip>
  )
}

export function AppSidebar({ className }: AppSidebarProps) {
  const pathname = usePathname()
  const { state, isMobile, setOpenMobile } = useSidebar()
  const { user, logout } = useSession()
  const org = useOptionalOrg()
  const collapsed = state === 'collapsed' && !isMobile

  // Administration is shown to admins/owners. When role information is not
  // available at all, the group stays visible (server-side authorisation is the
  // real gate); once a role is known and is not an admin role it is hidden.
  const adminAccess = resolveAdminAccess(user?.role, org?.selectedOrg?.role)
  const showAdmin = adminAccess !== false

  const closeMobile = () => {
    if (isMobile) setOpenMobile(false)
  }

  return (
    <Sidebar
      aria-label="Primary navigation"
      variant="sidebar"
      collapsible="icon"
      className={cn('border-sidebar-border bg-sidebar', className)}
    >
      <SidebarContent className="flex h-full flex-col overflow-visible bg-sidebar p-0">
        <nav aria-label="Product navigation" className={cn('flex-1 space-y-5 overflow-y-auto overflow-x-hidden p-3', collapsed && 'space-y-3 px-2')}>
          {NAVIGATION_ITEMS.filter((group) => showAdmin || !group.requiresAdmin).map((group) => {
            const headingId = `nav-group-${group.id}`
            return (
              <div key={group.id} role="group" aria-labelledby={headingId} className="space-y-1">
                <p
                  id={headingId}
                  className={cn('eyebrow px-3 pb-1', collapsed && 'sr-only')}
                >
                  {group.title}
                </p>
                {group.items.map((item) => (
                  <NavLink key={item.href} item={item} pathname={pathname} collapsed={collapsed} onNavigate={closeMobile} />
                ))}
              </div>
            )
          })}
        </nav>

        <div className={cn('space-y-1 border-t border-sidebar-border p-3', collapsed && 'px-2')}>
          <NavLink item={SETTINGS_NAV_ITEM} pathname={pathname} collapsed={collapsed} onNavigate={closeMobile} />
          {user && (
            collapsed ? (
              <>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <FramedIdentity name={user.username} collapsed label={`${user.username} profile`} className="w-full" />
                  </TooltipTrigger>
                  <TooltipContent side="right">{user.username}</TooltipContent>
                </Tooltip>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <button
                      type="button"
                      aria-label="Sign out"
                      onClick={() => void logout()}
                      className="flex min-h-11 w-full items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-sidebar-accent hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sidebar-ring"
                    >
                      <IconLogout className="h-5 w-5" aria-hidden="true" />
                    </button>
                  </TooltipTrigger>
                  <TooltipContent side="right">Sign out</TooltipContent>
                </Tooltip>
              </>
            ) : (
              <>
                <FramedIdentity name={user.username} email={user.email} label={`${user.username} profile`} />
                <button
                  type="button"
                  onClick={() => void logout()}
                  className="flex min-h-11 w-full items-center gap-3 rounded-md px-3 text-sm font-medium text-muted-foreground transition-colors hover:bg-sidebar-accent hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sidebar-ring"
                >
                  <IconLogout className="h-5 w-5 shrink-0" aria-hidden="true" />
                  Sign out
                </button>
              </>
            )
          )}
        </div>
      </SidebarContent>
    </Sidebar>
  )
}
