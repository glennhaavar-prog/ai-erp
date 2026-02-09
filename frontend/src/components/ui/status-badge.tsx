/**
 * StatusBadge Component
 * Semantic badge component for status indicators
 * 
 * Usage:
 *   <StatusBadge variant="success">Approved</StatusBadge>
 *   <StatusBadge variant="warning" icon={<Clock />}>Pending</StatusBadge>
 */

import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { AlertCircle, CheckCircle2, Clock, XCircle, Info } from "lucide-react"
import { cn } from "@/lib/utils"

const statusBadgeVariants = cva(
  "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium transition-colors cursor-default",
  {
    variants: {
      variant: {
        // Success - Green
        success:
          "bg-green-500/10 text-green-700 border-green-500/20 dark:bg-green-500/10 dark:text-green-400 dark:border-green-500/30",
        // Warning - Amber
        warning:
          "bg-amber-500/10 text-amber-700 border-amber-500/20 dark:bg-amber-500/10 dark:text-amber-400 dark:border-amber-500/30",
        // Error/Destructive - Red
        error:
          "bg-red-500/10 text-red-700 border-red-500/20 dark:bg-red-500/10 dark:text-red-400 dark:border-red-500/30",
        // Info - Blue
        info:
          "bg-blue-500/10 text-blue-700 border-blue-500/20 dark:bg-blue-500/10 dark:text-blue-400 dark:border-blue-500/30",
        // Neutral - Gray
        neutral:
          "bg-gray-500/10 text-gray-700 border-gray-500/20 dark:bg-gray-500/10 dark:text-gray-400 dark:border-gray-500/30",
      },
      size: {
        sm: "text-xs px-2 py-0.5",
        md: "text-sm px-2.5 py-0.5",
        lg: "text-sm px-3 py-1",
      },
    },
    defaultVariants: {
      variant: "neutral",
      size: "sm",
    },
  }
)

export interface StatusBadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof statusBadgeVariants> {
  icon?: React.ReactNode
  showDefaultIcon?: boolean
}

const defaultIcons = {
  success: CheckCircle2,
  warning: Clock,
  error: XCircle,
  info: Info,
  neutral: AlertCircle,
}

function StatusBadge({ 
  className, 
  variant = "neutral", 
  size = "sm",
  icon,
  showDefaultIcon = false,
  children,
  ...props 
}: StatusBadgeProps) {
  const DefaultIcon = variant ? defaultIcons[variant] : null
  
  return (
    <div className={cn(statusBadgeVariants({ variant, size }), className)} {...props}>
      {icon || (showDefaultIcon && DefaultIcon && <DefaultIcon className="w-3 h-3" />)}
      {children}
    </div>
  )
}

export { StatusBadge, statusBadgeVariants }
