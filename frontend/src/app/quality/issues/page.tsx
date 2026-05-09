"use client";

import { useEffect, useState } from "react";

import { RecentAuditLog } from "@/components/audit/RecentAuditLog";
import { Button } from "@/components/ui/Button";
import { DataTable } from "@/components/ui/DataTable";
import { api } from "@/lib/api";
import type { ApiResponse, DQIssue } from "@/lib/types";

function formatScore(score: number | null) {
  return score === null ? "-" : `${score}%`;
}

export default function QualityIssuesPage() {
  const [issues, setIssues] = useState<DQIssue[]>([]);
  const [statusFilter, setStatusFilter] = useState("open");
  const [message, setMessage] = useState("Loading issues");

  function loadIssues(nextStatus = statusFilter, nextMessage?: string) {
    setMessage("Loading issues");
    api
      .get<ApiResponse<DQIssue[]>>("/api/v1/dq/issues", { params: { status_filter: nextStatus || undefined } })
      .then((response) => {
        setIssues(response.data.data);
        setMessage(nextMessage ?? (response.data.data.length ? "Issues loaded" : "No issues found for this filter"));
      })
      .catch(() => setMessage("Unable to load issues"));
  }

  useEffect(() => {
    api
      .get<ApiResponse<DQIssue[]>>("/api/v1/dq/issues", { params: { status_filter: "open" } })
      .then((response) => {
        setIssues(response.data.data);
        setMessage(response.data.data.length ? "Issues loaded" : "No issues found for this filter");
      })
      .catch(() => setMessage("Unable to load issues"));
  }, []);

  async function resolveIssue(issue: DQIssue) {
    const confirmed = window.confirm(`Resolve ${issue.metric_name} issue? This will write an audit log entry.`);
    if (!confirmed) {
      return;
    }
    const note = window.prompt("Resolution note", "Reviewed and accepted for this scan");
    if (note === null) {
      setMessage("Resolution cancelled");
      return;
    }
    setMessage("Resolving issue");
    try {
      await api.patch<ApiResponse<DQIssue>>(`/api/v1/dq/issues/${issue.id}`, {
        status: "resolved",
        resolution_note: note
      });
      loadIssues(statusFilter, "Issue resolved and audit log updated");
    } catch {
      setMessage("Unable to resolve issue");
    }
  }

  return (
    <div className="grid gap-4">
      <section className="flex items-start justify-between gap-4">
        <div>
          <h1 className="m-0 text-[20px] font-medium">Quality issues</h1>
          <p className="mt-1 text-[13px] text-[var(--color-text-secondary)]">
            Resolve DQ score drops raised during scans.
          </p>
        </div>
        <label className="grid gap-1 text-[12px] font-medium">
          Status
          <select
            className="h-9 rounded-[7px] border border-[var(--color-border)] px-3"
            value={statusFilter}
            onChange={(event) => {
              setStatusFilter(event.target.value);
              loadIssues(event.target.value);
            }}
          >
            <option value="open">Open</option>
            <option value="resolved">Resolved</option>
            <option value="">All</option>
          </select>
        </label>
      </section>

      <div className="rounded-[8px] border border-[var(--color-border)] bg-white px-4 py-3 text-[12px] text-[var(--color-text-secondary)]">
        {message}
      </div>

      <DataTable headers={["Metric", "Severity", "Previous", "Current", "Delta", "Status", "Action"]}>
        {issues.map((issue) => (
          <tr key={issue.id} className="border-b border-[#F1F5F9] last:border-0">
            <td className="px-4 py-3 text-[12px] font-medium capitalize">{issue.metric_name}</td>
            <td className="px-4 py-3 text-[12px] capitalize">{issue.severity}</td>
            <td className="px-4 py-3 text-[12px]">{formatScore(issue.previous_score)}</td>
            <td className="px-4 py-3 text-[12px]">{formatScore(issue.current_score)}</td>
            <td className="px-4 py-3 text-[12px]">{issue.delta_value ?? "-"}</td>
            <td className="px-4 py-3 text-[12px] capitalize">{issue.status}</td>
            <td className="px-4 py-3">
              <Button type="button" disabled={issue.status === "resolved"} onClick={() => resolveIssue(issue)}>
                Resolve
              </Button>
            </td>
          </tr>
        ))}
        {!issues.length ? (
          <tr>
            <td className="px-4 py-8 text-center text-[12px] text-[var(--color-text-muted)]" colSpan={7}>
              No DQ issues to review.
            </td>
          </tr>
        ) : null}
      </DataTable>

      <RecentAuditLog eventType="quality" title="Recent quality audit log" />
    </div>
  );
}
