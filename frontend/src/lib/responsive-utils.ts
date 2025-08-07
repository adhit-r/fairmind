import React, { useEffect, useState } from 'react'

// Breakpoint definitions
export const breakpoints = {
  xs: 0,
  sm: 640,
  md: 768,
  lg: 1024,
  xl: 1280,
  '2xl': 1536,
} as const

export type Breakpoint = keyof typeof breakpoints

// Hook to get current breakpoint
export function useBreakpoint(): Breakpoint {
  const [breakpoint, setBreakpoint] = useState<Breakpoint>('lg')

  useEffect(() => {
    const handleResize = () => {
      const width = window.innerWidth
      
      if (width >= breakpoints['2xl']) {
        setBreakpoint('2xl')
      } else if (width >= breakpoints.xl) {
        setBreakpoint('xl')
      } else if (width >= breakpoints.lg) {
        setBreakpoint('lg')
      } else if (width >= breakpoints.md) {
        setBreakpoint('md')
      } else if (width >= breakpoints.sm) {
        setBreakpoint('sm')
      } else {
        setBreakpoint('xs')
      }
    }

    handleResize()
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  return breakpoint
}

// Hook to check if screen is mobile
export function useIsMobile(): boolean {
  const breakpoint = useBreakpoint()
  return breakpoint === 'xs' || breakpoint === 'sm'
}

// Hook to check if screen is tablet
export function useIsTablet(): boolean {
  const breakpoint = useBreakpoint()
  return breakpoint === 'md'
}

// Hook to check if screen is desktop
export function useIsDesktop(): boolean {
  const breakpoint = useBreakpoint()
  return breakpoint === 'lg' || breakpoint === 'xl' || breakpoint === '2xl'
}

// Utility functions for responsive design
export const responsiveUtils = {
  // Get responsive grid columns
  getGridCols: (breakpoint: Breakpoint): number => {
    switch (breakpoint) {
      case 'xs': return 1
      case 'sm': return 2
      case 'md': return 3
      case 'lg': return 4
      case 'xl': return 5
      case '2xl': return 6
      default: return 4
    }
  },

  // Get responsive table columns to show
  getTableCols: (breakpoint: Breakpoint): string[] => {
    switch (breakpoint) {
      case 'xs':
        return ['name', 'status'] // Only show essential columns on mobile
      case 'sm':
        return ['name', 'status', 'type']
      case 'md':
        return ['name', 'status', 'type', 'date']
      case 'lg':
        return ['name', 'status', 'type', 'date', 'assignedTo']
      default:
        return ['name', 'status', 'type', 'date', 'assignedTo', 'actions']
    }
  },

  // Get responsive card layout
  getCardLayout: (breakpoint: Breakpoint): 'grid' | 'list' => {
    return breakpoint === 'xs' || breakpoint === 'sm' ? 'list' : 'grid'
  },

  // Get responsive spacing
  getSpacing: (breakpoint: Breakpoint): string => {
    switch (breakpoint) {
      case 'xs': return 'space-y-2'
      case 'sm': return 'space-y-3'
      case 'md': return 'space-y-4'
      case 'lg': return 'space-y-6'
      default: return 'space-y-6'
    }
  },

  // Get responsive padding
  getPadding: (breakpoint: Breakpoint): string => {
    switch (breakpoint) {
      case 'xs': return 'p-2'
      case 'sm': return 'p-3'
      case 'md': return 'p-4'
      case 'lg': return 'p-6'
      default: return 'p-6'
    }
  },

  // Get responsive text sizes
  getTextSize: (breakpoint: Breakpoint, type: 'title' | 'subtitle' | 'body' | 'caption'): string => {
    switch (type) {
      case 'title':
        switch (breakpoint) {
          case 'xs': return 'text-lg'
          case 'sm': return 'text-xl'
          case 'md': return 'text-2xl'
          default: return 'text-3xl'
        }
      case 'subtitle':
        switch (breakpoint) {
          case 'xs': return 'text-sm'
          case 'sm': return 'text-base'
          case 'md': return 'text-lg'
          default: return 'text-xl'
        }
      case 'body':
        switch (breakpoint) {
          case 'xs': return 'text-xs'
          case 'sm': return 'text-sm'
          case 'md': return 'text-base'
          default: return 'text-base'
        }
      case 'caption':
        switch (breakpoint) {
          case 'xs': return 'text-xs'
          case 'sm': return 'text-xs'
          case 'md': return 'text-sm'
          default: return 'text-sm'
        }
    }
  },

  // Get responsive button sizes
  getButtonSize: (breakpoint: Breakpoint): 'sm' | 'default' | 'lg' => {
    switch (breakpoint) {
      case 'xs': return 'sm'
      case 'sm': return 'sm'
      case 'md': return 'default'
      default: return 'default'
    }
  },

  // Get responsive icon sizes
  getIconSize: (breakpoint: Breakpoint): string => {
    switch (breakpoint) {
      case 'xs': return 'h-3 w-3'
      case 'sm': return 'h-4 w-4'
      case 'md': return 'h-4 w-4'
      default: return 'h-5 w-5'
    }
  }
}

// Responsive component wrapper
export function withResponsive<T extends object>(
  Component: React.ComponentType<T>,
  responsiveProps: (breakpoint: Breakpoint) => Partial<T>
) {
  return function ResponsiveComponent(props: T) {
    const breakpoint = useBreakpoint()
    const responsivePropsData = responsiveProps(breakpoint)
    
    return React.createElement(Component, { ...props, ...responsivePropsData })
  }
}

// Responsive table column visibility
export function useResponsiveTableColumns<T extends Record<string, any>>(
  columns: Array<{ key: keyof T; header: string; responsive?: boolean }>
) {
  const breakpoint = useBreakpoint()
  
  return columns.filter(column => {
    if (!column.responsive) return true
    
    const visibleCols = responsiveUtils.getTableCols(breakpoint)
    return visibleCols.includes(column.key as string)
  })
}

// Responsive chart options
export function useResponsiveChartOptions() {
  const breakpoint = useBreakpoint()
  
  return {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: breakpoint !== 'xs' && breakpoint !== 'sm',
        position: 'top' as const,
        labels: {
          font: {
            size: breakpoint === 'xs' ? 10 : breakpoint === 'sm' ? 12 : 14
          }
        }
      },
      tooltip: {
        titleFont: {
          size: breakpoint === 'xs' ? 12 : 14
        },
        bodyFont: {
          size: breakpoint === 'xs' ? 10 : 12
        }
      }
    },
    scales: {
      x: {
        ticks: {
          font: {
            size: breakpoint === 'xs' ? 10 : breakpoint === 'sm' ? 12 : 14
          }
        }
      },
      y: {
        ticks: {
          font: {
            size: breakpoint === 'xs' ? 10 : breakpoint === 'sm' ? 12 : 14
          }
        }
      }
    }
  }
}

