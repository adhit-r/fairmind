import { createTheme, MantineThemeOverride, rem } from '@mantine/core';

// New Brutalist Professional theme for Mantine
export const brutalistTheme: MantineThemeOverride = createTheme({
  // Color scheme
  primaryColor: 'orange',
  
  // Custom color palette based on design system
  colors: {
    // Orange accent colors
    orange: [
      '#fff7ed', // 50
      '#ffedd5', // 100
      '#fed7aa', // 200
      '#fdba74', // 300
      '#fb923c', // 400
      '#ff6b35', // 500 - primary
      '#e55a2b', // 600
      '#c2410c', // 700
      '#9a3412', // 800
      '#7c2d12', // 900
    ],
    
    // Gray scale
    gray: [
      '#ffffff', // 0
      '#f5f5f5', // 100
      '#e5e5e5', // 200
      '#d4d4d4', // 300
      '#a3a3a3', // 400
      '#737373', // 500
      '#525252', // 600
      '#404040', // 700
      '#262626', // 800
      '#171717', // 900
    ],
    
    // Semantic colors
    green: [
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
    
    yellow: [
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
    
    red: [
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
    
    blue: [
      '#eff6ff', // 50
      '#dbeafe', // 100
      '#bfdbfe', // 200
      '#93c5fd', // 300
      '#60a5fa', // 400
      '#3b82f6', // 500
      '#2563eb', // 600
      '#1d4ed8', // 700
      '#1e40af', // 800
      '#1e3a8a', // 900
    ],
  },

  // Typography system
  fontFamily: 'var(--font-family-primary)',
  fontFamilyMonospace: 'var(--font-family-mono)',
  
  headings: {
    fontFamily: 'var(--font-family-display)',
    fontWeight: 'var(--font-weight-black)',
    sizes: {
      h1: { fontSize: rem(48), lineHeight: 'var(--line-height-tight)', fontWeight: 'var(--font-weight-black)' },
      h2: { fontSize: rem(36), lineHeight: 'var(--line-height-tight)', fontWeight: 'var(--font-weight-black)' },
      h3: { fontSize: rem(30), lineHeight: 'var(--line-height-snug)', fontWeight: 'var(--font-weight-bold)' },
      h4: { fontSize: rem(24), lineHeight: 'var(--line-height-snug)', fontWeight: 'var(--font-weight-bold)' },
      h5: { fontSize: rem(20), lineHeight: 'var(--line-height-normal)', fontWeight: 'var(--font-weight-semibold)' },
      h6: { fontSize: rem(16), lineHeight: 'var(--line-height-normal)', fontWeight: 'var(--font-weight-semibold)' },
    },
  },

  // Brutalist radius system (pure neobrutal: zero radius)
  radius: {
    xs: rem(0),
    sm: rem(0),
    md: rem(0),
    lg: rem(0),
    xl: rem(0),
  },

  // Spacing system
  spacing: {
    xs: rem(4),
    sm: rem(8),
    md: rem(16),
    lg: rem(24),
    xl: rem(32),
  },

  // Brutalist shadows
  shadows: {
    xs: 'var(--shadow-brutal-sm)',
    sm: 'var(--shadow-brutal-sm)',
    md: 'var(--shadow-brutal)',
    lg: 'var(--shadow-brutal-lg)',
    xl: 'var(--shadow-brutal-lg)',
  },

  // Component overrides with brutalist styling
  components: {
    Card: {
      defaultProps: {
        radius: 'md',
        p: 'lg',
      },
      styles: {
        root: {
          background: 'var(--color-white)',
          border: '4px solid var(--color-black)',
          borderRadius: '0',
          boxShadow: 'var(--shadow-brutal)',
          transition: 'all var(--transition-duration-fast) var(--transition-easing-ease-in-out)',
          '&:hover': {
            transform: 'translate(-4px, -4px)',
            boxShadow: 'var(--shadow-brutal-lg)',
          },
        },
      },
    },

    Paper: {
      defaultProps: {
        radius: 'md',
        p: 'lg',
      },
      styles: {
        root: {
          background: 'var(--color-white)',
          border: '2px solid var(--color-black)',
          borderRadius: 'var(--border-radius-base)',
          boxShadow: 'var(--shadow-brutal)',
        },
      },
    },

    Button: {
      defaultProps: {
        radius: 'md',
      },
      styles: (theme: any, params: any) => ({
        root: {
          border: '4px solid var(--color-black)',
          borderRadius: '0',
          boxShadow: 'var(--shadow-brutal)',
          fontWeight: 'var(--font-weight-black)',
          fontFamily: 'var(--font-family-display)',
          fontSize: 'var(--font-size-base)',
          letterSpacing: 'var(--letter-spacing-wide)',
          textTransform: 'uppercase',
          transition: 'all var(--transition-duration-fast) var(--transition-easing-ease-in-out)',
          
          '&[data-variant="filled"]': {
            background: params.color === 'orange' ? 'var(--color-orange)' : 'var(--color-black)',
            color: 'var(--color-white)',
            '&:hover': {
              background: params.color === 'orange' ? 'var(--color-orange-dark)' : 'var(--color-gray-800)',
              transform: 'translate(-4px, -4px)',
              boxShadow: 'var(--shadow-brutal-lg)',
            },
          },
          
          '&[data-variant="outline"]': {
            background: 'transparent',
            color: 'var(--color-black)',
            borderColor: 'var(--color-black)',
            '&:hover': {
              background: 'var(--color-gray-100)',
              transform: 'translate(-4px, -4px)',
              boxShadow: 'var(--shadow-brutal-lg)',
            },
          },
          
          '&[data-variant="light"]': {
            background: 'var(--color-white)',
            color: 'var(--color-black)',
            '&:hover': {
              background: 'var(--color-gray-100)',
              transform: 'translate(-4px, -4px)',
              boxShadow: 'var(--shadow-brutal-lg)',
            },
          },
          
          '&:active': {
            transform: 'translate(0, 0)',
            boxShadow: 'var(--shadow-brutal-sm)',
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
          background: 'var(--color-white)',
          border: '2px solid var(--color-black)',
          borderRadius: 'var(--border-radius-base)',
          fontSize: 'var(--font-size-base)',
          fontFamily: 'var(--font-family-primary)',
          transition: 'all var(--transition-duration-fast) var(--transition-easing-ease-in-out)',
          '&:focus': {
            borderColor: 'var(--color-orange)',
            boxShadow: '0 0 0 3px rgba(255, 107, 53, 0.1)',
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
          background: 'var(--color-white)',
          border: '4px solid var(--color-black)',
          borderRadius: '0',
          fontSize: 'var(--font-size-base)',
          fontFamily: 'var(--font-family-primary)',
          fontWeight: 'var(--font-weight-bold)',
          padding: '1rem 1.25rem',
          transition: 'all var(--transition-duration-fast) var(--transition-easing-ease-in-out)',
          '&:focus': {
            borderColor: 'var(--color-orange)',
            boxShadow: '6px 6px 0px 0px var(--color-orange)',
          },
        },
        dropdown: {
          background: 'var(--color-white)',
          border: '4px solid var(--color-black)',
          borderRadius: '0',
          boxShadow: 'var(--shadow-brutal)',
        },
      },
    },

    Modal: {
      styles: {
        content: {
          background: 'var(--color-white)',
          border: '4px solid var(--color-black)',
          borderRadius: '0',
          boxShadow: 'var(--shadow-brutal-lg)',
        },
        overlay: {
          background: 'rgba(0, 0, 0, 0.5)',
        },
      },
    },

    AppShell: {
      styles: {
        header: {
          background: 'var(--color-white)',
          border: '4px solid var(--color-black)',
          borderBottom: '4px solid var(--color-black)',
          boxShadow: 'var(--shadow-brutal)',
          zIndex: 1000,
        },
        navbar: {
          background: 'var(--color-white)',
          border: '4px solid var(--color-black)',
          borderRight: '4px solid var(--color-black)',
          boxShadow: 'var(--shadow-brutal)',
          zIndex: 999,
        },
        main: {
          background: 'var(--color-gray-100)',
          minHeight: '100vh',
        },
      },
    },

    Menu: {
      styles: {
        dropdown: {
          background: 'var(--color-white)',
          border: '2px solid var(--color-black)',
          borderRadius: 'var(--border-radius-base)',
          boxShadow: 'var(--shadow-brutal)',
        },
      },
    },

    Popover: {
      styles: {
        dropdown: {
          background: 'var(--color-white)',
          border: '2px solid var(--color-black)',
          borderRadius: 'var(--border-radius-base)',
          boxShadow: 'var(--shadow-brutal)',
        },
      },
    },

    Notification: {
      styles: {
        root: {
          background: 'var(--color-white)',
          border: '2px solid var(--color-black)',
          borderRadius: 'var(--border-radius-base)',
          boxShadow: 'var(--shadow-brutal)',
        },
      },
    },

    Badge: {
      styles: (theme: any, params: any) => ({
        root: {
          border: '4px solid var(--color-black)',
          borderRadius: '0',
          fontWeight: 'var(--font-weight-black)',
          fontSize: 'var(--font-size-xs)',
          letterSpacing: 'var(--letter-spacing-wide)',
          textTransform: 'uppercase',
        },
      }),
    },

    ActionIcon: {
      styles: {
        root: {
          border: '4px solid var(--color-black)',
          borderRadius: '0',
          boxShadow: 'var(--shadow-brutal)',
          transition: 'all var(--transition-duration-fast) var(--transition-easing-ease-in-out)',
          '&:hover': {
            transform: 'translate(-4px, -4px)',
            boxShadow: 'var(--shadow-brutal-lg)',
          },
          '&:active': {
            transform: 'translate(0, 0)',
            boxShadow: 'var(--shadow-brutal-sm)',
          },
        },
      },
    },
  },

  // Other theme properties
  other: {
    // Brutalist design tokens
    brutalist: {
      colors: {
        primary: 'var(--color-black)',
        accent: 'var(--color-orange)',
        background: 'var(--color-white)',
        surface: 'var(--color-gray-100)',
      },
      shadows: {
        sm: 'var(--shadow-brutal-sm)',
        md: 'var(--shadow-brutal)',
        lg: 'var(--shadow-brutal-lg)',
      },
      borders: {
        width: '2px',
        color: 'var(--color-black)',
        style: 'solid',
      },
    },
  },
});

// Utility functions for brutalist design
export const brutalistUtils = {
  getButtonStyle: (variant: 'primary' | 'secondary' | 'accent' = 'primary') => {
    const baseStyle = {
      border: '4px solid var(--color-black)',
      borderRadius: '0',
      boxShadow: 'var(--shadow-brutal)',
      fontWeight: 'var(--font-weight-black)',
      fontSize: 'var(--font-size-base)',
      letterSpacing: 'var(--letter-spacing-wide)',
      textTransform: 'uppercase',
      transition: 'all var(--transition-duration-fast) var(--transition-easing-ease-in-out)',
    };

    switch (variant) {
      case 'accent':
        return {
          ...baseStyle,
          background: 'var(--color-orange)',
          color: 'var(--color-white)',
        };
      case 'secondary':
        return {
          ...baseStyle,
          background: 'var(--color-white)',
          color: 'var(--color-black)',
        };
      case 'primary':
      default:
        return {
          ...baseStyle,
          background: 'var(--color-black)',
          color: 'var(--color-white)',
        };
    }
  },

  getCardStyle: () => ({
    background: 'var(--color-white)',
    border: '4px solid var(--color-black)',
    borderRadius: '0',
    boxShadow: 'var(--shadow-brutal)',
    transition: 'all var(--transition-duration-fast) var(--transition-easing-ease-in-out)',
  }),

  getInputStyle: () => ({
    background: 'var(--color-white)',
    border: '4px solid var(--color-black)',
    borderRadius: '0',
    fontSize: 'var(--font-size-base)',
    fontFamily: 'var(--font-family-primary)',
    fontWeight: 'var(--font-weight-bold)',
    padding: '1rem 1.25rem',
  }),
};

export default brutalistTheme;