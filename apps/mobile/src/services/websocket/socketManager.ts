/**
 * Single multiplexed WebSocket connection to the realtime gateway.
 *
 * - Attaches the JWT access token (if present) as ?token=
 * - Tracks subscriptions and re-subscribes after reconnect
 * - Exponential-backoff reconnect + heartbeat ping
 * - Fans incoming frames out to registered listeners
 */
import type { WsClientMessage, WsServerFrame } from '@finpulse/types';

import { env } from '@/config/env';
import { useAuthStore } from '@/store/authStore';

type Listener = (frame: WsServerFrame) => void;

function wsUrl(): string {
  const base = env.apiUrl.replace(/^http/, 'ws').replace(/\/api\/v1\/?$/, '');
  const url = `${base}/ws/`;
  const token = useAuthStore.getState().accessToken;
  return token ? `${url}?token=${encodeURIComponent(token)}` : url;
}

class SocketManager {
  private ws: WebSocket | null = null;
  private readonly listeners = new Set<Listener>();
  private readonly channels = new Set<string>();
  private reconnectAttempts = 0;
  private heartbeat: ReturnType<typeof setInterval> | null = null;
  private shouldRun = false;

  connect(): void {
    this.shouldRun = true;
    if (
      this.ws &&
      (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)
    ) {
      return;
    }

    const socket = new WebSocket(wsUrl());
    this.ws = socket;

    socket.onopen = () => {
      this.reconnectAttempts = 0;
      if (this.channels.size > 0) {
        this.send({ action: 'subscribe', channels: [...this.channels] });
      }
      this.startHeartbeat();
    };
    socket.onmessage = (event: MessageEvent) => {
      try {
        const frame = JSON.parse(event.data as string) as WsServerFrame;
        this.listeners.forEach((listener) => listener(frame));
      } catch {
        // ignore malformed frames
      }
    };
    socket.onclose = () => {
      this.stopHeartbeat();
      if (this.shouldRun) {
        this.scheduleReconnect();
      }
    };
    socket.onerror = () => socket.close();
  }

  disconnect(): void {
    this.shouldRun = false;
    this.stopHeartbeat();
    this.ws?.close();
    this.ws = null;
  }

  subscribe(channels: string[]): void {
    channels.forEach((channel) => this.channels.add(channel));
    if (this.isOpen()) {
      this.send({ action: 'subscribe', channels });
    } else {
      this.connect();
    }
  }

  unsubscribe(channels: string[]): void {
    channels.forEach((channel) => this.channels.delete(channel));
    if (this.isOpen()) {
      this.send({ action: 'unsubscribe', channels });
    }
  }

  on(listener: Listener): () => void {
    this.listeners.add(listener);
    return () => {
      this.listeners.delete(listener);
    };
  }

  private isOpen(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  private send(message: WsClientMessage): void {
    if (this.isOpen()) {
      this.ws?.send(JSON.stringify(message));
    }
  }

  private startHeartbeat(): void {
    this.stopHeartbeat();
    this.heartbeat = setInterval(() => this.send({ action: 'ping' }), 25_000);
  }

  private stopHeartbeat(): void {
    if (this.heartbeat) {
      clearInterval(this.heartbeat);
      this.heartbeat = null;
    }
  }

  private scheduleReconnect(): void {
    this.reconnectAttempts += 1;
    const delay = Math.min(30_000, 1_000 * 2 ** this.reconnectAttempts);
    setTimeout(() => {
      if (this.shouldRun) {
        this.connect();
      }
    }, delay);
  }
}

export const socketManager = new SocketManager();
