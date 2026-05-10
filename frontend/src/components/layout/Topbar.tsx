import { Play } from "lucide-react";
import { useEffect } from "react";

import { hasPermission } from "@/lib/permissions";
import { useAppStore } from "@/store/appStore";

export function Topbar() {
  const user = useAppStore((state) => state.user);
  const hydrate = useAppStore((state) => state.hydrate);

  useEffect(() => {
    hydrate();
  }, [hydrate]);

  return (
    <header className="sticky top-0 z-10 flex h-[var(--topbar-height)] items-center justify-between border-b border-[var(--color-border)] bg-white px-6">
      <div className="text-[12px] text-[var(--color-text-muted)]">
        Dashboard <span aria-hidden="true">/</span> <span className="font-medium text-[var(--color-text-primary)]">Overview</span>
      </div>
      {hasPermission(user, "scan.run") ? (
        <a
          href="/scan"
          aria-label="Run scan"
          className="inline-flex min-h-8 items-center gap-2 rounded-[7px] bg-[var(--color-brand)] px-3 text-[13px] font-medium text-white"
        >
          <Play size={14} aria-hidden="true" />
          Run scan
        </a>
      ) : <span />}
    </header>
  );
}
