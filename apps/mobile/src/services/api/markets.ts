import type { ApiSuccess, Instrument } from '@finpulse/types';

import { client, unwrap } from './client';

export const marketsApi = {
  /** Search active instruments by symbol or name (public endpoint). */
  searchInstruments: (query: string): Promise<Instrument[]> =>
    unwrap(
      client.get<ApiSuccess<Instrument[]>>('/markets/instruments/', {
        params: query ? { search: query } : undefined,
      })
    ),
};
