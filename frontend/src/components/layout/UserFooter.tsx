"use client";

import { LogOut } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { useAppStore } from "@/store/appStore";

export function UserFooter() {
  const router = useRouter();
  const user = useAppStore((state) => state.user);
  const hydrate = useAppStore((state) => state.hydrate);
  const logout = useAppStore((state) => state.logout);

  useEffect(() => {
    hydrate();
  }, [hydrate]);

  const initials = user?.fullName
    .split(" ")
    .map((part) => part[0])
    .join("")
    .slice(0, 2)
    .toUpperCase() ?? "DA";

  function handleLogout() {
    logout();
    router.replace("/login");
  }

  return (
    <div className="grid gap-2">
      <div className="flex items-center gap-2">
        <div className="grid h-7 w-7 place-items-center rounded-full bg-[var(--color-brand-surface)] text-[12px] font-medium text-[var(--color-brand)]">
          {initials}
        </div>
        <div>
          <div className="text-[12px] font-medium">{user?.fullName ?? "DataGov Admin"}</div>
          <div className="text-[11px] capitalize text-[var(--color-text-muted)]">{user?.role ?? "Admin"}</div>
        </div>
      </div>
      <button
        type="button"
        onClick={handleLogout}
        className="inline-flex h-8 items-center justify-center gap-2 rounded-[7px] border border-[var(--color-border)] bg-white text-[12px] font-medium text-[var(--color-text-secondary)] transition hover:border-[var(--color-brand)] hover:text-[var(--color-brand)]"
      >
        <LogOut size={14} aria-hidden="true" />
        Logout
      </button>
    </div>
  );
}
