import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"

import * as React from "react"

import { cn } from "@/lib/utils"

/**
 * Variants:
 *  default     teal primary
 *  action      Action Orange: the single primary CTA of a view
 *  secondary   quiet surface
 *  outline     bordered
 *  ghost       no chrome
 *  destructive critical red
 *  link        text link
 * Legacy aliases (kept so existing pages compile): noShadow -> default,
 * neutral -> outline, reverse -> secondary.
 */
const buttonVariants = cva(
  "inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium transition-colors gap-2 [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground hover:bg-primary/90",
        action: "bg-accent-action text-accent-action-foreground hover:bg-accent-action/90",
        secondary: "bg-secondary text-secondary-foreground hover:bg-secondary/80",
        outline: "border border-input bg-card text-foreground hover:bg-accent",
        ghost: "text-foreground hover:bg-accent",
        destructive: "bg-destructive text-destructive-foreground hover:bg-destructive/90",
        link: "text-primary-strong underline-offset-4 hover:underline",
        /* legacy aliases - remove after migration */
        noShadow: "bg-primary text-primary-foreground hover:bg-primary/90",
        neutral: "border border-input bg-card text-foreground hover:bg-accent",
        reverse: "bg-secondary text-secondary-foreground hover:bg-secondary/80",
      },
      size: {
        default: "h-11 px-4 py-2 min-h-[44px]",
        sm: "h-9 px-3 min-h-[36px] md:h-9 max-md:h-11 max-md:min-h-[44px]",
        lg: "h-12 px-6 min-h-[48px] text-base",
        icon: "size-11 min-h-[44px] min-w-[44px]",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  },
)

export interface ButtonProps
  extends React.ComponentProps<"button">,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button"

    return (
      <Comp
        ref={ref}
        data-slot="button"
        className={cn(buttonVariants({ variant, size, className }))}
        {...props}
      />
    )
  },
)
Button.displayName = "Button"

export { Button, buttonVariants }
