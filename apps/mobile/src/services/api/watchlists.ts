import type {
  AddWatchlistItem,
  ApiSuccess,
  Watchlist,
  WatchlistItem,
} from '@finpulse/types';

import { client, unwrap } from './client';

export const watchlistsApi = {
  list: (): Promise<Watchlist[]> =>
    unwrap(client.get<ApiSuccess<Watchlist[]>>('/watchlists/')),

  get: (id: string): Promise<Watchlist> =>
    unwrap(client.get<ApiSuccess<Watchlist>>(`/watchlists/${id}/`)),

  create: (name: string, isDefault = false): Promise<Watchlist> =>
    unwrap(
      client.post<ApiSuccess<Watchlist>>('/watchlists/', {
        name,
        is_default: isDefault,
      })
    ),

  remove: (id: string): Promise<unknown> => client.delete(`/watchlists/${id}/`),

  addItem: (id: string, body: AddWatchlistItem): Promise<WatchlistItem> =>
    unwrap(client.post<ApiSuccess<WatchlistItem>>(`/watchlists/${id}/items/`, body)),

  removeItem: (id: string, itemId: string): Promise<unknown> =>
    client.delete(`/watchlists/${id}/items/${itemId}/`),
};
