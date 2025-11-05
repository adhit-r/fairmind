'use client';

import { createContext, useContext, useState, ReactNode } from 'react';
import { MantineProvider, MantineColorScheme } from '@mantine/core';
import { ModalsProvider } from '@mantine/modals';
import { Notifications } from '@mantine/notifications';
import { brutalistTheme } from '@/lib/brutalist-theme';

// Use the imported brutalist theme
const theme = brutalistTheme;

interface ThemeContextType {
  colorScheme: MantineColorScheme;
  toggleColorScheme: () => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

interface ThemeProviderProps {
  children: ReactNode;
}

export function GlassmorphicThemeProvider({ children }: ThemeProviderProps) {
  const [colorScheme, setColorScheme] = useState<MantineColorScheme>('light');

  const toggleColorScheme = () => {
    setColorScheme(colorScheme === 'light' ? 'dark' : 'light');
  };

  const contextValue: ThemeContextType = {
    colorScheme,
    toggleColorScheme,
  };

  // Brutalist background with high contrast
  const getBackground = () => {
    if (colorScheme === 'dark') {
      return '#000000';
    }
    return '#ffffff';
  };

  return (
    <ThemeContext.Provider value={contextValue}>
      <MantineProvider theme={theme} defaultColorScheme={colorScheme}>
        <ModalsProvider>
          <Notifications 
            position="top-right"
            zIndex={2077}
            containerWidth={420}
          />
          <div
            style={{
              minHeight: '100vh',
              background: getBackground(),
              transition: 'background 250ms ease',
            }}
          >
            {children}
          </div>
        </ModalsProvider>
      </MantineProvider>
    </ThemeContext.Provider>
  );
}

export function useGlassmorphicTheme() {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useGlassmorphicTheme must be used within a GlassmorphicThemeProvider');
  }
  return context;
}

// Semantic colors for Fairmind AI Governance
export const semanticColors = {
  bias: {
    low: '#15803d',      // Success green
    medium: '#b45309',   // Warning orange
    high: '#dc2626',     // Error red
    critical: '#b91c1c', // Darker error red
  },
  fairness: {
    excellent: '#15803d', // Success green
    good: '#16a34a',     // Medium green
    moderate: '#d97706', // Warning orange
    poor: '#dc2626',     // Error red
  },
  status: {
    success: { color: '#15803d', icon: '✓' },
    warning: { color: '#b45309', icon: '⚠' },
    error: { color: '#dc2626', icon: '✗' },
    info: { color: '#1a6bff', icon: 'ℹ' },
  }
};