"use client";

import { BookOpen, Database, FolderKanban, GitBranch, LayoutDashboard, Search, Settings, ShieldCheck } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { UserFooter } from "@/components/layout/UserFooter";

const navItems = [
  { label: "Dashboard", href: "/", icon: LayoutDashboard },
  { label: "Catalogue", href: "/catalogue", icon: Database },
  { label: "Projects", href: "/projects", icon: FolderKanban },
  { label: "Quality", href: "/quality", icon: Search },
  { label: "Policies", href: "/governance", icon: ShieldCheck },
  { label: "Glossary", href: "/governance/glossary", icon: BookOpen },
  { label: "Lineage", href: "/lineage", icon: GitBranch },
  { label: "Settings", href: "/settings/connectors", icon: Settings }
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="min-h-screen border-r border-[var(--color-border)] bg-white">
      <div className="flex h-full flex-col">
        <div className="flex h-14 items-center gap-2 border-b border-[var(--color-border)] px-4">
          <div className="grid h-6 w-6 place-items-center rounded-[6px] bg-[var(--color-brand)] text-[12px] font-medium text-white">
            D
          </div>
          <div>
            <div className="text-[14px] font-medium leading-tight">DataGov</div>
            <div className="text-[10px] text-[var(--color-text-muted)]">MVP</div>
          </div>
        </div>

        <nav className="grid gap-1 p-3" aria-label="Primary navigation">
          <div className="px-2 pb-1 pt-2 text-[10px] font-medium uppercase tracking-[0.06em] text-[var(--color-text-muted)]">
            Workspace
          </div>
          {navItems.map((item) => {
            const Icon = item.icon;
            const active = item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                aria-current={active ? "page" : undefined}
                className={`flex items-center gap-2 rounded-[6px] px-2 py-[7px] text-[13px] ${
                  active
                    ? "bg-[var(--color-brand-surface)] font-medium text-[var(--color-brand)]"
                    : "text-[var(--color-text-secondary)]"
                }`}
              >
                <Icon size={16} aria-hidden="true" />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>

        <div className="mt-auto border-t border-[var(--color-border)] p-3">
          <UserFooter />
        </div>
      </div>
    </aside>
  );
}
