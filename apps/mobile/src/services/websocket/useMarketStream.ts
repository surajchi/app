/** Subscribe to live quotes for a symbol; returns the latest streamed quote. */
import { useEffect, useState } from 'react';
import type { WsQuoteData, WsServerFrame } from '@finpulse/types';

import { socketManager } from '@/services/websocket/socketManager';

export function useMarketStream(symbol: string | null): WsQuoteData | null {
  const [quote, setQuote] = useState<WsQuoteData | null>(null);

  useEffect(() => {
    if (!symbol) {
      return;
    }
    const channel = `quotes.${symbol.toUpperCase()}`;
    socketManager.connect();
    socketManager.subscribe([channel]);

    const off = socketManager.on((frame: WsServerFrame) => {
      if (frame.type === 'quote' && frame.channel === channel) {
        setQuote(frame.data);
      }
    });

    return () => {
      off();
      socketManager.unsubscribe([channel]);
    };
  }, [symbol]);

  return quote;
}
