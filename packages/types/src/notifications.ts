/** Notification types — mirror apps/notifications serializers. */

export interface Notification {
  id: string;
  type: string;
  priority: string;
  title: string;
  body: string;
  data: Record<string, unknown>;
  read_at: string | null;
  created_at: string;
}

export interface MarkRead {
  ids?: string[];
  all?: boolean;
}
