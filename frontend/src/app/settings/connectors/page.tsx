"use client";

import { FormEvent, useEffect, useState } from "react";

import { RecentAuditLog } from "@/components/audit/RecentAuditLog";
import { Button } from "@/components/ui/Button";
import { DataTable } from "@/components/ui/DataTable";
import { StatusMessage } from "@/components/ui/StatusMessage";
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
  const [messageTone, setMessageTone] = useState<"info" | "success" | "error">("info");
  const [actionKey, setActionKey] = useState<string | null>(null);

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
          setMessageTone("error");
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
    setActionKey("add-connector");
    setMessageTone("info");
    setMessage("Creating connector");
    try {
      await api.post("/api/v1/connectors", {
        name,
        connector_type: "sqlite",
        config: { database_path: databasePath }
      });
      setMessageTone("success");
      setMessage("Connector created");
      await loadConnectors();
    } catch {
      setMessageTone("error");
      setMessage("Unable to create connector");
    } finally {
      setActionKey(null);
    }
  }

  async function addNotification(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setActionKey("add-notification");
    setMessageTone("info");
    setMessage("Creating notification target");
    try {
      await api.post("/api/v1/notifications", {
        channel: notificationChannel,
        target: notificationTarget,
        enabled: true,
        events: ["scan_completed", "dq_issue_created"]
      });
      setMessageTone("success");
      setMessage("Notification setting created");
      await loadNotifications();
    } catch {
      setMessageTone("error");
      setMessage("Unable to create notification setting");
    } finally {
      setActionKey(null);
    }
  }

  async function toggleNotification(setting: NotificationSetting) {
    setActionKey(`notification-toggle-${setting.id}`);
    setMessageTone("info");
    setMessage("Updating notification setting");
    try {
      await api.patch(`/api/v1/notifications/${setting.id}`, {
        enabled: !setting.enabled
      });
      setMessageTone("success");
      setMessage("Notification setting updated");
      await loadNotifications();
    } catch {
      setMessageTone("error");
      setMessage("Unable to update notification setting");
    } finally {
      setActionKey(null);
    }
  }

  async function testNotification(setting: NotificationSetting) {
    setActionKey(`notification-test-${setting.id}`);
    setMessageTone("info");
    setMessage("Testing notification");
    try {
      const response = await api.post<ApiResponse<{ success: boolean; message: string }>>(`/api/v1/notifications/${setting.id}/test`);
      setMessageTone("success");
      setMessage(response.data.data.message);
    } catch {
      setMessageTone("error");
      setMessage("Unable to test notification");
    } finally {
      setActionKey(null);
    }
  }

  async function deleteNotification(setting: NotificationSetting) {
    setActionKey(`notification-delete-${setting.id}`);
    setMessageTone("info");
    setMessage("Deleting notification setting");
    try {
      await api.delete(`/api/v1/notifications/${setting.id}`);
      setMessageTone("success");
      setMessage("Notification setting deleted");
      await loadNotifications();
    } catch {
      setMessageTone("error");
      setMessage("Unable to delete notification setting");
    } finally {
      setActionKey(null);
    }
  }

  async function testConnector(connector: Connector) {
    setActionKey(`connector-test-${connector.id}`);
    setMessageTone("info");
    setMessage("Testing connector");
    try {
      const response = await api.post<ApiResponse<{ success: boolean; error?: string }>>(`/api/v1/connectors/${connector.id}/test`);
      setMessageTone(response.data.data.success ? "success" : "error");
      setMessage(response.data.data.success ? "Connection test passed" : `Connection failed: ${response.data.data.error}`);
      await loadConnectors();
    } catch {
      setMessageTone("error");
      setMessage("Unable to test connector");
    } finally {
      setActionKey(null);
    }
  }

  async function deleteConnector(connector: Connector) {
    setActionKey(`connector-delete-${connector.id}`);
    setMessageTone("info");
    setMessage("Deleting connector");
    try {
      await api.delete(`/api/v1/connectors/${connector.id}`);
      setMessageTone("success");
      setMessage("Connector deleted");
      await loadConnectors();
    } catch {
      setMessageTone("error");
      setMessage("Unable to delete connector");
    } finally {
      setActionKey(null);
    }
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
        <Button type="submit" variant="primary" isLoading={actionKey === "add-connector"} loadingText="Adding">
          Add connector
        </Button>
      </form>

      {message ? <StatusMessage tone={messageTone}>{message}</StatusMessage> : null}

      <DataTable headers={["Name", "Type", "Status", "Path", "Actions"]} caption="Configured source connectors">
        {connectors.map((connector) => (
          <tr key={connector.id} className="border-b border-[#F1F5F9] last:border-0">
            <td className="px-4 py-3 text-[12px] font-medium">{connector.name}</td>
            <td className="px-4 py-3 text-[12px]">{connector.connector_type}</td>
            <td className="px-4 py-3 text-[12px]"><StatusDot status={connector.status} /></td>
            <td className="px-4 py-3 font-mono text-[11px] text-[var(--color-text-secondary)]">{String(connector.config_encrypted.database_path ?? "")}</td>
            <td className="flex gap-2 px-4 py-3">
              <Button
                type="button"
                onClick={() => testConnector(connector)}
                isLoading={actionKey === `connector-test-${connector.id}`}
                loadingText="Testing"
              >
                Test
              </Button>
              <Button
                type="button"
                variant="danger"
                onClick={() => deleteConnector(connector)}
                isLoading={actionKey === `connector-delete-${connector.id}`}
                loadingText="Deleting"
              >
                Delete
              </Button>
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
          <Button type="submit" variant="primary" isLoading={actionKey === "add-notification"} loadingText="Adding">
            Add notification
          </Button>
        </form>
        <DataTable headers={["Channel", "Target", "Events", "Status", "Actions"]} caption="Notification settings">
          {notifications.map((setting) => (
            <tr key={setting.id} className="border-b border-[#F1F5F9] last:border-0">
              <td className="px-4 py-3 text-[12px] capitalize">{setting.channel}</td>
              <td className="px-4 py-3 text-[12px]">{setting.target}</td>
              <td className="px-4 py-3 font-mono text-[11px]">{setting.events.join(", ")}</td>
              <td className="px-4 py-3 text-[12px]">{setting.enabled ? "Enabled" : "Disabled"}</td>
              <td className="flex gap-2 px-4 py-3">
                <Button
                  type="button"
                  onClick={() => testNotification(setting)}
                  isLoading={actionKey === `notification-test-${setting.id}`}
                  loadingText="Testing"
                >
                  Test
                </Button>
                <Button
                  type="button"
                  onClick={() => toggleNotification(setting)}
                  isLoading={actionKey === `notification-toggle-${setting.id}`}
                  loadingText="Updating"
                >
                  {setting.enabled ? "Disable" : "Enable"}
                </Button>
                <Button
                  type="button"
                  variant="danger"
                  onClick={() => deleteNotification(setting)}
                  isLoading={actionKey === `notification-delete-${setting.id}`}
                  loadingText="Deleting"
                >
                  Delete
                </Button>
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
