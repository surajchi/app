/** Alert types — mirror apps/alerts serializers. */

export type AlertTriggerType =
  | 'price_above'
  | 'price_below'
  | 'pct_change'
  | 'news_keyword'
  | 'sentiment';

export type AlertFrequency = 'once' | 'recurring';

export interface AlertRule {
  id: string;
  name: string;
  instrument: string | null;
  trigger_type: AlertTriggerType;
  condition: Record<string, unknown>;
  frequency: AlertFrequency;
  cooldown_seconds: number;
  channels: string[];
  priority: string;
  is_active: boolean;
  last_triggered_at: string | null;
  expires_at: string | null;
  created_at: string;
}

export interface NewAlertRule {
  name: string;
  instrument?: string | null;
  trigger_type: AlertTriggerType;
  condition: Record<string, unknown>;
  frequency?: AlertFrequency;
  cooldown_seconds?: number;
  channels?: string[];
  priority?: string;
}

export interface Alert {
  id: string;
  rule: string;
  rule_name: string;
  trigger_type: AlertTriggerType;
  snapshot: Record<string, unknown>;
  status: string;
  triggered_at: string;
}
