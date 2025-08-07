"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"

export function MainNav() {
  const pathname = usePathname()

  const routes = [
    {
      href: "/",
      label: "Dashboard",
      active: pathname === "/",
    },
    {
      href: "/geographic-bias",
      label: "Geographic Bias",
      active: pathname === "/geographic-bias",
      badge: "New",
    },
    {
      href: "/models",
      label: "Models",
      active: pathname === "/models",
    },
    {
      href: "/compliance",
      label: "Compliance",
      active: pathname === "/compliance",
    },
    {
      href: "/reports",
      label: "Reports",
      active: pathname === "/reports",
    },
    {
      href: "/settings",
      label: "Settings",
      active: pathname === "/settings",
    },
    {
      href: "/ai-dna-profiling",
      label: "AI DNA Profiling",
      active: pathname === "/ai-dna-profiling",
    },
    {
      href: "/ai-genetic-engineering",
      label: "AI Genetic Engineering",
      active: pathname === "/ai-genetic-engineering",
    },
    {
      href: "/ai-time-travel",
      label: "AI Time Travel",
      active: pathname === "/ai-time-travel",
    },
    {
      href: "/ai-circus",
      label: "AI Circus",
      active: pathname === "/ai-circus",
    },
    {
      href: "/ai-ethics-observatory",
      label: "AI Ethics Observatory",
      active: pathname === "/ai-ethics-observatory",
    },
  ]

  return (
    <nav className="flex items-center space-x-4 lg:space-x-6">
      {routes.map((route) => (
        <Link
          key={route.href}
          href={route.href}
          className={cn(
            "text-sm font-medium transition-colors hover:text-primary",
            route.active ? "text-black dark:text-white" : "text-muted-foreground"
          )}
        >
          <div className="flex items-center space-x-1">
            <span>{route.label}</span>
            {route.badge && (
              <Badge variant="secondary" className="text-xs">
                {route.badge}
              </Badge>
            )}
          </div>
        </Link>
      ))}
    </nav>
  )
} 