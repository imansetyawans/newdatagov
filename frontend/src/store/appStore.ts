import { create } from "zustand";

export type CurrentUser = {
  id: string;
  email: string;
  fullName: string;
  role: string;
  permissions: string[];
};

type AppState = {
  token: string | null;
  user: CurrentUser | null;
  hydrate: () => void;
  setSession: (token: string, user: CurrentUser) => void;
  logout: () => void;
};

export const useAppStore = create<AppState>((set) => ({
  token: null,
  user: null,
  hydrate: () => {
    if (typeof window === "undefined") {
      return;
    }

    const token = window.localStorage.getItem("datagov-token");
    const rawUser = window.localStorage.getItem("datagov-user");
    if (!token || !rawUser) {
      return;
    }

    try {
      set({ token, user: JSON.parse(rawUser) as CurrentUser });
    } catch {
      window.localStorage.removeItem("datagov-token");
      window.localStorage.removeItem("datagov-user");
    }
  },
  setSession: (token, user) => {
    if (typeof window !== "undefined") {
      window.localStorage.setItem("datagov-token", token);
      window.localStorage.setItem("datagov-user", JSON.stringify(user));
      window.dispatchEvent(new Event("datagov-session"));
    }
    set({ token, user });
  },
  logout: () => {
    if (typeof window !== "undefined") {
      window.localStorage.removeItem("datagov-token");
      window.localStorage.removeItem("datagov-user");
      window.dispatchEvent(new Event("datagov-session"));
    }
    set({ token: null, user: null });
  }
}));
