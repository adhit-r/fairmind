'use client'

import * as React from 'react'

export type Theme = 'light' | 'dark' | 'system'
export type ResolvedTheme = 'light' | 'dark'

export const THEME_STORAGE_KEY = 'fairmind:theme'

/**
 * Inline script string run before first paint (see root layout) so the saved
 * theme is applied without a flash. Mirrors applyTheme() below.
 */
export const THEME_INIT_SCRIPT = `(function(){try{var t=null;try{t=localStorage.getItem('${THEME_STORAGE_KEY}')}catch(e){}var d=t==='dark'||((t!=='light')&&window.matchMedia('(prefers-color-scheme: dark)').matches);var r=document.documentElement;r.classList.toggle('dark',d);r.style.colorScheme=d?'dark':'light';}catch(e){}})();`

interface ThemeContextValue {
  theme: Theme
  resolvedTheme: ResolvedTheme
  setTheme: (theme: Theme) => void
}

const ThemeContext = React.createContext<ThemeContextValue | undefined>(undefined)

function readStoredTheme(): Theme {
  try {
    const stored = window.localStorage.getItem(THEME_STORAGE_KEY)
    if (stored === 'light' || stored === 'dark' || stored === 'system') return stored
  } catch {
    // storage unavailable (private mode / blocked): fall through to system
  }
  return 'system'
}

function systemPrefersDark() {
  return typeof window !== 'undefined'
    && typeof window.matchMedia === 'function'
    && window.matchMedia('(prefers-color-scheme: dark)').matches
}

function applyTheme(resolved: ResolvedTheme) {
  const root = document.documentElement
  root.classList.toggle('dark', resolved === 'dark')
  root.style.colorScheme = resolved
}

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setThemeState] = React.useState<Theme>('system')
  const [resolvedTheme, setResolvedTheme] = React.useState<ResolvedTheme>('light')

  React.useEffect(() => {
    setThemeState(readStoredTheme())
  }, [])

  React.useEffect(() => {
    const resolve = () => {
      const next: ResolvedTheme = theme === 'system' ? (systemPrefersDark() ? 'dark' : 'light') : theme
      setResolvedTheme(next)
      applyTheme(next)
    }
    resolve()
    if (theme !== 'system' || typeof window.matchMedia !== 'function') return
    const media = window.matchMedia('(prefers-color-scheme: dark)')
    media.addEventListener('change', resolve)
    return () => media.removeEventListener('change', resolve)
  }, [theme])

  const setTheme = React.useCallback((next: Theme) => {
    setThemeState(next)
    try {
      window.localStorage.setItem(THEME_STORAGE_KEY, next)
    } catch {
      // ignore: theme still applies for this page view
    }
  }, [])

  const value = React.useMemo(() => ({ theme, resolvedTheme, setTheme }), [theme, resolvedTheme, setTheme])

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
}

export function useTheme(): ThemeContextValue {
  const context = React.useContext(ThemeContext)
  if (!context) throw new Error('useTheme must be used within a ThemeProvider')
  return context
}
