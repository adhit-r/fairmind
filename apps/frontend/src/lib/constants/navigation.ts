import {
  IconActivity,
  IconAlertHexagon,
  IconBuilding,
  IconChecklist,
  IconClipboardList,
  IconFileAnalytics,
  IconFileText,
  IconKey,
  IconLayoutDashboard,
  IconReportAnalytics,
  IconRobot,
  IconSettings,
  IconShieldCheck,
  IconTool,
  IconUserCheck,
  IconUsers,
} from '@tabler/icons-react';
import type { TablerIcon } from '@tabler/icons-react';

export interface NavigationItem {
  title: string;
  href: string;
  description: string;
  icon: TablerIcon;
  /** Match only this exact path (default: the path and everything beneath it). */
  exact?: boolean;
  /** Extra path prefixes that should also mark this item active. */
  alsoActiveFor?: string[];
  /** Only org admins / owners / platform admins should see this item. */
  requiresAdmin?: boolean;
}

export interface NavigationGroup {
  id: string;
  title: string;
  items: NavigationItem[];
  /** Whole group is role-gated (Administration). */
  requiresAdmin?: boolean;
}

/** Legacy alias kept for older imports. */
export type NavigationCategory = NavigationGroup;

/**
 * Primary navigation, in governance-lifecycle order:
 * register -> apply framework -> evaluate -> evidence -> findings -> decide -> report -> monitor.
 */
export const NAVIGATION_ITEMS: NavigationGroup[] = [
  {
    id: 'overview',
    title: 'Overview',
    items: [
      {
        title: 'Dashboard',
        href: '/dashboard',
        description: 'Portfolio readiness, release blockers and the review queue',
        icon: IconLayoutDashboard,
      },
    ],
  },
  {
    id: 'govern',
    title: 'Govern',
    items: [
      {
        title: 'AI Systems',
        href: '/systems',
        description: 'Register and govern models, agents and applications',
        icon: IconRobot,
      },
      {
        title: 'Frameworks & Controls',
        href: '/frameworks',
        description: 'Apply framework versions and track control readiness',
        icon: IconShieldCheck,
      },
      {
        title: 'Policies',
        href: '/policies',
        description: 'Organisation policies and governance rules',
        icon: IconFileText,
      },
    ],
  },
  {
    id: 'assess',
    title: 'Assess',
    items: [
      {
        title: 'Evaluations',
        href: '/evaluations',
        description: 'Run fairness, LLM, explainability and governance evaluations',
        icon: IconChecklist,
        alsoActiveFor: ['/assurance/evaluations'],
      },
      {
        title: 'Evidence',
        href: '/evidence',
        description: 'Review evidence records and control mappings',
        icon: IconFileAnalytics,
      },
    ],
  },
  {
    id: 'remediate',
    title: 'Remediate',
    items: [
      {
        title: 'Findings',
        href: '/findings',
        description: 'Triage findings and release blockers',
        icon: IconAlertHexagon,
      },
      {
        title: 'Remediation',
        href: '/remediation',
        description: 'Plan, assign and retest fixes',
        icon: IconTool,
      },
    ],
  },
  {
    id: 'report',
    title: 'Report',
    items: [
      {
        title: 'Reports',
        href: '/reports',
        description: 'Version-pinned assurance reports for auditors',
        icon: IconReportAnalytics,
      },
    ],
  },
  {
    id: 'operate',
    title: 'Operate',
    items: [
      {
        title: 'Monitoring',
        href: '/monitoring',
        description: 'Operational health, alerts and scheduled compliance checks',
        icon: IconActivity,
      },
    ],
  },
  {
    id: 'administration',
    title: 'Administration',
    requiresAdmin: true,
    items: [
      {
        title: 'Admin Hub',
        href: '/admin',
        description: 'Administration overview',
        icon: IconSettings,
        exact: true,
        requiresAdmin: true,
      },
      {
        title: 'Members',
        href: '/admin/members',
        description: 'Manage members and invitations',
        icon: IconUsers,
        requiresAdmin: true,
      },
      {
        title: 'Roles',
        href: '/admin/roles',
        description: 'View and manage role permissions',
        icon: IconKey,
        requiresAdmin: true,
      },
      {
        title: 'Access Requests',
        href: '/admin/access-requests',
        description: 'Review sign-up and access requests',
        icon: IconUserCheck,
        requiresAdmin: true,
      },
      {
        title: 'Audit Log',
        href: '/admin/audit-log',
        description: 'Compliance audit trail',
        icon: IconClipboardList,
        requiresAdmin: true,
      },
      {
        title: 'Organization',
        href: '/admin/organization',
        description: 'Organisation profile and settings',
        icon: IconBuilding,
        requiresAdmin: true,
      },
    ],
  },
];

