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
} from '@tabler/icons-react';
import { ReactNode } from 'react';

export interface NavigationItem {
  title: string;
  href: string;
  description?: string;
  icon?: React.ComponentType<any>;
}

export interface NavigationCategory {
  id: string;
  title: string;
  href?: string;
  icon?: React.ComponentType<any>;
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
    id: 'bias_fairness',
    title: 'Bias & Fairness',
    icon: IconScale,
    items: [
      {
        title: 'Bias Detection',
        href: '/bias',
        description: 'Analyze models for bias',
        icon: IconScale,
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
        description: "AI Evaluation",
      },
      {
        title: "Model DNA",
        href: "/model-dna",
        icon: IconDna,
        description: "Lineage & Provenance",
      },
    ],
  },
  {
    id: 'compliance',
    title: 'Compliance',
    icon: IconShieldLock,
    items: [
      {
        title: 'Compliance Dashboard',
        href: '/compliance-dashboard',
        description: 'Global compliance status',
        icon: IconShieldLock,
      },
      {
        title: 'Reports',
        href: '/reports',
        icon: IconReportAnalytics,
      },
      {
        title: 'Compliance Automation',
        href: '/compliance-automation',
        description: 'Auto-reports & alerts',
        icon: IconRobot,
      },
      {
        title: 'Audit Reports',
        href: '/audit-reports',
        description: 'Generate and view reports',
        icon: IconFileAnalytics,
      },
    ],
  },
  {
    id: 'monitoring',
    title: 'Monitoring',
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
    id: 'settings',
    title: 'Settings',
    icon: IconSettings,
    href: '/settings',
  },
];
