import { ButtonHTMLAttributes, ReactNode } from "react";

interface NeonButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode;
  variant?: "primary" | "ghost";
}

export function NeonButton({
  children,
  variant = "primary",
  className = "",
  ...props
}: NeonButtonProps) {
  const base =
    "relative inline-flex items-center justify-center gap-2 px-5 py-2.5 " +
    "rounded-button font-mono text-sm font-semibold tracking-wide " +
    "transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 " +
    "focus-visible:ring-color-primary disabled:opacity-50 disabled:pointer-events-none";

  const styles: Record<string, string> = {
    primary:
      "bg-color-primary/12 text-color-primary " +
      "border border-color-primary/45 " +
      "hover:bg-color-primary/22 hover:border-color-primary/70 " +
      "neon-glow hover:shadow-[0_0_28px_rgb(var(--color-primary)/0.55)]",
    ghost:
      "bg-transparent text-color-primary " +
      "border border-color-primary/20 " +
      "hover:bg-color-primary/8 hover:border-color-primary/45",
  };

  return (
    <button type="button" className={`${base} ${styles[variant]} ${className}`} {...props}>
      {children}
    </button>
  );
}
