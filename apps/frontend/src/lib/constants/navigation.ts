import {
  IconActivity,
  IconAlertCircle,
  IconAlertHexagon,
  IconChartLine,
  IconClipboardList,
  IconDashboard,
  IconDatabase,
  IconDna,
  IconFileAnalytics,
  IconKey,
  IconMicroscope,
  IconReportAnalytics,
  IconRobot,
  IconScale,
  IconSettings,
  IconShieldLock,
  IconTarget,
  IconUsers,
} from '@tabler/icons-react'
import type { ComponentType } from 'react'

type NavigationIcon = ComponentType<{ className?: string }>

export interface NavigationItem {
  title: string
  href: string
  description?: string
  icon?: NavigationIcon
}

export interface NavigationCategory {
  id: string
  title: string
  href?: string
  icon?: NavigationIcon
  items?: NavigationItem[]
}

export const NAVIGATION_ITEMS: NavigationCategory[] = [
  {
    id: 'systems',
    title: 'Systems',
    icon: IconDatabase,
    items: [
      {
        title: 'System Overview',
        href: '/dashboard',
        description: 'Selected system context and current work',
        icon: IconDashboard,
      },
      {
        title: 'Register System',
        href: '/onboard',
        description: 'Create an AI system record',
        icon: IconTarget,
      },
      {
        title: 'Model Inventory',
        href: '/model-inventory',
        description: 'Models and their deployment context',
        icon: IconDatabase,
      },
      {
        title: 'Model DNA',
        href: '/model-dna',
        description: 'Static mock; unavailable as evidence',
        icon: IconDna,
      },
    ],
  },
  {
    id: 'test-lab',
    title: 'Test Lab',
    icon: IconMicroscope,
    items: [
      {
        title: 'Evaluation Runs',
        href: '/tests',
        description: 'Test run workspace',
        icon: IconClipboardList,
      },
      {
        title: 'Environmental',
        href: '/ai-governance',
        description: 'Validated environmental evidence path',
        icon: IconActivity,
      },
      {
        title: 'Tabular Bias',
        href: '/bias',
        description: 'Interface present; evaluator API unavailable',
        icon: IconScale,
      },
      {
        title: 'LLM Bias',
        href: '/modern-bias',
        description: 'Mock-only interface; not evidence-grade',
        icon: IconRobot,
      },
      {
        title: 'Multimodal Bias',
        href: '/multimodal-bias',
        description: 'Metadata-only media inspection',
        icon: IconMicroscope,
      },
      {
        title: 'LLM Judge',
        href: '/llm-judge',
        description: 'External-provider evaluation',
        icon: IconRobot,
      },
      {
        title: 'Explainability',
        href: '/explainability-studio',
        description: 'Interface only; evidence integration pending',
        icon: IconMicroscope,
      },
      {
        title: 'Security Testing',
        href: '/security',
        description: 'Interface only; evidence integration pending',
        icon: IconShieldLock,
      },
    ],
  },
  {
    id: 'evidence-controls',
    title: 'Evidence & Controls',
    icon: IconFileAnalytics,
    items: [
      {
        title: 'Evidence Workbench',
        href: '/evidence',
        description: 'Collect, inspect, and link artifacts',
        icon: IconFileAnalytics,
      },
      {
        title: 'Control Coverage',
        href: '/compliance-dashboard',
        description: 'Review recorded framework coverage',
        icon: IconShieldLock,
      },
      {
        title: 'Policies',
        href: '/policies',
        description: 'Policy records and control links',
        icon: IconClipboardList,
      },
      {
        title: 'Risks',
        href: '/risks',
        description: 'Risk register and release blockers',
        icon: IconAlertHexagon,
      },
      {
        title: 'Remediation',
        href: '/remediation',
        description: 'Findings, owners, and corrective work',
        icon: IconTarget,
      },
    ],
  },
  {
    id: 'assurance',
    title: 'Assurance',
    icon: IconShieldLock,
    items: [
      {
        title: 'Reports',
        href: '/reports',
        description: 'System and evaluation reports',
        icon: IconReportAnalytics,
      },
      {
        title: 'Audit Reports',
        href: '/audit-reports',
        description: 'Audit report generation',
        icon: IconFileAnalytics,
      },
      {
        title: 'AI BOM',
        href: '/ai-bom',
        description: 'Metadata-only AI bill of materials',
        icon: IconDna,
      },
    ],
  },
  {
    id: 'operations',
    title: 'Operations',
    icon: IconActivity,
    items: [
      {
        title: 'Monitoring',
        href: '/monitoring',
        description: 'Operational model monitoring',
        icon: IconActivity,
      },
      {
        title: 'Analytics',
        href: '/analytics',
        description: 'Trends and comparisons',
        icon: IconChartLine,
      },
      {
        title: 'Alerts',
        href: '/alerts',
        description: 'System notifications',
        icon: IconAlertCircle,
      },
    ],
  },
  {
    id: 'organization',
    title: 'Organization',
    icon: IconUsers,
    items: [
      {
        title: 'Members',
        href: '/org-admin/members',
        description: 'Manage organization members',
        icon: IconUsers,
      },
      {
        title: 'Roles',
        href: '/org-admin/roles',
        description: 'Manage organization roles',
        icon: IconKey,
      },
      {
        title: 'Audit Log',
        href: '/org-admin/audit-log',
        description: 'Organization audit trail',
        icon: IconClipboardList,
      },
      {
        title: 'Settings',
        href: '/org-admin/settings',
        description: 'Organization settings',
        icon: IconSettings,
      },
    ],
  },
]
