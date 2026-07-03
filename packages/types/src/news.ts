/** News types — mirror apps/news serializers. */

export type SentimentLabel = 'positive' | 'negative' | 'neutral';

export interface NewsSentiment {
  label: SentimentLabel;
  score: number;
  confidence: number;
}

export interface NewsCategory {
  id: string;
  slug: string;
  name: string;
}

export interface NewsArticle {
  id: string;
  source: string;
  title: string;
  summary: string;
  source_url: string;
  image_url: string;
  category: string | null;
  impact_score: number;
  is_breaking: boolean;
  published_at: string;
  sentiment: NewsSentiment | null;
}
