// Icons
import {
  IconDashboard,
  IconBrain,
  IconShield,
  IconUsers,
  IconChartBar,
  IconSettings,
  IconFileText,
  IconDatabase,
  IconTarget,
  IconEye,
  IconLock,
  IconAccessible,
} from "@tabler/icons-react"

export interface NavLink {
  title: string
  label: string
  href: string
  icon: any
}

export interface SideLink extends NavLink {
  subs?: NavLink[]
}

export const sideLinks: SideLink[] = [
  {
    title: "Dashboard",
    label: "Dashboard",
    href: "/dashboard",
    icon: IconDashboard,
  },
  {
    title: "AI Models",
    label: "AI Models",
    href: "/models",
    icon: IconBrain,
    subs: [
      {
        title: "Model Registry",
        label: "Model Registry",
        href: "/models",
        icon: IconDatabase,
      },
      {
        title: "Model Assessment",
        label: "Model Assessment",
        href: "/model-assessment",
        icon: IconTarget,
      },
    ],
  },
  {
    title: "Responsible AI",
    label: "Responsible AI",
    href: "/responsible-ai",
    icon: IconShield,
    subs: [
      {
        title: "Fairness",
        label: "Fairness",
        href: "/responsible-ai/fairness",
        icon: IconUsers,
      },
      {
        title: "Transparency",
        label: "Transparency",
        href: "/responsible-ai/transparency",
        icon: IconEye,
      },
      {
        title: "Privacy & Security",
        label: "Privacy & Security",
        href: "/responsible-ai/privacy",
        icon: IconLock,
      },
      {
        title: "Inclusiveness",
        label: "Inclusiveness",
        href: "/responsible-ai/inclusiveness",
        icon: IconAccessible,
      },
    ],
  },
  {
    title: "Analytics",
    label: "Analytics",
    href: "/analytics",
    icon: IconChartBar,
  },
  {
    title: "Compliance",
    label: "Compliance",
    href: "/compliance",
    icon: IconFileText,
  },
  {
    title: "Settings",
    label: "Settings",
    href: "/settings",
    icon: IconSettings,
  },
]

