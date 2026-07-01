import type { Alert, AlertRule, ApiSuccess, NewAlertRule } from '@finpulse/types';

import { client, unwrap } from './client';

type AlertRulePatch = Partial<NewAlertRule> & { is_active?: boolean };

export const alertsApi = {
  listRules: (): Promise<AlertRule[]> =>
    unwrap(client.get<ApiSuccess<AlertRule[]>>('/alerts/rules/')),

  createRule: (body: NewAlertRule): Promise<AlertRule> =>
    unwrap(client.post<ApiSuccess<AlertRule>>('/alerts/rules/', body)),

  updateRule: (id: string, body: AlertRulePatch): Promise<AlertRule> =>
    unwrap(client.patch<ApiSuccess<AlertRule>>(`/alerts/rules/${id}/`, body)),

  deleteRule: (id: string): Promise<unknown> =>
    client.delete(`/alerts/rules/${id}/`),

  history: (): Promise<Alert[]> =>
    unwrap(client.get<ApiSuccess<Alert[]>>('/alerts/history/')),
};
