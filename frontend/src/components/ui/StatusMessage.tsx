import type { ReactNode } from "react";

type StatusMessageTone = "info" | "success" | "error";

type StatusMessageProps = {
  children: ReactNode;
  tone?: StatusMessageTone;
  className?: string;
};

const tones: Record<StatusMessageTone, string> = {
  info: "border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text-secondary)]",
  success: "border-[var(--color-success-border)] bg-[var(--color-success-bg)] text-[var(--color-success-text)]",
  error: "border-[var(--color-danger-border)] bg-[var(--color-danger-bg)] text-[var(--color-danger-text)]"
};

export function StatusMessage({ children, tone = "info", className = "" }: StatusMessageProps) {
  if (!children) {
    return null;
  }

  return (
    <div
      className={`animate-datagov-enter rounded-[8px] border px-3 py-2 text-[12px] ${tones[tone]} ${className}`}
      role={tone === "error" ? "alert" : "status"}
      aria-live="polite"
    >
      {children}
    </div>
  );
}
