/** Daily/weekly brief — mirrors apps/dashboard/brief.build_brief. */

import type { Bias } from './analysis';
import type { EconomicEvent } from './calendar';

export interface BriefNews {
  id: string;
  title: string;
  source: string;
  impact_score: number;
  is_breaking: boolean;
  published_at: string;
  sentiment: string;
}

export interface BriefMover {
  symbol: string;
  name: string;
  change_percent: number | null;
}

export interface SentimentIndex {
  score: number; // 0-100 (0 = extreme fear, 100 = extreme greed)
  label: string;
  advancers: number;
  decliners: number;
}

export interface Brief {
  generated_at: string;
  market_mood: Bias;
  sentiment_index: SentimentIndex;
  summary: string;
  top_news: BriefNews[];
  week_ahead: EconomicEvent[];
  gainers: BriefMover[];
  losers: BriefMover[];
  disclaimer: string;
}
