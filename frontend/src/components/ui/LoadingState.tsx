type LoadingStateProps = {
  label?: string;
  description?: string;
  fullPage?: boolean;
};

export function LoadingState({
  label = "Loading",
  description = "Preparing your DataGov workspace.",
  fullPage = false
}: LoadingStateProps) {
  return (
    <div
      className={`grid place-items-center ${fullPage ? "min-h-screen" : "min-h-[220px]"} animate-datagov-enter text-center`}
      role="status"
      aria-live="polite"
    >
      <div className="grid justify-items-center gap-3">
        <div className="grid h-10 w-10 place-items-center rounded-full bg-[var(--color-brand-surface)]">
          <span className="h-5 w-5 rounded-full border-2 border-[var(--color-brand-light)] border-t-[var(--color-brand)] animate-datagov-spin" />
        </div>
        <div>
          <div className="text-[13px] font-medium text-[var(--color-text-primary)]">{label}</div>
          <div className="mt-1 text-[12px] text-[var(--color-text-secondary)]">{description}</div>
        </div>
        <div className="datagov-progress h-1.5 w-44 rounded-full bg-[var(--color-brand-light)]">
          <div className="h-full w-2/3 rounded-full bg-[var(--color-brand)]" />
        </div>
      </div>
    </div>
  );
}
