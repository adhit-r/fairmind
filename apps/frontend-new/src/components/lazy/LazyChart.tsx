'use client'

import dynamic from 'next/dynamic'
import { Skeleton } from '@/components/ui/skeleton'

// Lazy load chart components for better performance
export const LazySimpleChart = dynamic(
  () => import('@/components/charts/SimpleChart').then(mod => ({ default: mod.SimpleChart })),
  {
    loading: () => <Skeleton className="h-80 w-full" />,
    ssr: false,
  }
)

export const LazyPieChart = dynamic(
  () => import('@/components/charts/PieChart').then(mod => ({ default: mod.PieChart })),
  {
    loading: () => <Skeleton className="h-80 w-full" />,
    ssr: false,
  }
)

export const LazyAreaChart = dynamic(
  () => import('@/components/charts/AreaChart').then(mod => ({ default: mod.AreaChart })),
  {
    loading: () => <Skeleton className="h-80 w-full" />,
    ssr: false,
  }
)

export const LazyRadarChart = dynamic(
  () => import('@/components/charts/RadarChart').then(mod => ({ default: mod.RadarChart })),
  {
    loading: () => <Skeleton className="h-80 w-full" />,
    ssr: false,
  }
)

