'use client'

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react'

type Theme = 'light' | 'dark'

interface ThemeContextType {
  theme: Theme
  toggleTheme: () => void
  setTheme: (theme: Theme) => void
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined)

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setTheme] = useState<Theme>('dark') // Default to dark theme

  useEffect(() => {
    // Check for saved theme preference or default to dark
    if (typeof window !== 'undefined') {
      const savedTheme = localStorage.getItem('theme') as Theme
      if (savedTheme) {
        setTheme(savedTheme)
      }
    }
  }, [])

  useEffect(() => {
    // Update document attributes when theme changes
    if (typeof window !== 'undefined') {
      document.documentElement.setAttribute('data-theme', theme)
      document.documentElement.classList.remove('light', 'dark')
      document.documentElement.classList.add(theme)
      localStorage.setItem('theme', theme)
    }
  }, [theme])

  const toggleTheme = () => {
    setTheme(theme === 'light' ? 'dark' : 'light')
  }

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  )
}

export function useTheme() {
  const context = useContext(ThemeContext)
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider')
  }
  return context
}
