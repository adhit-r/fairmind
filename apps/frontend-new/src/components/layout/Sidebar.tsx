'use client'

import React, { useState, useEffect } from 'react'
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

// Reusable styles
const itemBaseClass = "flex items-center gap-3 px-3 py-3 w-full border-2 border-transparent transition-all duration-200 ease-in-out rounded-none font-bold text-sm uppercase tracking-tight"
const itemHoverClass = "hover:border-black hover:bg-orange hover:shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] hover:-translate-y-[2px] hover:-translate-x-[2px]"
const itemActiveClass = "bg-black text-white border-black shadow-[4px_4px_0px_0px_rgba(255,107,53,1)] translate-x-[0px] translate-y-[0px]" // Orange shadow for active black item

export function AppSidebar({ className }: AppSidebarProps) {
  const pathname = usePathname()
  const { state } = useSidebar()
  const [expandedCategories, setExpandedCategories] = useState<string[]>(['overview'])
  const isCollapsed = state === 'collapsed'

  // Automatically expand categories that contain the active pathname
  useEffect(() => {
    const activeCategoryIds = navigationCategories
      .filter((category) => category.items.some((item) => pathname === item.href))
      .map((category) => category.id)

    if (activeCategoryIds.length > 0) {
      setExpandedCategories((prev) => {
        const newExpanded = [...new Set([...prev, ...activeCategoryIds])]
        return newExpanded
      })
    }
  }, [pathname])

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
      className={cn('!border-r-[4px] border-black bg-white', className)}
    >
      <SidebarContent className="flex flex-col h-full p-0 overflow-hidden">
        {/* Navigation */}
        <div className="flex-1 overflow-y-auto overflow-x-hidden p-4 space-y-4">
          {navigationCategories.map((category) => {
            const CategoryIcon = category.icon
            const isExpanded = expandedCategories.includes(category.id)
            const hasActiveItem = category.items.some((item) => pathname === item.href)

            // When collapsed, show all items as icons directly (no categories)
            if (isCollapsed) {
              return (
                <div key={category.id} className="space-y-2">
                  {category.items.map((item) => {
                    const ItemIcon = item.icon
                    const isActive = pathname === item.href
                    return (
                      <TooltipProvider key={item.href}>
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <Link
                              href={item.href}
                              className={cn(
                                "flex items-center justify-center w-10 h-10 border-2 transition-all rounded-none",
                                isActive 
                                  ? "bg-black text-white border-black shadow-[2px_2px_0px_0px_#FF6B35]" 
                                  : "bg-white text-black border-transparent hover:border-black hover:bg-orange hover:shadow-[2px_2px_0px_0px_#000]"
                              )}
                            >
                              <ItemIcon className="h-5 w-5" />
                            </Link>
                          </TooltipTrigger>
                          <TooltipContent side="right" className="border-2 border-black shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] bg-white rounded-none">
                            <p className="font-black text-xs uppercase">{item.title}</p>
                          </TooltipContent>
                        </Tooltip>
                      </TooltipProvider>
                    )
                  })}
                </div>
              )
            }

            // Expanded state - show full menu
            // Force open if category has active item
            const shouldBeOpen = isExpanded || hasActiveItem
            
            return (
              <Collapsible 
                key={category.id} 
                open={shouldBeOpen} 
                onOpenChange={(open) => {
                  // Prevent collapsing if there's an active item in this category
                  if (hasActiveItem && !open) {
                    return // Don't allow collapse when active item is present
                  }
                  toggleCategory(category.id)
                }}
              >
                <CollapsibleTrigger asChild>
                  <button
                    className={cn(
                      itemBaseClass,
                      "justify-between group mb-1",
                      hasActiveItem ? "border-black bg-white" : "hover:bg-transparent", // Category header style
                      !hasActiveItem && "hover:border-black hover:shadow-[2px_2px_0px_0px_rgba(0,0,0,1)]"
                    )}
                  >
                    <div className="flex items-center gap-3">
                      <CategoryIcon className="h-5 w-5" />
                      <span>{category.title}</span>
                    </div>
                    <IconChevronRight
                      className={cn(
                        'h-4 w-4 transition-transform duration-200 border-2 border-transparent rounded-full',
                        shouldBeOpen && 'rotate-90 bg-orange border-black'
                      )}
                    />
                  </button>
                </CollapsibleTrigger>
                <CollapsibleContent className="pl-4 space-y-1 border-l-2 border-black ml-4 my-1">
                  <SidebarMenu>
                    {category.items.map((item) => {
                      const ItemIcon = item.icon
                      const isActive = pathname === item.href

                      return (
                        <SidebarMenuItem key={item.href}>
                          <SidebarMenuButton
                            asChild
                            className={cn(
                              "h-auto py-2.5 px-3 w-full border-2 transition-all rounded-none font-bold text-xs uppercase tracking-wide",
                              isActive 
                                ? "bg-black text-white border-black shadow-[3px_3px_0px_0px_#FF6B35] hover:bg-black hover:text-white" 
                                : "bg-transparent border-transparent hover:bg-orange hover:border-black hover:shadow-[3px_3px_0px_0px_#000] hover:-translate-y-0.5"
                            )}
                          >
                            <Link 
                              href={item.href} 
                              className="flex items-center gap-3"
                              onClick={(e) => {
                                // Prevent event bubbling that might trigger collapse
                                e.stopPropagation()
                              }}
                            >
                              <ItemIcon className={cn("h-4 w-4", isActive ? "text-orange" : "text-current")} />
                              <span>{item.title}</span>
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
          "border-t-4 border-black p-4 bg-white",
          isCollapsed && "p-2"
        )}>
          {/* Settings Button */}
          {isCollapsed ? (
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Link
                    href="/settings"
                    className="flex items-center justify-center w-10 h-10 border-2 border-black bg-white hover:bg-orange hover:shadow-[2px_2px_0px_0px_#000] transition-all rounded-none mb-3 mx-auto"
                  >
                    <IconSettings className="h-5 w-5" />
                  </Link>
                </TooltipTrigger>
                <TooltipContent side="right" className="border-2 border-black shadow-brutal bg-white rounded-none">
                  <p className="font-black text-xs uppercase">Settings</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          ) : (
            <Link
              href="/settings"
              className="flex items-center gap-3 w-full px-3 py-3 border-2 border-black bg-white hover:bg-orange hover:shadow-[4px_4px_0px_0px_#000] hover:-translate-y-0.5 transition-all rounded-none mb-4 font-black text-sm uppercase"
            >
              <IconSettings className="h-5 w-5" />
              Settings
            </Link>
          )}

          {/* User Profile Card */}
          {isCollapsed ? (
             <TooltipProvider>
             <Tooltip>
               <TooltipTrigger asChild>
                 <div className="w-10 h-10 mx-auto border-2 border-black cursor-pointer hover:bg-orange transition-colors">
                   <Avatar className="h-full w-full rounded-none">
                     <AvatarImage src="https://ui.shadcn.com/avatars/02.png" alt="User" />
                     <AvatarFallback className="bg-orange text-black font-black">U</AvatarFallback>
                   </Avatar>
                 </div>
               </TooltipTrigger>
               <TooltipContent side="right" className="border-2 border-black shadow-brutal bg-white rounded-none">
                 <p className="font-black text-xs">User Name</p>
               </TooltipContent>
             </Tooltip>
           </TooltipProvider>
          ) : (
            <div className="border-2 border-black p-3 bg-orange shadow-[4px_4px_0px_0px_#000]">
              <div className="flex items-center gap-3 mb-3">
                <Avatar className="h-10 w-10 border-2 border-black rounded-none bg-white">
                  <AvatarImage src="https://ui.shadcn.com/avatars/02.png" alt="User" />
                  <AvatarFallback className="bg-black text-white font-black">U</AvatarFallback>
                </Avatar>
                <div className="min-w-0">
                  <p className="text-sm font-black uppercase truncate">User Name</p>
                  <p className="text-[10px] font-bold truncate opacity-80">user@example.com</p>
                </div>
              </div>
              <Button
                className="w-full h-8 border-2 border-black bg-white text-black hover:bg-red-500 hover:text-white hover:border-black transition-all rounded-none font-black text-xs uppercase shadow-[2px_2px_0px_0px_#000] hover:shadow-none hover:translate-x-[2px] hover:translate-y-[2px]"
              >
                <IconLogout className="h-3 w-3 mr-2" />
                Logout
              </Button>
            </div>
          )}
        </div>
      </SidebarContent>
    </Sidebar>
  )
}
