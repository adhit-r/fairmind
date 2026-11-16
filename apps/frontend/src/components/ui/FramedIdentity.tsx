'use client'

import * as React from 'react'

import { cn } from '@/lib/utils'

export const APPROVED_PROFILE_PORTRAIT_URL = '/profile-portrait.svg'

export interface FramedIdentityProps
  extends Omit<React.ButtonHTMLAttributes<HTMLButtonElement>, 'children'> {
  name: string
  email?: string
  status?: string
  imageSrc?: string
  collapsed?: boolean
  label?: string
}

function initialsFor(name: string) {
  const words = name.trim().split(/\s+/).filter(Boolean)
  if (words.length === 0) return 'FM'
  return words.slice(0, 2).map((word) => word[0]?.toUpperCase()).join('')
}

/**
 * Account identity control using the self-hosted illustrated portrait, with a
 * labelled two-letter initials fallback when the image fails to load.
 */
export const FramedIdentity = React.forwardRef<HTMLButtonElement, FramedIdentityProps>(
  function FramedIdentity(
    {
      name,
      email,
      status,
      imageSrc = APPROVED_PROFILE_PORTRAIT_URL,
      collapsed = false,
      label = `${name} profile`,
      className,
      type = 'button',
      ...props
    },
    forwardedRef,
  ) {
    const [failedImageSource, setFailedImageSource] = React.useState<string | null>(null)
    const imageRef = React.useRef<HTMLImageElement>(null)
    const initials = initialsFor(name)
    const imageAvailable = failedImageSource !== imageSrc

    React.useEffect(() => {
      const image = imageRef.current
      if (image?.complete && image.naturalWidth === 0) {
        setFailedImageSource(imageSrc)
      }
    }, [imageSrc])

    return (
      <button
        {...props}
        ref={forwardedRef}
        type={type}
        aria-label={label}
        data-framed-identity="true"
        className={cn(
          'group/identity inline-flex min-h-11 items-center rounded-md text-left text-foreground',
          'transition-colors hover:bg-accent motion-reduce:transition-none',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background',
          collapsed ? 'h-11 w-11 justify-center p-0' : 'w-full gap-3 p-2',
          className,
        )}
      >
        <span
          className={cn(
            'relative flex shrink-0 items-center justify-center overflow-hidden rounded-md bg-accent-action',
            collapsed ? 'h-9 w-9' : 'h-10 w-10',
          )}
        >
          {imageAvailable ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              ref={imageRef}
              src={imageSrc}
              alt={`${name} illustrated profile`}
              className="h-full w-full object-cover"
              onError={() => setFailedImageSource(imageSrc)}
            />
          ) : (
            <span
              role="img"
              aria-label={`${name} profile image unavailable; showing initials ${initials}`}
              className="flex h-full w-full items-center justify-center bg-accent-action text-xs font-semibold text-accent-action-foreground"
            >
              {initials}
            </span>
          )}
        </span>
        {!collapsed && (
          <span className="min-w-0 flex-1">
            <span className="block truncate text-sm font-semibold">{name}</span>
            {email && <span className="block truncate text-xs text-muted-foreground">{email}</span>}
            {status && <span className="block truncate text-xs text-muted-foreground">{status}</span>}
          </span>
        )}
      </button>
    )
  },
)
