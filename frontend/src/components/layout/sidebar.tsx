"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
  Users, BarChart2, Upload, Settings, LogOut, School,
  LayoutDashboard, SlidersHorizontal, FileText, ClipboardList,
} from "lucide-react";

interface NavItem {
  href: string;
  label: string;
  icon: React.ElementType;
  roles: string[];
  group?: "main" | "admin";
}

const NAV: NavItem[] = [
  { href: "/dashboard",         label: "Dashboard",     icon: LayoutDashboard,   roles: ["it_admin", "district_admin", "principal", "teacher"], group: "main" },
  { href: "/students",          label: "Students",      icon: Users,             roles: ["it_admin", "district_admin", "principal", "teacher"], group: "main" },
  { href: "/scores/entry",      label: "Enter Scores",  icon: BarChart2,         roles: ["it_admin", "principal", "teacher"], group: "main" },
  { href: "/scores/import",     label: "Import Scores", icon: Upload,            roles: ["it_admin", "principal", "teacher"], group: "main" },
  { href: "/reports",           label: "Reports",       icon: FileText,          roles: ["it_admin", "district_admin", "principal", "teacher"], group: "main" },
  { href: "/admin/users",       label: "Users",         icon: Settings,          roles: ["it_admin"], group: "admin" },
  { href: "/admin/schools",     label: "Schools",       icon: School,            roles: ["it_admin"], group: "admin" },
  { href: "/admin/classes",     label: "Classes",       icon: School,            roles: ["it_admin"], group: "admin" },
  { href: "/admin/subjects",    label: "Subjects",      icon: BarChart2,         roles: ["it_admin"], group: "admin" },
  { href: "/admin/benchmarks",  label: "Benchmarks",    icon: SlidersHorizontal, roles: ["it_admin", "district_admin"], group: "admin" },
  { href: "/admin/audit",       label: "Audit Log",     icon: ClipboardList,     roles: ["it_admin", "district_admin"], group: "admin" },
];

const ROLE_LABELS: Record<string, string> = {
  it_admin: "IT Admin",
  district_admin: "District Admin",
  principal: "Principal",
  teacher: "Teacher",
};

function CompassRose() {
  return (
    <svg width="30" height="30" viewBox="0 0 30 30" fill="none" aria-hidden="true">
      <circle cx="15" cy="15" r="13.5" stroke="currentColor" strokeWidth="1" strokeOpacity="0.25" />
      <circle cx="15" cy="15" r="10.5" stroke="currentColor" strokeWidth="0.5" strokeOpacity="0.15" />
      {/* Cardinal ticks */}
      <line x1="15" y1="1.5" x2="15" y2="5" stroke="currentColor" strokeWidth="1.5" strokeOpacity="0.35" strokeLinecap="round" />
      <line x1="15" y1="25" x2="15" y2="28.5" stroke="currentColor" strokeWidth="1.5" strokeOpacity="0.2" strokeLinecap="round" />
      <line x1="1.5" y1="15" x2="5" y2="15" stroke="currentColor" strokeWidth="1.5" strokeOpacity="0.2" strokeLinecap="round" />
      <line x1="25" y1="15" x2="28.5" y2="15" stroke="currentColor" strokeWidth="1.5" strokeOpacity="0.2" strokeLinecap="round" />
      {/* North needle — amber */}
      <path d="M15 5L17.2 13.5H12.8L15 5Z" fill="var(--cp-amber)" />
      {/* South needle — dim */}
      <path d="M15 25L12.8 16.5H17.2L15 25Z" fill="currentColor" opacity="0.22" />
      {/* Center jewel */}
      <circle cx="15" cy="15" r="2.5" fill="var(--cp-amber)" opacity="0.85" />
      <circle cx="15" cy="15" r="1.1" fill="currentColor" opacity="0.8" />
    </svg>
  );
}

function NavLink({ item, pathname }: { item: NavItem; pathname: string }) {
  const active = pathname === item.href || (item.href !== "/dashboard" && pathname.startsWith(item.href));
  return (
    <Link
      href={item.href}
      className={cn(
        "group relative flex items-center gap-2.5 px-3 py-2 rounded-md text-sm transition-all duration-150",
        active
          ? "bg-sidebar-primary/10 text-sidebar-primary font-medium"
          : "text-muted-foreground hover:bg-sidebar-accent/50 hover:text-sidebar-foreground"
      )}
    >
      {active && (
        <span className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-5 rounded-r bg-sidebar-primary" />
      )}
      <item.icon className={cn("h-4 w-4 shrink-0 transition-colors", active ? "text-sidebar-primary" : "opacity-60 group-hover:opacity-100")} />
      {item.label}
    </Link>
  );
}

export function Sidebar() {
  const { user, logout } = useAuth();
  const pathname = usePathname();
  const router = useRouter();

  const visible = NAV.filter((item) => user && item.roles.includes(user.role));
  const mainNav = visible.filter((item) => item.group === "main");
  const adminNav = visible.filter((item) => item.group === "admin");

  async function handleLogout() {
    await logout();
    router.push("/login");
  }

  return (
    <aside className="w-58 shrink-0 flex flex-col h-screen sticky top-0 border-r border-sidebar-border bg-sidebar">
      {/* Brand */}
      <div className="flex items-center gap-3 px-5 py-4 border-b border-sidebar-border">
        <div className="text-sidebar-foreground/70 shrink-0">
          <CompassRose />
        </div>
        <div className="min-w-0">
          <div
            className="text-xl font-semibold tracking-wide text-sidebar-foreground leading-none"
            style={{ fontFamily: "var(--font-heading)" }}
          >
            Compass
          </div>
          <div className="text-[9px] uppercase tracking-[0.2em] text-muted-foreground/70 mt-0.5 font-sans">
            Analytics
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-3 overflow-y-auto space-y-0.5">
        {mainNav.map((item) => (
          <NavLink key={item.href} item={item} pathname={pathname} />
        ))}

        {adminNav.length > 0 && (
          <>
            <div className="px-3 pt-5 pb-1.5">
              <span className="text-[9px] uppercase tracking-[0.18em] text-muted-foreground/50 font-semibold">
                Administration
              </span>
            </div>
            {adminNav.map((item) => (
              <NavLink key={item.href} item={item} pathname={pathname} />
            ))}
          </>
        )}
      </nav>

      {/* User footer */}
      <div className="px-3 py-3 border-t border-sidebar-border space-y-1">
        <div className="px-3 py-2 rounded-md bg-sidebar-accent/40">
          <div className="text-sm font-medium text-sidebar-foreground/90 truncate leading-tight">
            {user?.username}
          </div>
          <div className="text-xs text-muted-foreground mt-0.5">
            {user ? (ROLE_LABELS[user.role] ?? user.role) : ""}
          </div>
        </div>
        <Button
          variant="ghost"
          size="sm"
          className="w-full justify-start gap-2 text-muted-foreground hover:text-sidebar-foreground h-8"
          onClick={() => void handleLogout()}
        >
          <LogOut className="h-3.5 w-3.5" />
          Sign out
        </Button>
      </div>
    </aside>
  );
}
