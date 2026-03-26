import React, { createContext, useState, ReactNode, useEffect, useCallback, useMemo } from 'react';
import { ensureCsrfCookie, getProfile, logoutSession } from '../services/api';
import { AuthUser } from '../types';

interface AuthContextType {
  user: AuthUser | null;
  isLoading: boolean;
  login: (user: AuthUser) => void;
  logout: () => Promise<void>;
}

export const AuthContext = createContext<AuthContextType>({
  user: null,
  isLoading: true,
  login: () => {},
  logout: async () => {},
});

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const login = useCallback((userData: AuthUser) => {
    setUser(userData);
  }, []);

  const logout = useCallback(async () => {
    try {
      await ensureCsrfCookie();
      await logoutSession();
    } catch {
      // Intentionally ignored: local session state should still be cleared.
    } finally {
      setUser(null);
    }
  }, []);

  useEffect(() => {
    const bootstrapSession = async () => {
      try {
        await ensureCsrfCookie();
        const response = await getProfile();
        setUser(response.data.user);
      } catch {
        setUser(null);
      } finally {
        setIsLoading(false);
      }
    };

    bootstrapSession();
  }, []);

  const value = useMemo(
    () => ({
      user,
      isLoading,
      login,
      logout,
    }),
    [isLoading, login, logout, user]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
