/** Portfolio types — mirror apps/portfolios serializers. */

import type { Instrument } from './markets';

export type TransactionType = 'buy' | 'sell';

export interface Portfolio {
  id: string;
  name: string;
  base_currency: string;
  is_default: boolean;
  created_at: string;
}

export interface Transaction {
  id: string;
  instrument: Instrument;
  type: TransactionType;
  quantity: string;
  price: string;
  fee: string;
  executed_at: string;
  note: string;
  created_at: string;
}

export interface NewTransaction {
  instrument_id: string;
  type: TransactionType;
  quantity: string;
  price: string;
  fee?: string;
  executed_at?: string;
  note?: string;
}

export interface Position {
  instrument_id: string;
  symbol: string;
  name: string;
  quantity: number;
  avg_cost: number;
  price: number;
  priced: boolean;
  market_value: number;
  cost_basis: number;
  unrealized_pnl: number;
  unrealized_pct: number;
  realized_pnl: number;
  allocation_pct: number;
}

export interface PortfolioTotals {
  market_value: number;
  cost_basis: number;
  unrealized_pnl: number;
  unrealized_pct: number;
  realized_pnl: number;
  position_count: number;
}

export interface PortfolioValuation {
  portfolio_id: string;
  name: string;
  base_currency: string;
  positions: Position[];
  totals: PortfolioTotals;
}
