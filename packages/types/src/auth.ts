/** Authentication request/response contracts — mirror apps/authentication serializers. */
import type { User } from './user';

export interface DeviceInfo {
  platform: 'ios' | 'android' | 'web';
  push_token?: string;
  device_name?: string;
  app_version?: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  full_name: string;
}

export interface LoginRequest {
  email: string;
  password: string;
  device?: DeviceInfo;
}

export interface TokenPair {
  access: string;
  refresh: string;
  expires_in: number;
}

export interface AuthResult extends TokenPair {
  user: User;
}

export interface RefreshRequest {
  refresh: string;
}

export interface RefreshResult {
  access: string;
  refresh: string;
  expires_in: number;
}

export interface LogoutRequest {
  refresh: string;
}
