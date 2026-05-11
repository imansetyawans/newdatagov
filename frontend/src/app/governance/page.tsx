"use client";

import { useEffect, useState } from "react";

import { RecentAuditLog } from "@/components/audit/RecentAuditLog";
import { Button } from "@/components/ui/Button";
import { DataTable } from "@/components/ui/DataTable";
import { StatusMessage } from "@/components/ui/StatusMessage";
import { api } from "@/lib/api";
import type { ApiResponse, ClassificationLabel, GovernanceCoverage, Policy } from "@/lib/types";

const defaultCoverage: GovernanceCoverage = {
  pii_columns: 0,
  gdpr_assets: 0,
  unclassified_assets: 0,
  fully_governed_assets: 0,
  total_assets: 0,
  total_columns: 0
};

export default function GovernancePage() {
  const [policies, setPolicies] = useState<Policy[]>([]);
  const [classifications, setClassifications] = useState<ClassificationLabel[]>([]);
  const [coverage, setCoverage] = useState<GovernanceCoverage>(defaultCoverage);
  const [name, setName] = useState("Classify email columns as PII");
  const [matchValue, setMatchValue] = useState("email");
  const [classification, setClassification] = useState("PII");
  const [newClassificationName, setNewClassificationName] = useState("Highly Confidential");
  const [newClassificationDescription, setNewClassificationDescription] = useState("Business-critical restricted data");
  const [newClassificationColor, setNewClassificationColor] = useState("danger");
  const [newClassificationMasksSamples, setNewClassificationMasksSamples] = useState(true);
  const [message, setMessage] = useState("Loading governance controls");
  const [messageTone, setMessageTone] = useState<"info" | "success" | "error">("info");
  const [actionKey, setActionKey] = useState<string | null>(null);

  function loadGovernance(nextMessage = "Governance controls loaded") {
    Promise.all([
      api.get<ApiResponse<Policy[]>>("/api/v1/policies"),
      api.get<ApiResponse<ClassificationLabel[]>>("/api/v1/classifications"),
      api.get<ApiResponse<GovernanceCoverage>>("/api/v1/governance/coverage")
    ])
      .then(([policyResponse, classificationResponse, coverageResponse]) => {
        setPolicies(policyResponse.data.data);
        setClassifications(classificationResponse.data.data);
        setCoverage(coverageResponse.data.data);
        setMessageTone(nextMessage.includes("Unable") ? "error" : nextMessage.includes("loaded") ? "info" : "success");
        setMessage(nextMessage);
      })
      .catch(() => {
        setMessageTone("error");
        setMessage("Unable to load governance controls");
      });
  }

  useEffect(() => {
    loadGovernance();
  }, []);

  async function createPolicy() {
    const confirmed = window.confirm("Create this active classification policy? It will apply on the next scan.");
    if (!confirmed) {
      return;
    }
    setActionKey("create-policy");
    setMessageTone("info");
    setMessage("Creating policy");
    try {
      await api.post<ApiResponse<Policy>>("/api/v1/policies", {
        name,
        policy_type: "classification",
        status: "active",
        rules: [{ field: "column_name", operator: "contains", value: matchValue }],
        action: { classification }
      });
      loadGovernance("Policy created. Run a scan to apply it.");
    } catch {
      setMessageTone("error");
      setMessage("Unable to create policy");
    } finally {
      setActionKey(null);
    }
  }

  async function createClassification() {
    const name = newClassificationName.trim();
    if (!name) {
      setMessageTone("error");
      setMessage("Classification name is required");
      return;
    }
    const confirmed = window.confirm(`Create classification "${name}"? It will be available for new policies.`);
    if (!confirmed) {
      return;
    }
    setActionKey("create-classification");
    setMessageTone("info");
    setMessage("Creating classification");
    try {
      await api.post<ApiResponse<ClassificationLabel>>("/api/v1/classifications", {
        name,
        color_key: newClassificationColor,
        description: newClassificationDescription,
        masks_samples: newClassificationMasksSamples
      });
      setClassification(name);
      loadGovernance("Classification created. You can now use it in a policy.");
    } catch {
      setMessageTone("error");
      setMessage("Unable to create classification. Check if the name already exists.");
    } finally {
      setActionKey(null);
    }
  }

  async function toggleClassificationMask(label: ClassificationLabel) {
    const nextMasksSamples = !label.masks_samples;
    const confirmed = window.confirm(
      `${nextMasksSamples ? "Mask" : "Stop masking"} sample data for "${label.name}" columns?`
    );
    if (!confirmed) {
      return;
    }
    setActionKey(`classification-mask-${label.id}`);
    setMessageTone("info");
    setMessage("Updating classification");
    try {
      await api.patch<ApiResponse<ClassificationLabel>>(`/api/v1/classifications/${label.id}`, {
        masks_samples: nextMasksSamples
      });
      loadGovernance(`Classification ${nextMasksSamples ? "will mask samples" : "will not mask samples"}`);
    } catch {
      setMessageTone("error");
      setMessage("Unable to update classification");
    } finally {
      setActionKey(null);
    }
  }

  async function deleteClassification(label: ClassificationLabel) {
    const confirmed = window.confirm(`Delete classification "${label.name}"? Only unused classifications can be deleted.`);
    if (!confirmed) {
      return;
    }
    setActionKey(`classification-delete-${label.id}`);
    setMessageTone("info");
    setMessage("Deleting classification");
    try {
      await api.delete(`/api/v1/classifications/${label.id}`);
      loadGovernance("Classification deleted");
    } catch {
      setMessageTone("error");
      setMessage("Unable to delete classification because it is still used");
    } finally {
      setActionKey(null);
    }
  }

  async function togglePolicy(policy: Policy) {
    const nextStatus = policy.status === "active" ? "disabled" : "active";
    const confirmed = window.confirm(`Set policy "${policy.name}" to ${nextStatus}?`);
    if (!confirmed) {
      return;
    }
    setActionKey(`policy-toggle-${policy.id}`);
    setMessageTone("info");
    setMessage("Updating policy");
    try {
      await api.patch<ApiResponse<Policy>>(`/api/v1/policies/${policy.id}`, { status: nextStatus });
      loadGovernance(`Policy ${nextStatus}`);
    } catch {
      setMessageTone("error");
      setMessage("Unable to update policy");
    } finally {
      setActionKey(null);
    }
  }

  async function deletePolicy(policy: Policy) {
    const confirmed = window.confirm(`Delete policy "${policy.name}"? This cannot be undone.`);
    if (!confirmed) {
      return;
    }
    setActionKey(`policy-delete-${policy.id}`);
    setMessageTone("info");
    setMessage("Deleting policy");
    try {
      await api.delete(`/api/v1/policies/${policy.id}`);
      loadGovernance("Policy deleted");
    } catch {
      setMessageTone("error");
      setMessage("Unable to delete policy");
    } finally {
      setActionKey(null);
    }
  }

  return (
    <div className="grid gap-4">
      <section>
        <h1 className="m-0 text-[20px] font-medium">Policies</h1>
        <p className="mt-1 text-[13px] text-[var(--color-text-secondary)]">
          Manage classification rules, coverage, and audit trail for local governance.
        </p>
      </section>

      <section className="grid grid-cols-4 gap-3">
        {[
          ["PII columns", coverage.pii_columns],
          ["Governed assets", coverage.fully_governed_assets],
          ["Unclassified assets", coverage.unclassified_assets],
          ["Total columns", coverage.total_columns]
        ].map(([label, value]) => (
          <article key={label} className="rounded-[8px] border border-[var(--color-border)] bg-white p-4">
            <div className="text-[10px] font-medium uppercase tracking-[0.05em] text-[var(--color-text-muted)]">{label}</div>
            <div className="mt-2 text-[24px] font-medium leading-none">{value}</div>
          </article>
        ))}
      </section>

      <section className="rounded-[8px] border border-[var(--color-border)] bg-white p-4">
        <div className="mb-3">
          <h2 className="m-0 text-[15px] font-medium">Classification management</h2>
          <p className="mt-1 text-[12px] text-[var(--color-text-secondary)]">
            Create reusable tags such as PII, Sensitive, or Highly Confidential.
          </p>
        </div>
        <div className="grid grid-cols-[220px_1fr_150px_150px_auto] items-end gap-3">
          <label className="grid gap-2 text-[12px] font-medium">
            Classification name
            <input
              className="h-9 rounded-[7px] border border-[var(--color-border)] px-3"
              value={newClassificationName}
              onChange={(event) => setNewClassificationName(event.target.value)}
              placeholder="Highly Confidential"
            />
          </label>
          <label className="grid gap-2 text-[12px] font-medium">
            Description
            <input
              className="h-9 rounded-[7px] border border-[var(--color-border)] px-3"
              value={newClassificationDescription}
              onChange={(event) => setNewClassificationDescription(event.target.value)}
              placeholder="Explain how this classification is used"
            />
          </label>
          <label className="grid gap-2 text-[12px] font-medium">
            Color
            <select
              className="h-9 rounded-[7px] border border-[var(--color-border)] px-3"
              value={newClassificationColor}
              onChange={(event) => setNewClassificationColor(event.target.value)}
            >
              <option value="danger">Danger</option>
              <option value="warning">Warning</option>
              <option value="blue">Blue</option>
              <option value="purple">Purple</option>
              <option value="success">Success</option>
              <option value="custom">Custom</option>
            </select>
          </label>
          <label className="flex h-9 items-center gap-2 text-[12px] font-medium">
            <input
              type="checkbox"
              checked={newClassificationMasksSamples}
              onChange={(event) => setNewClassificationMasksSamples(event.target.checked)}
            />
            Mask samples
          </label>
          <Button
            type="button"
            variant="primary"
            disabled={!newClassificationName.trim()}
            isLoading={actionKey === "create-classification"}
            loadingText="Creating"
            onClick={createClassification}
          >
            Create classification
          </Button>
        </div>
        <div className="mt-3 flex flex-wrap gap-2">
          {classifications.map((label) => (
            <span
              key={label.id}
              className="inline-flex items-center gap-2 rounded-[7px] border border-[var(--color-border)] px-3 py-1 text-[12px]"
              title={label.description ?? label.name}
            >
              <span>{label.name}</span>
              <span className="text-[var(--color-text-muted)]">{label.masks_samples ? "Masks samples" : "No masking"}</span>
              <button
                className="text-[var(--color-brand)] disabled:cursor-not-allowed disabled:opacity-50"
                type="button"
                disabled={Boolean(actionKey)}
                onClick={() => toggleClassificationMask(label)}
              >
                Toggle
              </button>
              <button
                className="text-red-600 disabled:cursor-not-allowed disabled:opacity-50"
                type="button"
                disabled={Boolean(actionKey)}
                onClick={() => deleteClassification(label)}
              >
                Delete
              </button>
            </span>
          ))}
        </div>
      </section>

      <section className="rounded-[8px] border border-[var(--color-border)] bg-white p-4">
        <div className="mb-3">
          <h2 className="m-0 text-[15px] font-medium">Policy rule</h2>
          <p className="mt-1 text-[12px] text-[var(--color-text-secondary)]">
            Apply a classification when a scanned column name contains the configured text.
          </p>
        </div>
        <div className="grid grid-cols-[1.4fr_1fr_180px_auto] items-end gap-3">
          <label className="grid gap-2 text-[12px] font-medium">
            Policy name
            <input
              className="h-9 rounded-[7px] border border-[var(--color-border)] px-3"
              value={name}
              onChange={(event) => setName(event.target.value)}
            />
          </label>
          <label className="grid gap-2 text-[12px] font-medium">
            Column contains
            <input
              className="h-9 rounded-[7px] border border-[var(--color-border)] px-3"
              value={matchValue}
              onChange={(event) => setMatchValue(event.target.value)}
            />
          </label>
          <label className="grid gap-2 text-[12px] font-medium">
            Policy classification
            <select
              className="h-9 rounded-[7px] border border-[var(--color-border)] px-3"
              value={classification}
              onChange={(event) => setClassification(event.target.value)}
            >
              {classifications.map((label) => (
                <option key={label.id} value={label.name}>
                  {label.name}
                </option>
              ))}
            </select>
          </label>
          <Button
            type="button"
            variant="primary"
            disabled={!name.trim() || !matchValue.trim()}
            isLoading={actionKey === "create-policy"}
            loadingText="Creating"
            onClick={createPolicy}
          >
            Create policy
          </Button>
        </div>
        <StatusMessage className="mt-3" tone={messageTone}>{message}</StatusMessage>
      </section>

      <DataTable headers={["Policy", "Type", "Status", "Rule", "Action", "Controls"]}>
        {policies.map((policy) => (
          <tr key={policy.id} className="border-b border-[#F1F5F9] last:border-0">
            <td className="px-4 py-3 text-[12px] font-medium">{policy.name}</td>
            <td className="px-4 py-3 text-[12px] capitalize">{policy.policy_type}</td>
            <td className="px-4 py-3 text-[12px] capitalize">{policy.status}</td>
            <td className="px-4 py-3 font-mono text-[11px] text-[var(--color-text-secondary)]">{JSON.stringify(policy.rules)}</td>
            <td className="px-4 py-3 font-mono text-[11px] text-[var(--color-text-secondary)]">{JSON.stringify(policy.action)}</td>
            <td className="px-4 py-3">
              <div className="flex gap-2">
                <Button
                  type="button"
                  onClick={() => togglePolicy(policy)}
                  isLoading={actionKey === `policy-toggle-${policy.id}`}
                  loadingText="Updating"
                >
                  {policy.status === "active" ? "Disable" : "Enable"}
                </Button>
                <Button
                  type="button"
                  variant="danger"
                  onClick={() => deletePolicy(policy)}
                  isLoading={actionKey === `policy-delete-${policy.id}`}
                  loadingText="Deleting"
                >
                  Delete
                </Button>
              </div>
            </td>
          </tr>
        ))}
        {!policies.length ? (
          <tr>
            <td className="px-4 py-8 text-center text-[12px] text-[var(--color-text-muted)]" colSpan={6}>
              No policies configured yet.
            </td>
          </tr>
        ) : null}
      </DataTable>

      <RecentAuditLog eventType="governance" title="Recent governance audit log" />
    </div>
  );
}
