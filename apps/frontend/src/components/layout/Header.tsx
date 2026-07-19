'use client'

import React from 'react'
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
import { Input } from '@/components/ui/input'
import { FramedIcon } from '@/components/ui/FramedIcon'
import { FramedIdentity } from '@/components/ui/FramedIdentity'
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

const brutalInputClass = "h-11 border-2 border-black bg-white text-black placeholder:text-gray-500 placeholder:font-bold shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] focus-visible:ring-0 focus-visible:translate-x-[2px] focus-visible:translate-y-[2px] focus-visible:shadow-none transition-all rounded-none text-sm font-bold"

export function Header({ onMenuToggle }: HeaderProps) {
  const [isDark, setIsDark] = React.useState(false)
  const [isSearchFocused, setIsSearchFocused] = React.useState(false)
  const { toggleSidebar } = useSidebar()

  const handleNavigationToggle = () => {
    onMenuToggle?.()
    toggleSidebar()
  }

  return (
    <header className="sticky top-0 z-30 bg-white border-b-4 border-black w-full py-2 sm:py-3">
      <div className="container mx-auto px-3 sm:px-4 md:px-6 flex items-center justify-between gap-2 sm:gap-4 md:gap-6">
        {/* Left: Sidebar Toggle + Logo */}
        <div className="flex items-center gap-2 sm:gap-4 flex-shrink-0">
          <FramedIcon
            icon={IconMenu2}
            label="Toggle navigation"
            onClick={handleNavigationToggle}
            title="Toggle navigation"
          />
          <div className="hidden sm:block">
            <OrangeLogo size="md" showText={true} />
          </div>
          <div className="block sm:hidden">
            <OrangeLogo size="sm" showText={false} />
          </div>
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
              onFocus={() => setIsSearchFocused(true)}
              onBlur={() => setIsSearchFocused(false)}
              style={isSearchFocused ? { outline: '2px solid #0F1412', outlineOffset: 2 } : undefined}
              className={`${brutalInputClass} pl-10 w-full uppercase tracking-wider`}
            />
          </div>
        </div>

        {/* Right: Actions */}
        <div className="flex items-center gap-2 sm:gap-3 md:gap-4">
          {/* Mobile Search */}
          <FramedIcon
            icon={IconSearch}
            label="Search"
            className="hidden sm:inline-flex lg:hidden"
            title="Search"
          />

          {/* Theme Toggle */}
          <FramedIcon
            icon={isDark ? IconSun : IconMoon}
            label={isDark ? 'Use light theme' : 'Use dark theme'}
            onClick={() => setIsDark(!isDark)}
            aria-pressed={isDark}
            className="hidden md:inline-flex"
          />

          {/* Notifications */}
          <FramedIcon
            icon={IconBell}
            label="Notifications"
            className="hidden sm:inline-flex"
            title="Notifications"
          />

          {/* User Menu */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <FramedIdentity
                name="User Name"
                collapsed
                label="Open user menu for User Name"
              />
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-64 border-2 border-black shadow-[6px_6px_0px_0px_rgba(0,0,0,1)] bg-white rounded-none p-0 mt-2">
              <div className="px-5 py-4 bg-orange border-b-2 border-black">
                <p className="text-base font-black text-black uppercase tracking-tight">User Name</p>
                <p className="text-xs text-black font-bold opacity-80">user@example.com</p>
              </div>
              <div className="p-2 space-y-1">
                <DropdownMenuItem className="min-h-11 px-4 border-2 border-transparent focus:border-black focus:bg-gray-100 focus:shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] transition-all cursor-pointer font-bold text-sm rounded-none">
                  <IconUser className="mr-3 h-5 w-5" />
                  PROFILE
                </DropdownMenuItem>
                <DropdownMenuItem className="min-h-11 px-4 border-2 border-transparent focus:border-black focus:bg-gray-100 focus:shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] transition-all cursor-pointer font-bold text-sm rounded-none">
                  <IconSettings className="mr-3 h-5 w-5" />
                  SETTINGS
                </DropdownMenuItem>
                <DropdownMenuSeparator className="bg-black h-0.5 my-2" />
                <DropdownMenuItem className="min-h-11 px-4 border-2 border-transparent text-red-600 focus:text-red-600 focus:border-black focus:bg-red-50 focus:shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] transition-all cursor-pointer font-bold text-sm rounded-none">
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
