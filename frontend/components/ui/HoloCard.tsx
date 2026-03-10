import { ReactNode } from "react";

interface HoloCardProps {
  children: ReactNode;
  className?: string;
}

export function HoloCard({ children, className = "" }: HoloCardProps) {
  return (
    <div
      className={
        "relative overflow-hidden rounded-xl p-6 " +
        "bg-color-background/90 backdrop-blur-xl " +
        "border border-color-primary/30 " +
        "shadow-[0_0_20px_rgb(var(--color-primary)/0.15)] " +
        className
      }
    >
      {/* circuit grid overlay */}
      <div
        aria-hidden="true"
        className={
          "pointer-events-none absolute inset-0 " +
          "bg-[linear-gradient(90deg,rgb(var(--color-primary)/0.06)_1px,transparent_1px)," +
          "linear-gradient(0deg,rgb(var(--color-primary)/0.06)_1px,transparent_1px)] " +
          "bg-[size:20px_20px]"
        }
      />
      {/* holo sheen */}
      <div aria-hidden="true" className="pointer-events-none absolute inset-0 holo-shimmer rounded-xl" />
      <div className="relative z-10">{children}</div>
    </div>
  );
}
