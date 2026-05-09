"use client";

import { Activity, Database, Server, ShieldCheck, TriangleAlert } from "lucide-react";
import { useEffect, useState } from "react";

import { RecentAuditLog } from "@/components/audit/RecentAuditLog";
import { api } from "@/lib/api";
import type { ApiResponse, Asset, DQIssue, DQScore, Policy } from "@/lib/types";

export default function DashboardPage() {
  const [health, setHealth] = useState<"checking" | "ok" | "error">("checking");
  const [assetCount, setAssetCount] = useState(0);
  const [dqScore, setDqScore] = useState<number | null>(null);
  const [activePolicyCount, setActivePolicyCount] = useState(0);
  const [openIssueCount, setOpenIssueCount] = useState(0);

  useEffect(() => {
    api
      .get<{ status: string }>("/health")
      .then((response) => setHealth(response.data.status === "ok" ? "ok" : "error"))
      .catch(() => setHealth("error"));
    api
      .get<ApiResponse<Asset[]>>("/api/v1/assets")
      .then((response) => setAssetCount(response.data.data.length))
      .catch(() => setAssetCount(0));
    api
      .get<ApiResponse<DQScore[]>>("/api/v1/dq/scores")
      .then((response) => {
        const scores = response.data.data.map((item) => item.dq_score).filter((score): score is number => score !== null);
        setDqScore(scores.length ? Math.round(scores.reduce((sum, score) => sum + score, 0) / scores.length) : null);
      })
      .catch(() => setDqScore(null));
    api
      .get<ApiResponse<Policy[]>>("/api/v1/policies")
      .then((response) => setActivePolicyCount(response.data.data.filter((policy) => policy.status === "active").length))
      .catch(() => setActivePolicyCount(0));
    api
      .get<ApiResponse<DQIssue[]>>("/api/v1/dq/issues", { params: { status_filter: "open" } })
      .then((response) => setOpenIssueCount(response.data.data.length))
      .catch(() => setOpenIssueCount(0));
  }, []);

  const dashboardMetrics = [
    {
      label: "DQ score",
      value: dqScore === null ? "Not scanned" : `${dqScore}`,
      hint: dqScore === null ? "Run scan to score data" : "Average data quality",
      icon: Activity
    },
    {
      label: "Assets",
      value: String(assetCount),
      hint: assetCount ? "Catalogued from scans" : "Run first scan",
      icon: Database
    },
    {
      label: "Active policies",
      value: String(activePolicyCount),
      hint: activePolicyCount ? "Applied during scans" : "No active rules",
      icon: ShieldCheck
    },
    {
      label: "Open issues",
      value: String(openIssueCount),
      hint: openIssueCount ? "Needs review" : "No issues detected",
      icon: TriangleAlert
    }
  ];

  return (
    <div className="grid gap-4">
      <section>
        <h1 className="m-0 text-[20px] font-medium">Dashboard</h1>
        <p className="mt-1 max-w-2xl text-[13px] text-[var(--color-text-secondary)]">
          Monitor catalogue coverage, governance readiness, and scan health for the local DataGov workspace.
        </p>
      </section>

      <section className="grid grid-cols-4 gap-4">
        {dashboardMetrics.map((metric) => {
          const Icon = metric.icon;
          return (
            <article key={metric.label} className="rounded-[8px] border border-[var(--color-border)] bg-white p-4">
              <div className="flex items-center justify-between gap-3">
                <div className="text-[10px] font-medium uppercase tracking-[0.05em] text-[var(--color-text-muted)]">
                  {metric.label}
                </div>
                <Icon size={16} aria-hidden="true" className="text-[var(--color-brand)]" />
              </div>
              <div className="mt-2 text-[24px] font-medium leading-none">{metric.value}</div>
              <div className="mt-2 text-[11px] text-[var(--color-text-secondary)]">{metric.hint}</div>
            </article>
          );
        })}
      </section>

      <section className="rounded-[8px] border border-[var(--color-border)] bg-white p-4">
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <Server size={18} aria-hidden="true" className="text-[var(--color-brand)]" />
            <div>
              <div className="text-[13px] font-medium">Backend API</div>
              <div className="text-[12px] text-[var(--color-text-secondary)]">FastAPI health endpoint at /health</div>
            </div>
          </div>
          <div className="text-[12px] capitalize text-[var(--color-text-secondary)]">{health}</div>
        </div>
      </section>

      <RecentAuditLog />
    </div>
  );
}
