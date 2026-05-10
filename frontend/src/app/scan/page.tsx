"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { RecentAuditLog } from "@/components/audit/RecentAuditLog";
import { Button } from "@/components/ui/Button";
import { StatusDot } from "@/components/ui/StatusDot";
import { api } from "@/lib/api";
import type { ApiResponse, CatalogueProject, Connector, ConnectorSchema, ConnectorScope, Scan } from "@/lib/types";

const steps = ["Select sources", "Configure", "Running", "Results"];

function allScope(schemas: ConnectorSchema[]): ConnectorScope {
  return {
    schemas: schemas.map((schema) => schema.name),
    tables: Object.fromEntries(schemas.map((schema) => [schema.name, schema.asset_names]))
  };
}

function scopeFromConnector(connector: Connector | undefined, schemas: ConnectorSchema[]): ConnectorScope {
  const configured = connector?.config_encrypted.catalogue_scope as ConnectorScope | undefined;
  if (configured?.schemas?.length && configured.tables) {
    return configured;
  }
  return allScope(schemas);
}

export default function ScanPage() {
  const [connectors, setConnectors] = useState<Connector[]>([]);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [scanType, setScanType] = useState("full");
  const [activeStep, setActiveStep] = useState(0);
  const [scan, setScan] = useState<Scan | null>(null);
  const [message, setMessage] = useState("");
  const [scheduleCron, setScheduleCron] = useState("0 8 * * *");
  const [notifyOnCompletion, setNotifyOnCompletion] = useState(true);
  const [scheduledScans, setScheduledScans] = useState<Scan[]>([]);
  const [connectorSchemas, setConnectorSchemas] = useState<Record<string, ConnectorSchema[]>>({});
  const [connectorScopes, setConnectorScopes] = useState<Record<string, ConnectorScope>>({});
  const [loadingSchemas, setLoadingSchemas] = useState<Record<string, boolean>>({});
  const [projects, setProjects] = useState<CatalogueProject[]>([]);
  const [projectId, setProjectId] = useState("");
  const [categoryId, setCategoryId] = useState("");

  const selectedConnectors = useMemo(
    () => connectors.filter((connector) => selectedIds.includes(connector.id)),
    [connectors, selectedIds]
  );
  const selectedProject = projects.find((project) => project.id === projectId);

  useEffect(() => {
    api
      .get<ApiResponse<Connector[]>>("/api/v1/connectors")
      .then((response) => {
        setConnectors(response.data.data);
        setSelectedIds(response.data.data.filter((connector) => connector.status !== "error").map((connector) => connector.id));
      })
      .catch(() => setMessage("Unable to load connectors"));
    api
      .get<ApiResponse<Scan[]>>("/api/v1/scans/schedules")
      .then((response) => setScheduledScans(response.data.data))
      .catch(() => setScheduledScans([]));
    api
      .get<ApiResponse<CatalogueProject[]>>("/api/v1/projects")
      .then((response) => {
        setProjects(response.data.data);
        if (response.data.data.length) {
          setProjectId(response.data.data[0].id);
          setCategoryId(response.data.data[0].categories[0]?.id ?? "");
        }
      })
      .catch(() => setProjects([]));
  }, []);

  const loadConnectorSchemas = useCallback(async (connectorId: string) => {
    setLoadingSchemas((current) => ({ ...current, [connectorId]: true }));
    try {
      const response = await api.get<ApiResponse<ConnectorSchema[]>>(`/api/v1/connectors/${connectorId}/schemas`);
      const schemas = response.data.data;
      setConnectorSchemas((current) => ({ ...current, [connectorId]: schemas }));
      setConnectorScopes((current) => {
        if (current[connectorId]) {
          return current;
        }
        const connector = connectors.find((item) => item.id === connectorId);
        return { ...current, [connectorId]: scopeFromConnector(connector, schemas) };
      });
    } catch {
      setMessage("Unable to discover connector schemas. Check connector settings.");
    } finally {
      setLoadingSchemas((current) => ({ ...current, [connectorId]: false }));
    }
  }, [connectors]);

  useEffect(() => {
    selectedIds.forEach((id) => {
      if (!connectorSchemas[id] && !loadingSchemas[id]) {
        void loadConnectorSchemas(id);
      }
    });
  }, [selectedIds, connectorSchemas, loadingSchemas, loadConnectorSchemas]);

  function toggleConnector(id: string) {
    setSelectedIds((current) => (current.includes(id) ? current.filter((item) => item !== id) : [...current, id]));
  }

  function toggleSchema(connectorId: string, schema: ConnectorSchema) {
    setConnectorScopes((current) => {
      const existing = current[connectorId] ?? allScope(connectorSchemas[connectorId] ?? []);
      const isSelected = existing.schemas.includes(schema.name);
      const nextSchemas = isSelected
        ? existing.schemas.filter((item) => item !== schema.name)
        : [...existing.schemas, schema.name];
      const nextTables = { ...existing.tables };
      if (isSelected) {
        delete nextTables[schema.name];
      } else {
        nextTables[schema.name] = schema.asset_names;
      }
      return { ...current, [connectorId]: { schemas: nextSchemas, tables: nextTables } };
    });
  }

  function toggleTable(connectorId: string, schema: ConnectorSchema, tableName: string) {
    setConnectorScopes((current) => {
      const existing = current[connectorId] ?? allScope(connectorSchemas[connectorId] ?? []);
      const selectedTables = existing.tables[schema.name] ?? [];
      const nextSelectedTables = selectedTables.includes(tableName)
        ? selectedTables.filter((item) => item !== tableName)
        : [...selectedTables, tableName];
      const nextSchemas = existing.schemas.includes(schema.name)
        ? existing.schemas
        : [...existing.schemas, schema.name];
      return {
        ...current,
        [connectorId]: {
          schemas: nextSchemas,
          tables: { ...existing.tables, [schema.name]: nextSelectedTables }
        }
      };
    });
  }

  function selectedTableCount(scope: ConnectorScope | undefined) {
    if (!scope) {
      return 0;
    }
    return Object.values(scope.tables).reduce((total, tables) => total + tables.length, 0);
  }

  function scopesForSelectedConnectors(): Record<string, ConnectorScope> {
    return selectedIds.reduce<Record<string, ConnectorScope>>((scopes, id) => {
      const scope = connectorScopes[id];
      if (scope) {
        scopes[id] = scope;
      }
      return scopes;
    }, {});
  }

  async function runScan() {
    const selectedScopes = scopesForSelectedConnectors();
    const totalTables = Object.values(selectedScopes).reduce((total, scope) => total + selectedTableCount(scope), 0);
    if (!totalTables) {
      setMessage("Select at least one schema table before starting the scan.");
      return;
    }
    if (!projectId || !categoryId) {
      setMessage("Choose a project and category before starting the scan.");
      return;
    }
    const confirmed = window.confirm(
      "Start scan for the selected connector scope? DataGov will store the selected schema/table metadata in its catalogue database."
    );
    if (!confirmed) {
      setMessage("Scan cancelled");
      return;
    }
    setActiveStep(2);
    setMessage("Saving connector scope and running scan");
    try {
      await Promise.all(
        selectedIds.map((id) =>
          api.patch(`/api/v1/connectors/${id}/scope`, {
            catalogue_scope: connectorScopes[id]
          })
        )
      );
      const response = await api.post<ApiResponse<Scan>>("/api/v1/scans", {
        connector_ids: selectedIds,
        scan_type: scanType,
        connector_scopes: selectedScopes,
        project_id: projectId,
        category_id: categoryId
      });
      setScan(response.data.data);
      setMessage(
        `Scan complete. ${response.data.data.assets_scanned} scoped asset(s) catalogued, ${response.data.data.dq_issues_raised} issue(s) raised, and ${response.data.data.policies_applied} policy action(s) applied.`
      );
      setActiveStep(3);
    } catch {
      setMessage("Scan failed. Check connector settings and try again.");
      setActiveStep(1);
    }
  }

  async function saveSchedule() {
    const selectedScopes = scopesForSelectedConnectors();
    const totalTables = Object.values(selectedScopes).reduce((total, scope) => total + selectedTableCount(scope), 0);
    if (!totalTables) {
      setMessage("Select at least one schema table before saving the schedule.");
      return;
    }
    const confirmed = window.confirm("Save this scheduled scan configuration?");
    if (!confirmed) {
      return;
    }
    setMessage("Saving connector scope and scheduled scan");
    try {
      await Promise.all(
        selectedIds.map((id) =>
          api.patch(`/api/v1/connectors/${id}/scope`, {
            catalogue_scope: connectorScopes[id]
          })
        )
      );
      const response = await api.post<ApiResponse<Scan>>("/api/v1/scans/schedules", {
        connector_ids: selectedIds,
        scan_type: scanType,
        schedule_cron: scheduleCron,
        notify_on_completion: notifyOnCompletion
      });
      setScheduledScans((current) => [response.data.data, ...current]);
      setMessage("Scheduled scan saved");
    } catch {
      setMessage("Unable to save scheduled scan");
    }
  }

  return (
    <div className="grid gap-4">
      <section>
        <h1 className="m-0 text-[20px] font-medium">Run scan</h1>
        <p className="mt-1 text-[13px] text-[var(--color-text-secondary)]">
          Discover selected connector schemas and write the metadata into the DataGov catalogue database.
        </p>
      </section>

      <div className="grid grid-cols-4 gap-2">
        {steps.map((step, index) => (
          <div key={step} className={`rounded-[8px] border p-3 text-[12px] ${index === activeStep ? "border-[var(--color-brand)] bg-[var(--color-brand-surface)] text-[var(--color-brand)]" : "border-[var(--color-border)] bg-white"}`}>
            {step}
          </div>
        ))}
      </div>

      {activeStep === 0 ? (
        <section className="grid grid-cols-3 gap-3">
          {connectors.map((connector) => (
            <button
              key={connector.id}
              type="button"
              onClick={() => toggleConnector(connector.id)}
              className={`rounded-[8px] border bg-white p-4 text-left ${selectedIds.includes(connector.id) ? "border-[var(--color-brand)]" : "border-[var(--color-border)]"}`}
            >
              <div className="text-[13px] font-medium">{connector.name}</div>
              <div className="mt-2 text-[12px] text-[var(--color-text-secondary)]"><StatusDot status={connector.status} /></div>
              <div className="mt-2 font-mono text-[11px] text-[var(--color-text-muted)]">{String(connector.config_encrypted.database_path ?? "")}</div>
            </button>
          ))}
        </section>
      ) : null}

      {activeStep === 1 ? (
        <section className="grid gap-4 rounded-[8px] border border-[var(--color-border)] bg-white p-4">
          <div className="grid grid-cols-[260px_1fr] gap-4">
            <label className="grid gap-2 text-[12px] font-medium">
              Scan type
              <select className="h-9 rounded-[7px] border border-[var(--color-border)] px-3" value={scanType} onChange={(event) => setScanType(event.target.value)}>
                <option value="full">Full</option>
                <option value="incremental">Incremental</option>
                <option value="metadata_only">Metadata only</option>
                <option value="dq_only">DQ only</option>
              </select>
            </label>
            <div className="rounded-[8px] bg-[var(--color-surface)] px-3 py-2 text-[12px] text-[var(--color-text-secondary)]">
              Selected sources: {selectedConnectors.map((connector) => connector.name).join(", ") || "None"}
              <div className="mt-1 text-[var(--color-text-muted)]">
                Only selected schemas and tables are stored as active assets in the DataGov catalogue.
              </div>
            </div>
          </div>

          <div className="grid grid-cols-[260px_260px_1fr] gap-3 rounded-[8px] bg-[var(--color-surface)] p-3">
            <label className="grid gap-2 text-[12px] font-medium">
              Target project
              <select
                className="h-9 rounded-[7px] border border-[var(--color-border)] px-3"
                value={projectId}
                onChange={(event) => {
                  const nextProject = projects.find((project) => project.id === event.target.value);
                  setProjectId(event.target.value);
                  setCategoryId(nextProject?.categories[0]?.id ?? "");
                }}
              >
                {projects.map((project) => (
                  <option key={project.id} value={project.id}>{project.name}</option>
                ))}
              </select>
            </label>
            <label className="grid gap-2 text-[12px] font-medium">
              Target category
              <select
                className="h-9 rounded-[7px] border border-[var(--color-border)] px-3"
                value={categoryId}
                onChange={(event) => setCategoryId(event.target.value)}
                disabled={!selectedProject}
              >
                {(selectedProject?.categories ?? []).map((category) => (
                  <option key={category.id} value={category.id}>{category.name}</option>
                ))}
              </select>
            </label>
            <div className="self-end rounded-[8px] bg-white px-3 py-2 text-[12px] text-[var(--color-text-secondary)]">
              Scanned assets will be written to this project/category in the catalogue database.
            </div>
          </div>

          <div className="grid gap-3">
            {selectedConnectors.map((connector) => {
              const schemas = connectorSchemas[connector.id] ?? [];
              const scope = connectorScopes[connector.id];
              return (
                <article key={connector.id} className="rounded-[8px] border border-[var(--color-border)] p-3">
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <div className="text-[13px] font-medium">{connector.name}</div>
                      <div className="font-mono text-[11px] text-[var(--color-text-muted)]">{String(connector.config_encrypted.database_path ?? "")}</div>
                    </div>
                    <div className="text-[12px] text-[var(--color-text-secondary)]">
                      {loadingSchemas[connector.id] ? "Discovering schema" : `${selectedTableCount(scope)} table(s) selected`}
                    </div>
                  </div>
                  <div className="mt-3 grid gap-3">
                    {schemas.map((schema) => {
                      const schemaSelected = Boolean(scope?.schemas.includes(schema.name));
                      const selectedTables = scope?.tables[schema.name] ?? [];
                      return (
                        <div key={schema.name} className="rounded-[8px] bg-[var(--color-surface)] p-3">
                          <label className="flex items-center gap-2 text-[12px] font-medium">
                            <input type="checkbox" checked={schemaSelected} onChange={() => toggleSchema(connector.id, schema)} />
                            Schema {schema.name}
                          </label>
                          <div className="mt-3 grid grid-cols-4 gap-2">
                            {schema.asset_names.map((assetName) => (
                              <label key={assetName} className="flex min-h-8 items-center gap-2 rounded-[7px] border border-[var(--color-border)] bg-white px-3 text-[12px]">
                                <input
                                  type="checkbox"
                                  checked={selectedTables.includes(assetName)}
                                  onChange={() => toggleTable(connector.id, schema, assetName)}
                                />
                                <span className="truncate">{assetName}</span>
                              </label>
                            ))}
                          </div>
                        </div>
                      );
                    })}
                    {!schemas.length && !loadingSchemas[connector.id] ? (
                      <div className="text-[12px] text-[var(--color-text-muted)]">No schema discovered for this connector.</div>
                    ) : null}
                  </div>
                </article>
              );
            })}
          </div>

          <div className="mt-4 grid grid-cols-[220px_1fr_auto] items-end gap-3 rounded-[8px] bg-[var(--color-surface)] p-3">
            <label className="grid gap-2 text-[12px] font-medium">
              Schedule cron
              <input
                className="h-9 rounded-[7px] border border-[var(--color-border)] px-3"
                value={scheduleCron}
                onChange={(event) => setScheduleCron(event.target.value)}
              />
            </label>
            <label className="flex h-9 items-center gap-2 text-[12px]">
              <input
                type="checkbox"
                checked={notifyOnCompletion}
                onChange={(event) => setNotifyOnCompletion(event.target.checked)}
              />
              Notify on completion
            </label>
            <Button type="button" disabled={!selectedIds.length || !scheduleCron.trim()} onClick={saveSchedule}>
              Save schedule
            </Button>
          </div>
        </section>
      ) : null}

      {activeStep === 2 ? (
        <section className="rounded-[8px] border border-[var(--color-border)] bg-white p-4">
          <div className="text-[13px] font-medium">Running scan</div>
          <div className="mt-3 h-2 overflow-hidden rounded-full bg-[#F1F5F9]">
            <div className="h-full w-3/4 rounded-full bg-[var(--color-brand)]" />
          </div>
          <pre className="mt-4 rounded-[8px] bg-[var(--color-surface)] p-3 font-mono text-[12px]" aria-live="polite">
            Connecting sources{"\n"}Discovering schema{"\n"}Writing catalogue metadata
          </pre>
        </section>
      ) : null}

      {activeStep === 3 && scan ? (
        <section className="grid grid-cols-5 gap-3">
          {[
            ["Status", scan.status],
            ["Assets scanned", String(scan.assets_scanned)],
            ["Columns scanned", String(scan.columns_scanned)],
            ["Issues raised", String(scan.dq_issues_raised)],
            ["Policies applied", String(scan.policies_applied)]
          ].map(([label, value]) => (
            <article key={label} className="rounded-[8px] border border-[var(--color-border)] bg-white p-4">
              <div className="text-[10px] font-medium uppercase tracking-[0.05em] text-[var(--color-text-muted)]">{label}</div>
              <div className="mt-2 text-[24px] font-medium capitalize">{value}</div>
            </article>
          ))}
        </section>
      ) : null}

      {message ? <div className="text-[12px] text-[var(--color-brand)]">{message}</div> : null}

      <section className="rounded-[8px] border border-[var(--color-border)] bg-white p-4">
        <div className="text-[13px] font-medium">Scheduled scans</div>
        <div className="mt-3 grid gap-2">
          {scheduledScans.slice(0, 4).map((item) => (
            <div key={item.id} className="grid grid-cols-[1fr_120px_120px] gap-3 rounded-[7px] bg-[var(--color-surface)] px-3 py-2 text-[12px]">
              <span className="font-mono">{item.schedule_cron}</span>
              <span className="capitalize">{item.scan_type}</span>
              <span className="capitalize">{item.status}</span>
            </div>
          ))}
          {!scheduledScans.length ? <div className="text-[12px] text-[var(--color-text-muted)]">No scheduled scans configured.</div> : null}
        </div>
      </section>

      <div className="flex gap-2">
        {activeStep > 0 && activeStep < 3 ? <Button type="button" onClick={() => setActiveStep(activeStep - 1)}>Back</Button> : null}
        {activeStep === 0 ? <Button type="button" variant="primary" disabled={!selectedIds.length} onClick={() => setActiveStep(1)}>Continue</Button> : null}
        {activeStep === 1 ? <Button type="button" variant="primary" disabled={!selectedIds.length} onClick={runScan}>Start scan</Button> : null}
      </div>

      <RecentAuditLog eventType="scan" title="Recent scan audit log" />
    </div>
  );
}
