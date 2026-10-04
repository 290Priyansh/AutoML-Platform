"use client";

import * as React from "react";
import { cn } from "../../lib/utils";

const TabsContext = React.createContext<{
  value?: string;
  onValueChange?: (value: string) => void;
}>({});

const Tabs = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement> & {
    defaultValue?: string;
    value?: string;
    onValueChange?: (value: string) => void;
  }
>(({ className, defaultValue, value: controlledValue, onValueChange, children, ...props }, ref) => {
  const [uncontrolledValue, setUncontrolledValue] = React.useState(defaultValue || "");
  const value = controlledValue !== undefined ? controlledValue : uncontrolledValue;

  const handleValueChange = (val: string) => {
    setUncontrolledValue(val);
    onValueChange?.(val);
  };

  return (
    <TabsContext.Provider value={{ value, onValueChange: handleValueChange }}>
      <div ref={ref} className={cn("flex flex-col gap-2", className)} {...props}>
        {children}
      </div>
    </TabsContext.Provider>
  );
});
Tabs.displayName = "Tabs";

const TabsList = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, children, ...props }, ref) => {
  return (
    <div
      ref={ref}
      role="tablist"
      aria-orientation="horizontal"
      className={cn(
        "inline-flex h-9 items-center justify-center squircle-sm border border-[var(--border)] bg-[var(--surface)] p-0.5 text-[var(--text-muted)]",
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
});
TabsList.displayName = "TabsList";

const TabsTrigger = React.forwardRef<
  HTMLButtonElement,
  React.ButtonHTMLAttributes<HTMLButtonElement> & {
    value: string;
  }
>(({ className, value, children, ...props }, ref) => {
  const context = React.useContext(TabsContext);
  const isActive = context.value === value;

  return (
    <button
      ref={ref}
      role="tab"
      type="button"
      aria-selected={isActive}
      data-state={isActive ? "active" : "inactive"}
      onClick={() => context.onValueChange?.(value)}
      className={cn(
        "inline-flex items-center justify-center whitespace-nowrap squircle-sm px-3 py-1 text-xs font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--accent)] disabled:pointer-events-none disabled:opacity-40 cursor-pointer",
        isActive
          ? "bg-[var(--surface-2)] text-[var(--text)] font-semibold shadow-none border border-[var(--border)]"
          : "text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-[var(--surface-2)]/60",
        className
      )}
      {...props}
    >
      {children}
    </button>
  );
});
TabsTrigger.displayName = "TabsTrigger";

const TabsContent = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement> & {
    value: string;
  }
>(({ className, value, children, ...props }, ref) => {
  const context = React.useContext(TabsContext);
  const isActive = context.value === value;

  if (!isActive) return null;

  return (
    <div
      ref={ref}
      role="tabpanel"
      data-state={isActive ? "active" : "inactive"}
      className={cn("mt-2 ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-purple-500 focus-visible:ring-offset-2", className)}
      {...props}
    >
      {children}
    </div>
  );
});
TabsContent.displayName = "TabsContent";

export { Tabs, TabsList, TabsTrigger, TabsContent };