import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import { ActivityIndicator, Pressable, RefreshControl, ScrollView, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Card } from '@/components/common/Card';
import { SentimentGauge } from '@/components/SentimentGauge';
import { formatCurrency, formatPercent, pnlColor } from '@/lib/format';
import { authApi } from '@/services/api/auth';
import { briefApi } from '@/services/api/brief';
import { dashboardApi } from '@/services/api/dashboard';
import { useAuthStore } from '@/store/authStore';
import type { RootScreenProps } from '@/navigation/types';

function NavPill({ label, onPress }: { label: string; onPress: () => void }) {
  return (
    <Pressable
      accessibilityRole="button"
      onPress={onPress}
      className="mr-2 mb-2 rounded-full border border-slate-200 px-4 py-2 active:bg-slate-100"
    >
      <Text className="text-sm font-medium text-slate-700">{label}</Text>
    </Pressable>
  );
}

export function HomeScreen({ navigation }: RootScreenProps<'Home'>) {
  const user = useAuthStore((s) => s.user);
  const refreshToken = useAuthStore((s) => s.refreshToken);
  const logout = useAuthStore((s) => s.logout);
  const [loggingOut, setLoggingOut] = useState(false);

  const { data, isLoading, refetch, isRefetching } = useQuery({
    queryKey: ['dashboard'],
    queryFn: dashboardApi.get,
  });

  const { data: brief } = useQuery({ queryKey: ['brief'], queryFn: briefApi.today });
  const moodColor =
    brief?.market_mood === 'bullish'
      ? 'text-emerald-600'
      : brief?.market_mood === 'bearish'
        ? 'text-rose-600'
        : 'text-slate-500';

  const onLogout = async () => {
    setLoggingOut(true);
    try {
      if (refreshToken) {
        await authApi.logout(refreshToken).catch(() => undefined);
      }
    } finally {
      await logout();
      setLoggingOut(false);
    }
  };

  const totals = data?.portfolio?.totals;
  const currency = data?.portfolio?.base_currency ?? 'USD';

  return (
    <SafeAreaView className="flex-1 bg-slate-50">
      <ScrollView
        contentContainerStyle={{ padding: 16 }}
        refreshControl={<RefreshControl refreshing={isRefetching} onRefresh={() => void refetch()} />}
      >
        <Text className="text-sm uppercase tracking-wide text-slate-400">Welcome back</Text>
        <Text className="mb-4 text-2xl font-bold text-slate-900">
          {user?.full_name ?? user?.email ?? 'Trader'}
        </Text>

        <View className="mb-4 flex-row flex-wrap">
          <NavPill label="Markets" onPress={() => navigation.navigate('Markets')} />
          <NavPill label="News" onPress={() => navigation.navigate('News')} />
          <NavPill label="Watchlist" onPress={() => navigation.navigate('Watchlist')} />
          <NavPill label="Portfolio" onPress={() => navigation.navigate('Portfolio')} />
          <NavPill label="Alerts" onPress={() => navigation.navigate('Alerts')} />
          <NavPill label="Profile" onPress={() => navigation.navigate('Profile')} />
        </View>

        <Card className="mb-4" onPress={() => navigation.navigate('News')}>
          <View className="mb-1 flex-row items-center justify-between">
            <Text className="text-sm font-medium text-slate-500">Daily brief</Text>
            {brief ? (
              <Text className={`text-xs font-semibold uppercase ${moodColor}`}>
                {brief.market_mood}
              </Text>
            ) : null}
          </View>
          <Text className="text-sm text-slate-700">
            {brief?.summary ?? 'Preparing your market brief…'}
          </Text>
          {brief?.sentiment_index ? <SentimentGauge index={brief.sentiment_index} /> : null}
          {brief?.week_ahead && brief.week_ahead.length > 0 ? (
            <View className="mt-2">
              <Text className="mb-0.5 text-xs font-medium text-slate-400">This week</Text>
              {brief.week_ahead.slice(0, 3).map((e) => (
                <Text key={e.id} className="text-xs text-slate-600">
                  • {e.currency} {e.title}
                </Text>
              ))}
            </View>
          ) : null}
        </Card>

        {isLoading ? (
          <ActivityIndicator className="mt-10" color="#4f46e5" />
        ) : (
          <>
            <Card className="mb-4" onPress={() => navigation.navigate('Portfolio')}>
              <Text className="mb-1 text-sm font-medium text-slate-500">Portfolio value</Text>
              {totals ? (
                <>
                  <Text className="text-3xl font-bold text-slate-900">
                    {formatCurrency(totals.market_value, currency)}
                  </Text>
                  <Text className={`mt-1 text-base font-semibold ${pnlColor(totals.unrealized_pnl)}`}>
                    {formatCurrency(totals.unrealized_pnl, currency)} ({formatPercent(totals.unrealized_pct)})
                  </Text>
                  <Text className="mt-1 text-xs text-slate-400">
                    {totals.position_count} position{totals.position_count === 1 ? '' : 's'}
                  </Text>
                </>
              ) : (
                <Text className="text-slate-400">No portfolio yet — tap to create one.</Text>
              )}
            </Card>

            <Card className="mb-4" onPress={() => navigation.navigate('Watchlist')}>
              <Text className="mb-2 text-sm font-medium text-slate-500">
                {data?.watchlist?.name ?? 'Watchlist'}
              </Text>
              {data?.watchlist?.items && data.watchlist.items.length > 0 ? (
                data.watchlist.items.slice(0, 5).map((item) => (
                  <Pressable
                    key={item.id}
                    onPress={() =>
                      navigation.navigate('InstrumentDetail', { symbol: item.instrument.symbol })
                    }
                    className="flex-row items-center justify-between py-1 active:opacity-70"
                  >
                    <Text className="text-base font-medium text-slate-800">
                      {item.instrument.symbol}
                    </Text>
                    <View className="flex-row items-center">
                      <Text className="mr-3 text-base text-slate-700">
                        {item.quote ? formatCurrency(item.quote.price, item.instrument.currency) : '—'}
                      </Text>
                      <Text className={`text-sm ${pnlColor(item.quote?.change_percent ?? 0)}`}>
                        {item.quote ? formatPercent(item.quote.change_percent) : ''}
                      </Text>
                    </View>
                  </Pressable>
                ))
              ) : (
                <Text className="text-slate-400">Empty — tap to add instruments.</Text>
              )}
            </Card>

            <Card className="mb-4">
              <Text className="mb-2 text-sm font-medium text-slate-500">Top movers</Text>
              {(data?.movers.gainers ?? []).slice(0, 3).map((m) => (
                <Pressable
                  key={m.instrument.id}
                  onPress={() =>
                    navigation.navigate('InstrumentDetail', { symbol: m.instrument.symbol })
                  }
                  className="flex-row justify-between py-1 active:opacity-70"
                >
                  <Text className="text-base text-slate-800">{m.instrument.symbol}</Text>
                  <Text className={`text-sm ${pnlColor(m.change_percent ?? 0)}`}>
                    {formatPercent(m.change_percent ?? 0)}
                  </Text>
                </Pressable>
              ))}
            </Card>

            <Card className="mb-4">
              <View className="mb-2 flex-row items-center justify-between">
                <Text className="text-sm font-medium text-slate-500">Recent alerts</Text>
                <Pressable onPress={() => navigation.navigate('Alerts')}>
                  <Text className="text-sm font-medium text-brand-600">Manage</Text>
                </Pressable>
              </View>
              {(data?.alerts ?? []).length > 0 ? (
                data!.alerts.slice(0, 3).map((a) => (
                  <Text key={a.id} className="py-0.5 text-sm text-slate-700">
                    • {a.rule_name}
                  </Text>
                ))
              ) : (
                <Text className="text-slate-400">No alerts triggered yet.</Text>
              )}
            </Card>

            <Card className="mb-6">
              <Text className="mb-2 text-sm font-medium text-slate-500">Market news</Text>
              {(data?.top_news ?? []).map((n) => (
                <View key={n.id} className="py-1">
                  <Text className="text-sm text-slate-800" numberOfLines={2}>
                    {n.is_breaking ? '🔴 ' : ''}
                    {n.title}
                  </Text>
                  <Text className="text-xs text-slate-400">
                    {n.source}
                    {n.sentiment ? ` · ${n.sentiment}` : ''}
                  </Text>
                </View>
              ))}
            </Card>

            <Pressable
              accessibilityRole="button"
              onPress={onLogout}
              className="items-center rounded-xl border border-slate-200 py-3 active:bg-slate-100"
            >
              <Text className="text-base font-semibold text-slate-600">
                {loggingOut ? 'Logging out…' : 'Log out'}
              </Text>
            </Pressable>
          </>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}
