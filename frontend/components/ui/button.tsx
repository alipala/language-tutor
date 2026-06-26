import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 rounded-xl font-semibold transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand focus-visible:ring-offset-2 focus-visible:ring-offset-bg disabled:pointer-events-none disabled:opacity-50 active:scale-[0.98]",
  {
    variants: {
      variant: {
        // Brand-filled primary CTA
        primary:
          "bg-brand text-brand-ink shadow-e1 hover:shadow-glow hover:scale-[1.02]",
        // Glass secondary
        secondary:
          "border border-white/15 bg-white/[0.06] text-white hover:bg-white/10 hover:border-brand/40",
        // Subtle ghost
        ghost: "text-white/70 hover:text-white hover:bg-white/[0.08]",
        // Destructive
        danger: "bg-danger text-white hover:bg-danger/90",
        // Outline
        outline:
          "border border-white/15 bg-transparent text-white hover:bg-white/[0.06] hover:border-brand/40",
        // Inline link
        link: "text-brand underline-offset-4 hover:underline",
        // Legacy default kept as alias of primary for back-compat
        default: "bg-brand text-brand-ink shadow-e1 hover:shadow-glow hover:scale-[1.02]",
      },
      size: {
        sm: "h-9 px-3 text-sm",
        default: "h-11 px-5 text-sm",
        lg: "h-12 px-7 text-base",
        // 48px min touch target for mobile
        touch: "min-h-[48px] px-6 text-sm",
        icon: "h-11 w-11",
      },
    },
    defaultVariants: {
      variant: "primary",
      size: "default",
    },
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button"
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    )
  }
)
Button.displayName = "Button"

export { Button, buttonVariants }
