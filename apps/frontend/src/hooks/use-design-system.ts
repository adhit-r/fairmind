import { useGlassmorphicTheme } from '@/providers/glassmorphic-theme-provider';

// Design system tokens interface
interface DesignTokens {
  // Colors
  colors: {
    primary: {
      black: string;
      white: string;
    };
    accent: {
      orange: string;
      orangeDark: string;
      orangeLight: string;
    };
    gray: {
      100: string;
      200: string;
      300: string;
      400: string;
      500: string;
      600: string;
      700: string;
      800: string;
      900: string;
    };
    semantic: {
      success: string;
      successLight: string;
      successDark: string;
      warning: string;
      warningLight: string;
      warningDark: string;
      error: string;
      errorLight: string;
      errorDark: string;
      info: string;
    };
  };
  
  // Typography
  typography: {
    fontFamilies: {
      primary: string;
      display: string;
      mono: string;
    };
    fontWeights: {
      light: number;
      normal: number;
      medium: number;
      semibold: number;
      bold: number;
      black: number;
    };
    fontSizes: {
      xs: string;
      sm: string;
      base: string;
      lg: string;
      xl: string;
      '2xl': string;
      '3xl': string;
      '4xl': string;
      '5xl': string;
      '6xl': string;
      '7xl': string;
    };
    lineHeights: {
      tight: number;
      snug: number;
      normal: number;
      relaxed: number;
    };
    letterSpacing: {
      tight: string;
      normal: string;
      wide: string;
    };
  };
  
  // Spacing
  spacing: {
    scale: string;
    baseUnit: string;
    values: {
      1: string;
      2: string;
      3: string;
      4: string;
      5: string;
      6: string;
      8: string;
      10: string;
      12: string;
      16: string;
      20: string;
      24: string;
      32: string;
    };
  };
  
  // Border Radius
  borderRadius: {
    philosophy: string;
    values: {
      none: string;
      sm: string;
      base: string;
      md: string;
      lg: string;
      xl: string;
    };
  };
  
  // Shadows
  shadows: {
    philosophy: string;
    values: {
      sm: string;
      base: string;
      md: string;
      lg: string;
      brutal: string;
      brutalLg: string;
      brutalSm: string;
    };
  };
  
  // Transitions
  transitions: {
    durations: {
      fast: string;
      base: string;
      slow: string;
    };
    easings: {
      easeInOut: string;
      easeOut: string;
      easeIn: string;
    };
  };
  
  // Z-Index
  zIndex: {
    scale: string;
    values: {
      dropdown: number;
      sticky: number;
      fixed: number;
      modalBackdrop: number;
      modal: number;
      popover: number;
      tooltip: number;
      toast: number;
    };
  };
  
  // Breakpoints
  breakpoints: {
    sm: string;
    md: string;
    lg: string;
    xl: string;
    '2xl': string;
  };
  
  // Accessibility
  accessibility: {
    contrastRatios: {
      normal: string;
      large: string;
    };
    focusStates: {
      outline: string;
      outlineOffset: string;
    };
  };
}

