'use client'

import * as React from 'react'
import { IconSearch } from '@tabler/icons-react'

import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { cn } from '@/lib/utils'

const ALL = '__all__'

export interface FilterOption {
  value: string
  label: string
}

export interface FilterSelect {
  id: string
  label: string
  /** Current value; '' means "all". */
  value: string
  onChange: (value: string) => void
  options: FilterOption[]
  allLabel?: string
}

export interface FilterBarProps {
  search?: {
    value: string
    onChange: (value: string) => void
    placeholder?: string
    label?: string
  }
  filters?: FilterSelect[]
  /** Right-aligned extras (export button, view toggle...). */
  actions?: React.ReactNode
  children?: React.ReactNode
  className?: string
}

/** Search + labelled selects row. Every control has a visible label. */
export function FilterBar({ search, filters, actions, children, className }: FilterBarProps) {
  const searchId = React.useId()
  return (
    <div role="search" className={cn('mb-4 flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-end', className)}>
      {search && (
        <div className="min-w-0 flex-1 space-y-1 sm:min-w-[220px] sm:max-w-sm">
          <Label htmlFor={searchId} className="text-xs text-muted-foreground">{search.label ?? 'Search'}</Label>
          <div className="relative">
            <IconSearch className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" aria-hidden="true" />
            <Input
              id={searchId}
              type="search"
              value={search.value}
              onChange={(event) => search.onChange(event.target.value)}
              placeholder={search.placeholder ?? 'Search...'}
              className="pl-9"
            />
          </div>
        </div>
      )}
      {filters?.map((filter) => (
        <div key={filter.id} className="space-y-1 sm:w-48">
          <Label htmlFor={`${filter.id}-trigger`} className="text-xs text-muted-foreground">{filter.label}</Label>
          <Select value={filter.value || ALL} onValueChange={(next) => filter.onChange(next === ALL ? '' : next)}>
            <SelectTrigger id={`${filter.id}-trigger`}>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value={ALL}>{filter.allLabel ?? 'All'}</SelectItem>
              {filter.options.map((option) => (
                <SelectItem key={option.value} value={option.value}>{option.label}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      ))}
      {children}
      {actions && <div className="flex flex-wrap items-center gap-2 sm:ml-auto">{actions}</div>}
    </div>
  )
}
