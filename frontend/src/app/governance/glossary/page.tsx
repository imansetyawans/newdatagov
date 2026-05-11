"use client";

import { useEffect, useMemo, useState } from "react";

import { RecentAuditLog } from "@/components/audit/RecentAuditLog";
import { Button } from "@/components/ui/Button";
import { DataTable } from "@/components/ui/DataTable";
import { StatusMessage } from "@/components/ui/StatusMessage";
import { api } from "@/lib/api";
import type { ApiResponse, GlossarySuggestion, GlossaryTerm } from "@/lib/types";

export default function GlossaryPage() {
  const [terms, setTerms] = useState<GlossaryTerm[]>([]);
  const [suggestions, setSuggestions] = useState<GlossarySuggestion[]>([]);
  const [query, setQuery] = useState("");
  const [term, setTerm] = useState("");
  const [definition, setDefinition] = useState("");
  const [synonyms, setSynonyms] = useState("");
  const [message, setMessage] = useState("Loading glossary");
  const [messageTone, setMessageTone] = useState<"info" | "success" | "error">("info");
  const [actionKey, setActionKey] = useState<string | null>(null);

  function loadGlossary(nextMessage = "Glossary loaded") {
    Promise.all([
      api.get<ApiResponse<GlossaryTerm[]>>("/api/v1/glossary", { params: { q: query || undefined } }),
      api.get<ApiResponse<GlossarySuggestion[]>>("/api/v1/glossary/suggestions")
    ])
      .then(([termResponse, suggestionResponse]) => {
        setTerms(termResponse.data.data);
        setSuggestions(suggestionResponse.data.data);
        setMessageTone(nextMessage.includes("created") || nextMessage.includes("saved") ? "success" : "info");
        setMessage(nextMessage);
      })
      .catch(() => {
        setMessageTone("error");
        setMessage("Unable to load glossary");
      });
  }

  useEffect(() => {
    const timer = window.setTimeout(() => loadGlossary(), 250);
    return () => window.clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [query]);

  const approvedCount = useMemo(() => terms.filter((item) => item.status === "approved").length, [terms]);

  async function createTerm() {
    const confirmed = window.confirm("Create this glossary term?");
    if (!confirmed) {
      return;
    }
    setActionKey("create-term");
    setMessageTone("info");
    setMessage("Creating glossary term");
    try {
      await api.post<ApiResponse<GlossaryTerm>>("/api/v1/glossary", {
        term,
        definition,
        synonyms: synonyms.split(",").map((item) => item.trim()).filter(Boolean),
        status: "approved"
      });
      setTerm("");
      setDefinition("");
      setSynonyms("");
      loadGlossary("Glossary term created");
    } catch {
      setMessageTone("error");
      setMessage("Unable to create glossary term");
    } finally {
      setActionKey(null);
    }
  }

  async function approveSuggestion(suggestion: GlossarySuggestion) {
    const targetTerm = terms.find((item) => item.id === suggestion.term_id);
    if (!targetTerm) {
      setMessageTone("error");
      setMessage("Glossary term not found for suggestion");
      return;
    }
    const confirmed = window.confirm(`Link ${suggestion.term} to ${suggestion.resource_name}?`);
    if (!confirmed) {
      return;
    }
    const linked_asset_ids =
      suggestion.resource_type === "asset"
        ? Array.from(new Set([...targetTerm.linked_asset_ids, suggestion.resource_id]))
        : targetTerm.linked_asset_ids;
    const linked_column_ids =
      suggestion.resource_type === "column"
        ? Array.from(new Set([...targetTerm.linked_column_ids, suggestion.resource_id]))
        : targetTerm.linked_column_ids;
    setActionKey(`suggestion-${suggestion.resource_id}`);
    setMessageTone("info");
    setMessage("Saving glossary link");
    try {
      await api.patch<ApiResponse<GlossaryTerm>>(`/api/v1/glossary/${targetTerm.id}`, {
        linked_asset_ids,
        linked_column_ids
      });
      loadGlossary("Glossary link saved");
    } catch {
      setMessageTone("error");
      setMessage("Unable to save glossary link");
    } finally {
      setActionKey(null);
    }
  }

  return (
    <div className="grid gap-4">
      <section className="flex items-start justify-between gap-4">
        <div>
          <h1 className="m-0 text-[20px] font-medium">Glossary</h1>
          <p className="mt-1 text-[13px] text-[var(--color-text-secondary)]">Manage business terms and link them to assets or columns.</p>
        </div>
        <input
          className="h-9 w-[320px] rounded-[7px] border border-[var(--color-border)] px-3"
          placeholder="Search glossary"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
        />
      </section>

      <section className="grid grid-cols-3 gap-3">
        <article className="rounded-[8px] border border-[var(--color-border)] bg-white p-4">
          <div className="text-[10px] font-medium uppercase tracking-[0.05em] text-[var(--color-text-muted)]">Terms</div>
          <div className="mt-2 text-[24px] font-medium">{terms.length}</div>
        </article>
        <article className="rounded-[8px] border border-[var(--color-border)] bg-white p-4">
          <div className="text-[10px] font-medium uppercase tracking-[0.05em] text-[var(--color-text-muted)]">Approved</div>
          <div className="mt-2 text-[24px] font-medium">{approvedCount}</div>
        </article>
        <article className="rounded-[8px] border border-[var(--color-border)] bg-white p-4">
          <div className="text-[10px] font-medium uppercase tracking-[0.05em] text-[var(--color-text-muted)]">Suggestions</div>
          <div className="mt-2 text-[24px] font-medium">{suggestions.length}</div>
        </article>
      </section>

      <section className="rounded-[8px] border border-[var(--color-border)] bg-white p-4">
        <div className="grid grid-cols-[220px_1fr_220px_auto] items-end gap-3">
          <label className="grid gap-2 text-[12px] font-medium">
            Term
            <input className="h-9 rounded-[7px] border border-[var(--color-border)] px-3" value={term} onChange={(event) => setTerm(event.target.value)} />
          </label>
          <label className="grid gap-2 text-[12px] font-medium">
            Definition
            <input className="h-9 rounded-[7px] border border-[var(--color-border)] px-3" value={definition} onChange={(event) => setDefinition(event.target.value)} />
          </label>
          <label className="grid gap-2 text-[12px] font-medium">
            Synonyms
            <input className="h-9 rounded-[7px] border border-[var(--color-border)] px-3" value={synonyms} onChange={(event) => setSynonyms(event.target.value)} />
          </label>
          <Button
            type="button"
            variant="primary"
            disabled={!term.trim() || !definition.trim()}
            isLoading={actionKey === "create-term"}
            loadingText="Creating"
            onClick={createTerm}
          >
            Create term
          </Button>
        </div>
        <StatusMessage className="mt-3" tone={messageTone}>{message}</StatusMessage>
      </section>

      <DataTable headers={["Term", "Definition", "Synonyms", "Status", "Links"]}>
        {terms.map((item) => (
          <tr key={item.id} className="border-b border-[#F1F5F9] last:border-0">
            <td className="px-4 py-3 text-[12px] font-medium">{item.term}</td>
            <td className="px-4 py-3 text-[12px] text-[var(--color-text-secondary)]">{item.definition}</td>
            <td className="px-4 py-3 text-[12px]">{item.synonyms.join(", ") || "-"}</td>
            <td className="px-4 py-3 text-[12px] capitalize">{item.status}</td>
            <td className="px-4 py-3 text-[12px]">{item.linked_asset_ids.length + item.linked_column_ids.length}</td>
          </tr>
        ))}
      </DataTable>

      <section className="rounded-[8px] border border-[var(--color-border)] bg-white p-4">
        <div className="text-[13px] font-medium">Link suggestions</div>
        <div className="mt-3 grid gap-2">
          {suggestions.slice(0, 8).map((suggestion) => (
            <div key={`${suggestion.term_id}-${suggestion.resource_id}`} className="grid grid-cols-[1fr_120px_auto] items-center gap-3 rounded-[7px] bg-[var(--color-surface)] px-3 py-2 text-[12px]">
              <span>{suggestion.term} to {suggestion.resource_name}</span>
              <span>{Math.round(suggestion.confidence * 100)}%</span>
              <Button
                type="button"
                onClick={() => approveSuggestion(suggestion)}
                isLoading={actionKey === `suggestion-${suggestion.resource_id}`}
                loadingText="Saving"
              >
                Link
              </Button>
            </div>
          ))}
          {!suggestions.length ? <div className="text-[12px] text-[var(--color-text-muted)]">No suggestions yet. Run a scan or add terms.</div> : null}
        </div>
      </section>

      <RecentAuditLog eventType="glossary" title="Recent glossary audit log" />
    </div>
  );
}
