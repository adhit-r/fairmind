import { createTheme, MantineThemeOverride, rem } from '@mantine/core';

// Clean glassmorphic theme without gradients or purple colors
export const theme: MantineThemeOverride = createTheme({
  primaryColor: 'neuralBlue',
  
  colors: {
    // Neural Blue - Primary brand color
    neuralBlue: [
      '#eff6ff', '#dbeafe', '#bfdbfe', '#93c5fd', '#60a5fa',
      '#3b82f6', '#2563eb', '#1d4ed8', '#1e40af', '#1e3a8a'
    ],
    
    // Steel Gray - Secondary color
    steelGray: [
      '#f8fafc', '#f1f5f9', '#e2e8f0', '#cbd5e1', '#94a3b8',
      '#64748b', '#475569', '#334155', '#1e293b', '#0f172a'
    ],
    
    // Fairness Green - Success states
    fairnessGreen: [
      '#f0fdf4', '#dcfce7', '#bbf7d0', '#86efac', '#4ade80',
      '#22c55e', '#16a34a', '#15803d', '#166534', '#14532d'
    ],
    
    // Alert Amber - Warning states
    alertAmber: [
      '#fffbeb', '#fef3c7', '#fde68a', '#fcd34d', '#fbbf24',
      '#f59e0b', '#d97706', '#b45309', '#92400e', '#78350f'
    ],
    
    // Critical Red - Error states
    criticalRed: [
      '#fef2f2', '#fee2e2', '#fecaca', '#fca5a5', '#f87171',
      '#ef4444', '#dc2626', '#b91c1c', '#991b1b', '#7f1d1d'
    ],
  },

  fontFamily: '-apple-system, BlinkMacSystemFont, "SF Pro Display", Inter, "Segoe UI", Roboto, sans-serif',
  
  headings: {
    fontFamily: '-apple-system, BlinkMacSystemFont, "SF Pro Display", Inter, "Segoe UI", Roboto, sans-serif',
    fontWeight: '700',
    sizes: {
      h1: { fontSize: rem(48), lineHeight: '1.2', fontWeight: '800' },
      h2: { fontSize: rem(36), lineHeight: '1.3', fontWeight: '700' },
      h3: { fontSize: rem(30), lineHeight: '1.4', fontWeight: '600' },
      h4: { fontSize: rem(24), lineHeight: '1.4', fontWeight: '600' },
      h5: { fontSize: rem(20), lineHeight: '1.5', fontWeight: '500' },
      h6: { fontSize: rem(16), lineHeight: '1.5', fontWeight: '500' },
    },
  },

  radius: {
    xs: rem(4),
    sm: rem(6),
    md: rem(12),
    lg: rem(16),
    xl: rem(24),
  },

  spacing: {
    xs: rem(8),
    sm: rem(12),
    md: rem(16),
    lg: rem(24),
    xl: rem(32),
  },

  shadows: {
    xs: '0 2px 8px rgba(0, 0, 0, 0.04)',
    sm: '0 4px 16px rgba(0, 0, 0, 0.06)',
    md: '0 8px 32px rgba(0, 0, 0, 0.08)',
    lg: '0 16px 64px rgba(0, 0, 0, 0.1)',
    xl: '0 32px 128px rgba(0, 0, 0, 0.12)',
  },

  components: {
    Card: {
      defaultProps: {
        radius: 'xl',
        p: 'xl',
      },
      styles: {
        root: {
          background: 'rgba(255, 255, 255, 0.8)',
          backdropFilter: 'blur(20px)',
          border: '1px solid rgba(255, 255, 255, 0.2)',
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
          transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
          '&:hover': {
            transform: 'translateY(-4px)',
            boxShadow: '0 16px 64px rgba(0, 0, 0, 0.15)',
            background: 'rgba(255, 255, 255, 0.9)',
          },
        },
      },
    },

    Paper: {
      defaultProps: {
        radius: 'lg',
        p: 'lg',
      },
      styles: {
        root: {
          background: 'rgba(255, 255, 255, 0.7)',
          backdropFilter: 'blur(16px)',
          border: '1px solid rgba(255, 255, 255, 0.2)',
          boxShadow: '0 4px 16px rgba(0, 0, 0, 0.08)',
        },
      },
    },

    Button: {
      defaultProps: {
        radius: 'md',
      },
      styles: {
        root: {
          fontWeight: '600',
          transition: 'all 0.25s cubic-bezier(0.4, 0, 0.2, 1)',
        },
      },
    },

    TextInput: {
      styles: {
        input: {
          background: 'rgba(255, 255, 255, 0.6)',
          backdropFilter: 'blur(12px)',
          border: '1px solid rgba(255, 255, 255, 0.3)',
          '&:focus': {
            background: 'rgba(255, 255, 255, 0.8)',
            borderColor: 'rgba(59, 130, 246, 0.4)',
          },
        },
      },
    },

    Modal: {
      styles: {
        content: {
          background: 'rgba(255, 255, 255, 0.95)',
          backdropFilter: 'blur(40px)',
          border: '1px solid rgba(255, 255, 255, 0.3)',
        },
        overlay: {
          background: 'rgba(0, 0, 0, 0.4)',
          backdropFilter: 'blur(8px)',
        },
      },
    },
  },

  other: {
    backgrounds: {
      primary: 'rgba(248, 250, 252, 0.95)',
      secondary: 'rgba(241, 245, 249, 0.90)',
      accent: 'rgba(239, 246, 255, 0.85)',
    },
    
    glassmorphic: {
      light: {
        background: 'rgba(255, 255, 255, 0.6)',
        backdropFilter: 'blur(12px)',
        border: '1px solid rgba(255, 255, 255, 0.2)',
      },
      medium: {
        background: 'rgba(255, 255, 255, 0.8)',
        backdropFilter: 'blur(20px)',
        border: '1px solid rgba(255, 255, 255, 0.2)',
      },
      strong: {
        background: 'rgba(255, 255, 255, 0.95)',
        backdropFilter: 'blur(40px)',
        border: '1px solid rgba(255, 255, 255, 0.3)',
      },
    },
  },
});

export const semanticColors = {
  bias: {
    low: '#22c55e',
    medium: '#f59e0b', 
    high: '#ef4444',
    critical: '#dc2626',
  },
  fairness: {
    excellent: '#10b981',
    good: '#22c55e',
    moderate: '#f59e0b',
    poor: '#ef4444',
  },
  compliance: {
    compliant: '#22c55e',
    warning: '#f59e0b',
    violation: '#ef4444',
  },
};

export default theme;