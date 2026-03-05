import React from "react"
import { NavLink } from "react-router"
import { cn } from "../../lib/utils"
import { 
  Activity, 
  Briefcase, 
  CalendarDays, 
  CheckSquare, 
  FileText, 
  Newspaper, 
  Settings, 
  LayoutDashboard
} from "lucide-react"

const NAV_ITEMS = [
  { name: "Command Centre", path: "/", icon: LayoutDashboard },
  { name: "Account Intel", path: "/intel", icon: Activity },
  { name: "Bid Packs", path: "/bids", icon: Briefcase },
  { name: "Tasks", path: "/tasks", icon: CheckSquare },
  { name: "Diary", path: "/diary", icon: CalendarDays },
  { name: "Documents", path: "/docs", icon: FileText },
  { name: "News Feed", path: "/news", icon: Newspaper },
]

export function Sidebar() {
  return (
    <aside className="w-64 h-screen border-r border-border-subtle bg-surface flex flex-col pt-6 z-10 glass-panel">
      {/* Brand */}
      <div className="px-6 mb-8 flex items-center gap-2">
        <span className="text-primary font-bold text-xl tracking-tight">aLiGN</span>
        <span className="text-text-faint text-xs font-medium uppercase tracking-widest">OS</span>
      </div>

      <nav className="flex-1 flex flex-col gap-1 px-3">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) => cn(
              "flex items-center gap-3 px-3 py-2.5 rounded-md text-sm font-medium transition-all relative overflow-hidden",
              isActive 
                ? "bg-primary/10 text-primary" 
                : "text-text-muted hover:bg-white/5 hover:text-text-main"
            )}
          >
            {({ isActive }) => (
              <>
                {isActive && (
                  <div className="absolute left-0 top-0 bottom-0 w-1 bg-primary glow-primary" />
                )}
                <item.icon className={cn("w-4 h-4", isActive ? "text-primary" : "text-text-muted")} />
                {item.name}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      <div className="p-4 mt-auto border-t border-border-subtle">
        <NavLink to="/settings" className="flex items-center gap-3 px-3 py-2 text-sm font-medium text-text-muted hover:text-text-main transition-colors">
          <Settings className="w-4 h-4" />
          System Config
        </NavLink>
      </div>
    </aside>
  )
}
