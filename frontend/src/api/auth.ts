import { apiFetch } from "./client";
import type { Token, User } from "@/types/api";

export function login(email: string, password: string): Promise<Token> {
  return apiFetch<Token>("/auth/login", { method: "POST", form: { username: email, password } });
}

export function getMe(): Promise<User> {
  return apiFetch<User>("/auth/me");
}
