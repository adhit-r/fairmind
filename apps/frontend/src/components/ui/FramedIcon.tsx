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
          'flex h-8 w-8 shrink-0 items-center justify-center border-2 border-[#0F1412] shadow-[2px_2px_0_0_#0F1412]',
          active ? 'bg-[#FF6B35] text-[#0F1412]' : 'bg-[#FCFDF8] text-[#0F1412]',
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
    'group/framed-icon inline-flex min-h-11 min-w-11 items-center justify-center border-2 font-extrabold text-[#0F1412]',
    'outline outline-0 outline-offset-2 focus:outline-2 focus:outline-[#0F1412]',
    'transition-[transform,box-shadow,background-color,color] duration-150 ease-out',
    'motion-reduce:transition-none motion-reduce:transform-none',
    compact
      ? 'h-11 w-11 border-[#0F1412] bg-[#FCFDF8] shadow-[3px_3px_0_0_#0F1412] hover:translate-x-[2px] hover:translate-y-[2px] hover:bg-[#FF6B35] hover:shadow-none active:translate-x-[3px] active:translate-y-[3px] active:shadow-none'
      : 'w-full justify-start gap-3 border-transparent px-2 py-1.5 text-sm uppercase tracking-tight hover:border-[#0F1412] hover:bg-[#FF6B35]',
    compact && active && 'bg-[#0F1412] text-white shadow-[3px_3px_0_0_#FF6B35] hover:bg-[#0F1412]',
    !compact && active && 'border-[#0F1412] bg-[#0F1412] text-white hover:bg-[#0F1412] hover:text-white',
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
