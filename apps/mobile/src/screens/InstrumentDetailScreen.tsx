import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import {
  ActivityIndicator,
  Modal,
  Pressable,
  ScrollView,
  Text,
  TextInput,
  useWindowDimensions,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import type { Bias } from '@finpulse/types';

import { PriceChart } from '@/components/PriceChart';
import { formatCurrency, formatPercent } from '@/lib/format';
import { alertsApi } from '@/services/api/alerts';
import { marketsApi } from '@/services/api/markets';
import { watchlistsApi } from '@/services/api/watchlists';
import { useMarketStream } from '@/services/websocket/useMarketStream';
import type { RootScreenProps } from '@/navigation/types';

const TIMEFRAMES: { key: string; days: number }[] = [
  { key: '1M', days: 30 },
  { key: '3M', days: 90 },
  { key: 'ALL', days: 9999 },
];

function biasClasses(bias: Bias): string {
  if (bias === 'bullish') return 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30';
  if (bias === 'bearish') return 'bg-rose-500/15 text-rose-400 border-rose-500/30';
  return 'bg-slate-700/40 text-slate-300 border-slate-600/40';
}

function biasTextColor(bias: Bias): string {
  if (bias === 'bullish') return 'text-emerald-400';
  if (bias === 'bearish') return 'text-rose-400';
  return 'text-slate-300';
}

function effectArrow(effect: Bias): { glyph: string; color: string } {
  if (effect === 'bullish') return { glyph: '▲', color: 'text-emerald-400' };
  if (effect === 'bearish') return { glyph: '▼', color: 'text-rose-400' };
  return { glyph: '–', color: 'text-slate-500' };
}

function impactDot(score: number): string {
  if (score >= 70) return 'bg-rose-500';
  if (score >= 40) return 'bg-amber-500';
  return 'bg-yellow-400';
}

function timeAgo(iso: string): string {
  const diffMs = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diffMs / 60000);
  if (mins < 60) return `${Math.max(mins, 0)}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

function Stat({ label, value, color }: { label: string; value: string; color?: string }) {
  return (
    <View className="flex-1">
      <Text className="text-xs text-slate-500">{label}</Text>
      <Text className={`text-base font-semibold ${color ?? 'text-slate-100'}`}>{value}</Text>
    </View>
  );
}

export function InstrumentDetailScreen({ route, navigation }: RootScreenProps<'InstrumentDetail'>) {
  const { symbol } = route.params;
  const { width } = useWindowDimensions();
  const queryClient = useQueryClient();
  const [tf, setTf] = useState('3M');
  const [message, setMessage] = useState<string | null>(null);
  const [alertOpen, setAlertOpen] = useState(false);
  const [alertSide, setAlertSide] = useState<'price_above' | 'price_below'>('price_above');
  const [alertValue, setAlertValue] = useState('');

  const { data, isLoading, isError, refetch, isRefetching } = useQuery({
    queryKey: ['analysis', symbol],
    queryFn: () => marketsApi.analysis(symbol),
  });

  const addWatchlistMutation = useMutation({
    mutationFn: async () => {
      if (!data?.instrument.id) return;
      const lists = await watchlistsApi.list();
      const watchlist =
        lists.find((list) => list.is_default) ??
        lists[0] ??
        (await watchlistsApi.create('My Watchlist', true));
      return watchlistsApi.addItem(watchlist.id, { instrument_id: data.instrument.id });
    },
    onSuccess: () => {
      setMessage('Added to watchlist');
      void queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      void queryClient.invalidateQueries({ queryKey: ['watchlists'] });
    },
    onError: () => setMessage('Already in watchlist'),
  });

  const createAlertMutation = useMutation({
    mutationFn: async () => {
      if (!data?.instrument.id) return;
      const value = Number(alertValue);
      if (!Number.isFinite(value) || value <= 0) {
        throw new Error('Enter a valid price');
      }
      return alertsApi.createRule({
        name: `${data.instrument.symbol} ${alertSide === 'price_above' ? 'above' : 'below'} ${value}`,
        instrument: data.instrument.id,
        trigger_type: alertSide,
        condition: { value },
        frequency: 'once',
        channels: ['in_app'],
        priority: 'high',
      });
    },
    onSuccess: () => {
      setAlertOpen(false);
      setMessage('Alert created');
      void queryClient.invalidateQueries({ queryKey: ['alerts'] });
      void queryClient.invalidateQueries({ queryKey: ['dashboard'] });
    },
    onError: (error) => setMessage(error instanceof Error ? error.message : 'Could not create alert'),
  });

  const currency = data?.instrument.currency ?? 'USD';
  const closes = (data?.history.points ?? []).map((p) => p.close);
  const days = TIMEFRAMES.find((t) => t.key === tf)?.days ?? 90;
  const shownCloses = closes.slice(Math.max(0, closes.length - days));
  const forecastMeans = (data?.forecast?.points ?? []).map((p) => p.mean);

  const live = useMarketStream(data ? symbol : null);
  const price = live?.price ?? data?.quote?.price ?? closes[closes.length - 1] ?? null;
  const changePct = live?.change_percent ?? data?.quote?.change_percent ?? 0;
  const changeColor = changePct >= 0 ? 'text-emerald-400' : 'text-rose-400';

  const tech = data?.technical?.indicators;

  const openAlertModal = () => {
    setAlertValue(price !== null ? String(Number(price.toFixed(4))) : '');
    setAlertOpen(true);
    setMessage(null);
  };

  return (
    <SafeAreaView className="flex-1 bg-slate-950">
      {/* Header bar */}
      <View className="flex-row items-center justify-between px-4 py-3">
        <Pressable onPress={() => navigation.goBack()} accessibilityRole="button">
          <Text className="text-base text-slate-300">‹ Back</Text>
        </Pressable>
        <View className="flex-row items-center">
          <View className={`mr-2 h-2 w-2 rounded-full ${live ? 'bg-emerald-400' : 'bg-slate-600'}`} />
          <Text className="text-xs uppercase tracking-wide text-slate-500">
            {live ? 'Live' : 'Delayed'}
          </Text>
        </View>
      </View>

      {isLoading ? (
        <ActivityIndicator className="mt-16" color="#34d399" />
      ) : isError || !data ? (
        <View className="flex-1 items-center justify-center px-8">
          <Text className="text-center text-slate-400">
            Couldn&apos;t load analysis for {symbol}.
          </Text>
          <Pressable onPress={() => void refetch()} className="mt-4">
            <Text className="text-emerald-400">Retry</Text>
          </Pressable>
        </View>
      ) : (
        <ScrollView
          contentContainerStyle={{ padding: 16, paddingTop: 4 }}
          refreshControl={undefined}
        >
          {/* Title + price */}
          <Text className="text-2xl font-bold text-slate-50">{data.instrument.symbol}</Text>
          <Text className="mb-3 text-sm text-slate-400">
            {data.instrument.name} · {data.instrument.asset_class}
          </Text>
          <View className="flex-row items-end">
            <Text className="text-4xl font-bold text-slate-50">
              {price !== null ? formatCurrency(price, currency) : '—'}
            </Text>
            <Text className={`mb-1 ml-3 text-lg font-semibold ${changeColor}`}>
              {formatPercent(changePct)}
            </Text>
          </View>

          <View className="mt-4 flex-row">
            <Pressable
              accessibilityRole="button"
              disabled={addWatchlistMutation.isPending}
              onPress={() => addWatchlistMutation.mutate()}
              className="mr-2 flex-1 rounded-lg bg-slate-100 px-4 py-3 active:opacity-80"
            >
              <Text className="text-center text-sm font-bold text-slate-950">
                {addWatchlistMutation.isPending ? 'Adding...' : 'Add to watchlist'}
              </Text>
            </Pressable>
            <Pressable
              accessibilityRole="button"
              onPress={openAlertModal}
              className="flex-1 rounded-lg border border-emerald-400/40 px-4 py-3 active:bg-emerald-400/10"
            >
              <Text className="text-center text-sm font-bold text-emerald-300">Set alert</Text>
            </Pressable>
          </View>
          {message ? <Text className="mt-2 text-center text-xs text-slate-400">{message}</Text> : null}

          {/* Chart */}
          <View className="mt-4 rounded-2xl border border-slate-800 bg-slate-900 p-3">
            <PriceChart history={shownCloses} forecast={forecastMeans} width={width - 56} />
            <View className="mt-2 flex-row items-center justify-between">
              <View className="flex-row">
                {TIMEFRAMES.map((t) => (
                  <Pressable
                    key={t.key}
                    onPress={() => setTf(t.key)}
                    className={`mr-2 rounded-md px-3 py-1 ${
                      tf === t.key ? 'bg-slate-100' : 'border border-slate-700'
                    }`}
                  >
                    <Text
                      className={`text-xs font-medium ${
                        tf === t.key ? 'text-slate-900' : 'text-slate-400'
                      }`}
                    >
                      {t.key}
                    </Text>
                  </Pressable>
                ))}
              </View>
              {forecastMeans.length > 0 ? (
                <Text className="text-xs text-amber-400">— — forecast</Text>
              ) : null}
            </View>
          </View>

          {/* AI analysis */}
          <View className="mt-4 rounded-2xl border border-slate-800 bg-slate-900 p-4">
            <View className="mb-3 flex-row items-center justify-between">
              <Text className="text-sm font-semibold uppercase tracking-wide text-slate-400">
                AI Analysis
              </Text>
              <View className={`rounded-full border px-3 py-1 ${biasClasses(data.ai_summary.bias)}`}>
                <Text className={`text-xs font-bold uppercase ${biasTextColor(data.ai_summary.bias)}`}>
                  {data.ai_summary.bias}
                </Text>
              </View>
            </View>

            {/* Confidence */}
            <Text className="text-xs text-slate-500">Confidence</Text>
            <View className="mt-1 h-2 w-full overflow-hidden rounded-full bg-slate-800">
              <View
                className="h-2 rounded-full bg-emerald-400"
                style={{ width: `${Math.min(100, data.ai_summary.confidence)}%` }}
              />
            </View>
            <Text className="mt-1 text-xs text-slate-400">{data.ai_summary.confidence}%</Text>

            <View className="mt-3 flex-row">
              <Stat
                label="Forecast target"
                value={
                  data.ai_summary.target !== null
                    ? formatCurrency(data.ai_summary.target, currency)
                    : 'n/a'
                }
              />
              <Stat
                label="Implied move"
                value={
                  data.ai_summary.target_change_pct !== null
                    ? formatPercent(data.ai_summary.target_change_pct)
                    : 'n/a'
                }
                color={
                  (data.ai_summary.target_change_pct ?? 0) >= 0
                    ? 'text-emerald-400'
                    : 'text-rose-400'
                }
              />
              <Stat
                label="Horizon"
                value={data.forecast?.horizon ?? '—'}
              />
            </View>

            <Text className="mt-3 text-sm leading-5 text-slate-300">
              {data.ai_summary.rationale}
            </Text>
          </View>

          {/* Technicals */}
          <View className="mt-4 rounded-2xl border border-slate-800 bg-slate-900 p-4">
            <Text className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-400">
              Technical signals
            </Text>
            {tech && Object.keys(tech).length > 0 ? (
              <>
                <View className="flex-row">
                  <Stat label="RSI (14)" value={`${tech.rsi ?? '—'}`} />
                  <Stat
                    label="MACD"
                    value={
                      tech.macd != null && tech.macd_signal != null
                        ? tech.macd > tech.macd_signal
                          ? 'Bullish ▲'
                          : 'Bearish ▼'
                        : '—'
                    }
                    color={
                      tech.macd != null && tech.macd_signal != null
                        ? tech.macd > tech.macd_signal
                          ? 'text-emerald-400'
                          : 'text-rose-400'
                        : undefined
                    }
                  />
                  <Stat
                    label="Signal"
                    value={(data.technical?.signal ?? 'hold').toUpperCase()}
                    color={
                      data.technical?.signal === 'buy'
                        ? 'text-emerald-400'
                        : data.technical?.signal === 'sell'
                          ? 'text-rose-400'
                          : 'text-slate-300'
                    }
                  />
                </View>
                <View className="mt-3 flex-row">
                  <Stat
                    label="Price vs SMA20"
                    value={
                      tech.price != null && tech.sma20 != null
                        ? tech.price >= tech.sma20
                          ? 'Above ▲'
                          : 'Below ▼'
                        : '—'
                    }
                    color={
                      tech.price != null && tech.sma20 != null
                        ? tech.price >= tech.sma20
                          ? 'text-emerald-400'
                          : 'text-rose-400'
                        : undefined
                    }
                  />
                  <Stat label="SMA 20" value={tech.sma20 != null ? `${tech.sma20}` : '—'} />
                  <View className="flex-1" />
                </View>
              </>
            ) : (
              <Text className="text-sm text-slate-500">
                Technical signals are temporarily unavailable.
              </Text>
            )}
          </View>

          {/* News + effect */}
          <View className="mt-4 rounded-2xl border border-slate-800 bg-slate-900 p-4">
            <View className="mb-1 flex-row items-center justify-between">
              <Text className="text-sm font-semibold uppercase tracking-wide text-slate-400">
                News & effect
              </Text>
              <Text className={`text-xs font-semibold ${biasTextColor(data.news_effect.bias)}`}>
                {data.news_effect.bias}
              </Text>
            </View>
            <Text className="mb-3 text-xs text-slate-500">{data.news_effect.note}</Text>

            {data.news.length === 0 ? (
              <Text className="text-sm text-slate-500">No instrument-specific news yet.</Text>
            ) : (
              data.news.map((item) => {
                const arrow = effectArrow(item.effect);
                return (
                  <View
                    key={item.id}
                    className="flex-row items-start border-t border-slate-800 py-3"
                  >
                    <View className={`mt-1.5 mr-3 h-2.5 w-2.5 rounded-full ${impactDot(item.impact_score)}`} />
                    <View className="flex-1 pr-2">
                      <Text className="text-sm text-slate-100" numberOfLines={2}>
                        {item.title}
                      </Text>
                      <Text className="mt-0.5 text-xs text-slate-500">
                        {item.source} · {timeAgo(item.published_at)}
                      </Text>
                    </View>
                    <Text className={`text-base font-bold ${arrow.color}`}>{arrow.glyph}</Text>
                  </View>
                );
              })
            )}
          </View>

          <Text className="mt-4 text-center text-xs text-slate-600">{data.disclaimer}</Text>
          {isRefetching ? <ActivityIndicator className="mt-3" color="#34d399" /> : null}
        </ScrollView>
      )}

      <Modal visible={alertOpen} transparent animationType="fade" onRequestClose={() => setAlertOpen(false)}>
        <View className="flex-1 justify-end bg-black/70 px-4 pb-6">
          <View className="rounded-2xl border border-slate-800 bg-slate-900 p-4">
            <View className="mb-4 flex-row items-center justify-between">
              <Text className="text-lg font-bold text-slate-50">Set price alert</Text>
              <Pressable onPress={() => setAlertOpen(false)} accessibilityRole="button">
                <Text className="text-base text-slate-400">Close</Text>
              </Pressable>
            </View>

            <View className="mb-4 flex-row">
              {(['price_above', 'price_below'] as const).map((side) => (
                <Pressable
                  key={side}
                  onPress={() => setAlertSide(side)}
                  className={`mr-2 flex-1 rounded-lg px-3 py-2 ${
                    alertSide === side ? 'bg-emerald-400' : 'border border-slate-700'
                  }`}
                >
                  <Text
                    className={`text-center text-sm font-bold ${
                      alertSide === side ? 'text-slate-950' : 'text-slate-300'
                    }`}
                  >
                    {side === 'price_above' ? 'Above' : 'Below'}
                  </Text>
                </Pressable>
              ))}
            </View>

            <Text className="mb-1 text-xs font-medium uppercase text-slate-500">Target price</Text>
            <TextInput
              value={alertValue}
              onChangeText={setAlertValue}
              keyboardType="decimal-pad"
              placeholder="0.00"
              placeholderTextColor="#64748b"
              className="rounded-lg border border-slate-700 px-3 py-3 text-base text-slate-50"
            />

            <Pressable
              accessibilityRole="button"
              disabled={createAlertMutation.isPending}
              onPress={() => createAlertMutation.mutate()}
              className="mt-4 rounded-lg bg-emerald-400 px-4 py-3 active:opacity-80"
            >
              <Text className="text-center text-sm font-bold text-slate-950">
                {createAlertMutation.isPending ? 'Creating...' : 'Create alert'}
              </Text>
            </Pressable>
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
}