// Hook to access design system tokens
export function useDesignSystem(): DesignTokens {
  const { colorScheme } = useGlassmorphicTheme();
  
  // Design system tokens
  const tokens: DesignTokens = {
    colors: {
      primary: {
        black: '#000000',
        white: '#ffffff',
      },
      accent: {
        orange: '#ff6b35',
        orangeDark: '#e55a2b',
        orangeLight: '#ff8c69',
      },
      gray: {
        100: '#f5f5f5',
        200: '#e5e5e5',
        300: '#d4d4d4',
        400: '#a3a3a3',
        500: '#737373',
        600: '#525252',
        700: '#404040',
        800: '#262626',
        900: '#171717',
      },
      semantic: {
        success: '#22c55e',
        successLight: '#dcfce7',
        successDark: '#16a34a',
        warning: '#f59e0b',
        warningLight: '#fef3c7',
        warningDark: '#d97706',
        error: '#ef4444',
        errorLight: '#fee2e2',
        errorDark: '#dc2626',
        info: '#3b82f6',
      },
    },
    
    typography: {
      fontFamilies: {
        primary: "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
        display: "Space Grotesk, Inter, sans-serif",
        mono: "JetBrains Mono, 'Fira Code', 'Monaco', monospace",
      },
      fontWeights: {
        light: 300,
        normal: 400,
        medium: 500,
        semibold: 600,
        bold: 700,
        black: 900,
      },
      fontSizes: {
        xs: '0.75rem',
        sm: '0.875rem',
        base: '1rem',
        lg: '1.125rem',
        xl: '1.25rem',
        '2xl': '1.5rem',
        '3xl': '1.875rem',
        '4xl': '2.25rem',
        '5xl': '3rem',
        '6xl': '3.75rem',
        '7xl': '4.5rem',
      },
      lineHeights: {
        tight: 1.1,
        snug: 1.2,
        normal: 1.5,
        relaxed: 1.6,
      },
      letterSpacing: {
        tight: '-0.02em',
        normal: '0',
        wide: '0.05em',
      },
    },
    
    spacing: {
      scale: 'Brutalist Grid System',
      baseUnit: '0.25rem (4px)',
      values: {
        1: '0.25rem',
        2: '0.5rem',
        3: '0.75rem',
        4: '1rem',
        5: '1.25rem',
        6: '1.5rem',
        8: '2rem',
        10: '2.5rem',
        12: '3rem',
        16: '4rem',
        20: '5rem',
        24: '6rem',
        32: '8rem',
      },
    },
    
    borderRadius: {
      philosophy: 'Minimal border radius for sharp, brutalist edges',
      values: {
        none: '0',
        sm: '0.125rem',
        base: '0.25rem',
        md: '0.375rem',
        lg: '0.5rem',
        xl: '0.75rem',
      },
    },
    
    shadows: {
      philosophy: 'Brutalist shadows with hard edges and strong contrast',
      values: {
        sm: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
        base: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
        md: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
        lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
        brutal: '4px 4px 0px 0px #000000',
        brutalLg: '8px 8px 0px 0px #000000',
        brutalSm: '2px 2px 0px 0px #000000',
      },
    },
    
    transitions: {
      durations: {
        fast: '150ms',
        base: '250ms',
        slow: '350ms',
      },
      easings: {
        easeInOut: 'ease-in-out',
        easeOut: 'ease-out',
        easeIn: 'ease-in',
      },
    },
    
    zIndex: {
      scale: 'Layered z-index system for proper stacking',
      values: {
        dropdown: 1000,
        sticky: 1020,
        fixed: 1030,
        modalBackdrop: 1040,
        modal: 1050,
        popover: 1060,
        tooltip: 1070,
        toast: 1080,
      },
    },
    
    breakpoints: {
      sm: '640px',
      md: '768px',
      lg: '1024px',
      xl: '1280px',
      '2xl': '1536px',
    },
    
    accessibility: {
      contrastRatios: {
        normal: '4.5:1',
        large: '3:1',
      },
      focusStates: {
        outline: '2px solid #ff6b35',
        outlineOffset: '2px',
      },
    },
  };
  
  return tokens;
}

// Hook to access brutalist component styles
export function useBrutalistStyles() {
  const { colors } = useDesignSystem();
  
  return {
    card: {
      base: {
        background: colors.primary.white,
        border: `2px solid ${colors.primary.black}`,
        borderRadius: '0.25rem',
        boxShadow: '4px 4px 0px 0px #000000',
      },
      hover: {
        transform: 'translate(-2px, -2px)',
        boxShadow: '8px 8px 0px 0px #000000',
      },
    },
    button: {
      base: {
        background: colors.primary.black,
        color: colors.primary.white,
        border: `2px solid ${colors.primary.black}`,
        borderRadius: '0.25rem',
        boxShadow: '4px 4px 0px 0px #000000',
      },
      hover: {
        transform: 'translate(-2px, -2px)',
        boxShadow: '8px 8px 0px 0px #000000',
      },
    },
    input: {
      base: {
        background: colors.primary.white,
        border: `2px solid ${colors.primary.black}`,
        borderRadius: '0.25rem',
        padding: '0.75rem 1rem',
        fontSize: '1rem',
      },
      focus: {
        borderColor: colors.accent.orange,
        boxShadow: '0 0 0 3px rgba(255, 107, 53, 0.1)',
      },
    },
  };
}