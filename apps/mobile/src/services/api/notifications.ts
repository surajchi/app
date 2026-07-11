import type { ApiSuccess, Notification } from '@finpulse/types';

import { client, unwrap } from './client';

export const notificationsApi = {
  list: (unreadOnly = false): Promise<Notification[]> =>
    unwrap(
      client.get<ApiSuccess<Notification[]>>('/notifications/', {
        params: unreadOnly ? { unread: 'true' } : undefined,
      })
    ),

  markRead: (ids: string[]): Promise<{ marked: number }> =>
    unwrap(client.post<ApiSuccess<{ marked: number }>>('/notifications/read/', { ids })),

  markAll: (): Promise<{ marked: number }> =>
    unwrap(client.post<ApiSuccess<{ marked: number }>>('/notifications/read/', { all: true })),
};
