'use client'

import { IconDeviceDesktop, IconMoon, IconSun } from '@tabler/icons-react'

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Button } from '@/components/ui/button'
import { useTheme, type Theme } from './ThemeProvider'

export function ThemeToggle({ className }: { className?: string }) {
  const { theme, resolvedTheme, setTheme } = useTheme()
  const Icon = resolvedTheme === 'dark' ? IconMoon : IconSun

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon" className={className} aria-label={`Theme: ${theme}. Change theme`}>
          <Icon aria-hidden="true" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-40">
        <DropdownMenuRadioGroup value={theme} onValueChange={(value) => setTheme(value as Theme)}>
          <DropdownMenuRadioItem value="light"><IconSun className="mr-2 h-4 w-4" aria-hidden="true" />Light</DropdownMenuRadioItem>
          <DropdownMenuRadioItem value="dark"><IconMoon className="mr-2 h-4 w-4" aria-hidden="true" />Dark</DropdownMenuRadioItem>
          <DropdownMenuRadioItem value="system"><IconDeviceDesktop className="mr-2 h-4 w-4" aria-hidden="true" />System</DropdownMenuRadioItem>
        </DropdownMenuRadioGroup>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
