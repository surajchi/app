import type { ApiSuccess, Instrument, InstrumentAnalysis } from '@finpulse/types';

import { client, unwrap } from './client';

interface InstrumentQuery {
  search?: string;
  assetClass?: string;
}

export const marketsApi = {
  /** Search active instruments by symbol or name (public endpoint). */
  searchInstruments: (query: string): Promise<Instrument[]> =>
    unwrap(
      client.get<ApiSuccess<Instrument[]>>('/markets/instruments/', {
        params: query ? { search: query } : undefined,
      })
    ),

  /** List/browse instruments filtered by search text and/or asset class. */
  listInstruments: ({ search, assetClass }: InstrumentQuery = {}): Promise<Instrument[]> =>
    unwrap(
      client.get<ApiSuccess<Instrument[]>>('/markets/instruments/', {
        params: {
          ...(search ? { search } : {}),
          ...(assetClass && assetClass !== 'all' ? { asset_class: assetClass } : {}),
        },
      })
    ),

  /** Fused AI analysis for one instrument (quote + forecast + technical + news). */
  analysis: (symbol: string): Promise<InstrumentAnalysis> =>
    unwrap(
      client.get<ApiSuccess<InstrumentAnalysis>>(
        `/markets/instruments/${encodeURIComponent(symbol)}/analysis/`
      )
    ),
};
