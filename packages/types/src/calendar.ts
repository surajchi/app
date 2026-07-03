/** Economic calendar types — mirror apps/econcalendar serializers. */

export type EventImportance = 'high' | 'medium' | 'low';

export interface EconomicEvent {
  id: string;
  title: string;
  country: string;
  currency: string;
  importance: EventImportance;
  category: string;
  event_time: string;
  actual: string;
  forecast: string;
  previous: string;
  unit: string;
}

export interface CalendarWeek {
  start: string;
  end: string;
  events: EconomicEvent[];
}
