/** Instrument analysis — mirrors apps/markets/analysis.build_instrument_analysis. */

import type { Instrument, Quote } from './markets';

export type Bias = 'bullish' | 'bearish' | 'neutral';

export interface ForecastPoint {
  step: number;
  mean: number;
  low: number;
  high: number;
}

export interface Forecast {
  points: ForecastPoint[];
  confidence: number;
  model: string;
  symbol?: string;
  horizon?: string;
}

export interface Technical {
  indicators: Record<string, number | null>;
  signal: string; // buy | sell | hold
  strength: number;
  model: string;
  symbol?: string;
}

export interface AnalysisNewsItem {
  id: string;
  title: string;
  source: string;
  published_at: string;
  impact_score: number;
  sentiment: string;
  effect: Bias;
}

export interface NewsEffect {
  bias: Bias;
  bullish: number;
  bearish: number;
  neutral: number;
  count: number;
  note: string;
}

export interface AiSummary {
  bias: Bias;
  confidence: number;
  target: number | null;
  target_change_pct: number | null;
  signals_considered: number;
  rationale: string;
}

export interface HistoryPoint {
  ts: string;
  close: number;
}

export interface InstrumentAnalysis {
  instrument: Instrument;
  quote: Quote | null;
  history: { interval: string; points: HistoryPoint[] };
  forecast: Forecast | null;
  technical: Technical | null;
  news: AnalysisNewsItem[];
  news_effect: NewsEffect;
  ai_summary: AiSummary;
  disclaimer: string;
}
