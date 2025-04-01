"use client"

import * as React from "react"
import { cn } from "@/lib/utils"

// Custom progress component that doesn't rely on Radix UI
// This implementation provides the same functionality but avoids the dependency
const Progress = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement> & {
    value?: number;
    indicatorClassName?: string;
  }
>(({ className, value = 0, indicatorClassName, ...props }, ref) => {
  // Ensure value is between 0 and 100
  const clampedValue = Math.max(0, Math.min(100, value));
  
  return (
    <div
      ref={ref}
      className={cn(
        "relative h-4 w-full overflow-hidden rounded-full bg-secondary",
        className
      )}
      role="progressbar"
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={clampedValue}
      {...props}
    >
      <div
        className={cn(
          "h-full w-full flex-1 bg-primary transition-all",
          indicatorClassName
        )}
        style={{ transform: `translateX(-${100 - clampedValue}%)` }}
      />
    </div>
  );
});

Progress.displayName = "Progress";

export { Progress }
