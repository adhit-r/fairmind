import * as React from 'react'

import { OrangeLogo } from '@/components/OrangeLogo'
import { cn } from '@/lib/utils'

interface AuthShellProps {
  title: string
  description?: React.ReactNode
  children: React.ReactNode
  footer?: React.ReactNode
  /** Card width: default max-w-md, wide max-w-lg. */
  wide?: boolean
}

/**
 * Centered card used by every auth screen (login, register, callback,
 * invitations). Auth routes render outside the product shell, so this provides
 * its own <main> landmark and the page's single <h1>.
 */
export function AuthShell({ title, description, children, footer, wide = false }: AuthShellProps) {
  return (
    <main id="main-content" className="flex min-h-screen items-center justify-center bg-background p-4">
      <div className={cn('w-full rounded-lg border border-border bg-card p-6 sm:p-8', wide ? 'max-w-lg' : 'max-w-md')}>
        <div className="mb-6 flex flex-col items-center text-center">
          <OrangeLogo size="lg" showText />
          <h1 className="mt-5 text-2xl font-semibold tracking-tight text-foreground">{title}</h1>
          {description && <p className="mt-1 text-sm text-muted-foreground">{description}</p>}
        </div>
        {children}
        {footer && <div className="mt-6 text-center text-sm text-muted-foreground">{footer}</div>}
      </div>
    </main>
  )
}
