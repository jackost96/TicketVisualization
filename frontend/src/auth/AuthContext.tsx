import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { getAuthToken, setAuthToken, setUnauthorizedHandler } from "@/api/client";
import { getMe, login as loginRequest } from "@/api/auth";
import type { User } from "@/types/api";

interface AuthContextValue {
  user: User | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  const [hasToken, setHasToken] = useState(() => Boolean(getAuthToken()));

  const { data: user, isLoading } = useQuery({
    queryKey: ["me"],
    queryFn: getMe,
    enabled: hasToken,
    retry: false,
  });

  useEffect(() => {
    setUnauthorizedHandler(() => {
      setHasToken(false);
      queryClient.clear();
    });
  }, [queryClient]);

  async function login(email: string, password: string) {
    const token = await loginRequest(email, password);
    setAuthToken(token.access_token);
    setHasToken(true);
    await queryClient.invalidateQueries({ queryKey: ["me"] });
  }

  function logout() {
    setAuthToken(null);
    setHasToken(false);
    queryClient.clear();
  }

  return (
    <AuthContext.Provider
      value={{ user: user ?? null, isLoading: hasToken && isLoading, login, logout }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
