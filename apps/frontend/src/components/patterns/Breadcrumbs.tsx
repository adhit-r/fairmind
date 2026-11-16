import * as React from 'react'
import Link from 'next/link'
import { IconChevronRight } from '@tabler/icons-react'

import { cn } from '@/lib/utils'

export interface BreadcrumbItem {
  label: string
  href?: string
}

export interface BreadcrumbsProps {
  items: BreadcrumbItem[]
  className?: string
}

export function Breadcrumbs({ items, className }: BreadcrumbsProps) {
  if (items.length === 0) return null
  return (
    <nav aria-label="Breadcrumb" className={className}>
      <ol className="flex flex-wrap items-center gap-1 text-xs text-muted-foreground">
        {items.map((item, index) => {
          const isLast = index === items.length - 1
          return (
            <li key={`${item.label}-${index}`} className="flex items-center gap-1">
              {item.href && !isLast ? (
                <Link
                  href={item.href}
                  className={cn(
                    'inline-flex min-h-6 items-center rounded-sm hover:text-foreground hover:underline',
                    'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring',
                  )}
                >
                  {item.label}
                </Link>
              ) : (
                <span aria-current={isLast ? 'page' : undefined} className={cn(isLast && 'font-medium text-foreground')}>
                  {item.label}
                </span>
              )}
              {!isLast && <IconChevronRight className="h-3 w-3" aria-hidden="true" />}
            </li>
          )
        })}
      </ol>
    </nav>
  )
}
