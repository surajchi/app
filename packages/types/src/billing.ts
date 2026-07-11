/** Billing types — mirror apps/billing serializers. */

export interface Plan {
  id: string;
  code: string;
  name: string;
  description: string;
  price_cents: number;
  price: number;
  currency: string;
  interval: string;
  trial_days: number;
  tier: number;
  features: Record<string, unknown>;
  is_active: boolean;
}

export interface Subscription {
  id: string;
  plan: Plan;
  status: string;
  current_period_start: string | null;
  current_period_end: string | null;
  cancel_at_period_end: boolean;
  trial_end: string | null;
  provider: string;
  created_at: string;
}

export interface Entitlements {
  plan: string;
  status: string;
  features: Record<string, unknown>;
  current_period_end: string | null;
  cancel_at_period_end: boolean;
}

export interface SubscriptionState {
  subscription: Subscription | null;
  entitlements: Entitlements;
}
