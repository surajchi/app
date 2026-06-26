/**
 * Runtime configuration. EXPO_PUBLIC_* vars are inlined into the bundle at build
 * time by Expo — never put secrets here.
 */
export const env = {
  apiUrl: process.env.EXPO_PUBLIC_API_URL ?? 'http://localhost:8000/api/v1',
} as const;
