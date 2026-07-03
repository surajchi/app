import type { ApiSuccess, NewsArticle, NewsCategory } from '@finpulse/types';

import { client, unwrap } from './client';

interface FeedParams {
  category?: string;
  symbol?: string;
  q?: string;
}

export const newsApi = {
  feed: (params: FeedParams = {}): Promise<NewsArticle[]> =>
    unwrap(client.get<ApiSuccess<NewsArticle[]>>('/news/', { params })),

  trending: (): Promise<NewsArticle[]> =>
    unwrap(client.get<ApiSuccess<NewsArticle[]>>('/news/trending/')),

  categories: (): Promise<NewsCategory[]> =>
    unwrap(client.get<ApiSuccess<NewsCategory[]>>('/news/categories/')),
};
