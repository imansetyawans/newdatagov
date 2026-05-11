"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { RecentAuditLog } from "@/components/audit/RecentAuditLog";
import { Button } from "@/components/ui/Button";
import { DataTable } from "@/components/ui/DataTable";
import { LoadingState } from "@/components/ui/LoadingState";
import { StatusMessage } from "@/components/ui/StatusMessage";
import { api } from "@/lib/api";
import { hasPermission } from "@/lib/permissions";
import type { ApiResponse, Asset, CatalogueProject, Column } from "@/lib/types";
import { useAppStore } from "@/store/appStore";

export default function AssetDetailPage() {
  const params = useParams<{ id: string }>();
  const [asset, setAsset] = useState<Asset | null>(null);
  const [projects, setProjects] = useState<CatalogueProject[]>([]);
  const [description, setDescription] = useState("");
  const [projectId, setProjectId] = useState("");
  const [categoryId, setCategoryId] = useState("");
  const [columnDescriptions, setColumnDescriptions] = useState<Record<string, string>>({});
  const [columnStandardFormats, setColumnStandardFormats] = useState<Record<string, string>>({});
  const [message, setMessage] = useState("");
  const [messageTone, setMessageTone] = useState<"info" | "success" | "error">("info");
  const [generating, setGenerating] = useState(false);
  const [detectingFormats, setDetectingFormats] = useState(false);
  const [savingAction, setSavingAction] = useState<string | null>(null);
  const [columnSamples, setColumnSamples] = useState<Record<string, unknown[]>>({});
  const user = useAppStore((state) => state.user);
  const hydrate = useAppStore((state) => state.hydrate);
  const canEditMetadata = hasPermission(user, "catalogue.edit_metadata");
  const canGenerateMetadata = hasPermission(user, "catalogue.generate_metadata");
  const canAssignProject = hasPermission(user, "catalogue.assign_project");

  useEffect(() => {
    hydrate();
    api
      .get<ApiResponse<Asset>>(`/api/v1/assets/${params.id}`)
      .then((response) => {
        setAsset(response.data.data);
        setDescription(response.data.data.description ?? "");
        setProjectId(response.data.data.project_id ?? "");
        setCategoryId(response.data.data.category_id ?? "");
        setColumnDescriptions(
          Object.fromEntries((response.data.data.columns ?? []).map((column) => [column.id, column.description ?? ""]))
        );
        setColumnStandardFormats(
          Object.fromEntries((response.data.data.columns ?? []).map((column) => [column.id, column.standard_format ?? ""]))
        );
      })
      .catch(() => {
        setMessageTone("error");
        setMessage("Unable to load asset");
      });
    api
      .get<ApiResponse<Array<Record<string, unknown>>>>(`/api/v1/assets/${params.id}/sample`)
      .then((response) => {
        setColumnSamples((response.data.meta.column_samples as Record<string, unknown[]> | undefined) ?? {});
      })
      .catch(() => setColumnSamples({}));
    api
      .get<ApiResponse<CatalogueProject[]>>("/api/v1/projects")
      .then((response) => setProjects(response.data.data))
      .catch(() => setProjects([]));
  }, [hydrate, params.id]);

  const selectedProject = projects.find((project) => project.id === projectId);

  async function saveDescription() {
    setSavingAction("description");
    setMessageTone("info");
    setMessage("Saving description");
    try {
      const response = await api.patch<ApiResponse<Asset>>(`/api/v1/assets/${params.id}`, { description });
      setAsset(response.data.data);
      setMessageTone("success");
      setMessage("Description saved");
      window.setTimeout(() => setMessage(""), 1800);
    } catch {
      setMessageTone("error");
      setMessage("Unable to save description");
    } finally {
      setSavingAction(null);
    }
  }

  async function saveAssignment() {
    setSavingAction("assignment");
    setMessageTone("info");
    setMessage("Saving assignment");
    try {
      const response = await api.patch<ApiResponse<Asset>>(`/api/v1/assets/${params.id}`, {
        project_id: projectId,
        category_id: categoryId
      });
      setAsset(response.data.data);
      setProjectId(response.data.data.project_id ?? "");
      setCategoryId(response.data.data.category_id ?? "");
      setMessageTone("success");
      setMessage("Assignment saved");
      window.setTimeout(() => setMessage(""), 1800);
    } catch {
      setMessageTone("error");
      setMessage("Unable to save assignment");
    } finally {
      setSavingAction(null);
    }
  }

  async function saveColumnDescription(column: Column) {
    setSavingAction(`column-${column.id}`);
    setMessageTone("info");
    setMessage(`Saving ${column.name} metadata`);
    try {
      const response = await api.patch<ApiResponse<Column>>(
        `/api/v1/assets/${params.id}/columns/${column.id}`,
        {
          description: columnDescriptions[column.id] ?? "",
          standard_format: columnStandardFormats[column.id] ?? ""
        }
      );
      setAsset((current) => {
        if (!current) {
          return current;
        }
        return {
          ...current,
          columns: (current.columns ?? []).map((item) => (item.id === column.id ? response.data.data : item))
        };
      });
      setMessageTone("success");
      setMessage("Column metadata saved");
      window.setTimeout(() => setMessage(""), 1800);
    } catch {
      setMessageTone("error");
      setMessage("Unable to save column metadata");
    } finally {
      setSavingAction(null);
    }
  }

  async function generateMetadata() {
    const confirmed = window.confirm(
      "Generate AI metadata for all columns in this table? Existing column descriptions will be replaced."
    );
    if (!confirmed) {
      return;
    }

    setGenerating(true);
    setMessageTone("info");
    setMessage("Generating column metadata");
    try {
      const response = await api.post<ApiResponse<Asset>>(
        `/api/v1/assets/${params.id}/columns/generate-metadata`
      );
      setAsset(response.data.data);
      setColumnDescriptions(
        Object.fromEntries((response.data.data.columns ?? []).map((column) => [column.id, column.description ?? ""]))
      );
      setColumnStandardFormats(
        Object.fromEntries((response.data.data.columns ?? []).map((column) => [column.id, column.standard_format ?? ""]))
      );
      const provider = String(response.data.meta.provider ?? "local");
      setMessageTone("success");
      setMessage(`Generated metadata with ${provider}`);
    } catch {
      setMessageTone("error");
      setMessage("Unable to generate metadata");
    } finally {
      setGenerating(false);
      window.setTimeout(() => setMessage(""), 2500);
    }
  }

  async function detectStandardFormats() {
    const confirmed = window.confirm(
      "Detect standard formats from distinct sample values? Existing standard format values will be replaced."
    );
    if (!confirmed) {
      return;
    }

    setDetectingFormats(true);
    setMessageTone("info");
    setMessage("Detecting standard formats");
    try {
      const response = await api.post<ApiResponse<Asset>>(
        `/api/v1/assets/${params.id}/columns/detect-formats`
      );
      setAsset(response.data.data);
      setColumnStandardFormats(
        Object.fromEntries((response.data.data.columns ?? []).map((column) => [column.id, column.standard_format ?? ""]))
      );
      const updatedCount = Number(response.data.meta.updated_count ?? 0);
      setMessageTone("success");
      setMessage(`Detected standard formats for ${updatedCount} columns`);
    } catch {
      setMessageTone("error");
      setMessage("Unable to detect standard formats");
    } finally {
      setDetectingFormats(false);
      window.setTimeout(() => setMessage(""), 2500);
    }
  }

  function formatScore(score: number | null) {
    return score === null ? "-" : `${score}%`;
  }

  function sampleValues(column: Column) {
    const values = columnSamples[column.name] ?? [];
    return values.map((value) => String(value));
  }

  if (!asset) {
    return message ? (
      <StatusMessage tone={messageTone}>{message}</StatusMessage>
    ) : (
      <LoadingState label="Loading asset" description="Opening table metadata and governed samples." />
    );
  }

  return (
    <div className="grid gap-4">
      <section className="flex items-start justify-between gap-4">
        <div>
          <h1 className="m-0 text-[20px] font-medium">{asset.name}</h1>
          <p className="mt-1 font-mono text-[11px] text-[var(--color-text-secondary)]">{asset.source_path}</p>
        </div>
        <div className="flex gap-2">
          {canEditMetadata ? (
            <Button
              onClick={detectStandardFormats}
              isLoading={detectingFormats}
              loadingText="Detecting formats"
              disabled={detectingFormats || !(asset.columns ?? []).length}
            >
              Detect formats
            </Button>
          ) : null}
          {canGenerateMetadata ? (
            <Button
              variant="primary"
              onClick={generateMetadata}
              isLoading={generating}
              loadingText="Generating metadata"
              disabled={generating || !(asset.columns ?? []).length}
            >
              Generate metadata
            </Button>
          ) : null}
        </div>
      </section>

      <section className="grid grid-cols-[1fr_280px] gap-4">
        <div className="rounded-[8px] border border-[var(--color-border)] bg-white p-4">
          <label className="grid gap-2 text-[12px] font-medium">
            Description
            <textarea
              className="min-h-24 rounded-[7px] border border-[var(--color-border)] p-3 text-[13px] font-normal"
              value={description}
              onChange={(event) => setDescription(event.target.value)}
            />
          </label>
          {canEditMetadata ? (
            <Button
              className="mt-3"
              variant="primary"
              onClick={saveDescription}
              isLoading={savingAction === "description"}
              loadingText="Saving"
            >
              Save description
            </Button>
          ) : null}
          {message ? <StatusMessage className="mt-3" tone={messageTone}>{message}</StatusMessage> : null}
        </div>
        <div className="rounded-[8px] border border-[var(--color-border)] bg-white p-4">
          <div className="text-[10px] font-medium uppercase tracking-[0.05em] text-[var(--color-text-muted)]">Summary</div>
          <div className="mt-3 grid gap-2 text-[12px]">
            <div>Project: {asset.project_name ?? "Unassigned"}</div>
            <div>Category: {asset.category_name ?? "-"}</div>
            <div>Type: <span className="capitalize">{asset.asset_type}</span></div>
            <div>Rows: {asset.row_count ?? "-"}</div>
            <div>Columns: {asset.columns?.length ?? 0}</div>
            <div>DQ score: {asset.dq_score ?? "-"}</div>
          </div>
        </div>
      </section>

      {canAssignProject ? (
      <section className="grid grid-cols-[260px_260px_auto_1fr] items-end gap-3 rounded-[8px] border border-[var(--color-border)] bg-white p-4">
        <label className="grid gap-1.5 text-[12px] font-medium">
          Project
          <select
            className="h-9 rounded-[7px] border border-[var(--color-border)] px-3 text-[13px] font-normal"
            value={projectId}
            onChange={(event) => {
              const nextProject = projects.find((project) => project.id === event.target.value);
              setProjectId(event.target.value);
              setCategoryId(nextProject?.categories[0]?.id ?? "");
            }}
          >
            <option value="">Unassigned</option>
            {projects.map((project) => (
              <option key={project.id} value={project.id}>{project.name}</option>
            ))}
          </select>
        </label>
        <label className="grid gap-1.5 text-[12px] font-medium">
          Category
          <select
            className="h-9 rounded-[7px] border border-[var(--color-border)] px-3 text-[13px] font-normal"
            value={categoryId}
            onChange={(event) => setCategoryId(event.target.value)}
            disabled={!selectedProject}
          >
            <option value="">No category</option>
            {(selectedProject?.categories ?? []).map((category) => (
              <option key={category.id} value={category.id}>{category.name}</option>
            ))}
          </select>
        </label>
        <Button
          variant="primary"
          onClick={saveAssignment}
          isLoading={savingAction === "assignment"}
          loadingText="Saving"
        >
          Save assignment
        </Button>
        <div className="text-[12px] text-[var(--color-text-muted)]">Project/category controls where this asset appears in the catalogue.</div>
      </section>
      ) : null}

      <DataTable headers={["Column", "Type", "Description", "Sample data", "Standard format", "Classifications", "Completeness", "Uniqueness", "Consistency", "Accuracy", "Action"]}>
        {(asset.columns ?? []).map((column) => (
          <tr key={column.id} className="border-b border-[#F1F5F9] last:border-0">
            <td className="px-4 py-3 font-mono text-[12px] font-medium">{column.name}</td>
            <td className="px-4 py-3 font-mono text-[11px] text-[var(--color-text-secondary)]">{column.data_type}</td>
            <td className="min-w-[240px] px-4 py-3 align-top">
              <textarea
                aria-label={`Description for ${column.name}`}
                className="h-14 min-h-14 w-full resize-y overflow-hidden rounded-[7px] border border-[var(--color-border)] px-2 py-1.5 text-[12px] leading-snug transition-[height] focus:h-28 focus:overflow-auto"
                value={columnDescriptions[column.id] ?? ""}
                onChange={(event) =>
                  setColumnDescriptions((current) => ({ ...current, [column.id]: event.target.value }))
                }
                placeholder="Add column description"
              />
            </td>
            <td className="min-w-[280px] max-w-[340px] px-4 py-3 align-top">
              {sampleValues(column).length ? (
                <div className="flex flex-wrap gap-1.5" aria-label={`Sample data for ${column.name}`}>
                  {sampleValues(column).map((value, index) => {
                    const masked = value === "*****";
                    return (
                      <span
                        key={`${column.id}-${value}-${index}`}
                        className={`max-w-full rounded-[6px] border px-2 py-1 font-mono text-[11px] leading-snug ${
                          masked
                            ? "border-[#FECACA] bg-[#FEF2F2] text-[#991B1B]"
                            : "border-[#E2E8F0] bg-[#F8FAFC] text-[var(--color-text-secondary)]"
                        }`}
                        title={value}
                      >
                        <span className="break-words">{value}</span>
                      </span>
                    );
                  })}
                </div>
              ) : (
                <span className="text-[12px] text-[var(--color-text-muted)]">-</span>
              )}
            </td>
            <td className="min-w-[220px] px-4 py-3 align-top">
              <textarea
                aria-label={`Standard format for ${column.name}`}
                className="h-14 min-h-14 w-full resize-y overflow-hidden rounded-[7px] border border-[var(--color-border)] px-2 py-1.5 text-[12px] leading-snug transition-[height] focus:h-24 focus:overflow-auto"
                value={columnStandardFormats[column.id] ?? ""}
                onChange={(event) =>
                  setColumnStandardFormats((current) => ({ ...current, [column.id]: event.target.value }))
                }
                placeholder="e.g. lowercase email, YYYY-MM-DD"
              />
            </td>
            <td className="px-4 py-3 text-[12px]">{column.classifications.length ? column.classifications.join(", ") : "-"}</td>
            <td className="px-4 py-3 text-[12px]">{formatScore(column.completeness_score)}</td>
            <td className="px-4 py-3 text-[12px]">{formatScore(column.uniqueness_score)}</td>
            <td className="px-4 py-3 text-[12px]">{formatScore(column.consistency_score)}</td>
            <td className="px-4 py-3 text-[12px]">{formatScore(column.accuracy_score)}</td>
            <td className="px-4 py-3">
              {canEditMetadata ? (
                <Button
                  className="min-h-7 px-3 py-1 text-[12px]"
                  onClick={() => saveColumnDescription(column)}
                  isLoading={savingAction === `column-${column.id}`}
                  loadingText="Saving"
                >
                  Save
                </Button>
              ) : null}
            </td>
          </tr>
        ))}
      </DataTable>

      <RecentAuditLog eventType="catalogue" title="Recent catalogue audit log" />
    </div>
  );
}
