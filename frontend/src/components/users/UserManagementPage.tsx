"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";

import { RecentAuditLog } from "@/components/audit/RecentAuditLog";
import { Button } from "@/components/ui/Button";
import { DataTable } from "@/components/ui/DataTable";
import { StatusMessage } from "@/components/ui/StatusMessage";
import { api } from "@/lib/api";
import type { ApiResponse, PermissionGroup, RoleDefinition, User } from "@/lib/types";

function codeFromName(value: string) {
  return value.trim().toLowerCase().replace(/[^0-9a-zA-Z]+/g, "_").replace(/_+/g, "_").replace(/^_|_$/g, "");
}

export function UserManagementPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [roles, setRoles] = useState<RoleDefinition[]>([]);
  const [permissionGroups, setPermissionGroups] = useState<PermissionGroup[]>([]);
  const [selectedRoleId, setSelectedRoleId] = useState("");
  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [inviteRole, setInviteRole] = useState("viewer");
  const [roleName, setRoleName] = useState("");
  const [roleDescription, setRoleDescription] = useState("");
  const [message, setMessage] = useState("");
  const [messageTone, setMessageTone] = useState<"info" | "success" | "error">("info");
  const [actionKey, setActionKey] = useState<string | null>(null);

  const selectedRole = useMemo(
    () => roles.find((role) => role.id === selectedRoleId) ?? roles[0],
    [roles, selectedRoleId]
  );

  async function loadIdentityData(preferredRoleId = selectedRoleId) {
    const [usersResponse, rolesResponse, permissionsResponse] = await Promise.all([
      api.get<ApiResponse<User[]>>("/api/v1/users"),
      api.get<ApiResponse<RoleDefinition[]>>("/api/v1/roles", { params: { include_inactive: true } }),
      api.get<ApiResponse<PermissionGroup[]>>("/api/v1/permissions")
    ]);
    setUsers(usersResponse.data.data);
    setRoles(rolesResponse.data.data);
    setPermissionGroups(permissionsResponse.data.data);
    const nextRole = rolesResponse.data.data.find((role) => role.id === preferredRoleId) ?? rolesResponse.data.data[0];
    setSelectedRoleId(nextRole?.id ?? "");
    if (!inviteRole && rolesResponse.data.data.length) {
      setInviteRole(rolesResponse.data.data[0].code);
    }
  }

  useEffect(() => {
    Promise.all([
      api.get<ApiResponse<User[]>>("/api/v1/users"),
      api.get<ApiResponse<RoleDefinition[]>>("/api/v1/roles", { params: { include_inactive: true } }),
      api.get<ApiResponse<PermissionGroup[]>>("/api/v1/permissions")
    ])
      .then(([usersResponse, rolesResponse, permissionsResponse]) => {
        setUsers(usersResponse.data.data);
        setRoles(rolesResponse.data.data);
        setPermissionGroups(permissionsResponse.data.data);
        setSelectedRoleId(rolesResponse.data.data[0]?.id ?? "");
        setInviteRole(rolesResponse.data.data.find((role) => role.code === "viewer")?.code ?? rolesResponse.data.data[0]?.code ?? "");
      })
      .catch(() => {
        setMessageTone("error");
        setMessage("Unable to load user management data");
      });
  }, []);

  async function inviteUser(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setActionKey("invite-user");
    setMessageTone("info");
    setMessage("");
    try {
      await api.post("/api/v1/users/invite", {
        email,
        full_name: fullName,
        role: inviteRole,
        password: "changeme123"
      });
      setEmail("");
      setFullName("");
      setInviteRole("viewer");
      setMessageTone("success");
      setMessage("User invited with temporary password changeme123");
      await loadIdentityData();
    } catch (error: unknown) {
      const detail = typeof error === "object" && error && "response" in error
        ? (error as { response?: { data?: { detail?: string } } }).response?.data?.detail
        : undefined;
      setMessageTone("error");
      setMessage(detail ?? "Unable to invite user");
    } finally {
      setActionKey(null);
    }
  }

  async function updateUser(user: User, changes: Partial<User>) {
    setActionKey(`user-${user.id}`);
    setMessageTone("info");
    setMessage("Updating user");
    try {
      await api.patch(`/api/v1/users/${user.id}`, changes);
      setMessageTone("success");
      setMessage("User updated");
      await loadIdentityData();
    } catch {
      setMessageTone("error");
      setMessage("Unable to update user");
    } finally {
      setActionKey(null);
    }
  }

  async function createRole(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!roleName.trim()) {
      setMessageTone("error");
      setMessage("Role name is required");
      return;
    }
    setActionKey("create-role");
    setMessageTone("info");
    setMessage("Creating role");
    try {
      const response = await api.post<ApiResponse<RoleDefinition>>("/api/v1/roles", {
        name: roleName.trim(),
        code: codeFromName(roleName),
        description: roleDescription.trim() || null,
        permissions: ["dashboard.view"]
      });
      setRoleName("");
      setRoleDescription("");
      setMessageTone("success");
      setMessage("Role created");
      await loadIdentityData(response.data.data.id);
    } catch {
      setMessageTone("error");
      setMessage("Unable to create role. Check if the role code already exists.");
    } finally {
      setActionKey(null);
    }
  }

  async function toggleRoleStatus(role: RoleDefinition) {
    setActionKey(`role-status-${role.id}`);
    setMessageTone("info");
    setMessage("Updating role");
    try {
      await api.patch(`/api/v1/roles/${role.id}`, { is_active: !role.is_active });
      setMessageTone("success");
      setMessage(`Role ${role.is_active ? "disabled" : "enabled"}`);
      await loadIdentityData(role.id);
    } catch {
      setMessageTone("error");
      setMessage("Unable to update role");
    } finally {
      setActionKey(null);
    }
  }

  async function togglePermission(permissionKey: string) {
    if (!selectedRole) {
      return;
    }
    const permissions = selectedRole.permissions.includes(permissionKey)
      ? selectedRole.permissions.filter((key) => key !== permissionKey)
      : [...selectedRole.permissions, permissionKey];
    setActionKey(`permission-${permissionKey}`);
    setMessageTone("info");
    setMessage("Updating role permissions");
    try {
      const response = await api.put<ApiResponse<RoleDefinition>>(`/api/v1/roles/${selectedRole.id}/permissions`, {
        permissions
      });
      setRoles((current) => current.map((role) => (role.id === selectedRole.id ? response.data.data : role)));
      setMessageTone("success");
      setMessage("Role permissions updated");
    } catch {
      setMessageTone("error");
      setMessage("Unable to update role permissions");
    } finally {
      setActionKey(null);
    }
  }

  return (
    <div className="grid gap-4">
      <section>
        <h1 className="m-0 text-[20px] font-medium">Users</h1>
        <p className="mt-1 text-[13px] text-[var(--color-text-secondary)]">
          Manage users, roles, and action-level access for each DataGov menu.
        </p>
      </section>

      {message ? <StatusMessage tone={messageTone}>{message}</StatusMessage> : null}

      <form onSubmit={inviteUser} className="grid grid-cols-[1fr_1fr_180px_auto] items-end gap-3 rounded-[8px] border border-[var(--color-border)] bg-white p-4">
        <label className="grid gap-2 text-[12px] font-medium">
          Email
          <input className="h-9 rounded-[7px] border border-[var(--color-border)] px-3" value={email} onChange={(event) => setEmail(event.target.value)} required />
        </label>
        <label className="grid gap-2 text-[12px] font-medium">
          Full name
          <input className="h-9 rounded-[7px] border border-[var(--color-border)] px-3" value={fullName} onChange={(event) => setFullName(event.target.value)} required />
        </label>
        <label className="grid gap-2 text-[12px] font-medium">
          Role
          <select className="h-9 rounded-[7px] border border-[var(--color-border)] px-3" value={inviteRole} onChange={(event) => setInviteRole(event.target.value)}>
            {roles.filter((role) => role.is_active).map((role) => (
              <option key={role.id} value={role.code}>{role.name}</option>
            ))}
          </select>
        </label>
        <Button type="submit" variant="primary" isLoading={actionKey === "invite-user"} loadingText="Inviting">
          Invite
        </Button>
      </form>

      <DataTable headers={["Name", "Email", "Role", "Status", "Actions"]}>
        {users.map((user) => (
          <tr key={user.id} className="border-b border-[#F1F5F9] last:border-0">
            <td className="px-4 py-3 text-[12px] font-medium">{user.full_name}</td>
            <td className="px-4 py-3 text-[12px] text-[var(--color-text-secondary)]">{user.email}</td>
            <td className="px-4 py-3">
              <select className="h-8 rounded-[7px] border border-[var(--color-border)] px-2 capitalize disabled:cursor-not-allowed disabled:opacity-50" value={user.role} disabled={actionKey === `user-${user.id}`} onChange={(event) => updateUser(user, { role: event.target.value })}>
                {roles.filter((role) => role.is_active || role.code === user.role).map((role) => (
                  <option key={role.id} value={role.code}>{role.name}</option>
                ))}
              </select>
            </td>
            <td className="px-4 py-3 text-[12px]">{user.is_active ? "Active" : "Inactive"}</td>
            <td className="px-4 py-3">
              <Button
                type="button"
                onClick={() => updateUser(user, { is_active: !user.is_active })}
                isLoading={actionKey === `user-${user.id}`}
                loadingText="Updating"
              >
                {user.is_active ? "Deactivate" : "Activate"}
              </Button>
            </td>
          </tr>
        ))}
      </DataTable>

      <section className="grid grid-cols-[420px_1fr] gap-4">
        <div className="rounded-[8px] border border-[var(--color-border)] bg-white p-4">
          <h2 className="m-0 text-[15px] font-medium">Roles</h2>
          <form onSubmit={createRole} className="mt-4 grid gap-3">
            <label className="grid gap-2 text-[12px] font-medium">
              Role name
              <input className="h-9 rounded-[7px] border border-[var(--color-border)] px-3" value={roleName} onChange={(event) => setRoleName(event.target.value)} placeholder="Data Steward" />
            </label>
            <label className="grid gap-2 text-[12px] font-medium">
              Description
              <textarea className="min-h-20 rounded-[7px] border border-[var(--color-border)] p-3" value={roleDescription} onChange={(event) => setRoleDescription(event.target.value)} placeholder="Role purpose" />
            </label>
            <Button type="submit" variant="primary" isLoading={actionKey === "create-role"} loadingText="Creating">
              Create role
            </Button>
          </form>
          <div className="mt-4 grid gap-2">
            {roles.map((role) => (
              <button
                key={role.id}
                type="button"
                onClick={() => setSelectedRoleId(role.id)}
                className={`grid grid-cols-[1fr_auto] items-center gap-3 rounded-[7px] border px-3 py-2 text-left text-[12px] ${
                  selectedRole?.id === role.id ? "border-[var(--color-brand)] bg-[var(--color-brand-surface)]" : "border-[var(--color-border)]"
                }`}
              >
                <span>
                  <span className="block font-medium">{role.name}</span>
                  <span className="block text-[var(--color-text-muted)]">{role.permissions.length} permission(s)</span>
                </span>
                <span className="capitalize text-[var(--color-text-secondary)]">{role.is_active ? "Active" : "Inactive"}</span>
              </button>
            ))}
          </div>
        </div>

        <div className="rounded-[8px] border border-[var(--color-border)] bg-white p-4">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h2 className="m-0 text-[15px] font-medium">Permission matrix</h2>
              <p className="mt-1 text-[12px] text-[var(--color-text-secondary)]">
                {selectedRole ? `Configure menu and function access for ${selectedRole.name}.` : "Select a role to configure permissions."}
              </p>
            </div>
            {selectedRole ? (
              <Button
                type="button"
                onClick={() => toggleRoleStatus(selectedRole)}
                disabled={selectedRole.code === "admin"}
                isLoading={actionKey === `role-status-${selectedRole.id}`}
                loadingText="Updating"
              >
                {selectedRole.is_active ? "Disable role" : "Enable role"}
              </Button>
            ) : null}
          </div>
          <div className="mt-4 grid gap-4">
            {permissionGroups.map((group) => (
              <section key={group.module} className="rounded-[8px] bg-[var(--color-surface)] p-3">
                <div className="text-[12px] font-medium">{group.module}</div>
                <div className="mt-3 grid grid-cols-2 gap-2">
                  {group.permissions.map((permission) => (
                    <label key={permission.key} className="flex min-h-8 items-center gap-2 rounded-[7px] border border-[var(--color-border)] bg-white px-3 text-[12px]">
                      <input
                        type="checkbox"
                        checked={Boolean(selectedRole?.permissions.includes(permission.key))}
                        disabled={!selectedRole || selectedRole.code === "admin" || actionKey === `permission-${permission.key}`}
                        onChange={() => togglePermission(permission.key)}
                      />
                      <span>{permission.label}</span>
                    </label>
                  ))}
                </div>
              </section>
            ))}
          </div>
        </div>
      </section>

      <RecentAuditLog eventType="security" title="Recent security audit log" />
    </div>
  );
}
