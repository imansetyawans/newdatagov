"use client";

import { usePathname, useRouter } from "next/navigation";
import { useEffect, useSyncExternalStore } from "react";

import { Sidebar } from "@/components/layout/Sidebar";
import { Topbar } from "@/components/layout/Topbar";
import { useAppStore } from "@/store/appStore";

const publicPaths = new Set(["/login"]);

function subscribeToSession(onStoreChange: () => void) {
  window.addEventListener("storage", onStoreChange);
  window.addEventListener("datagov-session", onStoreChange);
  return () => {
    window.removeEventListener("storage", onStoreChange);
    window.removeEventListener("datagov-session", onStoreChange);
  };
}

function getTokenSnapshot() {
  return window.localStorage.getItem("datagov-token");
}

function getServerTokenSnapshot() {
  return null;
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const hydrate = useAppStore((state) => state.hydrate);
  const token = useSyncExternalStore(subscribeToSession, getTokenSnapshot, getServerTokenSnapshot);
  const hasToken = Boolean(token);
  const isPublicPath = publicPaths.has(pathname);

  useEffect(() => {
    hydrate();

    const hasToken = Boolean(window.localStorage.getItem("datagov-token"));
    const isPublicPath = publicPaths.has(pathname);

    if (!hasToken && !isPublicPath) {
      router.replace("/login");
      return;
    }

    if (hasToken && pathname === "/login") {
      router.replace("/");
      return;
    }
  }, [hydrate, pathname, router]);

  if ((!hasToken && !isPublicPath) || (hasToken && pathname === "/login")) {
    return (
      <div className="grid min-h-screen place-items-center text-[13px] text-[var(--color-text-secondary)]">
        Loading
      </div>
    );
  }

  if (isPublicPath) {
    return <>{children}</>;
  }

  return (
    <div className="grid min-h-screen grid-cols-[var(--sidebar-width)_minmax(0,1fr)]">
      <a href="#main-content" className="skip-link">
        Skip to content
      </a>
      <Sidebar />
      <div className="min-w-0">
        <Topbar />
        <main id="main-content" tabIndex={-1} className="p-6">
          {children}
        </main>
      </div>
    </div>
  );
}
