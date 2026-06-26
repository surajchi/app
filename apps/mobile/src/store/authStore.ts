/** Auth client-state (Zustand). Tokens persist to secure storage. */
import { create } from 'zustand';
import type { AuthResult, User } from '@finpulse/types';

import { secureStorage } from '@/services/storage/secureStore';

const ACCESS_KEY = 'fp.access';
const REFRESH_KEY = 'fp.refresh';
const USER_KEY = 'fp.user';

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  user: User | null;
  hydrated: boolean;
  isAuthenticated: () => boolean;
  setSession: (result: AuthResult) => Promise<void>;
  updateTokens: (access: string, refresh: string) => Promise<void>;
  logout: () => Promise<void>;
  hydrate: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  accessToken: null,
  refreshToken: null,
  user: null,
  hydrated: false,

  isAuthenticated: () => get().user !== null && get().accessToken !== null,

  setSession: async (result) => {
    await Promise.all([
      secureStorage.setItem(ACCESS_KEY, result.access),
      secureStorage.setItem(REFRESH_KEY, result.refresh),
      secureStorage.setItem(USER_KEY, JSON.stringify(result.user)),
    ]);
    set({ accessToken: result.access, refreshToken: result.refresh, user: result.user });
  },

  updateTokens: async (access, refresh) => {
    await Promise.all([
      secureStorage.setItem(ACCESS_KEY, access),
      secureStorage.setItem(REFRESH_KEY, refresh),
    ]);
    set({ accessToken: access, refreshToken: refresh });
  },

  logout: async () => {
    await Promise.all([
      secureStorage.deleteItem(ACCESS_KEY),
      secureStorage.deleteItem(REFRESH_KEY),
      secureStorage.deleteItem(USER_KEY),
    ]);
    set({ accessToken: null, refreshToken: null, user: null });
  },

  hydrate: async () => {
    const [access, refresh, userRaw] = await Promise.all([
      secureStorage.getItem(ACCESS_KEY),
      secureStorage.getItem(REFRESH_KEY),
      secureStorage.getItem(USER_KEY),
    ]);
    set({
      accessToken: access,
      refreshToken: refresh,
      user: userRaw ? (JSON.parse(userRaw) as User) : null,
      hydrated: true,
    });
  },
}));
