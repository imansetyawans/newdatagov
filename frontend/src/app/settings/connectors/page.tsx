"use client";

import { FormEvent, useEffect, useState } from "react";

import { RecentAuditLog } from "@/components/audit/RecentAuditLog";
import { Button } from "@/components/ui/Button";
import { DataTable } from "@/components/ui/DataTable";
import { StatusDot } from "@/components/ui/StatusDot";
import { api } from "@/lib/api";
import type { ApiResponse, Connector, NotificationSetting } from "@/lib/types";

export default function ConnectorsPage() {
  const [connectors, setConnectors] = useState<Connector[]>([]);
  const [name, setName] = useState("Local DataGov SQLite");
  const [databasePath, setDatabasePath] = useState("datagov.db");
  const [notifications, setNotifications] = useState<NotificationSetting[]>([]);
  const [notificationChannel, setNotificationChannel] = useState("email");
  const [notificationTarget, setNotificationTarget] = useState("admin@datagov.local");
  const [message, setMessage] = useState("");

  async function loadConnectors() {
    const response = await api.get<ApiResponse<Connector[]>>("/api/v1/connectors");
    setConnectors(response.data.data);
  }

  async function loadNotifications() {
    const response = await api.get<ApiResponse<NotificationSetting[]>>("/api/v1/notifications");
    setNotifications(response.data.data);
  }

  useEffect(() => {
    let mounted = true;
    api
      .get<ApiResponse<Connector[]>>("/api/v1/connectors")
      .then((response) => {
        if (mounted) {
          setConnectors(response.data.data);
        }
      })
      .catch(() => {
        if (mounted) {
          setMessage("Unable to load connectors");
        }
      });
    api
      .get<ApiResponse<NotificationSetting[]>>("/api/v1/notifications")
      .then((response) => {
        if (mounted) {
          setNotifications(response.data.data);
        }
      })
      .catch(() => {
        if (mounted) {
          setNotifications([]);
        }
      });
    return () => {
      mounted = false;
    };
  }, []);

  async function addConnector(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await api.post("/api/v1/connectors", {
      name,
      connector_type: "sqlite",
      config: { database_path: databasePath }
    });
    setMessage("Connector created");
    await loadConnectors();
  }

  async function addNotification(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await api.post("/api/v1/notifications", {
      channel: notificationChannel,
      target: notificationTarget,
      enabled: true,
      events: ["scan_completed", "dq_issue_created"]
    });
    setMessage("Notification setting created");
    await loadNotifications();
  }

  async function toggleNotification(setting: NotificationSetting) {
    await api.patch(`/api/v1/notifications/${setting.id}`, {
      enabled: !setting.enabled
    });
    setMessage("Notification setting updated");
    await loadNotifications();
  }

  async function testNotification(setting: NotificationSetting) {
    const response = await api.post<ApiResponse<{ success: boolean; message: string }>>(`/api/v1/notifications/${setting.id}/test`);
    setMessage(response.data.data.message);
  }

  async function deleteNotification(setting: NotificationSetting) {
    await api.delete(`/api/v1/notifications/${setting.id}`);
    setMessage("Notification setting deleted");
    await loadNotifications();
  }

  async function testConnector(connector: Connector) {
    const response = await api.post<ApiResponse<{ success: boolean; error?: string }>>(`/api/v1/connectors/${connector.id}/test`);
    setMessage(response.data.data.success ? "Connection test passed" : `Connection failed: ${response.data.data.error}`);
    await loadConnectors();
  }

  async function deleteConnector(connector: Connector) {
    await api.delete(`/api/v1/connectors/${connector.id}`);
    await loadConnectors();
  }

  return (
    <div className="grid gap-4">
      <section>
        <h1 className="m-0 text-[20px] font-medium">Connectors</h1>
        <p className="mt-1 text-[13px] text-[var(--color-text-secondary)]">Configure local SQLite sources for metadata discovery.</p>
      </section>

      <form onSubmit={addConnector} className="grid grid-cols-[1fr_1fr_auto] items-end gap-3 rounded-[8px] border border-[var(--color-border)] bg-white p-4">
        <label className="grid gap-2 text-[12px] font-medium">
          Name
          <input className="h-9 rounded-[7px] border border-[var(--color-border)] px-3" value={name} onChange={(event) => setName(event.target.value)} required />
        </label>
        <label className="grid gap-2 text-[12px] font-medium">
          SQLite database path
          <input className="h-9 rounded-[7px] border border-[var(--color-border)] px-3 font-mono text-[12px]" value={databasePath} onChange={(event) => setDatabasePath(event.target.value)} required />
        </label>
        <Button type="submit" variant="primary">Add connector</Button>
      </form>

      {message ? <div className="text-[12px] text-[var(--color-brand)]">{message}</div> : null}

      <DataTable headers={["Name", "Type", "Status", "Path", "Actions"]} caption="Configured source connectors">
        {connectors.map((connector) => (
          <tr key={connector.id} className="border-b border-[#F1F5F9] last:border-0">
            <td className="px-4 py-3 text-[12px] font-medium">{connector.name}</td>
            <td className="px-4 py-3 text-[12px]">{connector.connector_type}</td>
            <td className="px-4 py-3 text-[12px]"><StatusDot status={connector.status} /></td>
            <td className="px-4 py-3 font-mono text-[11px] text-[var(--color-text-secondary)]">{String(connector.config_encrypted.database_path ?? "")}</td>
            <td className="flex gap-2 px-4 py-3">
              <Button type="button" onClick={() => testConnector(connector)}>Test</Button>
              <Button type="button" variant="danger" onClick={() => deleteConnector(connector)}>Delete</Button>
            </td>
          </tr>
        ))}
      </DataTable>

      <section className="grid gap-3 rounded-[8px] border border-[var(--color-border)] bg-white p-4">
        <div>
          <h2 className="m-0 text-[15px] font-medium">Notifications</h2>
          <p className="mt-1 text-[12px] text-[var(--color-text-secondary)]">
            Configure localhost email or Slack targets for scan completion and quality alerts.
          </p>
        </div>
        <form onSubmit={addNotification} className="grid grid-cols-[160px_1fr_auto] items-end gap-3">
          <label className="grid gap-2 text-[12px] font-medium">
            Channel
            <select
              className="h-9 rounded-[7px] border border-[var(--color-border)] px-3"
              value={notificationChannel}
              onChange={(event) => {
                setNotificationChannel(event.target.value);
                setNotificationTarget(event.target.value === "slack" ? "https://hooks.slack.com/services/local/test" : "admin@datagov.local");
              }}
            >
              <option value="email">Email</option>
              <option value="slack">Slack</option>
            </select>
          </label>
          <label className="grid gap-2 text-[12px] font-medium">
            Target
            <input
              className="h-9 rounded-[7px] border border-[var(--color-border)] px-3"
              value={notificationTarget}
              onChange={(event) => setNotificationTarget(event.target.value)}
              required
            />
          </label>
          <Button type="submit" variant="primary">Add notification</Button>
        </form>
        <DataTable headers={["Channel", "Target", "Events", "Status", "Actions"]} caption="Notification settings">
          {notifications.map((setting) => (
            <tr key={setting.id} className="border-b border-[#F1F5F9] last:border-0">
              <td className="px-4 py-3 text-[12px] capitalize">{setting.channel}</td>
              <td className="px-4 py-3 text-[12px]">{setting.target}</td>
              <td className="px-4 py-3 font-mono text-[11px]">{setting.events.join(", ")}</td>
              <td className="px-4 py-3 text-[12px]">{setting.enabled ? "Enabled" : "Disabled"}</td>
              <td className="flex gap-2 px-4 py-3">
                <Button type="button" onClick={() => testNotification(setting)}>Test</Button>
                <Button type="button" onClick={() => toggleNotification(setting)}>{setting.enabled ? "Disable" : "Enable"}</Button>
                <Button type="button" variant="danger" onClick={() => deleteNotification(setting)}>Delete</Button>
              </td>
            </tr>
          ))}
          {!notifications.length ? (
            <tr>
              <td colSpan={5} className="px-4 py-6 text-center text-[12px] text-[var(--color-text-muted)]">
                No notification targets configured.
              </td>
            </tr>
          ) : null}
        </DataTable>
      </section>

      <RecentAuditLog title="Recent audit log" />
    </div>
  );
}
