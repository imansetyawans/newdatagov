import { Play } from "lucide-react";

export function Topbar() {
  return (
    <header className="sticky top-0 z-10 flex h-[var(--topbar-height)] items-center justify-between border-b border-[var(--color-border)] bg-white px-6">
      <div className="text-[12px] text-[var(--color-text-muted)]">
        Dashboard <span aria-hidden="true">/</span> <span className="font-medium text-[var(--color-text-primary)]">Overview</span>
      </div>
      <a
        href="/scan"
        aria-label="Run scan"
        className="inline-flex min-h-8 items-center gap-2 rounded-[7px] bg-[var(--color-brand)] px-3 text-[13px] font-medium text-white"
      >
        <Play size={14} aria-hidden="true" />
        Run scan
      </a>
    </header>
  );
}
