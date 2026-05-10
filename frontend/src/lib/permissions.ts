import type { CurrentUser } from "@/store/appStore";

export function hasPermission(user: CurrentUser | null, permission: string) {
  if (!user) {
    return false;
  }
  if (user.role === "admin") {
    return true;
  }
  return user.permissions.includes(permission);
}
