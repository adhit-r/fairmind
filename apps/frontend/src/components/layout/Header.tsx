'use client'

import React from 'react'
import { OrangeLogo } from '@/components/OrangeLogo'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { useSidebar } from '@/components/ui/sidebar'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { Input } from '@/components/ui/input'
import {
  IconSearch,
  IconBell,
  IconSettings,
  IconUser,
  IconLogout,
  IconMoon,
  IconSun,
  IconMenu2,
} from '@tabler/icons-react'

interface HeaderProps {
  onMenuToggle?: () => void
}

// Reusable "Brutal" Button Style
const brutalBtnClass = "h-11 w-11 border-2 border-black bg-white text-black shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-none transition-all rounded-none"
const brutalInputClass = "h-11 border-2 border-black bg-white text-black placeholder:text-gray-500 placeholder:font-bold shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] focus-visible:ring-0 focus-visible:translate-x-[2px] focus-visible:translate-y-[2px] focus-visible:shadow-none transition-all rounded-none text-sm font-bold"

export function Header({ onMenuToggle }: HeaderProps) {
  const [isDark, setIsDark] = React.useState(false)
  const { toggleSidebar } = useSidebar()

  return (
    <header className="sticky top-0 z-30 bg-white border-b-4 border-black w-full py-3">
      <div className="container mx-auto px-6 flex items-center justify-between gap-6">
        {/* Left: Sidebar Toggle + Logo */}
        <div className="flex items-center gap-4 flex-shrink-0">
          <Button
            variant="ghost"
            size="icon"
            onClick={toggleSidebar}
            className={brutalBtnClass}
            title="Toggle Sidebar"
          >
            <IconMenu2 className="h-6 w-6" />
          </Button>
          <OrangeLogo size="md" showText={true} />
        </div>

        {/* Center: Search */}
        <div className="hidden lg:flex items-center flex-1 max-w-2xl mx-auto">
          <div className="relative w-full group">
            <div className="absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none z-10">
               <IconSearch className="h-5 w-5 text-black" />
            </div>
            <Input
              type="search"
              placeholder="SEARCH..."
              className={`${brutalInputClass} pl-10 w-full uppercase tracking-wider`}
            />
          </div>
        </div>

        {/* Right: Actions */}
        <div className="flex items-center gap-4">
          {/* Mobile Search */}
          <Button
            variant="ghost"
            size="icon"
            className={`lg:hidden ${brutalBtnClass}`}
            title="Search"
          >
            <IconSearch className="h-5 w-5" />
          </Button>

          {/* Theme Toggle */}
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setIsDark(!isDark)}
            className={brutalBtnClass}
            title="Toggle Theme"
          >
            {isDark ? <IconSun className="h-5 w-5" /> : <IconMoon className="h-5 w-5" />}
          </Button>

          {/* Notifications */}
          <Button
            variant="ghost"
            size="icon"
            className={`${brutalBtnClass} relative`}
            title="Notifications"
          >
            <IconBell className="h-5 w-5" />
            <span className="absolute -top-2 -right-2 h-6 w-6 bg-orange border-2 border-black flex items-center justify-center text-xs font-black shadow-[2px_2px_0px_0px_rgba(0,0,0,1)]">
              3
            </span>
          </Button>

          {/* User Menu */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className={`${brutalBtnClass} p-0 overflow-hidden`}
              >
                <Avatar className="h-full w-full rounded-none border-none">
                  <AvatarImage src="https://ui.shadcn.com/avatars/02.png" alt="User" />
                  <AvatarFallback className="bg-orange text-black font-black">U</AvatarFallback>
                </Avatar>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-64 border-2 border-black shadow-[6px_6px_0px_0px_rgba(0,0,0,1)] bg-white rounded-none p-0 mt-2">
              <div className="px-5 py-4 bg-orange border-b-2 border-black">
                <p className="text-base font-black text-black uppercase tracking-tight">User Name</p>
                <p className="text-xs text-black font-bold opacity-80">user@example.com</p>
              </div>
              <div className="p-2 space-y-1">
                <DropdownMenuItem className="h-10 px-4 border-2 border-transparent focus:border-black focus:bg-gray-100 focus:shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] transition-all cursor-pointer font-bold text-sm rounded-none">
                  <IconUser className="mr-3 h-5 w-5" />
                  PROFILE
                </DropdownMenuItem>
                <DropdownMenuItem className="h-10 px-4 border-2 border-transparent focus:border-black focus:bg-gray-100 focus:shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] transition-all cursor-pointer font-bold text-sm rounded-none">
                  <IconSettings className="mr-3 h-5 w-5" />
                  SETTINGS
                </DropdownMenuItem>
                <DropdownMenuSeparator className="bg-black h-0.5 my-2" />
                <DropdownMenuItem className="h-10 px-4 border-2 border-transparent text-red-600 focus:text-red-600 focus:border-black focus:bg-red-50 focus:shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] transition-all cursor-pointer font-bold text-sm rounded-none">
                  <IconLogout className="mr-3 h-5 w-5" />
                  LOGOUT
                </DropdownMenuItem>
              </div>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </header>
  )
}
