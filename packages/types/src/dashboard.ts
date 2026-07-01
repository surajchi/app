/** Dashboard aggregation type — mirrors apps/dashboard services.build_dashboard. */

import type { Alert } from './alerts';
import type { Instrument } from './markets';
import type { PortfolioValuation } from './portfolios';
import type { Watchlist } from './watchlists';

export interface Mover {
  instrument: Instrument;
  price: number | null;
  change_percent: number | null;
}

export interface TopNewsItem {
  id: string;
  title: string;
  source: string;
  impact_score: number;
  is_breaking: boolean;
  published_at: string;
  sentiment: string | null;
}

export interface Dashboard {
  portfolio: PortfolioValuation | null;
  watchlist: Watchlist | null;
  alerts: Alert[];
  top_news: TopNewsItem[];
  movers: { gainers: Mover[]; losers: Mover[] };
}
