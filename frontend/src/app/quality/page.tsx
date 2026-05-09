"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { RecentAuditLog } from "@/components/audit/RecentAuditLog";
import { DataTable } from "@/components/ui/DataTable";
import { api } from "@/lib/api";
import type { ApiResponse, DQIssue, DQScore } from "@/lib/types";

function scoreLabel(score: number | null) {
  return score === null ? "Not scanned" : `${score}%`;
}

function scoreTone(score: number | null) {
  if (score === null) {
    return "text-[var(--color-text-muted)]";
  }
  if (score < 70) {
    return "text-[var(--color-danger-text)]";
  }
  if (score < 90) {
    return "text-[var(--color-warning-text)]";
  }
  return "text-[var(--color-success-text)]";
}

export default function QualityPage() {
  const [scores, setScores] = useState<DQScore[]>([]);
  const [openIssues, setOpenIssues] = useState<DQIssue[]>([]);
  const [message, setMessage] = useState("Loading quality results");

  useEffect(() => {
    Promise.all([
      api.get<ApiResponse<DQScore[]>>("/api/v1/dq/scores"),
      api.get<ApiResponse<DQIssue[]>>("/api/v1/dq/issues", { params: { status_filter: "open" } })
    ])
      .then(([scoreResponse, issueResponse]) => {
        setScores(scoreResponse.data.data);
        setOpenIssues(issueResponse.data.data);
        setMessage(scoreResponse.data.data.length ? "Quality results loaded" : "No quality scores yet. Run a scan first.");
      })
      .catch(() => setMessage("Unable to load quality results"));
  }, []);

  const averageScore = useMemo(() => {
    const values = scores.map((score) => score.dq_score).filter((score): score is number => score !== null);
    if (!values.length) {
      return null;
    }
    return Math.round(values.reduce((sum, score) => sum + score, 0) / values.length);
  }, [scores]);

  return (
    <div className="grid gap-4">
      <section className="flex items-start justify-between gap-4">
        <div>
          <h1 className="m-0 text-[20px] font-medium">Quality</h1>
          <p className="mt-1 text-[13px] text-[var(--color-text-secondary)]">
            Review DQ scores, scan freshness, and open quality issues.
          </p>
        </div>
        <Link
          className="rounded-[7px] border border-[var(--color-border)] px-3 py-2 text-[13px] font-medium text-[var(--color-text-secondary)]"
          href="/quality/issues"
        >
          Open issues
        </Link>
      </section>

      <section className="grid grid-cols-3 gap-3">
        <article className="rounded-[8px] border border-[var(--color-border)] bg-white p-4">
          <div className="text-[10px] font-medium uppercase tracking-[0.05em] text-[var(--color-text-muted)]">Average score</div>
          <div className={`mt-2 text-[28px] font-medium leading-none ${scoreTone(averageScore)}`}>{scoreLabel(averageScore)}</div>
        </article>
        <article className="rounded-[8px] border border-[var(--color-border)] bg-white p-4">
          <div className="text-[10px] font-medium uppercase tracking-[0.05em] text-[var(--color-text-muted)]">Scored assets</div>
          <div className="mt-2 text-[28px] font-medium leading-none">{scores.filter((score) => score.dq_score !== null).length}</div>
        </article>
        <article className="rounded-[8px] border border-[var(--color-border)] bg-white p-4">
          <div className="text-[10px] font-medium uppercase tracking-[0.05em] text-[var(--color-text-muted)]">Open issues</div>
          <div className="mt-2 text-[28px] font-medium leading-none">{openIssues.length}</div>
        </article>
      </section>

      <div className="rounded-[8px] border border-[var(--color-border)] bg-white px-4 py-3 text-[12px] text-[var(--color-text-secondary)]">
        {message}
      </div>

      <DataTable headers={["Asset", "Source", "DQ score", "Last scanned", "Action"]}>
        {scores.map((score) => (
          <tr key={score.asset_id} className="border-b border-[#F1F5F9] last:border-0">
            <td className="px-4 py-3 text-[12px] font-medium">{score.asset_name}</td>
            <td className="px-4 py-3 font-mono text-[11px] text-[var(--color-text-secondary)]">{score.source_path}</td>
            <td className={`px-4 py-3 text-[12px] font-medium ${scoreTone(score.dq_score)}`}>{scoreLabel(score.dq_score)}</td>
            <td className="px-4 py-3 text-[12px] text-[var(--color-text-secondary)]">
              {score.last_scanned_at ? new Date(score.last_scanned_at).toLocaleString() : "Never"}
            </td>
            <td className="px-4 py-3 text-[12px]">
              <Link className="text-[var(--color-brand)]" href={`/catalogue/${score.asset_id}`}>
                View columns
              </Link>
            </td>
          </tr>
        ))}
        {!scores.length ? (
          <tr>
            <td className="px-4 py-8 text-center text-[12px] text-[var(--color-text-muted)]" colSpan={5}>
              No scored assets yet. Run a scan to calculate completeness, uniqueness, consistency, and accuracy.
            </td>
          </tr>
        ) : null}
      </DataTable>

      <RecentAuditLog eventType="quality" title="Recent quality audit log" />
    </div>
  );
}
