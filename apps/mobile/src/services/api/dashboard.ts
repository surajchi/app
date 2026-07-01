import type { ApiSuccess, Dashboard } from '@finpulse/types';

import { client, unwrap } from './client';

export const dashboardApi = {
  get: (): Promise<Dashboard> =>
    unwrap(client.get<ApiSuccess<Dashboard>>('/dashboard/')),
};
