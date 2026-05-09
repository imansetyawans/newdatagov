"use client";

import { FormEvent, useState } from "react";
import { LockKeyhole } from "lucide-react";

import { Button } from "@/components/ui/Button";
import { api } from "@/lib/api";
import { useAppStore, type CurrentUser } from "@/store/appStore";

type LoginResponse = {
  data: {
    access_token: string;
    user: {
      id: string;
      email: string;
      full_name: string;
      role: CurrentUser["role"];
    };
  };
};

export default function LoginPage() {
  const setSession = useAppStore((state) => state.setSession);
  const [email, setEmail] = useState("admin@datagov.local");
  const [password, setPassword] = useState("admin123");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError("");

    try {
      const response = await api.post<LoginResponse>("/api/v1/auth/login", {
        email,
        password
      });
      const user = response.data.data.user;
      setSession(response.data.data.access_token, {
        id: user.id,
        email: user.email,
        fullName: user.full_name,
        role: user.role
      });
      window.location.assign("/");
    } catch {
      setError("Invalid email or password");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="grid min-h-screen place-items-center p-6">
      <form
        onSubmit={handleSubmit}
        className="w-[360px] rounded-[8px] border border-[var(--color-border)] bg-white p-5"
      >
        <div className="mb-5 flex items-center gap-3">
          <div className="grid h-9 w-9 place-items-center rounded-[8px] bg-[var(--color-brand-surface)] text-[var(--color-brand)]">
            <LockKeyhole size={18} aria-hidden="true" />
          </div>
          <div>
            <h1 className="m-0 text-[20px] font-medium">Sign in</h1>
            <p className="m-0 text-[12px] text-[var(--color-text-secondary)]">Use your DataGov account</p>
          </div>
        </div>

        <label className="grid gap-2 text-[12px] font-medium text-[var(--color-text-primary)]">
          Email
          <input
            className="h-9 rounded-[7px] border border-[var(--color-border)] px-3 text-[13px] font-normal"
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            autoComplete="email"
            required
          />
        </label>

        <label className="mt-3 grid gap-2 text-[12px] font-medium text-[var(--color-text-primary)]">
          Password
          <input
            className="h-9 rounded-[7px] border border-[var(--color-border)] px-3 text-[13px] font-normal"
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            autoComplete="current-password"
            required
          />
        </label>

        {error ? <div className="mt-3 text-[11px] text-[var(--color-danger-text)]">{error}</div> : null}

        <Button className="mt-5 w-full" type="submit" variant="primary" disabled={loading}>
          {loading ? "Signing in" : "Sign in"}
        </Button>
      </form>
    </div>
  );
}
