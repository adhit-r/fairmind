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

export function Header({ onMenuToggle }: HeaderProps) {
  const [isDark, setIsDark] = React.useState(false)
  const { toggleSidebar } = useSidebar()

  return (
    <header className="sticky top-0 z-30 bg-white border-b-4 border-black shadow-brutal w-full">
      <div className="h-16 flex items-center justify-between px-6 gap-6">
        {/* Left: Sidebar Toggle + Logo */}
        <div className="flex items-center gap-3 flex-shrink-0">
          <Button
            variant="noShadow"
            size="icon"
            onClick={toggleSidebar}
            className="border-2 border-black hover:bg-orange hover:shadow-brutal transition-all h-10 w-10"
            title="Toggle Sidebar"
          >
            <IconMenu2 className="h-5 w-5" />
          </Button>
          <OrangeLogo size="md" showText={true} />
        </div>

        {/* Center: Search */}
        <div className="hidden lg:flex items-center flex-1 max-w-xl">
          <div className="relative w-full">
            <IconSearch className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-600 pointer-events-none" />
            <Input
              type="search"
              placeholder="Search..."
              className="pl-10 h-10 border-4 border-black shadow-brutal focus:shadow-brutal-lg font-bold text-sm rounded-base"
            />
          </div>
        </div>

        {/* Right: Actions */}
        <div className="flex items-center gap-2">
          {/* Mobile Search */}
          <Button
            variant="noShadow"
            size="icon"
            className="lg:hidden border-2 border-black h-10 w-10"
            title="Search"
          >
            <IconSearch className="h-4 w-4" />
          </Button>

          {/* Theme Toggle */}
          <Button
            variant="noShadow"
            size="icon"
            onClick={() => setIsDark(!isDark)}
            className="border-2 border-black h-10 w-10"
            title="Toggle Theme"
          >
            {isDark ? <IconSun className="h-4 w-4" /> : <IconMoon className="h-4 w-4" />}
          </Button>

          {/* Notifications */}
          <Button
            variant="noShadow"
            size="icon"
            className="border-2 border-black h-10 w-10 relative"
            title="Notifications"
          >
            <IconBell className="h-4 w-4" />
            <span className="absolute -top-1 -right-1 h-5 w-5 bg-orange border-2 border-black rounded-base flex items-center justify-center text-[10px] font-black shadow-brutal">
              3
            </span>
          </Button>

          {/* User Menu */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="noShadow"
                size="icon"
                className="border-2 border-black h-10 w-10 p-0"
              >
                <Avatar className="h-10 w-10 border-2 border-black">
                  <AvatarImage src="https://ui.shadcn.com/avatars/02.png" alt="User" />
                  <AvatarFallback className="bg-orange text-black font-black">U</AvatarFallback>
                </Avatar>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56 border-4 border-black shadow-brutal-lg bg-white">
              <DropdownMenuLabel className="px-3 py-2.5 font-black uppercase text-xs">
                <div className="flex items-center gap-2">
                  <Avatar className="h-8 w-8 border-2 border-black">
                    <AvatarImage src="https://ui.shadcn.com/avatars/02.png" alt="User" />
                    <AvatarFallback className="bg-orange text-black font-black">U</AvatarFallback>
                  </Avatar>
                  <div className="flex-1">
                    <p className="text-xs font-black">User Name</p>
                    <p className="text-[10px] text-gray-600">user@example.com
                    </p>
                  </div>
                </div>
              </DropdownMenuLabel>
              <DropdownMenuSeparator className="bg-black h-0.5 my-2" />
              <DropdownMenuItem className="px-3 py-2.5 border-2 border-transparent hover:border-black hover:bg-orange hover:shadow-brutal transition-all font-black text-xs cursor-pointer">
                <IconUser className="mr-2 h-4 w-4" />
                Profile
              </DropdownMenuItem>
              <DropdownMenuItem className="px-3 py-2.5 border-2 border-transparent hover:border-black hover:bg-orange hover:shadow-brutal transition-all font-black text-xs cursor-pointer">
                <IconSettings className="mr-2 h-4 w-4" />
                Settings
              </DropdownMenuItem>
              <DropdownMenuSeparator className="bg-black h-0.5 my-2" />
              <DropdownMenuItem className="px-3 py-2.5 border-2 border-transparent hover:border-red-500 hover:bg-red-50 hover:shadow-brutal transition-all font-black text-xs text-red-600 cursor-pointer">
                <IconLogout className="mr-2 h-4 w-4" />
                Logout
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </header>
  )
}