// Mobile-first responsive classes
export const responsiveClasses = {
  // Grid layouts
  grid: {
    xs: 'grid-cols-1',
    sm: 'sm:grid-cols-2',
    md: 'md:grid-cols-3',
    lg: 'lg:grid-cols-4',
    xl: 'xl:grid-cols-5',
    '2xl': '2xl:grid-cols-6'
  },

  // Flex layouts
  flex: {
    xs: 'flex-col',
    sm: 'sm:flex-row',
    md: 'md:flex-row',
    lg: 'lg:flex-row'
  },

  // Text sizes
  text: {
    title: {
      xs: 'text-lg',
      sm: 'sm:text-xl',
      md: 'md:text-2xl',
      lg: 'lg:text-3xl'
    },
    subtitle: {
      xs: 'text-sm',
      sm: 'sm:text-base',
      md: 'md:text-lg',
      lg: 'lg:text-xl'
    },
    body: {
      xs: 'text-xs',
      sm: 'sm:text-sm',
      md: 'md:text-base',
      lg: 'lg:text-base'
    }
  },

  // Spacing
  spacing: {
    xs: 'space-y-2',
    sm: 'sm:space-y-3',
    md: 'md:space-y-4',
    lg: 'lg:space-y-6'
  },

  // Padding
  padding: {
    xs: 'p-2',
    sm: 'sm:p-3',
    md: 'md:p-4',
    lg: 'lg:p-6'
  },

  // Margins
  margin: {
    xs: 'm-2',
    sm: 'sm:m-3',
    md: 'md:m-4',
    lg: 'lg:m-6'
  }
}

// Utility to combine responsive classes
export function combineResponsiveClasses(...classSets: string[][]): string {
  return classSets.flat().join(' ')
} 