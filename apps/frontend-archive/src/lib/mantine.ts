import { createTheme, MantineThemeOverride, rem } from '@mantine/core';

// CSS Custom Properties for glassmorphic effects
const glassmorphicCSSVars = `
  :root {
    /* Glassmorphic backgrounds */
    --glass-light: rgba(255, 255, 255, 0.6);
    --glass-medium: rgba(255, 255, 255, 0.8);
    --glass-strong: rgba(255, 255, 255, 0.95);
    --glass-dark-light: rgba(0, 0, 0, 0.1);
    --glass-dark-medium: rgba(0, 0, 0, 0.2);
    --glass-dark-strong: rgba(0, 0, 0, 0.3);
    
    /* Blur effects */
    --blur-light: blur(12px);
    --blur-medium: blur(20px);
    --blur-strong: blur(40px);
    
    /* Borders */
    --border-light: 1px solid rgba(255, 255, 255, 0.2);
    --border-medium: 1px solid rgba(255, 255, 255, 0.3);
    --border-strong: 1px solid rgba(255, 255, 255, 0.4);
    
    /* Shadows */
    --shadow-light: 0 4px 16px rgba(0, 0, 0, 0.06);
    --shadow-medium: 0 8px 32px rgba(0, 0, 0, 0.1);
    --shadow-strong: 0 16px 64px rgba(0, 0, 0, 0.15);
    
    /* Semantic colors for AI governance */
    --bias-low: #22c55e;
    --bias-medium: #f59e0b;
    --bias-high: #ef4444;
    --bias-critical: #dc2626;
    
    --compliance-compliant: #22c55e;
    --compliance-warning: #f59e0b;
    --compliance-violation: #ef4444;
    
    --fairness-excellent: #10b981;
    --fairness-good: #22c55e;
    --fairness-moderate: #f59e0b;
    --fairness-poor: #ef4444;
    
    /* Animation presets */
    --transition-smooth: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    --transition-spring: all 0.3s cubic-bezier(0.68, -0.55, 0.265, 1.55);
    --transition-fast: all 0.15s cubic-bezier(0.4, 0, 0.2, 1);
  }
  
  [data-mantine-color-scheme="dark"] {
    --glass-light: rgba(0, 0, 0, 0.6);
    --glass-medium: rgba(0, 0, 0, 0.8);
    --glass-strong: rgba(0, 0, 0, 0.95);
    --border-light: 1px solid rgba(255, 255, 255, 0.1);
    --border-medium: 1px solid rgba(255, 255, 255, 0.2);
    --border-strong: 1px solid rgba(255, 255, 255, 0.3);
  }
`;

// Inject CSS custom properties
if (typeof document !== 'undefined') {
  const style = document.createElement('style');
  style.textContent = glassmorphicCSSVars;
  document.head.appendChild(style);
}

