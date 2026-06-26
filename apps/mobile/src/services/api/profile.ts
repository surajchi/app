import type { ApiSuccess, Profile, ProfileUpdate } from '@finpulse/types';

import { client, unwrap } from './client';

export const profileApi = {
  get: (): Promise<Profile> => unwrap(client.get<ApiSuccess<Profile>>('/profile/')),

  update: (body: ProfileUpdate): Promise<Profile> =>
    unwrap(client.patch<ApiSuccess<Profile>>('/profile/', body)),
};
