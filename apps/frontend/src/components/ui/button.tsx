import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"

import * as React from "react"

import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center whitespace-nowrap rounded-full text-[13px] font-semibold ring-offset-white transition-colors gap-2 [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--fm-ink)] focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-60",
  {
    variants: {
      variant: {
        default: "bg-[var(--fm-ink)] text-white hover:bg-black",
        noShadow: "bg-[var(--fm-ink)] text-white hover:bg-black",
        reverse: "bg-[var(--fm-ink)] text-white hover:bg-black",
        neutral:
          "border border-[var(--fm-line)] bg-white font-medium text-[var(--fm-ink2)] hover:border-[var(--fm-ink)] hover:text-[var(--fm-ink)]",
        outline:
          "border border-[var(--fm-line)] bg-white font-medium text-[var(--fm-ink2)] hover:border-[var(--fm-ink)] hover:text-[var(--fm-ink)]",
        secondary: "bg-[var(--fm-bg)] font-medium text-[var(--fm-ink)] hover:bg-[rgba(21,23,26,.08)]",
        light: "bg-[var(--fm-bg)] font-medium text-[var(--fm-ink)] hover:bg-[rgba(21,23,26,.08)]",
        destructive: "bg-[#b4232c] text-white hover:bg-[#961d25]",
      },
      size: {
        default: "h-10 px-4",
        sm: "h-9 px-3.5 text-[12.5px]",
        lg: "h-11 px-6",
        icon: "size-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  },
)

const Button = React.forwardRef<
  HTMLButtonElement,
  React.ComponentProps<"button"> &
    VariantProps<typeof buttonVariants> & {
      asChild?: boolean
    }
>(({ className, variant, size, asChild = false, ...props }, ref) => {
  const Comp = asChild ? Slot : "button"

  return (
    <Comp
      ref={ref}
      data-slot="button"
      className={cn(buttonVariants({ variant, size, className }))}
      {...props}
    />
  )
})
Button.displayName = "Button"

export { Button, buttonVariants }
