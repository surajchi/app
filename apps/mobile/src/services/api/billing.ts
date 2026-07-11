import type { ApiSuccess, Plan, Subscription, SubscriptionState } from '@finpulse/types';

import { client, unwrap } from './client';

export const billingApi = {
  plans: (): Promise<Plan[]> => unwrap(client.get<ApiSuccess<Plan[]>>('/billing/plans/')),

  subscription: (): Promise<SubscriptionState> =>
    unwrap(client.get<ApiSuccess<SubscriptionState>>('/billing/subscription/')),

  subscribe: (plan: string, startTrial = false): Promise<Subscription> =>
    unwrap(
      client.post<ApiSuccess<Subscription>>('/billing/subscribe/', {
        plan,
        start_trial: startTrial,
      })
    ),

  cancel: (atPeriodEnd = true): Promise<Subscription> =>
    unwrap(
      client.post<ApiSuccess<Subscription>>('/billing/cancel/', { at_period_end: atPeriodEnd })
    ),
};
