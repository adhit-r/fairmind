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
          'group/identity inline-flex min-h-11 items-center border-2 border-[#0F1412] bg-[#FCFDF8] text-left text-[#0F1412]',
          'shadow-[3px_3px_0_0_#0F1412] outline outline-0 outline-offset-2 focus:outline-2 focus:outline-[#0F1412]',
          'transition-[transform,box-shadow,background-color] duration-150 ease-out hover:translate-x-[2px] hover:translate-y-[2px] hover:bg-[#FF6B35] hover:shadow-none',
          'active:translate-x-[3px] active:translate-y-[3px] active:shadow-none motion-reduce:transition-none motion-reduce:transform-none',
          collapsed ? 'h-11 w-11 justify-center p-0' : 'w-full gap-3 p-2',
          className,
        )}
      >
        <span className={cn('relative flex shrink-0 items-center justify-center overflow-hidden bg-[#FF6B35]', collapsed ? 'h-10 w-10' : 'h-11 w-11 border-2 border-[#0F1412]')}>
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
              className="flex h-full w-full items-center justify-center bg-[#FF6B35] text-xs font-black"
            >
              {initials}
            </span>
          )}
        </span>
        {!collapsed && (
          <span className="min-w-0 flex-1">
            <span className="block truncate text-sm font-black uppercase">{name}</span>
            {email && <span className="block truncate text-xs font-bold text-[#3F4944]">{email}</span>}
            {status && <span className="block truncate text-xs font-bold text-[#3F4944]">{status}</span>}
          </span>
        )}
      </button>
    )
  },
)
