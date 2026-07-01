/** WebSocket message contracts — mirror realtime/consumers.py. */

export type WsClientMessage =
  | { action: 'subscribe'; channels: string[] }
  | { action: 'unsubscribe'; channels: string[] }
  | { action: 'ping' };

export interface WsQuoteData {
  symbol: string;
  price: number;
  change: number;
  change_percent: number;
  volume: number;
  ts: string;
}

export type WsServerFrame =
  | { type: 'connected' }
  | { type: 'pong' }
  | { type: 'subscribed'; channels: string[] }
  | { type: 'unsubscribed'; channels: string[] }
  | { type: 'error'; message: string }
  | { channel: string; type: 'quote'; data: WsQuoteData }
  | { channel: string; type: 'alert'; data: Record<string, unknown> };
