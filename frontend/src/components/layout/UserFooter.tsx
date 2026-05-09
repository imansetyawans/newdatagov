"use client";

import { useEffect } from "react";

import { useAppStore } from "@/store/appStore";

export function UserFooter() {
  const user = useAppStore((state) => state.user);
  const hydrate = useAppStore((state) => state.hydrate);

  useEffect(() => {
    hydrate();
  }, [hydrate]);

  const initials = user?.fullName
    .split(" ")
    .map((part) => part[0])
    .join("")
    .slice(0, 2)
    .toUpperCase() ?? "DA";

  return (
    <div className="flex items-center gap-2">
      <div className="grid h-7 w-7 place-items-center rounded-full bg-[var(--color-brand-surface)] text-[12px] font-medium text-[var(--color-brand)]">
        {initials}
      </div>
      <div>
        <div className="text-[12px] font-medium">{user?.fullName ?? "DataGov Admin"}</div>
        <div className="text-[11px] capitalize text-[var(--color-text-muted)]">{user?.role ?? "Admin"}</div>
      </div>
    </div>
  );
}