/** Footer item: appears once, in the sidebar footer. */
export const SETTINGS_NAV_ITEM: NavigationItem = {
  title: 'Settings',
  href: '/settings',
  description: 'Personal preferences, integrations and system status',
  icon: IconSettings,
};

/** Is this nav item the current location? Prefix match unless `exact`. */
export function isNavigationItemActive(pathname: string, item: Pick<NavigationItem, 'href' | 'exact' | 'alsoActiveFor'>): boolean {
  const matches = (base: string) => pathname === base || (!item.exact && pathname.startsWith(`${base}/`));
  if (matches(item.href)) return true;
  return (item.alsoActiveFor ?? []).some((prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`));
}

export interface QuickJumpDestination {
  title: string;
  href: string;
  description: string;
  group: string;
  keywords: string[];
}

/** Extra destinations (not sidebar items) reachable from the header quick-jump. */
const EXTRA_DESTINATIONS: QuickJumpDestination[] = [
  { title: 'Register AI system', href: '/systems/new', description: 'Start the registration wizard', group: 'Govern', keywords: ['new', 'add', 'onboard', 'create', 'model', 'agent'] },
  { title: 'Fairness evaluation', href: '/evaluations/fairness', description: 'Bias and fairness testing', group: 'Assess', keywords: ['bias', 'fairness', 'disparate', 'demographic'] },
  { title: 'LLM evaluation', href: '/evaluations/llm', description: 'LLM judge, benchmarks and testing', group: 'Assess', keywords: ['llm', 'judge', 'benchmark', 'prompt'] },
  { title: 'Explainability evaluation', href: '/evaluations/explainability', description: 'Attribution and attention analysis', group: 'Assess', keywords: ['explain', 'shap', 'attribution'] },
  { title: 'Alerts', href: '/monitoring?tab=alerts', description: 'Operational alerts', group: 'Operate', keywords: ['notifications', 'incident'] },
  { title: 'Scheduled compliance checks', href: '/monitoring?tab=checks', description: 'Automated recurring checks', group: 'Operate', keywords: ['automation', 'schedule', 'cron'] },
  { title: 'System status', href: '/settings?tab=status', description: 'Backend and service health', group: 'Settings', keywords: ['health', 'uptime', 'status'] },
];

/**
 * Flat list for the header quick-jump (Ctrl/Cmd+K). Pass `includeAdmin=false`
 * to hide the Administration group for non-admin users.
 */
export function getQuickJumpDestinations(includeAdmin: boolean): QuickJumpDestination[] {
  const fromNav: QuickJumpDestination[] = NAVIGATION_ITEMS
    .filter((group) => includeAdmin || !group.requiresAdmin)
    .flatMap((group) =>
      group.items
        .filter((item) => includeAdmin || !item.requiresAdmin)
        .map((item) => ({ title: item.title, href: item.href, description: item.description, group: group.title, keywords: [] as string[] })),
    );
  return [
    ...fromNav,
    ...EXTRA_DESTINATIONS,
    { title: SETTINGS_NAV_ITEM.title, href: SETTINGS_NAV_ITEM.href, description: SETTINGS_NAV_ITEM.description, group: 'Settings', keywords: ['preferences', 'integrations', 'mlops'] },
  ];
}

const ADMIN_ROLES = new Set(['admin', 'owner', 'superadmin', 'super_admin', 'platform_admin']);

/**
 * Role gate for the Administration group. `undefined` means role information
 * is not available (still loading / not returned) - callers decide how to
 * treat that; server-side authorisation remains authoritative either way.
 */
export function resolveAdminAccess(userRole?: string | null, orgRole?: string | null): boolean | undefined {
  const roles = [userRole, orgRole].filter((role): role is string => typeof role === 'string' && role.length > 0);
  if (roles.length === 0) return undefined;
  return roles.some((role) => ADMIN_ROLES.has(role.trim().toLowerCase()));
}
