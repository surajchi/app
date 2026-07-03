/** Market-data types — mirror apps/markets serializers. */

export type AssetClass =
  | 'forex'
  | 'stock'
  | 'crypto'
  | 'commodity'
  | 'index'
  | 'etf';

export interface Instrument {
  id: string;
  asset_class: string;
  symbol: string;
  name: string;
  exchange: string | null;
  currency: string;
  is_active: boolean;
  quote?: Quote | null;
}

export interface Quote {
  price: number;
  change?: number;
  change_percent: number;
  volume?: number;
  ts?: string;
  stale?: boolean;
}
