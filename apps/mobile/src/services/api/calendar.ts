import type { ApiSuccess, CalendarWeek } from '@finpulse/types';

import { client, unwrap } from './client';

export const calendarApi = {
  week: (highOnly = false): Promise<CalendarWeek> =>
    unwrap(
      client.get<ApiSuccess<CalendarWeek>>('/calendar/week/', {
        params: highOnly ? { high: 1 } : undefined,
      })
    ),
};
