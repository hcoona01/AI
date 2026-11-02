import axios, { AxiosError, AxiosResponse, InternalAxiosRequestConfig } from 'axios';
import { User } from '../types';

// Default to VITE_API_URL or fallback to local backend v1 API
export const API_BASE_URL: string =
  (import.meta.env.VITE_API_URL as string | undefined) || 'http://localhost:8000/api/v1';

const REFRESH_TOKEN_KEY = 'workload_refresh_token';
const USER_KEY = 'workload_user';

export const getStoredRefreshToken = (): string | null => {
  try {
    return localStorage.getItem(REFRESH_TOKEN_KEY);
  } catch {
    return null;
  }
};

export const setStoredRefreshToken = (token: string | null): void => {
  try {
    if (token) {
      localStorage.setItem(REFRESH_TOKEN_KEY, token);
    } else {
      localStorage.removeItem(REFRESH_TOKEN_KEY);
    }
  } catch {}
};

export const getStoredUser = (): User | null => {
  try {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? (JSON.parse(raw) as User) : null;
  } catch {
    return null;
  }
};

export const setStoredUser = (user: User | null): void => {
  try {
    if (user) {
      localStorage.setItem(USER_KEY, JSON.stringify(user));
    } else {
      localStorage.removeItem(USER_KEY);
    }
  } catch {}
};

// In-memory token storage (NEVER stored in localStorage or sessionStorage)
let inMemoryAccessToken: string | null = null;

export const setAccessToken = (token: string | null): void => {
  inMemoryAccessToken = token;
};

export const getAccessToken = (): string | null => inMemoryAccessToken;

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Enables httpOnly refresh token cookies
  timeout: 15000,
});

// Request interceptor: attach in-memory bearer token
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    if (inMemoryAccessToken && config.headers) {
      config.headers.Authorization = `Bearer ${inMemoryAccessToken}`;
    }
    return config;
  },
  (error: AxiosError) => Promise.reject(error)
);

// Response interceptor: clear in-memory token on 401
apiClient.interceptors.response.use(
  (response: AxiosResponse) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      inMemoryAccessToken = null;
    }
    return Promise.reject(error);
  }
);

export interface HealthResponse {
  status: string;
  service: string;
  version: string;
  environment: string;
  store_backend: string;
  forecast_mode: string;
  timestamp: string;
}

export interface OTPResponse {
  message: string;
  status: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
  refresh_token?: string;
}

export interface MessageResponse {
  message: string;
}

// API methods
export const fetchHealth = async (): Promise<HealthResponse> => {
  const response = await apiClient.get<HealthResponse>('/health');
  return response.data;
};

export const requestOtpApi = async (email: string): Promise<OTPResponse> => {
  const response = await apiClient.post<OTPResponse>('/auth/request-otp', { email });
  return response.data;
};

export const verifyOtpApi = async (email: string, otp: string): Promise<TokenResponse> => {
  const response = await apiClient.post<TokenResponse>('/auth/verify-otp', { email, otp });
  if (response.data.refresh_token) {
    setStoredRefreshToken(response.data.refresh_token);
  }
  if (response.data.user) {
    setStoredUser(response.data.user);
  }
  return response.data;
};

export const refreshSessionApi = async (refreshToken?: string | null): Promise<TokenResponse> => {
  const token = refreshToken || getStoredRefreshToken();
  const body = token ? { refresh_token: token } : {};
  const response = await apiClient.post<TokenResponse>('/auth/refresh', body);
  if (response.data.refresh_token) {
    setStoredRefreshToken(response.data.refresh_token);
  }
  if (response.data.user) {
    setStoredUser(response.data.user);
  }
  return response.data;
};

export const logoutApi = async (): Promise<MessageResponse> => {
  setStoredRefreshToken(null);
  setStoredUser(null);
  const response = await apiClient.post<MessageResponse>('/auth/logout');
  return response.data;
};

export const fetchCurrentUserApi = async (): Promise<User> => {
  const response = await apiClient.get<User>('/me');
  return response.data;
};
