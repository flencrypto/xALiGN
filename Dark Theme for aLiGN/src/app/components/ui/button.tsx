import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cn } from "../../../lib/utils"

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  asChild?: boolean
  variant?: "default" | "outline" | "ghost" | "danger" | "nav"
  size?: "default" | "sm" | "lg" | "icon"
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "default", size = "default", asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button"
    return (
      <Comp
        className={cn(
          "inline-flex items-center justify-center whitespace-nowrap rounded-[6px] text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
          {
            "bg-primary text-[#0A0F1C] font-semibold glow-primary hover:glow-primary-hover hover:bg-primary-dark": variant === "default",
            "border border-primary text-primary hover:bg-primary/10": variant === "outline",
            "hover:bg-surface hover:text-text-main text-text-muted": variant === "ghost",
            "bg-danger text-white hover:bg-danger/90 shadow-sm": variant === "danger",
            "w-full justify-start gap-3 px-4 py-3 text-text-muted hover:bg-surface hover:text-text-main": variant === "nav",
            "h-10 px-4 py-2": size === "default",
            "h-8 rounded-[4px] px-3 text-xs": size === "sm",
            "h-11 rounded-[8px] px-8 text-base": size === "lg",
            "h-10 w-10": size === "icon",
          },
          className
        )}
        ref={ref}
        {...props}
      />
    )
  }
)
Button.displayName = "Button"

export { Button }
