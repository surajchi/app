/**
 * Axios instance with auth + transparent refresh.
 *
 * - Request interceptor attaches the current access token.
 * - Response interceptor catches a single 401, attempts a token refresh
 *   (de-duplicated across concurrent requests), retries the original request,
 *   and logs out if refresh fails.
 */
import axios, { type AxiosError, type InternalAxiosRequestConfig } from 'axios';
import type { ApiSuccess, RefreshResult } from '@finpulse/types';

import { env } from '@/config/env';
import { useAuthStore } from '@/store/authStore';

type RetriableConfig = InternalAxiosRequestConfig & { _retry?: boolean };

export const client = axios.create({
  baseURL: env.apiUrl,
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
});

client.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

let refreshPromise: Promise<string | null> | null = null;

async function refreshAccessToken(): Promise<string | null> {
  const refresh = useAuthStore.getState().refreshToken;
  if (!refresh) {
    return null;
  }
  try {
    // Bare axios call to avoid recursing through this interceptor.
    const res = await axios.post<ApiSuccess<RefreshResult>>(`${env.apiUrl}/auth/refresh/`, {
      refresh,
    });
    if (res.data.success) {
      const { access, refresh: rotated } = res.data.data;
      await useAuthStore.getState().updateTokens(access, rotated ?? refresh);
      return access;
    }
    return null;
  } catch {
    return null;
  }
}

client.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as RetriableConfig | undefined;
    if (error.response?.status === 401 && original && !original._retry) {
      original._retry = true;
      refreshPromise = refreshPromise ?? refreshAccessToken();
      const newToken = await refreshPromise;
      refreshPromise = null;

      if (newToken) {
        original.headers.Authorization = `Bearer ${newToken}`;
        return client(original);
      }
      await useAuthStore.getState().logout();
    }
    return Promise.reject(error);
  }
);

/** Unwrap the success envelope, throwing on a non-2xx / unsuccessful body. */
export async function unwrap<T>(promise: Promise<{ data: ApiSuccess<T> }>): Promise<T> {
  const res = await promise;
  return res.data.data;
}
