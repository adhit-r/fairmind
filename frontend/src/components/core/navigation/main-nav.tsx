"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/common/button"
import { Badge } from "@/components/ui/common/badge"
import { Fingerprint } from "lucide-react"

export function MainNav() {
  const pathname = usePathname()

  const routes = [
    {
      href: "/",
      label: "Home",
      active: pathname === "/",
    },
    {
      href: "/about",
      label: "About",
      active: pathname === "/about",
    },
    {
      href: "/features",
      label: "Features",
      active: pathname === "/features",
    },
    {
      href: "/bias-detection",
      label: "Bias Detection",
      active: pathname === "/bias-detection",
      badge: "New",
    },
    {
      href: "/bias-test",
      label: "Bias Test",
      active: pathname === "/bias-test",
      badge: "Test",
    },
    {
      href: "/geographic-bias",
      label: "Geographic Bias",
      active: pathname === "/geographic-bias",
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
    {
      href: "/provenance",
      label: "Provenance",
      active: pathname === "/provenance",
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
      <Link href="/provenance" className="flex items-center gap-2 px-3 py-2 text-sm rounded-md hover:bg-gray-100 dark:hover:bg-gray-800">
        <Fingerprint className="h-4 w-4" />
        Provenance
      </Link>
    </nav>
  )
} 