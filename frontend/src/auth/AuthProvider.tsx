import {
  useEffect,
  useState,
  type ReactNode,
} from "react";

import { getCurrentUser, login as loginRequest } from "../api/authApi";
import type { LoginRequest, User } from "../types/auth";
import { AuthContext } from "./AuthContext";
import {
  getAccessToken,
  removeAccessToken,
  setAccessToken,
} from "./tokenStorage";

type AuthProviderProps = {
  children: ReactNode;
};

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Restore authentication when the browser refreshes.
  useEffect(() => {
    async function restoreSession() {
      const accessToken = getAccessToken();

      if (!accessToken) {
        setIsLoading(false);
        return;
      }

      try {
        const currentUser = await getCurrentUser();

        setUser(currentUser);
      } catch {
        // Remove an expired or invalid token.
        removeAccessToken();
        setUser(null);
      } finally {
        setIsLoading(false);
      }
    }

    restoreSession();
  }, []);

  async function login(credentials: LoginRequest): Promise<void> {
    const tokenResponse = await loginRequest(credentials);

    setAccessToken(tokenResponse.access_token);

    try {
      const currentUser = await getCurrentUser();

      setUser(currentUser);
    } catch (error) {
      // Do not keep a token if user loading fails.
      removeAccessToken();
      throw error;
    }
  }

  function logout(): void {
    removeAccessToken();
    setUser(null);
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: user !== null,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}