'use client'

import React, { useEffect, useState } from 'react'
import { usePathname } from 'next/navigation'
import { IconChevronRight, IconLogout, IconSettings } from '@tabler/icons-react'

import {
  Sidebar,
  SidebarContent,
  useSidebar,
} from '@/components/ui/sidebar'
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import { FramedIcon } from '@/components/ui/FramedIcon'
import { FramedIdentity } from '@/components/ui/FramedIdentity'
import { NAVIGATION_ITEMS as navigationCategories } from '@/lib/constants/navigation'
import { cn } from '@/lib/utils'

interface AppSidebarProps {
  className?: string
}

const isNavigationItemActive = (pathname: string, href: string) => (
  pathname === href || pathname.startsWith(`${href}/`)
)

function FramedTooltip({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>{children}</TooltipTrigger>
        <TooltipContent
          side="right"
          className="rounded-none border-2 border-[#0F1412] bg-[#FCFDF8] shadow-[4px_4px_0_0_#0F1412]"
        >
          <p className="text-xs font-black uppercase">{label}</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  )
}

export function AppSidebar({ className }: AppSidebarProps) {
  const pathname = usePathname()
  const { state } = useSidebar()
  const [expandedCategories, setExpandedCategories] = useState<string[]>([])
  const isCollapsed = state === 'collapsed'

  useEffect(() => {
    const activeCategoryIds = navigationCategories
      .filter((category) => category.items?.some((item) => isNavigationItemActive(pathname, item.href)))
      .map((category) => category.id)
    if (activeCategoryIds.length === 0) return
    setExpandedCategories((current) => [...new Set([...current, ...activeCategoryIds])])
  }, [pathname])

  return (
    <Sidebar
      aria-label="Primary navigation"
      variant="sidebar"
      collapsible="icon"
      className={cn('!border-r-[4px] border-[#0F1412] bg-[#FCFDF8]', className)}
    >
      <SidebarContent className="flex h-full flex-col overflow-visible bg-[#FCFDF8] p-0">
        <nav
          aria-label="Product navigation"
          className={cn(
            'flex-1 space-y-3 overflow-y-auto overflow-x-visible p-3',
            isCollapsed && 'space-y-2 p-0.5',
          )}
        >
          {navigationCategories.map((category) => {
            const CategoryIcon = category.icon!
            const hasActiveItem = category.items?.some((item) => isNavigationItemActive(pathname, item.href)) ?? false

            if (isCollapsed) {
              if (category.href && !category.items) {
                const isActive = isNavigationItemActive(pathname, category.href)
                return (
                  <FramedTooltip key={category.id} label={category.title}>
                    <FramedIcon
                      href={category.href}
                      icon={CategoryIcon}
                      label={category.title}
                      active={isActive}
                    />
                  </FramedTooltip>
                )
              }

              if (!category.items) return null
              return (
                <div key={category.id} className="space-y-2">
                  {category.items.map((item) => {
                    const ItemIcon = item.icon!
                    return (
                      <FramedTooltip key={item.href} label={item.title}>
                        <FramedIcon
                          href={item.href}
                          icon={ItemIcon}
                          label={item.title}
                          active={isNavigationItemActive(pathname, item.href)}
                        />
                      </FramedTooltip>
                    )
                  })}
                </div>
              )
            }

            if (category.href && !category.items) {
              return (
                <FramedIcon
                  key={category.id}
                  href={category.href}
                  icon={CategoryIcon}
                  label={category.title}
                  text={category.title}
                  active={isNavigationItemActive(pathname, category.href)}
                />
              )
            }

            const isOpen = expandedCategories.includes(category.id) || hasActiveItem
            return (
              <Collapsible
                key={category.id}
                open={isOpen}
                onOpenChange={(open) => {
                  if (hasActiveItem && !open) return
                  setExpandedCategories((current) => open
                    ? [...new Set([...current, category.id])]
                    : current.filter((id) => id !== category.id))
                }}
              >
                <CollapsibleTrigger asChild>
                  <FramedIcon
                    icon={CategoryIcon}
                    label={`Toggle ${category.title}`}
                    text={category.title}
                    active={hasActiveItem}
                    trailing={(
                      <IconChevronRight
                        aria-hidden="true"
                        className={cn(
                          'h-4 w-4 shrink-0 transition-transform duration-150 motion-reduce:transition-none',
                          isOpen && 'rotate-90',
                        )}
                      />
                    )}
                  />
                </CollapsibleTrigger>
                <CollapsibleContent className="ml-4 space-y-1 py-1 pl-2">
                  {category.items?.map((item) => {
                    const ItemIcon = item.icon!
                    return (
                      <FramedIcon
                        key={item.href}
                        href={item.href}
                        icon={ItemIcon}
                        label={item.title}
                        text={item.title}
                        active={isNavigationItemActive(pathname, item.href)}
                      />
                    )
                  })}
                </CollapsibleContent>
              </Collapsible>
            )
          })}
        </nav>

        <div className={cn('border-t-4 border-[#0F1412] bg-[#FCFDF8] p-3', isCollapsed && 'p-0.5')}>
          {isCollapsed ? (
            <div className="space-y-2">
              <FramedTooltip label="Settings">
                <FramedIcon href="/settings" icon={IconSettings} label="Settings" />
              </FramedTooltip>
              <FramedTooltip label="User Name">
                <FramedIdentity name="User Name" collapsed label="User Name profile" />
              </FramedTooltip>
            </div>
          ) : (
            <div className="space-y-3">
              <FramedIcon
                href="/settings"
                icon={IconSettings}
                label="Settings"
                text="Settings"
                active={isNavigationItemActive(pathname, '/settings')}
              />
              <FramedIdentity
                name="User Name"
                email="user@example.com"
                label="User Name profile"
              />
              <FramedIcon
                icon={IconLogout}
                label="Logout"
                text="Logout"
                className="hover:border-[#D83A2E] hover:bg-[#D83A2E] hover:text-white"
              />
            </div>
          )}
        </div>
      </SidebarContent>
    </Sidebar>
  )
}
