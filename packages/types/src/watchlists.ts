/** Watchlist types — mirror apps/watchlists serializers. */

import type { Instrument, Quote } from './markets';

export interface WatchlistItem {
  id: string;
  instrument: Instrument;
  position: number;
  note: string;
  quote: Quote | null;
  created_at: string;
}

export interface Watchlist {
  id: string;
  name: string;
  is_default: boolean;
  item_count: number;
  created_at: string;
  items?: WatchlistItem[];
}

export interface AddWatchlistItem {
  instrument_id: string;
  note?: string;
}
