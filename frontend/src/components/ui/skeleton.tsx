/**
 * Skeleton Component
 * Loading placeholder with shimmer animation
 * 
 * Usage:
 *   <Skeleton className="h-12 w-full" />
 *   <Skeleton className="h-4 w-32 rounded-full" />
 */

import { cn } from "@/lib/utils"

function Skeleton({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "animate-pulse rounded-md bg-muted/50",
        className
      )}
      {...props}
    />
  )
}

/**
 * Shimmer Skeleton - Enhanced version with shimmer effect
 */
function ShimmerSkeleton({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "relative overflow-hidden rounded-md bg-muted/30",
        "before:absolute before:inset-0",
        "before:-translate-x-full",
        "before:animate-[shimmer_2s_infinite]",
        "before:bg-gradient-to-r",
        "before:from-transparent before:via-muted/50 before:to-transparent",
        className
      )}
      {...props}
    />
  )
}

/**
 * Card Skeleton - Pre-made skeleton for card-like content
 */
function CardSkeleton({ className }: { className?: string }) {
  return (
    <div className={cn("space-y-4 p-6 border border-border rounded-lg", className)}>
      <Skeleton className="h-6 w-2/3" />
      <Skeleton className="h-4 w-full" />
      <Skeleton className="h-4 w-5/6" />
      <div className="flex gap-2 mt-4">
        <Skeleton className="h-10 w-20 rounded-full" />
        <Skeleton className="h-10 w-20 rounded-full" />
      </div>
    </div>
  )
}

/**
 * Table Row Skeleton
 */
function TableRowSkeleton({ columns = 4 }: { columns?: number }) {
  return (
    <div className="flex items-center gap-4 py-4 border-b border-border">
      {Array.from({ length: columns }).map((_, i) => (
        <Skeleton key={i} className="h-4 flex-1" />
      ))}
    </div>
  )
}

/**
 * Client Status Row Skeleton - Matches ClientStatusRow layout
 */
function ClientStatusRowSkeleton() {
  return (
    <div className="bg-card border border-border rounded-2xl p-6">
      <div className="flex items-center justify-between">
        {/* Client Name */}
        <div className="flex-1">
          <Skeleton className="h-6 w-48 mb-2" />
        </div>

        {/* Status Indicators */}
        <div className="flex items-center gap-6 mr-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="text-center">
              <Skeleton className="h-3 w-12 mb-2 mx-auto" />
              <Skeleton className="h-12 w-16 rounded-lg" />
            </div>
          ))}
        </div>

        {/* Arrow */}
        <Skeleton className="h-5 w-5 rounded" />
      </div>
    </div>
  )
}

export { Skeleton, ShimmerSkeleton, CardSkeleton, TableRowSkeleton, ClientStatusRowSkeleton }
