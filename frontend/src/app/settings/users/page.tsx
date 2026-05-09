"use client";

import { FormEvent, useEffect, useState } from "react";

import { RecentAuditLog } from "@/components/audit/RecentAuditLog";
import { Button } from "@/components/ui/Button";
import { DataTable } from "@/components/ui/DataTable";
import { api } from "@/lib/api";
import type { ApiResponse, User } from "@/lib/types";

export default function UsersPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [role, setRole] = useState<User["role"]>("viewer");
  const [message, setMessage] = useState("");

  async function loadUsers() {
    const response = await api.get<ApiResponse<User[]>>("/api/v1/users");
    setUsers(response.data.data);
  }

  useEffect(() => {
    let mounted = true;
    api
      .get<ApiResponse<User[]>>("/api/v1/users")
      .then((response) => {
        if (mounted) {
          setUsers(response.data.data);
        }
      })
      .catch(() => {
        if (mounted) {
          setMessage("Unable to load users");
        }
      });
    return () => {
      mounted = false;
    };
  }, []);

  async function inviteUser(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage("");
    await api.post("/api/v1/users/invite", {
      email,
      full_name: fullName,
      role,
      password: "changeme123"
    });
    setEmail("");
    setFullName("");
    setRole("viewer");
    setMessage("User invited with temporary password changeme123");
    await loadUsers();
  }

  async function updateUser(user: User, changes: Partial<User>) {
    await api.patch(`/api/v1/users/${user.id}`, changes);
    await loadUsers();
  }

  return (
    <div className="grid gap-4">
      <section>
        <h1 className="m-0 text-[20px] font-medium">Users and roles</h1>
        <p className="mt-1 text-[13px] text-[var(--color-text-secondary)]">Invite users, assign roles, and deactivate access.</p>
      </section>

      <form onSubmit={inviteUser} className="grid grid-cols-[1fr_1fr_160px_auto] items-end gap-3 rounded-[8px] border border-[var(--color-border)] bg-white p-4">
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
          <select className="h-9 rounded-[7px] border border-[var(--color-border)] px-3" value={role} onChange={(event) => setRole(event.target.value as User["role"])}>
            <option value="viewer">Viewer</option>
            <option value="editor">Editor</option>
            <option value="admin">Admin</option>
          </select>
        </label>
        <Button type="submit" variant="primary">Invite</Button>
      </form>

      {message ? <div className="text-[12px] text-[var(--color-brand)]">{message}</div> : null}

      <DataTable headers={["Name", "Email", "Role", "Status", "Actions"]}>
        {users.map((user) => (
          <tr key={user.id} className="border-b border-[#F1F5F9] last:border-0">
            <td className="px-4 py-3 text-[12px] font-medium">{user.full_name}</td>
            <td className="px-4 py-3 text-[12px] text-[var(--color-text-secondary)]">{user.email}</td>
            <td className="px-4 py-3">
              <select className="h-8 rounded-[7px] border border-[var(--color-border)] px-2 capitalize" value={user.role} onChange={(event) => updateUser(user, { role: event.target.value as User["role"] })}>
                <option value="viewer">Viewer</option>
                <option value="editor">Editor</option>
                <option value="admin">Admin</option>
              </select>
            </td>
            <td className="px-4 py-3 text-[12px]">{user.is_active ? "Active" : "Inactive"}</td>
            <td className="px-4 py-3">
              <Button type="button" onClick={() => updateUser(user, { is_active: !user.is_active })}>
                {user.is_active ? "Deactivate" : "Activate"}
              </Button>
            </td>
          </tr>
        ))}
      </DataTable>

      <RecentAuditLog title="Recent audit log" />
    </div>
  );
}
