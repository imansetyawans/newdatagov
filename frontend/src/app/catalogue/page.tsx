"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { RecentAuditLog } from "@/components/audit/RecentAuditLog";
import { DataTable } from "@/components/ui/DataTable";
import { api } from "@/lib/api";
import type { ApiResponse, Asset } from "@/lib/types";

export default function CataloguePage() {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [query, setQuery] = useState("");
  const [message, setMessage] = useState("");

  useEffect(() => {
    const timer = window.setTimeout(() => {
      api
        .get<ApiResponse<Asset[]>>("/api/v1/assets", { params: { q: query || undefined } })
        .then((response) => setAssets(response.data.data))
        .catch(() => setMessage("Unable to load catalogue"));
    }, 250);
    return () => window.clearTimeout(timer);
  }, [query]);

  return (
    <div className="grid gap-4">
      <section className="flex items-start justify-between gap-4">
        <div>
          <h1 className="m-0 text-[20px] font-medium">Catalogue</h1>
          <p className="mt-1 text-[13px] text-[var(--color-text-secondary)]">Search discovered tables, views, and columns.</p>
        </div>
        <input
          className="h-9 w-[320px] rounded-[7px] border border-[var(--color-border)] px-3"
          placeholder="Search assets"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
        />
      </section>

      {message ? <div className="text-[12px] text-[var(--color-danger-text)]">{message}</div> : null}

      <DataTable headers={["Asset", "Source", "Type", "Rows", "DQ score", "Last scanned"]}>
        {assets.map((asset) => (
          <tr key={asset.id} className="border-b border-[#F1F5F9] last:border-0">
            <td className="px-4 py-3 text-[12px] font-medium">
              <Link className="text-[var(--color-brand)]" href={`/catalogue/${asset.id}`}>{asset.name}</Link>
            </td>
            <td className="px-4 py-3 font-mono text-[11px] text-[var(--color-text-secondary)]">{asset.source_path}</td>
            <td className="px-4 py-3 text-[12px] capitalize">{asset.asset_type}</td>
            <td className="px-4 py-3 text-[12px]">{asset.row_count ?? "-"}</td>
            <td className="px-4 py-3 text-[12px]">{asset.dq_score ?? "-"}</td>
            <td className="px-4 py-3 text-[12px] text-[var(--color-text-secondary)]">
              {asset.last_scanned_at ? new Date(asset.last_scanned_at).toLocaleString() : "Never"}
            </td>
          </tr>
        ))}
        {!assets.length ? (
          <tr>
            <td className="px-4 py-8 text-center text-[12px] text-[var(--color-text-muted)]" colSpan={6}>
              No assets catalogued yet. Run a scan from the topbar.
            </td>
          </tr>
        ) : null}
      </DataTable>

      <RecentAuditLog eventType="catalogue" title="Recent catalogue audit log" />
    </div>
  );
}
