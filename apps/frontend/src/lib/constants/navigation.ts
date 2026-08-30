import {
  IconDashboard,
  IconScale,
  IconShieldLock,
  IconActivity,
  IconChartLine,
  IconDna,
  IconSettings,
  IconRobot,
  IconTarget,
  IconReportAnalytics,
  IconFileAnalytics,
  IconAlertCircle,
  IconAlertHexagon,
  IconMicroscope,
  IconUsers,
  IconKey,
  IconClipboardList,
  IconUserCheck,
  IconDatabase,
  IconChecklist,
} from '@tabler/icons-react';
import type { TablerIcon } from '@tabler/icons-react';

export interface NavigationItem {
  title: string;
  href: string;
  description?: string;
  icon?: TablerIcon;
}

export interface NavigationCategory {
  id: string;
  title: string;
  href?: string;
  icon?: TablerIcon;
  items?: NavigationItem[];
}

export const NAVIGATION_ITEMS: NavigationCategory[] = [
  {
    id: 'dashboard',
    title: 'Dashboard',
    href: '/dashboard',
    icon: IconDashboard,
  },
  {
    id: 'onboard',
    title: 'Onboard',
    href: '/onboard',
    icon: IconTarget,
  },
  {
    id: 'bias_fairness',
    title: 'Assess',
    icon: IconScale,
    items: [
      {
        title: 'Bias Detection',
        href: '/bias',
        description: 'Analyze models for bias',
        icon: IconScale,
      },
      {
        title: 'Evaluation Runs',
        href: '/tests',
        description: 'Plan evaluations and trace evidence-backed runs',
        icon: IconChecklist,
      },
      {
        title: 'Remediation Wizard',
        href: '/remediation-wizard',
        description: 'Step-by-step bias fixing',
        icon: IconTarget,
      },
      {
        title: "LLM Judge",
        href: "/llm-judge",
        icon: IconRobot,
        description: "Evaluation pack unavailable",
      },
      {
        title: "Model DNA",
        href: "/model-dna",
        icon: IconDna,
        description: "Lineage & Provenance",
      },
      {
        title: "Explainability Studio",
        href: "/explainability-studio",
        icon: IconMicroscope,
        description: "Evaluation pack unavailable",
      },
    ],
  },
  {
    id: 'compliance',
    title: 'Govern & Prove',
    icon: IconShieldLock,
    items: [
      {
        title: 'Overview',
        href: '/ai-governance',
        description: 'Governance readiness overview',
        icon: IconDashboard,
      },
      {
        title: 'AI Systems',
        href: '/model-inventory',
        description: 'Governed models, agents, and applications',
        icon: IconDatabase,
      },
      {
        title: 'Frameworks & Controls',
        href: '/compliance-dashboard',
        description: 'Framework versions and control readiness',
        icon: IconShieldLock,
      },
      {
        title: 'Evidence & Evaluations',
        href: '/evidence',
        description: 'Evidence records and completed evaluation runs',
        icon: IconFileAnalytics,
      },
      {
        title: 'Findings',
        href: '/risks',
        description: 'Findings and release blockers',
        icon: IconAlertHexagon,
      },
      {
        title: 'Reports & Assurance',
        href: '/reports',
        icon: IconReportAnalytics,
      },
    ],
  },
  {
    id: 'monitoring',
    title: 'Operate',
    icon: IconActivity,
    items: [
      {
        title: 'Advanced Analytics',
        href: '/analytics',
        icon: IconChartLine,
        description: 'Trends and comparisons',
      },
      {
        title: 'Real-time Monitoring',
        href: '/monitoring',
        description: 'Live model performance',
        icon: IconActivity,
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
    id: 'community',
    title: 'Community',
    icon: IconRobot,
    items: [
      {
        title: 'Model Marketplace',
        href: '/marketplace',
        description: 'Discover & share models',
        icon: IconTarget,
      },
    ],
  },
  {
    id: 'admin',
    title: 'Admin',
    icon: IconUsers,
    items: [
      {
        title: 'Users',
        href: '/admin/users',
        description: 'Manage user access and roles',
        icon: IconUsers,
      },
      {
        title: 'Roles',
        href: '/admin/roles',
        description: 'View role permissions',
        icon: IconKey,
      },
      {
        title: 'Audit Log',
        href: '/admin/audit-log',
        description: 'Compliance audit trail',
        icon: IconClipboardList,
      },
      {
        title: 'Access Requests',
        href: '/admin/registrations',
        description: 'Review signup requests',
        icon: IconUserCheck,
      },
    ],
  },
  {
    id: 'org-admin',
    title: 'Organization',
    icon: IconUsers,
    items: [
      {
        title: 'Members',
        href: '/org-admin/members',
        description: 'Manage team members',
        icon: IconUsers,
      },
      {
        title: 'Roles',
        href: '/org-admin/roles',
        description: 'Manage organization roles',
        icon: IconKey,
      },
      {
        title: 'Settings',
        href: '/org-admin/settings',
        description: 'Organization settings',
        icon: IconSettings,
      },
      {
        title: 'Audit Log',
        href: '/org-admin/audit-log',
        description: 'Organization audit trail',
        icon: IconClipboardList,
      },
    ],
  },
  {
    id: 'settings',
    title: 'Settings',
    icon: IconSettings,
    href: '/settings',
  },
];
