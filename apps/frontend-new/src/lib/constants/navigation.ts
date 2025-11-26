/**
 * Navigation Constants - Categorized menu structure
 * Organized into logical groups for better UX
 */

import {
  IconDashboard,
  IconActivity,
  IconBrain,
  IconDatabase,
  IconFileText,
  IconShield,
  IconTarget,
  IconChartBar,
  IconTrendingUp,
  IconFileAnalytics,
  IconLock,
  IconAlertTriangle,
  IconSettings,
  IconDatabase as IconData,
  IconFolder,
  IconCode,
  IconChecklist,
  IconPlugConnected,
} from '@tabler/icons-react'

export interface NavItem {
  title: string
  href: string
  icon: typeof IconDashboard
  description?: string
}

export interface NavCategory {
  id: string
  title: string
  icon: typeof IconDashboard
  items: NavItem[]
}

export const navigationCategories: NavCategory[] = [
  {
    id: 'overview',
    title: 'Overview',
    icon: IconDashboard,
    items: [
      {
        title: 'Dashboard',
        href: '/dashboard',
        icon: IconDashboard,
        description: 'Main dashboard with system overview',
      },
      {
        title: 'System Status',
        href: '/status',
        icon: IconActivity,
        description: 'System health and status',
      },
    ],
  },
  {
    id: 'ai-models',
    title: 'AI Models',
    icon: IconBrain,
    items: [
      {
        title: 'Model Registry',
        href: '/models',
        icon: IconDatabase,
        description: 'Manage and register AI models',
      },
      {
        title: 'Real-time Integration',
        href: '/realtime',
        icon: IconPlugConnected,
        description: 'Connect and test live models',
      },
      {
        title: 'Model Provenance',
        href: '/provenance',
        icon: IconFileText,
        description: 'Track model lineage and provenance',
      },
      {
        title: 'AI BOM',
        href: '/ai-bom',
        icon: IconCode,
        description: 'AI Bill of Materials',
      },
      {
        title: 'Lifecycle',
        href: '/lifecycle',
        icon: IconActivity,
        description: 'Manage model lifecycle stages',
      },
    ],
  },
  {
    id: 'governance',
    title: 'Governance',
    icon: IconShield,
    items: [
      {
        title: 'AI Governance',
        href: '/ai-governance',
        icon: IconShield,
        description: 'AI governance and compliance',
      },
      {
        title: 'Policies',
        href: '/policies',
        icon: IconFileText,
        description: 'Governance policies and rules',
      },
      {
        title: 'Compliance',
        href: '/compliance-dashboard',
        icon: IconChecklist,
        description: 'Compliance frameworks and checks',
      },
    ],
  },
  {
    id: 'bias-detection',
    title: 'Bias & Fairness',
    icon: IconTarget,
    items: [
      {
        title: 'Bias Detection (Production)',
        href: '/bias-simple',
        icon: IconTarget,
        description: '✨ NEW: Real fairness calculations with actionable recommendations',
      },
      {
        title: 'Bias Detection',
        href: '/bias',
        icon: IconTarget,
        description: 'Detect bias in models and data',
      },
      {
        title: 'Advanced Bias',
        href: '/advanced-bias',
        icon: IconTarget,
        description: 'Advanced bias analysis techniques',
      },
      {
        title: 'Modern Bias',
        href: '/modern-bias',
        icon: IconBrain,
        description: 'WEAT, SEAT, Minimal Pairs, StereoSet, BBQ tests',
      },
      {
        title: 'Multimodal Bias',
        href: '/multimodal-bias',
        icon: IconTarget,
        description: 'Image, audio, video, and cross-modal bias detection',
      },
      {
        title: 'LLM Testing (SOTA)',
        href: '/llm-testing',
        icon: IconBrain,
        description: '⭐ LLM-as-Judge, Counterfactual, Red Teaming & more SOTA methods',
      },
      {
        title: 'Fairness Analysis',
        href: '/fairness',
        icon: IconChartBar,
        description: 'Fairness metrics and analysis',
      },
    ],
  },
  {
    id: 'security',
    title: 'Security',
    icon: IconLock,
    items: [
      {
        title: 'Security Scans',
        href: '/security',
        icon: IconShield,
        description: 'Security scanning and analysis',
      },
      {
        title: 'Risk Management',
        href: '/risks',
        icon: IconAlertTriangle,
        description: 'Risk assessment and management',
      },
    ],
  },
  {
    id: 'monitoring',
    title: 'Monitoring',
    icon: IconChartBar,
    items: [
      {
        title: 'Monitoring',
        href: '/monitoring',
        icon: IconActivity,
        description: 'Real-time system monitoring',
      },
      {
        title: 'Analytics',
        href: '/analytics',
        icon: IconChartBar,
        description: 'Analytics and insights',
      },
      {
        title: 'Benchmarks',
        href: '/benchmarks',
        icon: IconTrendingUp,
        description: 'Model benchmarking',
      },
      {
        title: 'Reports',
        href: '/reports',
        icon: IconFileAnalytics,
        description: 'Generate and view reports',
      },
    ],
  },
  {
    id: 'data',
    title: 'Data',
    icon: IconData,
    items: [
      {
        title: 'Datasets',
        href: '/datasets',
        icon: IconFolder,
        description: 'Manage datasets',
      },
      {
        title: 'Evidence',
        href: '/evidence',
        icon: IconFileText,
        description: 'Evidence collection and management',
      },
    ],
  },
]
