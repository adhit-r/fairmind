import {
  Bot,
  ClipboardCheck,
  FileCheck2,
  FlaskConical,
  Gauge,
  Home,
  Inbox,
  Layers,
  Leaf,
  ListChecks,
  MessageSquare,
  Package,
  PlayCircle,
  Radar,
  Rocket,
  Scale,
  ScrollText,
  Settings,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  Stamp,
  type LucideIcon,
} from 'lucide-react'

/** A page in the menu. `count` names a live count the shell reads from the API; the shell never shows a made-up number. */
export type Place = { href: string; label: string; icon: LucideIcon; count?: 'needs' | 'systems' | 'found' | 'runs' | 'findings' }
export type Group = { key: string; short: string; title: string; icon: LucideIcon; places: Place[] }

export const NAV: Group[] = [
  {
    key: 'start',
    short: 'Home',
    title: 'Home',
    icon: Home,
    places: [
      { href: '/dashboard', label: 'Home', icon: Gauge },
      { href: '/needs-you', label: 'Needs you', icon: Inbox, count: 'needs' },
    ],
  },
  {
    key: 'inventory',
    short: 'Inventory',
    title: 'Inventory',
    icon: Layers,
    places: [
      { href: '/systems', label: 'AI systems', icon: Layers, count: 'systems' },
      { href: '/discovery', label: 'Discovery', icon: Radar, count: 'found' },
    ],
  },
  {
    key: 'rules',
    short: 'Rules',
    title: 'Rules',
    icon: Scale,
    places: [
      { href: '/plan', label: 'Plan', icon: ListChecks },
      { href: '/frameworks', label: 'Frameworks', icon: Scale },
      { href: '/policies', label: 'Policies', icon: ScrollText },
    ],
  },
  {
    key: 'testing',
    short: 'Testing',
    title: 'Testing',
    icon: FlaskConical,
    places: [
      { href: '/evaluations', label: 'Evaluations', icon: FlaskConical },
      { href: '/runs', label: 'Runs', icon: PlayCircle, count: 'runs' },
      { href: '/agent-audits', label: 'Agent audits', icon: ShieldCheck },
    ],
  },
  {
    key: 'release',
    short: 'Release',
    title: 'Release and operate',
    icon: Rocket,
    places: [
      { href: '/decisions', label: 'Decisions', icon: Stamp },
      { href: '/monitoring', label: 'Monitoring', icon: Gauge },
      { href: '/findings', label: 'Findings', icon: ShieldAlert, count: 'findings' },
      { href: '/environment', label: 'Environment', icon: Leaf },
    ],
  },
  {
    key: 'records',
    short: 'Records',
    title: 'Records',
    icon: FileCheck2,
    places: [
      { href: '/evidence', label: 'Evidence', icon: ClipboardCheck },
      { href: '/auditor-packs', label: 'Auditor packs', icon: Package },
    ],
  },
  {
    key: 'agents',
    short: 'Agents',
    title: 'Agents',
    icon: Bot,
    places: [
      { href: '/autopilot', label: 'Autopilot', icon: Sparkles },
      { href: '/ask', label: 'Ask FairMind', icon: MessageSquare },
    ],
  },
]

export const SETTINGS: Place = { href: '/settings', label: 'Settings', icon: Settings }

export const ALL: Place[] = [...NAV.flatMap((g) => g.places), SETTINGS]

const within = (path: string, href: string) => path === href || path.startsWith(`${href}/`)

/** The group a path belongs to. A system file keeps Inventory lit; a page outside the menu lights nothing. */
export function groupOf(path: string): Group | null {
  return NAV.find((g) => g.places.some((p) => within(path, p.href))) ?? null
}

export function isOn(path: string, place: Place) {
  return within(path, place.href)
}
