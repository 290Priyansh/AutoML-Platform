"use client";

import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cn } from "../../lib/utils";

const Button = React.forwardRef<
  HTMLButtonElement,
  React.ButtonHTMLAttributes<HTMLButtonElement> & {
    variant?: "default" | "destructive" | "outline" | "secondary" | "ghost" | "link";
    size?: "default" | "sm" | "lg" | "icon";
    asChild?: boolean;
  }
>(({ className, variant = "default", size = "default", asChild = false, ...props }, ref) => {
  const Comp = asChild ? Slot : "button";
  return (
    <Comp
      className={cn(
        "inline-flex items-center justify-center whitespace-nowrap squircle-sm text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--accent)] focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-40 cursor-pointer",
        {
          "bg-[var(--accent)] text-[var(--accent-contrast)] hover:bg-[var(--accent-hover)] border border-black/10 dark:border-white/10 shadow-[var(--shadow-subtle)]": variant === "default",
          "bg-[var(--status-error)] text-white hover:opacity-90": variant === "destructive",
          "border border-[var(--border)] bg-transparent text-[var(--text)] hover:bg-[var(--surface-2)]": variant === "outline",
          "bg-[var(--surface-2)] text-[var(--text)] hover:bg-[var(--border)]": variant === "secondary",
          "text-[var(--text)] hover:bg-[var(--surface-2)]": variant === "ghost",
          "text-[var(--accent)] underline-offset-4 hover:underline": variant === "link",
        },
        {
          "h-9 px-4 py-2": size === "default",
          "h-8 px-3 text-xs": size === "sm",
          "h-11 px-6 text-base": size === "lg",
          "h-9 w-9": size === "icon",
        },
        className
      )}
      ref={ref}
      {...props}
    />
  );
});
Button.displayName = "Button";

export { Button };