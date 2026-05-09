"use client";

import { useEffect, useState } from "react";

import { api } from "@/lib/api";
import type { ApiResponse, AuditLog } from "@/lib/types";

type RecentAuditLogProps = {
  eventType?: string;
  limit?: number;
  title?: string;
};

function formatAction(action: string) {
  return action.replaceAll("_", " ");
}

function actorName(entry: AuditLog) {
  return entry.user_name || entry.user_email || entry.user_id || "System";
}

export function RecentAuditLog({ eventType, limit = 6, title = "Recent audit log" }: RecentAuditLogProps) {
  const [entries, setEntries] = useState<AuditLog[]>([]);
  const [message, setMessage] = useState("Loading audit activity");

  useEffect(() => {
    api
      .get<ApiResponse<AuditLog[]>>("/api/v1/audit-log", {
        params: { limit, event_type: eventType || undefined }
      })
      .then((response) => {
        setEntries(response.data.data);
        setMessage(response.data.data.length ? "" : "No audit activity yet");
      })
      .catch(() => {
        setEntries([]);
        setMessage("Audit activity is available for admin users");
      });
  }, [eventType, limit]);

  return (
    <section className="rounded-[8px] border border-[var(--color-border)] bg-white p-4">
      <div className="text-[13px] font-medium">{title}</div>
      <div className="mt-3 grid gap-2">
        {entries.map((entry) => (
          <div
            key={entry.id}
            className="grid grid-cols-[180px_1fr_180px_120px] gap-3 rounded-[7px] bg-[var(--color-surface)] px-3 py-2 text-[12px]"
          >
            <span className="text-[var(--color-text-secondary)]">{new Date(entry.created_at).toLocaleString()}</span>
            <span className="capitalize">{formatAction(entry.action)}</span>
            <span className="truncate text-[var(--color-text-secondary)]" title={actorName(entry)}>
              {actorName(entry)}
            </span>
            <span className="capitalize text-[var(--color-text-secondary)]">{entry.event_type}</span>
          </div>
        ))}
        {message ? <div className="text-[12px] text-[var(--color-text-muted)]">{message}</div> : null}
      </div>
    </section>
  );
}
