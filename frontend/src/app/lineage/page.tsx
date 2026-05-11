"use client";

import { GitBranch } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { RecentAuditLog } from "@/components/audit/RecentAuditLog";
import { Button } from "@/components/ui/Button";
import { DataTable } from "@/components/ui/DataTable";
import { StatusMessage } from "@/components/ui/StatusMessage";
import { api } from "@/lib/api";
import type { ApiResponse, LineageGraph } from "@/lib/types";

export default function LineagePage() {
  const [graph, setGraph] = useState<LineageGraph>({ nodes: [], edges: [] });
  const [message, setMessage] = useState("Loading lineage graph");
  const [messageTone, setMessageTone] = useState<"info" | "success" | "error">("info");
  const [extracting, setExtracting] = useState(false);

  function loadLineage(nextMessage = "Lineage graph loaded") {
    api
      .get<ApiResponse<LineageGraph>>("/api/v1/lineage")
      .then((response) => {
        setGraph(response.data.data);
        setMessageTone(nextMessage.includes("extracted") ? "success" : "info");
        setMessage(nextMessage);
      })
      .catch(() => {
        setMessageTone("error");
        setMessage("Unable to load lineage graph");
      });
  }

  useEffect(() => {
    loadLineage();
  }, []);

  const assetNames = useMemo(
    () => Object.fromEntries(graph.nodes.map((node) => [node.id, node.name])),
    [graph.nodes]
  );

  async function extractLineage() {
    const confirmed = window.confirm("Extract table-level lineage from scanned columns?");
    if (!confirmed) {
      return;
    }
    setExtracting(true);
    setMessageTone("info");
    setMessage("Extracting lineage");
    try {
      await api.post("/api/v1/lineage/extract");
      loadLineage("Lineage extracted");
    } catch {
      setMessageTone("error");
      setMessage("Unable to extract lineage");
    } finally {
      setExtracting(false);
    }
  }

  return (
    <div className="grid gap-4">
      <section className="flex items-start justify-between gap-4">
        <div>
          <h1 className="m-0 text-[20px] font-medium">Lineage</h1>
          <p className="mt-1 text-[13px] text-[var(--color-text-secondary)]">
            Review table-level upstream and downstream relationships.
          </p>
        </div>
        <Button type="button" variant="primary" onClick={extractLineage} isLoading={extracting} loadingText="Extracting">
          Extract lineage
        </Button>
      </section>

      <section className="grid grid-cols-[1fr_280px] gap-4">
        <div className="min-h-[360px] rounded-[8px] border border-[var(--color-border)] bg-white p-4">
          <div className="relative min-h-[320px] overflow-hidden rounded-[8px] bg-[var(--color-surface)]">
            {graph.nodes.map((node, index) => {
              const left = 40 + (index % 3) * 250;
              const top = 44 + Math.floor(index / 3) * 110;
              return (
                <div
                  key={node.id}
                  className="absolute grid w-[190px] gap-1 rounded-[8px] border border-[var(--color-border)] bg-white p-3 shadow-sm"
                  style={{ left, top }}
                >
                  <div className="flex items-center gap-2 text-[12px] font-medium">
                    <GitBranch size={14} className="text-[var(--color-brand)]" aria-hidden="true" />
                    {node.name}
                  </div>
                  <div className="font-mono text-[10px] text-[var(--color-text-muted)]">{node.source_path}</div>
                  <div className="text-[11px] text-[var(--color-text-secondary)]">DQ {node.dq_score ?? "-"}</div>
                </div>
              );
            })}
            {!graph.nodes.length ? (
              <div className="grid min-h-[320px] place-items-center text-[12px] text-[var(--color-text-muted)]">
                No lineage nodes yet. Run a scan first.
              </div>
            ) : null}
          </div>
        </div>
        <aside className="rounded-[8px] border border-[var(--color-border)] bg-white p-4">
          <div className="text-[10px] font-medium uppercase tracking-[0.05em] text-[var(--color-text-muted)]">Summary</div>
          <div className="mt-3 grid gap-2 text-[12px]">
            <div>Nodes: {graph.nodes.length}</div>
            <div>Edges: {graph.edges.length}</div>
            <StatusMessage tone={messageTone}>{message}</StatusMessage>
          </div>
        </aside>
      </section>

      <DataTable headers={["Upstream", "Downstream", "Source", "Confidence"]}>
        {graph.edges.map((edge) => (
          <tr key={edge.id} className="border-b border-[#F1F5F9] last:border-0">
            <td className="px-4 py-3 text-[12px] font-medium">{assetNames[edge.upstream_asset_id] ?? edge.upstream_asset_id}</td>
            <td className="px-4 py-3 text-[12px]">{assetNames[edge.downstream_asset_id] ?? edge.downstream_asset_id}</td>
            <td className="px-4 py-3 text-[12px] capitalize">{edge.source_type}</td>
            <td className="px-4 py-3 text-[12px]">{edge.confidence === null ? "-" : `${Math.round(edge.confidence * 100)}%`}</td>
          </tr>
        ))}
        {!graph.edges.length ? (
          <tr>
            <td className="px-4 py-8 text-center text-[12px] text-[var(--color-text-muted)]" colSpan={4}>
              No lineage edges yet.
            </td>
          </tr>
        ) : null}
      </DataTable>

      <RecentAuditLog eventType="lineage" title="Recent lineage audit log" />
    </div>
  );
}
