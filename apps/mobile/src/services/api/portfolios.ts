import type {
  ApiSuccess,
  NewTransaction,
  Portfolio,
  PortfolioValuation,
  Transaction,
} from '@finpulse/types';

import { client, unwrap } from './client';

export const portfoliosApi = {
  list: (): Promise<Portfolio[]> =>
    unwrap(client.get<ApiSuccess<Portfolio[]>>('/portfolios/')),

  create: (name: string, baseCurrency = 'USD', isDefault = false): Promise<Portfolio> =>
    unwrap(
      client.post<ApiSuccess<Portfolio>>('/portfolios/', {
        name,
        base_currency: baseCurrency,
        is_default: isDefault,
      })
    ),

  summary: (id: string): Promise<PortfolioValuation> =>
    unwrap(client.get<ApiSuccess<PortfolioValuation>>(`/portfolios/${id}/summary/`)),

  transactions: (id: string): Promise<Transaction[]> =>
    unwrap(client.get<ApiSuccess<Transaction[]>>(`/portfolios/${id}/transactions/`)),

  addTransaction: (id: string, body: NewTransaction): Promise<Transaction> =>
    unwrap(
      client.post<ApiSuccess<Transaction>>(`/portfolios/${id}/transactions/`, body)
    ),
};
