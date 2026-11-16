import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

/**
 * Generic badge. For domain states (risk, severity, status, verdicts) use
 * StatusBadge from @/components/patterns instead.
 */
const badgeVariants = cva(
  "inline-flex items-center gap-1 rounded-md border px-2 py-0.5 text-xs font-medium transition-colors",
  {
    variants: {
      variant: {
        default: "border-transparent bg-primary-subtle text-primary-strong",
        secondary: "border-transparent bg-secondary text-secondary-foreground",
        destructive: "border-transparent bg-destructive-subtle text-destructive-strong",
        outline: "border-border text-foreground",
        success: "border-transparent bg-success-subtle text-success-strong",
        warning: "border-transparent bg-warning-subtle text-warning-strong",
        info: "border-transparent bg-info-subtle text-info-strong",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  )
}

export { Badge, badgeVariants }
