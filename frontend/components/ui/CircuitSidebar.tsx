import { ReactNode } from "react";
import Link from "next/link";
import AlignLogo from "@/components/layout/AlignLogo";

interface NavItem {
  label: string;
  href: string;
  icon?: ReactNode;
}

interface CircuitSidebarProps {
  items?: NavItem[];
}

export function CircuitSidebar({ items = [] }: CircuitSidebarProps) {
  return (
    <aside
      className={
        "relative flex h-screen w-72 flex-col overflow-hidden " +
        "border-r border-color-primary/30 " +
        "bg-color-background font-mono text-color-primary"
      }
    >
      {/* vertical circuit line decoration */}
      <div
        aria-hidden="true"
        className={
          "pointer-events-none absolute inset-0 " +
          "bg-[linear-gradient(90deg,rgb(var(--color-primary)/0.05)_1px,transparent_1px)," +
          "linear-gradient(0deg,rgb(var(--color-primary)/0.05)_1px,transparent_1px)] " +
          "bg-[size:24px_24px]"
        }
      />

      {/* logo */}
      <div className="relative z-10 flex items-center gap-3 px-6 py-8 mb-4">
        <AlignLogo compact />
      </div>

      {/* nav items */}
      <nav className="relative z-10 flex flex-col gap-1 px-3 flex-1 overflow-y-auto">
        {items.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={
              "group flex items-center gap-3 rounded-lg px-4 py-2.5 text-sm " +
              "text-color-primary/75 " +
              "hover:bg-color-primary/8 " +
              "hover:text-color-primary " +
              "hover:shadow-[0_0_12px_rgb(var(--color-primary)/0.20)] " +
              "transition-all duration-150"
            }
          >
            {item.icon && (
              <span className="flex-shrink-0 transition-transform duration-150 group-hover:scale-110">
                {item.icon}
              </span>
            )}
            <span className="truncate">{item.label}</span>
          </Link>
        ))}
      </nav>

      {/* bottom glow strip */}
      <div
        aria-hidden="true"
        className={
          "pointer-events-none absolute bottom-0 left-0 right-0 h-24 " +
          "bg-[linear-gradient(to_top,rgb(var(--color-primary)/0.08),transparent)]"
        }
      />
    </aside>
  );
}
