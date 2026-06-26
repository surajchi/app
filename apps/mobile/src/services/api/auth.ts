import type {
  ApiSuccess,
  AuthResult,
  LoginRequest,
  RefreshResult,
  RegisterRequest,
} from '@finpulse/types';

import { client, unwrap } from './client';

export const authApi = {
  register: (body: RegisterRequest): Promise<AuthResult> =>
    unwrap(client.post<ApiSuccess<AuthResult>>('/auth/register/', body)),

  login: (body: LoginRequest): Promise<AuthResult> =>
    unwrap(client.post<ApiSuccess<AuthResult>>('/auth/login/', body)),

  refresh: (refresh: string): Promise<RefreshResult> =>
    unwrap(client.post<ApiSuccess<RefreshResult>>('/auth/refresh/', { refresh })),

  logout: (refresh: string): Promise<void> => client.post('/auth/logout/', { refresh }).then(() => undefined),
};
