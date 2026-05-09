const colors: Record<string, string> = {
  active: "bg-[#22C55E]",
  completed: "bg-[#22C55E]",
  connected: "bg-[#22C55E]",
  inactive: "bg-[#CBD5E1]",
  draft: "bg-[#CBD5E1]",
  running: "bg-[#F59E0B]",
  warning: "bg-[#F59E0B]",
  error: "bg-[#EF4444]",
  failed: "bg-[#EF4444]"
};

export function StatusDot({ status }: { status: string }) {
  return (
    <span className="inline-flex items-center gap-2">
      <span className={`h-2 w-2 rounded-full ${colors[status] ?? colors.inactive}`} aria-hidden="true" />
      <span className="capitalize">{status}</span>
    </span>
  );
}

