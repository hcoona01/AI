import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { AxiosError } from 'axios';
import { User } from '../../types';
import {
  setAccessToken,
  requestOtpApi,
  verifyOtpApi,
  refreshSessionApi,
  logoutApi,
  getStoredRefreshToken,
  setStoredRefreshToken,
  getStoredUser,
  setStoredUser,
} from '../../lib/apiClient';
import { queryClient } from '../../app/queryClient';

export interface AuthContextType {
  user: User | null;
  accessToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  requestOtp: (email: string) => Promise<{ message: string }>;
  verifyOtp: (email: string, otp: string) => Promise<User>;
  logout: () => Promise<void>;
  clearError: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export interface AuthProviderProps {
  children: React.ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(() => getStoredUser());
  const [accessTokenState, setAccessTokenState] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(() => Boolean(getStoredRefreshToken()));
  const [error, setError] = useState<string | null>(null);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  // Silent refresh on initial page load via stored refresh token or httpOnly cookie
  useEffect(() => {
    let isMounted = true;

    const performSilentRefresh = async (): Promise<void> => {
      const storedToken = getStoredRefreshToken();
      if (!storedToken) {
        if (isMounted) {
          setIsLoading(false);
        }
        return;
      }

      try {
        const data = await refreshSessionApi(storedToken);
        if (isMounted) {
          setAccessToken(data.access_token);
          setAccessTokenState(data.access_token);
          setUser(data.user);
          setStoredUser(data.user);
          if (data.refresh_token) {
            setStoredRefreshToken(data.refresh_token);
          }
        }
      } catch {
        // Silent failure if token expired or revoked
        if (isMounted) {
          setAccessToken(null);
          setAccessTokenState(null);
          setUser(null);
          setStoredUser(null);
          setStoredRefreshToken(null);
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    };

    void performSilentRefresh();

    return () => {
      isMounted = false;
    };
  }, []);

  const requestOtp = useCallback(async (email: string): Promise<{ message: string }> => {
    setError(null);
    try {
      const response = await requestOtpApi(email);
      return response;
    } catch (err: unknown) {
      let errorMessage = 'Failed to send one-time passcode. Please try again.';
      if (err instanceof AxiosError && err.response?.data) {
        const data = err.response.data as { message?: string };
        if (data.message) {
          errorMessage = data.message;
        }
      }
      setError(errorMessage);
      throw new Error(errorMessage);
    }
  }, []);

  const verifyOtp = useCallback(
    async (email: string, otp: string): Promise<User> => {
      setError(null);
      try {
        const data = await verifyOtpApi(email, otp);
        setAccessToken(data.access_token);
        setAccessTokenState(data.access_token);
        setUser(data.user);
        return data.user;
      } catch (err: unknown) {
        let errorMessage = 'Invalid passcode. Please verify the code and try again.';
        if (err instanceof AxiosError && err.response?.data) {
          const data = err.response.data as { message?: string };
          if (data.message) {
            errorMessage = data.message;
          }
        }
        setError(errorMessage);
        throw new Error(errorMessage);
      }
    },
    []
  );

  const logout = useCallback(async (): Promise<void> => {
    try {
      await logoutApi();
    } catch {
      // Ignore network errors on logout to guarantee clean local state teardown
    } finally {
      setAccessToken(null);
      setAccessTokenState(null);
      setUser(null);
      setStoredRefreshToken(null);
      setStoredUser(null);
      queryClient.clear();
    }
  }, []);

  const value: AuthContextType = {
    user,
    accessToken: accessTokenState,
    isAuthenticated: Boolean(user && accessTokenState),
    isLoading,
    error,
    requestOtp,
    verifyOtp,
    logout,
    clearError,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
