'use client'

import Link from 'next/link'
import * as React from 'react'
import type { TablerIcon } from '@tabler/icons-react'

import { cn } from '@/lib/utils'

type IconComponent = TablerIcon

type SharedProps = {
  icon: IconComponent
  label: string
  text?: React.ReactNode
  trailing?: React.ReactNode
  active?: boolean
}

type FramedIconButtonProps = SharedProps &
  Omit<React.ButtonHTMLAttributes<HTMLButtonElement>, 'aria-label' | 'children'> & {
    href?: undefined
  }

type FramedIconLinkProps = SharedProps &
  Omit<React.AnchorHTMLAttributes<HTMLAnchorElement>, 'aria-label' | 'children' | 'href'> & {
    href: string
  }

export type FramedIconProps = FramedIconButtonProps | FramedIconLinkProps

function FramedIconContent({
  icon: Icon,
  text,
  trailing,
  active,
}: Pick<FramedIconProps, 'icon' | 'text' | 'trailing' | 'active'>) {
  if (!text) {
    return <Icon className="h-5 w-5" aria-hidden focusable="false" />
  }

  return (
    <>
      <span
        aria-hidden="true"
        className={cn(
          'flex h-8 w-8 shrink-0 items-center justify-center rounded-full',
          active ? 'bg-white/15 text-white' : 'bg-[var(--fm-bg)] text-[var(--fm-ink)]',
        )}
      >
        <Icon className="h-4 w-4" aria-hidden focusable="false" />
      </span>
      <span className="min-w-0 flex-1 truncate text-left">{text}</span>
      {trailing}
    </>
  )
}

export const FramedIcon = React.forwardRef<
  HTMLButtonElement | HTMLAnchorElement,
  FramedIconProps
>(function FramedIcon(props, forwardedRef) {
  const { icon, label, text, trailing, active = false, className } = props
  const compact = !text
  const classes = cn(
    'group/framed-icon inline-flex min-h-10 min-w-10 items-center justify-center font-medium text-[var(--fm-ink)]',
    'outline outline-0 outline-offset-2 focus-visible:outline-2 focus-visible:outline-[var(--fm-ink)]',
    'transition-colors duration-150 ease-out motion-reduce:transition-none',
    compact
      ? 'h-10 w-10 rounded-full border border-[var(--fm-line)] bg-white hover:border-[var(--fm-ink)]'
      : 'w-full justify-start gap-3 rounded-[10px] px-2 py-1.5 text-[13.5px] hover:bg-[var(--fm-bg)]',
    active && 'bg-[var(--fm-ink)] text-white hover:bg-black',
    className,
  )
  const content = (
    <FramedIconContent icon={icon} text={text} trailing={trailing} active={active} />
  )

  if ('href' in props && props.href) {
    const {
      href,
      icon: _icon,
      label: _label,
      text: _text,
      trailing: _trailing,
      active: _active,
      className: _className,
      ...anchorProps
    } = props
    return (
      <Link
        {...anchorProps}
        ref={forwardedRef as React.Ref<HTMLAnchorElement>}
        href={href}
        aria-label={label}
        data-framed-icon="true"
        className={classes}
      >
        {content}
      </Link>
    )
  }

  const buttonOnlyProps = props as FramedIconButtonProps
  const {
    icon: _icon,
    label: _label,
    text: _text,
    trailing: _trailing,
    active: _active,
    className: _className,
    type = 'button',
    ...buttonProps
  } = buttonOnlyProps
  return (
    <button
      {...buttonProps}
      ref={forwardedRef as React.Ref<HTMLButtonElement>}
      type={type}
      aria-label={label}
      data-framed-icon="true"
      className={classes}
    >
      {content}
    </button>
  )
})
