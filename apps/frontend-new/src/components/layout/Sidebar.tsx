'use client'

import React, { useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
  Sidebar,
  SidebarContent,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
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
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { IconSettings, IconChevronRight, IconLogout } from '@tabler/icons-react'
import { navigationCategories } from '@/lib/constants/navigation'
import { cn } from '@/lib/utils'
import { useSidebar } from '@/components/ui/sidebar'

interface AppSidebarProps {
  className?: string
}

export function AppSidebar({ className }: AppSidebarProps) {
  const pathname = usePathname()
  const { state } = useSidebar()
  const [expandedCategories, setExpandedCategories] = useState<string[]>(['overview'])
  const isCollapsed = state === 'collapsed'

  const toggleCategory = (categoryId: string) => {
    setExpandedCategories((prev) =>
      prev.includes(categoryId)
        ? prev.filter((id) => id !== categoryId)
        : [...prev, categoryId]
    )
  }

  return (
    <Sidebar 
      variant="sidebar"
      collapsible="icon"
      className={cn('border-r-4 border-black bg-white', className)}
    >
      <SidebarContent className="flex flex-col h-full p-0 overflow-hidden">
        {/* Navigation - no top padding needed since sidebar starts below header */}
        <div className="flex-1 overflow-y-auto overflow-x-hidden p-3 space-y-1">
          {navigationCategories.map((category) => {
            const CategoryIcon = category.icon
            const isExpanded = expandedCategories.includes(category.id)
            const hasActiveItem = category.items.some((item) => pathname === item.href)

            // When collapsed, show all items as icons directly (no categories)
            if (isCollapsed) {
              return (
                <div key={category.id} className="space-y-1">
                  {category.items.map((item) => {
                    const ItemIcon = item.icon
                    const isActive = pathname === item.href
                    return (
                      <TooltipProvider key={item.href}>
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <Button
                              variant="noShadow"
                              size="icon"
                              asChild
                              className={cn(
                                'w-10 h-10 border-2 border-transparent hover:border-black transition-all rounded-base',
                                isActive && 'border-black shadow-brutal bg-orange'
                              )}
                            >
                              <Link href={item.href}>
                                <ItemIcon className="h-5 w-5" />
                              </Link>
                            </Button>
                          </TooltipTrigger>
                          <TooltipContent side="right" className="border-2 border-black shadow-brutal bg-white">
                            <p className="font-black text-xs">{item.title}</p>
                          </TooltipContent>
                        </Tooltip>
                      </TooltipProvider>
                    )
                  })}
                </div>
              )
            }

            // Expanded state - show full menu
            return (
              <Collapsible key={category.id} open={isExpanded} onOpenChange={() => toggleCategory(category.id)}>
                <CollapsibleTrigger asChild>
                  <button
                    className={cn(
                      'w-full flex items-center justify-between px-3 py-2.5 border-2 border-transparent hover:border-black transition-all rounded-base',
                      'font-black uppercase text-xs',
                      hasActiveItem && 'border-black bg-orange shadow-brutal',
                      !hasActiveItem && 'hover:bg-orange hover:shadow-brutal'
                    )}
                  >
                    <div className="flex items-center gap-2.5 flex-1 min-w-0">
                      <CategoryIcon className="h-4 w-4 flex-shrink-0" />
                      <span className="truncate">{category.title}</span>
                    </div>
                    <IconChevronRight
                      className={cn(
                        'h-4 w-4 flex-shrink-0 transition-transform',
                        isExpanded && 'rotate-90'
                      )}
                    />
                  </button>
                </CollapsibleTrigger>
                <CollapsibleContent className="pt-1 pl-2 space-y-0.5">
                  <SidebarMenu>
                    {category.items.map((item) => {
                      const ItemIcon = item.icon
                      const isActive = pathname === item.href

                      return (
                        <SidebarMenuItem key={item.href}>
                          <SidebarMenuButton
                            asChild
                            isActive={isActive}
                            className={cn(
                              'px-3 py-2 border-2 border-transparent transition-all rounded-base font-bold text-xs',
                              isActive && 'border-black shadow-brutal bg-orange',
                              !isActive && 'hover:border-black hover:shadow-brutal hover:bg-orange'
                            )}
                          >
                            <Link href={item.href} className="flex items-center gap-2 min-w-0">
                              <ItemIcon className="h-3.5 w-3.5 flex-shrink-0" />
                              <span className="truncate">{item.title}</span>
                            </Link>
                          </SidebarMenuButton>
                        </SidebarMenuItem>
                      )
                    })}
                  </SidebarMenu>
                </CollapsibleContent>
              </Collapsible>
            )
          })}
        </div>

        {/* Bottom: Settings & User */}
        <div className={cn(
          "border-t-4 border-black p-3 space-y-3 bg-gray-50",
          isCollapsed && "p-2 space-y-2"
        )}>
          {/* Settings Button */}
          {isCollapsed ? (
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="default"
                    size="icon"
                    className="w-10 h-10 border-2 border-black shadow-brutal hover:shadow-brutal-lg font-black rounded-base"
                    asChild
                  >
                    <Link href="/settings">
                      <IconSettings className="h-5 w-5" />
                    </Link>
                  </Button>
                </TooltipTrigger>
                <TooltipContent side="right" className="border-2 border-black shadow-brutal">
                  <p className="font-black text-xs">Settings</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          ) : (
            <Button
              variant="default"
              className="w-full justify-start border-2 border-black shadow-brutal hover:shadow-brutal-lg font-black text-xs uppercase h-9 rounded-base"
              asChild
            >
              <Link href="/settings" className="flex items-center gap-2">
                <IconSettings className="h-3.5 w-3.5" />
                Settings
              </Link>
            </Button>
          )}

          {!isCollapsed && <Separator className="bg-black h-0.5" />}

          {/* User Profile Card */}
          {isCollapsed ? (
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Avatar className="h-10 w-10 border-4 border-black shadow-brutal mx-auto cursor-pointer">
                    <AvatarImage src="https://ui.shadcn.com/avatars/02.png" alt="User" />
                    <AvatarFallback className="bg-orange text-black font-black text-sm">U</AvatarFallback>
                  </Avatar>
                </TooltipTrigger>
                <TooltipContent side="right" className="border-2 border-black shadow-brutal">
                  <div>
                    <p className="font-black text-xs">User Name</p>
                    <p className="text-[10px] text-gray-600">user@example.com</p>
                  </div>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          ) : (
            <>
              <div className="p-2.5 border-4 border-black bg-white shadow-brutal">
                <div className="flex items-start gap-2.5">
                  <Avatar className="h-10 w-10 border-4 border-black shadow-brutal flex-shrink-0">
                    <AvatarImage src="https://ui.shadcn.com/avatars/02.png" alt="User" />
                    <AvatarFallback className="bg-orange text-black font-black text-sm">U</AvatarFallback>
                  </Avatar>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-black uppercase truncate">User Name</p>
                    <p className="text-[10px] text-gray-600 truncate">user@example.com</p>
                    <Badge className="mt-1.5 border-2 border-black bg-orange text-black text-[10px] font-black px-1.5 py-0 h-4 leading-none">
                      Admin
                    </Badge>
                  </div>
                </div>
              </div>

              {/* Logout Button */}
              <Button
                variant="noShadow"
                className="w-full justify-start border-2 border-red-600 hover:bg-red-50 hover:shadow-brutal transition-all font-black text-xs uppercase h-9 text-red-600 rounded-base"
              >
                <IconLogout className="h-3.5 w-3.5" />
                Logout
              </Button>
            </>
          )}
        </div>
      </SidebarContent>
    </Sidebar>
  )
}
