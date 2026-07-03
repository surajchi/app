import type { ApiSuccess, Brief } from '@finpulse/types';

import { client, unwrap } from './client';

export const briefApi = {
  today: (): Promise<Brief> =>
    unwrap(client.get<ApiSuccess<Brief>>('/dashboard/brief/')),
};
