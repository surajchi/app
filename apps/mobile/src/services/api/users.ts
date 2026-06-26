import type { ApiSuccess, User, UserUpdate } from '@finpulse/types';

import { client, unwrap } from './client';

export const usersApi = {
  me: (): Promise<User> => unwrap(client.get<ApiSuccess<User>>('/users/me/')),

  updateMe: (body: UserUpdate): Promise<User> =>
    unwrap(client.patch<ApiSuccess<User>>('/users/me/', body)),
};
