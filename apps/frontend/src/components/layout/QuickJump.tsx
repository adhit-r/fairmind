'use client'

import * as React from 'react'
import { useRouter } from 'next/navigation'
import { IconCornerDownLeft, IconSearch } from '@tabler/icons-react'

import { Dialog, DialogContent, DialogDescription, DialogTitle } from '@/components/ui/dialog'
import { useSession } from '@/context/SessionContext'
import { useOptionalOrg } from '@/context/OrgContext'
import { getQuickJumpDestinations, resolveAdminAccess, type QuickJumpDestination } from '@/lib/constants/navigation'
import { cn } from '@/lib/utils'

function matches(destination: QuickJumpDestination, query: string) {
  const needle = query.trim().toLowerCase()
  if (!needle) return true
  const haystack = [destination.title, destination.group, destination.description, ...destination.keywords].join(' ').toLowerCase()
  return needle.split(/\s+/).every((part) => haystack.includes(part))
}

/**
 * Header quick-jump: filters navigation destinations. Opens with the trigger
 * button or Ctrl/Cmd+K. Arrow keys move, Enter navigates, Escape closes.
 */
export function QuickJump({ className }: { className?: string }) {
  const router = useRouter()
  const { user } = useSession()
  const org = useOptionalOrg()
  const [open, setOpen] = React.useState(false)
  const [query, setQuery] = React.useState('')
  const [activeIndex, setActiveIndex] = React.useState(0)
  const listboxId = React.useId()

  const includeAdmin = resolveAdminAccess(user?.role, org?.selectedOrg?.role) !== false
  const results = React.useMemo(
    () => getQuickJumpDestinations(includeAdmin).filter((destination) => matches(destination, query)),
    [includeAdmin, query],
  )

  React.useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key.toLowerCase() === 'k' && (event.metaKey || event.ctrlKey)) {
        event.preventDefault()
        setOpen((current) => !current)
      }
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [])

  React.useEffect(() => {
    if (!open) {
      setQuery('')
      setActiveIndex(0)
    }
  }, [open])

  React.useEffect(() => {
    setActiveIndex(0)
  }, [query])

  const go = (destination: QuickJumpDestination | undefined) => {
    if (!destination) return
    setOpen(false)
    router.push(destination.href)
  }

  const onInputKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'ArrowDown') {
      event.preventDefault()
      setActiveIndex((index) => (results.length === 0 ? 0 : (index + 1) % results.length))
    } else if (event.key === 'ArrowUp') {
      event.preventDefault()
      setActiveIndex((index) => (results.length === 0 ? 0 : (index - 1 + results.length) % results.length))
    } else if (event.key === 'Enter') {
      event.preventDefault()
      go(results[activeIndex])
    }
  }

  const optionId = (index: number) => `${listboxId}-option-${index}`

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        aria-label="Jump to a page (Control K)"
        aria-haspopup="dialog"
        className={cn(
          'inline-flex h-11 min-w-11 items-center justify-center gap-2 rounded-md border border-input bg-card px-3 text-sm text-muted-foreground transition-colors hover:bg-accent',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background',
          'lg:w-72 lg:justify-start',
          className,
        )}
      >
        <IconSearch className="h-4 w-4 shrink-0" aria-hidden="true" />
        <span className="hidden truncate lg:inline">Jump to a page</span>
        <kbd className="ml-auto hidden rounded border border-border bg-muted px-1.5 py-0.5 text-[10px] font-medium text-muted-foreground lg:inline">Ctrl K</kbd>
      </button>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="top-[20%] max-w-xl translate-y-0 gap-0 p-0 sm:p-0">
          <DialogTitle className="sr-only">Jump to a page</DialogTitle>
          <DialogDescription className="sr-only">Type to filter pages. Use the arrow keys and Enter to open one.</DialogDescription>
          <div className="flex items-center gap-2 border-b border-border px-4 pr-12">
            <IconSearch className="h-4 w-4 shrink-0 text-muted-foreground" aria-hidden="true" />
            <input
              autoFocus
              role="combobox"
              aria-expanded="true"
              aria-controls={listboxId}
              aria-activedescendant={results.length > 0 ? optionId(activeIndex) : undefined}
              aria-label="Search pages"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              onKeyDown={onInputKeyDown}
              placeholder="Search pages, e.g. evidence, findings, members"
              className="h-12 min-h-[44px] flex-1 bg-transparent text-sm text-foreground outline-none placeholder:text-muted-foreground"
            />
          </div>
          <ul id={listboxId} role="listbox" aria-label="Pages" className="max-h-80 overflow-y-auto p-2">
            {results.length === 0 && (
              <li role="presentation" className="px-3 py-6 text-center text-sm text-muted-foreground">
                No pages match &ldquo;{query}&rdquo;.
              </li>
            )}
            {results.map((destination, index) => (
              <li
                key={`${destination.href}-${destination.title}`}
                id={optionId(index)}
                role="option"
                aria-selected={index === activeIndex}
                onMouseEnter={() => setActiveIndex(index)}
                onClick={() => go(destination)}
                className={cn(
                  'flex min-h-11 cursor-pointer items-center justify-between gap-3 rounded-md px-3 py-2',
                  index === activeIndex && 'bg-accent',
                )}
              >
                <span className="min-w-0">
                  <span className="block truncate text-sm font-medium text-foreground">{destination.title}</span>
                  <span className="block truncate text-xs text-muted-foreground">{destination.description}</span>
                </span>
                <span className="flex shrink-0 items-center gap-2 text-xs text-muted-foreground">
                  {destination.group}
                  {index === activeIndex && <IconCornerDownLeft className="h-3.5 w-3.5" aria-hidden="true" />}
                </span>
              </li>
            ))}
          </ul>
        </DialogContent>
      </Dialog>
    </>
  )
}
