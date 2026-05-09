"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { Upload } from "lucide-react";

import { RecentAuditLog } from "@/components/audit/RecentAuditLog";
import { Button } from "@/components/ui/Button";
import { DataTable } from "@/components/ui/DataTable";
import { api } from "@/lib/api";
import type { ApiResponse, Asset } from "@/lib/types";

export default function CataloguePage() {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [query, setQuery] = useState("");
  const [message, setMessage] = useState("");
  const [uploadOpen, setUploadOpen] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [schemaName, setSchemaName] = useState("uploaded");
  const [tableName, setTableName] = useState("");
  const [tableDescription, setTableDescription] = useState("");

  const loadAssets = useCallback(async (search = query) => {
    try {
      const response = await api.get<ApiResponse<Asset[]>>("/api/v1/assets", { params: { q: search || undefined } });
      setAssets(response.data.data);
    } catch {
      setMessage("Unable to load catalogue");
    }
  }, [query]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void loadAssets(query);
    }, 250);
    return () => window.clearTimeout(timer);
  }, [query, loadAssets]);

  function inferTableName(file: File) {
    const baseName = file.name.replace(/\.(csv|xlsx)$/i, "");
    return baseName.replace(/[^0-9a-zA-Z_]+/g, "_").replace(/_+/g, "_").replace(/^_|_$/g, "") || "uploaded_dataset";
  }

  function onFileSelected(file: File | null) {
    setUploadFile(file);
    if (file && !tableName) {
      setTableName(inferTableName(file));
    }
  }

  async function uploadDataset() {
    if (!uploadFile || !schemaName.trim() || !tableName.trim()) {
      setMessage("Choose a file, schema name, and table name before upload");
      return;
    }
    const confirmed = window.confirm(
      `Upload and process ${uploadFile.name} into catalogue asset ${schemaName.trim()}.${tableName.trim()}?`
    );
    if (!confirmed) {
      return;
    }

    setUploading(true);
    setMessage("Processing uploaded dataset");
    const formData = new FormData();
    formData.append("file", uploadFile);
    formData.append("schema_name", schemaName.trim());
    formData.append("table_name", tableName.trim());
    if (tableDescription.trim()) {
      formData.append("description", tableDescription.trim());
    }

    try {
      const response = await api.post<ApiResponse<Asset>>("/api/v1/uploads/datasets", formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });
      setUploadOpen(false);
      setUploadFile(null);
      setTableDescription("");
      setMessage(`Uploaded ${response.data.data.name} with ${response.data.meta.columns ?? 0} columns`);
      await loadAssets();
      window.setTimeout(() => setMessage(""), 3000);
    } catch (error: unknown) {
      const detail = typeof error === "object" && error && "response" in error
        ? (error as { response?: { data?: { detail?: string } } }).response?.data?.detail
        : undefined;
      setMessage(detail ?? "Unable to upload dataset");
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="grid gap-4">
      <section className="flex items-start justify-between gap-4">
        <div>
          <h1 className="m-0 text-[20px] font-medium">Catalogue</h1>
          <p className="mt-1 text-[13px] text-[var(--color-text-secondary)]">Search discovered tables, views, and columns.</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="primary" onClick={() => setUploadOpen(true)}>
            <Upload className="mr-2 h-4 w-4" aria-hidden="true" />
            Upload dataset
          </Button>
          <input
            className="h-9 w-[320px] rounded-[7px] border border-[var(--color-border)] px-3"
            placeholder="Search assets"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
        </div>
      </section>

      {message ? <div className="text-[12px] text-[var(--color-danger-text)]">{message}</div> : null}

      {uploadOpen ? (
        <div className="fixed inset-0 z-40 grid place-items-center bg-black/30 px-4">
          <section className="w-full max-w-[520px] rounded-[8px] border border-[var(--color-border)] bg-white p-5 shadow-xl">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h2 className="m-0 text-[18px] font-medium">Upload dataset</h2>
                <p className="mt-1 text-[12px] text-[var(--color-text-secondary)]">CSV or one-sheet XLSX will be processed into catalogue metadata.</p>
              </div>
              <button
                className="text-[18px] leading-none text-[var(--color-text-muted)]"
                onClick={() => setUploadOpen(false)}
                aria-label="Close upload"
              >
                x
              </button>
            </div>

            <div className="mt-5 grid gap-4">
              <label className="grid gap-1.5 text-[12px] font-medium">
                Dataset file
                <input
                  className="rounded-[7px] border border-[var(--color-border)] px-3 py-2 text-[13px] font-normal"
                  type="file"
                  accept=".csv,.xlsx"
                  onChange={(event) => onFileSelected(event.target.files?.[0] ?? null)}
                />
              </label>
              <div className="grid grid-cols-2 gap-3">
                <label className="grid gap-1.5 text-[12px] font-medium">
                  Schema name
                  <input
                    className="h-9 rounded-[7px] border border-[var(--color-border)] px-3 text-[13px] font-normal"
                    value={schemaName}
                    onChange={(event) => setSchemaName(event.target.value)}
                    placeholder="loan"
                  />
                </label>
                <label className="grid gap-1.5 text-[12px] font-medium">
                  Table name
                  <input
                    className="h-9 rounded-[7px] border border-[var(--color-border)] px-3 text-[13px] font-normal"
                    value={tableName}
                    onChange={(event) => setTableName(event.target.value)}
                    placeholder="loan_sanction_test"
                  />
                </label>
              </div>
              <label className="grid gap-1.5 text-[12px] font-medium">
                Description
                <textarea
                  className="min-h-20 rounded-[7px] border border-[var(--color-border)] p-3 text-[13px] font-normal"
                  value={tableDescription}
                  onChange={(event) => setTableDescription(event.target.value)}
                  placeholder="Optional table description"
                />
              </label>
            </div>

            <div className="mt-5 flex justify-end gap-2">
              <Button onClick={() => setUploadOpen(false)} disabled={uploading}>Cancel</Button>
              <Button variant="primary" onClick={uploadDataset} disabled={uploading}>
                {uploading ? "Processing" : "Process upload"}
              </Button>
            </div>
          </section>
        </div>
      ) : null}

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
