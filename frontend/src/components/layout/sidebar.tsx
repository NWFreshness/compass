"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Users, BarChart2, Upload, Settings, LogOut, School, LayoutDashboard, SlidersHorizontal, FileText, ClipboardList } from "lucide-react";

interface NavItem {
  href: string;
  label: string;
  icon: React.ElementType;
  roles: string[];
}

const NAV: NavItem[] = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard, roles: ["it_admin", "district_admin", "principal", "teacher"] },
  { href: "/students", label: "Students", icon: Users, roles: ["it_admin", "district_admin", "principal", "teacher"] },
  { href: "/scores/entry", label: "Enter Scores", icon: BarChart2, roles: ["it_admin", "principal", "teacher"] },
  { href: "/scores/import", label: "Import Scores", icon: Upload, roles: ["it_admin", "principal", "teacher"] },
  { href: "/admin/users", label: "Users", icon: Settings, roles: ["it_admin"] },
  { href: "/admin/schools", label: "Schools", icon: School, roles: ["it_admin"] },
  { href: "/admin/classes", label: "Classes", icon: School, roles: ["it_admin"] },
  { href: "/admin/subjects", label: "Subjects", icon: BarChart2, roles: ["it_admin"] },
  { href: "/admin/benchmarks", label: "Benchmarks", icon: SlidersHorizontal, roles: ["it_admin", "district_admin"] },
  { href: "/reports", label: "Reports", icon: FileText, roles: ["it_admin", "district_admin", "principal", "teacher"] },
  { href: "/admin/audit", label: "Audit Log", icon: ClipboardList, roles: ["it_admin", "district_admin"] },
];

export function Sidebar() {
  const { user, logout } = useAuth();
  const pathname = usePathname();
  const router = useRouter();

  const visible = NAV.filter((item) => user && item.roles.includes(user.role));

  async function handleLogout() {
    await logout();
    router.push("/login");
  }

  return (
    <aside className="w-56 shrink-0 flex flex-col border-r bg-white dark:bg-slate-900 h-screen sticky top-0">
      <div className="p-4 border-b">
        <span className="text-xl font-bold text-slate-800 dark:text-slate-100">Compass</span>
      </div>
      <nav className="flex-1 p-2 space-y-0.5 overflow-y-auto">
        {visible.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              "flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors",
              pathname.startsWith(item.href)
                ? "bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100"
                : "text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800"
            )}
          >
            <item.icon className="h-4 w-4 shrink-0" />
            {item.label}
          </Link>
        ))}
      </nav>
      <div className="p-2 border-t">
        <div className="px-3 py-1 text-xs text-slate-400 truncate">{user?.username} &middot; {user?.role}</div>
        <Button variant="ghost" size="sm" className="w-full justify-start gap-2 mt-1" onClick={handleLogout}>
          <LogOut className="h-4 w-4" /> Sign out
        </Button>
      </div>
    </aside>
  );
}
