import { apiFetch } from "./client";
import type { User } from "@/types/api";

export function listUsers(): Promise<User[]> {
  return apiFetch<User[]>("/users");
}

export function registerUser(email: string, displayName: string, password: string): Promise<User> {
  return apiFetch<User>("/users", {
    method: "POST",
    body: { email, display_name: displayName, password },
  });
}
