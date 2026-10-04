"use client";

import * as React from "react";
import { cn } from "../../lib/utils";

const Progress = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement> & {
    value?: number;
    max?: number;
  }
>(({ className, value = 0, max = 100, ...props }, ref) => {
  const percentage = Math.min(Math.max((value / max) * 100, 0), 100);
  return (
    <div
      ref={ref}
      className={cn(
        "relative h-1.5 w-full overflow-hidden squircle-sm bg-[var(--surface-2)] border border-[var(--border)]",
        className
      )}
      {...props}
    >
      <div
        className="h-full bg-[var(--accent)] transition-all duration-300 ease-out squircle-sm"
        style={{ width: `${percentage}%` }}
      />
    </div>
  );
});
Progress.displayName = "Progress";

export { Progress };