// Apple Taohe / iOS 26 inspired glassmorphic theme for Mantine
export const theme: MantineThemeOverride = createTheme({
  // Color scheme
  primaryColor: 'neuralBlue',
  
  // Custom color palette inspired by Apple's design language
  colors: {
    // Neural Blue - Primary brand color
    neuralBlue: [
      '#eff6ff', // 50
      '#dbeafe', // 100
      '#bfdbfe', // 200
      '#93c5fd', // 300
      '#60a5fa', // 400
      '#3b82f6', // 500 - primary
      '#2563eb', // 600
      '#1d4ed8', // 700
      '#1e40af', // 800
      '#1e3a8a', // 900
    ],
    
    // Steel Gray - Secondary color
    steelGray: [
      '#f8fafc', // 50
      '#f1f5f9', // 100
      '#e2e8f0', // 200
      '#cbd5e1', // 300
      '#94a3b8', // 400
      '#64748b', // 500
      '#475569', // 600
      '#334155', // 700
      '#1e293b', // 800
      '#0f172a', // 900
    ],
    
    // Fairness Green - Success states
    fairnessGreen: [
      '#f0fdf4', // 50
      '#dcfce7', // 100
      '#bbf7d0', // 200
      '#86efac', // 300
      '#4ade80', // 400
      '#22c55e', // 500
      '#16a34a', // 600
      '#15803d', // 700
      '#166534', // 800
      '#14532d', // 900
    ],
    
    // Alert Amber - Warning states
    alertAmber: [
      '#fffbeb', // 50
      '#fef3c7', // 100
      '#fde68a', // 200
      '#fcd34d', // 300
      '#fbbf24', // 400
      '#f59e0b', // 500
      '#d97706', // 600
      '#b45309', // 700
      '#92400e', // 800
      '#78350f', // 900
    ],
    
    // Critical Red - Error states
    criticalRed: [
      '#fef2f2', // 50
      '#fee2e2', // 100
      '#fecaca', // 200
      '#fca5a5', // 300
      '#f87171', // 400
      '#ef4444', // 500
      '#dc2626', // 600
      '#b91c1c', // 700
      '#991b1b', // 800
      '#7f1d1d', // 900
    ],
  },

  // Typography system inspired by SF Pro
  fontFamily: '-apple-system, BlinkMacSystemFont, "SF Pro Display", Inter, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
  fontFamilyMonospace: '"SF Mono", Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace',
  
  headings: {
    fontFamily: '-apple-system, BlinkMacSystemFont, "SF Pro Display", Inter, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
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

  // Modern radius system
  radius: {
    xs: rem(4),
    sm: rem(6),
    md: rem(12),
    lg: rem(16),
    xl: rem(24),
  },

  // Spacing system
  spacing: {
    xs: rem(8),
    sm: rem(12),
    md: rem(16),
    lg: rem(24),
    xl: rem(32),
  },

  // Shadows with glassmorphic effect
  shadows: {
    xs: '0 2px 8px rgba(0, 0, 0, 0.04), 0 1px 3px rgba(0, 0, 0, 0.06)',
    sm: '0 4px 16px rgba(0, 0, 0, 0.06), 0 2px 8px rgba(0, 0, 0, 0.08)',
    md: '0 8px 32px rgba(0, 0, 0, 0.08), 0 4px 16px rgba(0, 0, 0, 0.1)',
    lg: '0 16px 64px rgba(0, 0, 0, 0.1), 0 8px 32px rgba(0, 0, 0, 0.12)',
    xl: '0 32px 128px rgba(0, 0, 0, 0.12), 0 16px 64px rgba(0, 0, 0, 0.15)',
  },

  // Component overrides with glassmorphic styling
  components: {
    Card: {
      defaultProps: {
        radius: 'xl',
        p: 'xl',
      },
      styles: {
        root: {
          background: 'var(--glass-medium)',
          backdropFilter: 'var(--blur-medium)',
          border: 'var(--border-medium)',
          boxShadow: 'var(--shadow-medium)',
          transition: 'var(--transition-smooth)',
          '&:hover': {
            transform: 'translateY(-4px)',
            boxShadow: 'var(--shadow-strong)',
            background: 'var(--glass-strong)',
          },
          '&[data-interactive="true"]': {
            cursor: 'pointer',
            '&:active': {
              transform: 'translateY(-2px)',
            },
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
          background: 'var(--glass-light)',
          backdropFilter: 'var(--blur-light)',
          border: 'var(--border-light)',
          boxShadow: 'var(--shadow-light)',
          transition: 'var(--transition-smooth)',
        },
      },
    },

    Button: {
      defaultProps: {
        radius: 'md',
      },
      styles: () => ({
        root: {
          transition: 'var(--transition-smooth)',
          fontWeight: 600,
          '&[data-variant="light"]': {
            background: 'rgba(59, 130, 246, 0.1)',
            backdropFilter: 'var(--blur-light)',
            border: '1px solid rgba(59, 130, 246, 0.2)',
            color: '#2563eb',
            '&:hover': {
              background: 'rgba(59, 130, 246, 0.15)',
              transform: 'translateY(-2px)',
              boxShadow: '0 8px 24px rgba(59, 130, 246, 0.25)',
            },
            '&:active': {
              transform: 'translateY(0)',
            },
          },
          '&[data-variant="outline"]': {
            background: 'transparent',
            border: '1px solid rgba(59, 130, 246, 0.3)',
            color: '#2563eb',
            '&:hover': {
              background: 'rgba(59, 130, 246, 0.05)',
              transform: 'translateY(-2px)',
              boxShadow: '0 8px 24px rgba(59, 130, 246, 0.15)',
            },
            '&:active': {
              transform: 'translateY(0)',
            },
          },
          '&[data-variant="filled"]': {
            background: 'linear-gradient(135deg, #3b82f6, #2563eb)',
            border: 'none',
            color: 'white',
            '&:hover': {
              background: 'linear-gradient(135deg, #2563eb, #1d4ed8)',
              transform: 'translateY(-2px)',
              boxShadow: 'var(--shadow-medium)',
            },
            '&:active': {
              transform: 'translateY(0)',
            },
          },
        },
      }),
    },

    TextInput: {
      defaultProps: {
        radius: 'md',
      },
      styles: {
        input: {
          background: 'var(--glass-light)',
          backdropFilter: 'var(--blur-light)',
          border: 'var(--border-light)',
          transition: 'var(--transition-smooth)',
          '&:focus': {
            background: 'var(--glass-medium)',
            borderColor: 'rgba(59, 130, 246, 0.4)',
            boxShadow: '0 0 0 2px rgba(59, 130, 246, 0.2)',
          },
          '&::placeholder': {
            color: 'rgba(100, 116, 139, 0.7)',
          },
        },
      },
    },

    Select: {
      defaultProps: {
        radius: 'md',
      },
      styles: {
        input: {
          background: 'rgba(255, 255, 255, 0.6)',
          backdropFilter: 'blur(12px)',
          border: '1px solid rgba(255, 255, 255, 0.3)',
          transition: 'all 0.25s cubic-bezier(0.4, 0, 0.2, 1)',
          '&:focus': {
            background: 'rgba(255, 255, 255, 0.8)',
            borderColor: 'rgba(59, 130, 246, 0.4)',
            boxShadow: '0 0 0 2px rgba(59, 130, 246, 0.2)',
          },
        },
        dropdown: {
          background: 'rgba(255, 255, 255, 0.9)',
          backdropFilter: 'blur(24px)',
          border: '1px solid rgba(255, 255, 255, 0.3)',
          boxShadow: '0 16px 64px rgba(0, 0, 0, 0.15)',
        },
      },
    },

    Modal: {
      styles: {
        content: {
          background: 'rgba(255, 255, 255, 0.95)',
          backdropFilter: 'blur(40px)',
          border: '1px solid rgba(255, 255, 255, 0.3)',
          boxShadow: '0 32px 128px rgba(0, 0, 0, 0.2)',
        },
        overlay: {
          background: 'rgba(0, 0, 0, 0.4)',
          backdropFilter: 'blur(8px)',
        },
      },
    },

    ThemeIcon: {
      styles: (theme: any, params: any) => ({
        root: {
          ...(params.variant === 'light' && {
            background: `rgba(${theme.colors[params.color || 'neuralBlue'][5]
              .replace('#', '')
              .match(/.{2}/g)
              ?.map((hex: string) => parseInt(hex, 16))
              .join(', ') || '59, 130, 246'}, 0.1)`,
            backdropFilter: 'blur(12px)',
            border: `1px solid rgba(${theme.colors[params.color || 'neuralBlue'][5]
              .replace('#', '')
              .match(/.{2}/g)
              ?.map((hex: string) => parseInt(hex, 16))
              .join(', ') || '59, 130, 246'}, 0.2)`,
          }),
        },
      }),
    },

    Badge: {
      styles: (theme: any, params: any) => ({
        root: {
          ...(params.variant === 'light' && {
            background: `rgba(${theme.colors[params.color || 'neuralBlue'][5]
              .replace('#', '')
              .match(/.{2}/g)
              ?.map((hex: string) => parseInt(hex, 16))
              .join(', ') || '59, 130, 246'}, 0.1)`,
            backdropFilter: 'blur(8px)',
            border: `1px solid rgba(${theme.colors[params.color || 'neuralBlue'][5]
              .replace('#', '')
              .match(/.{2}/g)
              ?.map((hex: string) => parseInt(hex, 16))
              .join(', ') || '59, 130, 246'}, 0.2)`,
          }),
        },
      }),
    },

    Spotlight: {
      styles: {
        content: {
          background: 'rgba(255, 255, 255, 0.9)',
          backdropFilter: 'blur(32px)',
          border: '1px solid rgba(255, 255, 255, 0.3)',
          boxShadow: '0 24px 96px rgba(0, 0, 0, 0.2)',
        },
        overlay: {
          background: 'rgba(0, 0, 0, 0.3)',
          backdropFilter: 'blur(12px)',
        },
      },
    },

    AppShell: {
      styles: {
        header: {
          background: 'var(--glass-strong)',
          backdropFilter: 'var(--blur-medium)',
          borderBottom: 'var(--border-light)',
          boxShadow: 'var(--shadow-light)',
          zIndex: 1000,
        },
        navbar: {
          background: 'var(--glass-strong)',
          backdropFilter: 'var(--blur-medium)',
          borderRight: 'var(--border-light)',
          boxShadow: 'var(--shadow-light)',
          zIndex: 999,
        },
        main: {
          background: 'transparent',
          minHeight: '100vh',
        },
      },
    },

    Menu: {
      styles: {
        dropdown: {
          background: 'rgba(255, 255, 255, 0.9)',
          backdropFilter: 'blur(24px)',
          border: '1px solid rgba(255, 255, 255, 0.3)',
          boxShadow: '0 16px 64px rgba(0, 0, 0, 0.15)',
        },
      },
    },

    Popover: {
      styles: {
        dropdown: {
          background: 'rgba(255, 255, 255, 0.9)',
          backdropFilter: 'blur(24px)',
          border: '1px solid rgba(255, 255, 255, 0.3)',
          boxShadow: '0 16px 64px rgba(0, 0, 0, 0.15)',
        },
      },
    },

    Notification: {
      styles: {
        root: {
          background: 'rgba(255, 255, 255, 0.9)',
          backdropFilter: 'blur(24px)',
          border: '1px solid rgba(255, 255, 255, 0.3)',
          boxShadow: '0 16px 64px rgba(0, 0, 0, 0.15)',
        },
      },
    },

    Tabs: {
      styles: {
        root: {
          '& [data-active]': {
            background: 'rgba(59, 130, 246, 0.1)',
            backdropFilter: 'blur(12px)',
            border: '1px solid rgba(59, 130, 246, 0.2)',
            borderRadius: '8px',
          },
        },
      },
    },

    Progress: {
      styles: (theme: any) => ({
        root: {
          background: 'rgba(0, 0, 0, 0.05)',
          borderRadius: '12px',
          overflow: 'hidden',
        },
        bar: {
          background: 'linear-gradient(90deg, #3b82f6, #2563eb)',
          borderRadius: '12px',
        },
      }),
    },

    RingProgress: {
      styles: (theme: any) => ({
        root: {
          '& .mantine-RingProgress-curve': {
            filter: 'drop-shadow(0 4px 8px rgba(59, 130, 246, 0.25))',
          },
        },
      }),
    },
  },

  // Other theme properties
  other: {
    // Glassmorphic backgrounds for different contexts
    backgrounds: {
      primary: 'rgba(248, 250, 252, 0.95)',
      secondary: 'rgba(241, 245, 249, 0.90)',
      accent: 'rgba(239, 246, 255, 0.85)',
    },
    
    // Animation presets
    animations: {
      smooth: 'all 0.25s cubic-bezier(0.4, 0, 0.2, 1)',
      spring: 'all 0.3s cubic-bezier(0.68, -0.55, 0.265, 1.55)',
      fast: 'all 0.15s cubic-bezier(0.4, 0, 0.2, 1)',
    },
    
    // Glassmorphic effects
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

// Enhanced semantic color utilities for AI governance
export const semanticColors = {
  bias: {
    low: 'var(--bias-low)',
    medium: 'var(--bias-medium)', 
    high: 'var(--bias-high)',
    critical: 'var(--bias-critical)',
  },
  compliance: {
    compliant: 'var(--compliance-compliant)',
    warning: 'var(--compliance-warning)',
    violation: 'var(--compliance-violation)',
  },
  fairness: {
    excellent: 'var(--fairness-excellent)',
    good: 'var(--fairness-good)',
    moderate: 'var(--fairness-moderate)',
    poor: 'var(--fairness-poor)',
  },
};

// Enhanced glassmorphic utilities
export const glassmorphicUtils = {
  getBackground: (intensity: 'light' | 'medium' | 'strong' = 'medium') => {
    const backgrounds = {
      light: 'var(--glass-light)',
      medium: 'var(--glass-medium)',
      strong: 'var(--glass-strong)',
    };
    return backgrounds[intensity];
  },
  
  getBlur: (intensity: 'light' | 'medium' | 'strong' = 'medium') => {
    const blurs = {
      light: 'var(--blur-light)',
      medium: 'var(--blur-medium)',
      strong: 'var(--blur-strong)',
    };
    return blurs[intensity];
  },
  
  getBorder: (intensity: 'light' | 'medium' | 'strong' = 'medium') => {
    const borders = {
      light: 'var(--border-light)',
      medium: 'var(--border-medium)',
      strong: 'var(--border-strong)',
    };
    return borders[intensity];
  },
  
  getShadow: (intensity: 'light' | 'medium' | 'strong' = 'medium') => {
    const shadows = {
      light: 'var(--shadow-light)',
      medium: 'var(--shadow-medium)',
      strong: 'var(--shadow-strong)',
    };
    return shadows[intensity];
  },
  
  getTransition: (type: 'smooth' | 'spring' | 'fast' = 'smooth') => {
    const transitions = {
      smooth: 'var(--transition-smooth)',
      spring: 'var(--transition-spring)',
      fast: 'var(--transition-fast)',
    };
    return transitions[type];
  },
  
  // Create a complete glassmorphic style object
  createGlassmorphicStyle: (
    intensity: 'light' | 'medium' | 'strong' = 'medium',
    options: {
      hover?: boolean;
      interactive?: boolean;
      borderRadius?: string;
    } = {}
  ) => {
    const { hover = false, interactive = false, borderRadius = '16px' } = options;
    
    const baseStyle = {
      background: glassmorphicUtils.getBackground(intensity),
      backdropFilter: glassmorphicUtils.getBlur(intensity),
      border: glassmorphicUtils.getBorder(intensity),
      boxShadow: glassmorphicUtils.getShadow(intensity),
      borderRadius,
      transition: glassmorphicUtils.getTransition('smooth'),
    };
    
    if (hover) {
      return {
        ...baseStyle,
        '&:hover': {
          background: glassmorphicUtils.getBackground('strong'),
          boxShadow: glassmorphicUtils.getShadow('strong'),
          transform: 'translateY(-2px)',
        },
      };
    }
    
    if (interactive) {
      return {
        ...baseStyle,
        cursor: 'pointer',
        '&:hover': {
          background: glassmorphicUtils.getBackground('strong'),
          boxShadow: glassmorphicUtils.getShadow('strong'),
          transform: 'translateY(-2px)',
        },
        '&:active': {
          transform: 'translateY(0)',
        },
      };
    }
    
    return baseStyle;
  },
};

// Bias severity color helper
export const getBiasColor = (score: number): string => {
  if (score <= 0.1) return semanticColors.bias.low;
  if (score <= 0.3) return semanticColors.bias.medium;
  if (score <= 0.6) return semanticColors.bias.high;
  return semanticColors.bias.critical;
};

// Compliance status color helper
export const getComplianceColor = (status: 'compliant' | 'warning' | 'violation'): string => {
  return semanticColors.compliance[status];
};

// Fairness score color helper
export const getFairnessColor = (score: number): string => {
  if (score >= 0.9) return semanticColors.fairness.excellent;
  if (score >= 0.5) return semanticColors.fairness.good;
  if (score >= 0.5) return semanticColors.fairness.moderate;
  return semanticColors.fairness.poor;
};

export default theme;