import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import { ActivityIndicator, Pressable, RefreshControl, ScrollView, Text, View } from 'react-native';

import { BottomNav } from '@/components/BottomNav';
import { InstrumentPicker } from '@/components/InstrumentPicker';
import { Card } from '@/components/ui/Card';
import { Screen } from '@/components/ui/Screen';
import { SentimentGauge } from '@/components/SentimentGauge';
import { formatCurrency, formatPercent } from '@/lib/format';
import { authApi } from '@/services/api/auth';
import { briefApi } from '@/services/api/brief';
import { dashboardApi } from '@/services/api/dashboard';
import { notificationsApi } from '@/services/api/notifications';
import { useAuthStore } from '@/store/authStore';
import type { RootScreenProps } from '@/navigation/types';

function pnl(value: number): string {
  return value >= 0 ? 'text-emerald-400' : 'text-rose-400';
}

function NavPill({ label, onPress }: { label: string; onPress: () => void }) {
  return (
    <Pressable
      accessibilityRole="button"
      onPress={onPress}
      className="mr-2 mb-2 rounded-full border border-slate-700 px-4 py-2 active:bg-slate-800"
    >
      <Text className="text-sm font-medium text-slate-200">{label}</Text>
    </Pressable>
  );
}

export function HomeScreen({ navigation }: RootScreenProps<'Home'>) {
  const user = useAuthStore((s) => s.user);
  const refreshToken = useAuthStore((s) => s.refreshToken);
  const logout = useAuthStore((s) => s.logout);
  const [loggingOut, setLoggingOut] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);

  const { data, isLoading, refetch, isRefetching } = useQuery({
    queryKey: ['dashboard'],
    queryFn: dashboardApi.get,
  });

  const { data: brief } = useQuery({ queryKey: ['brief'], queryFn: briefApi.today });
  const { data: unreadItems } = useQuery({
    queryKey: ['notifications', 'unread'],
    queryFn: () => notificationsApi.list(true),
  });
  const unread = unreadItems?.length ?? 0;
  const moodColor =
    brief?.market_mood === 'bullish'
      ? 'text-emerald-400'
      : brief?.market_mood === 'bearish'
        ? 'text-rose-400'
        : 'text-slate-400';

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
    <Screen>
      <ScrollView
        contentContainerStyle={{ padding: 16 }}
        refreshControl={
          <RefreshControl
            tintColor="#34d399"
            refreshing={isRefetching}
            onRefresh={() => void refetch()}
          />
        }
      >
        <Text className="text-sm uppercase tracking-wide text-slate-500">Welcome back</Text>
        <Text className="mb-4 text-2xl font-bold text-slate-50">
          {user?.full_name ?? user?.email ?? 'Trader'}
        </Text>

        <Pressable
          onPress={() => setSearchOpen(true)}
          className="mb-4 rounded-xl border border-slate-800 bg-slate-900 px-4 py-3 active:bg-slate-800"
        >
          <Text className="text-slate-500">🔍  Search any market…</Text>
        </Pressable>

        <View className="mb-4 flex-row flex-wrap">
          <NavPill label="Watchlist" onPress={() => navigation.navigate('Watchlist')} />
          <NavPill label="Alerts" onPress={() => navigation.navigate('Alerts')} />
          <NavPill
            label={unread > 0 ? `Inbox (${unread})` : 'Inbox'}
            onPress={() => navigation.navigate('Notifications')}
          />
          <NavPill label="Plans" onPress={() => navigation.navigate('Subscription')} />
          <NavPill label="Convert" onPress={() => navigation.navigate('Converter')} />
        </View>

        <Card className="mb-4" onPress={() => navigation.navigate('News')}>
          <View className="mb-1 flex-row items-center justify-between">
            <Text className="text-sm font-medium text-slate-400">Daily brief</Text>
            {brief ? (
              <Text className={`text-xs font-semibold uppercase ${moodColor}`}>
                {brief.market_mood}
              </Text>
            ) : null}
          </View>
          <Text className="text-sm text-slate-300">
            {brief?.summary ?? 'Preparing your market brief…'}
          </Text>
          {brief?.sentiment_index ? <SentimentGauge index={brief.sentiment_index} /> : null}
          {brief?.week_ahead && brief.week_ahead.length > 0 ? (
            <View className="mt-2">
              <Text className="mb-0.5 text-xs font-medium text-slate-500">This week</Text>
              {brief.week_ahead.slice(0, 3).map((e) => (
                <Text key={e.id} className="text-xs text-slate-400">
                  • {e.currency} {e.title}
                </Text>
              ))}
            </View>
          ) : null}
        </Card>

        {isLoading ? (
          <ActivityIndicator className="mt-10" color="#34d399" />
        ) : (
          <>
            <Card className="mb-4" onPress={() => navigation.navigate('Portfolio')}>
              <Text className="mb-1 text-sm font-medium text-slate-400">Portfolio value</Text>
              {totals ? (
                <>
                  <Text className="text-3xl font-bold text-slate-50">
                    {formatCurrency(totals.market_value, currency)}
                  </Text>
                  <Text className={`mt-1 text-base font-semibold ${pnl(totals.unrealized_pnl)}`}>
                    {formatCurrency(totals.unrealized_pnl, currency)} ({formatPercent(totals.unrealized_pct)})
                  </Text>
                  <Text className="mt-1 text-xs text-slate-500">
                    {totals.position_count} position{totals.position_count === 1 ? '' : 's'}
                  </Text>
                </>
              ) : (
                <Text className="text-slate-500">No portfolio yet — tap to create one.</Text>
              )}
            </Card>

            <Card className="mb-4" onPress={() => navigation.navigate('Watchlist')}>
              <Text className="mb-2 text-sm font-medium text-slate-400">
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
                    <Text className="text-base font-medium text-slate-100">
                      {item.instrument.symbol}
                    </Text>
                    <View className="flex-row items-center">
                      <Text className="mr-3 text-base text-slate-200">
                        {item.quote ? formatCurrency(item.quote.price, item.instrument.currency) : '—'}
                      </Text>
                      <Text className={`text-sm ${pnl(item.quote?.change_percent ?? 0)}`}>
                        {item.quote ? formatPercent(item.quote.change_percent) : ''}
                      </Text>
                    </View>
                  </Pressable>
                ))
              ) : (
                <Text className="text-slate-500">Empty — tap to add instruments.</Text>
              )}
            </Card>

            <Card className="mb-4">
              <Text className="mb-2 text-sm font-medium text-slate-400">Top movers</Text>
              {(data?.movers.gainers ?? []).slice(0, 3).map((m) => (
                <Pressable
                  key={m.instrument.id}
                  onPress={() =>
                    navigation.navigate('InstrumentDetail', { symbol: m.instrument.symbol })
                  }
                  className="flex-row justify-between py-1 active:opacity-70"
                >
                  <Text className="text-base text-slate-100">{m.instrument.symbol}</Text>
                  <Text className={`text-sm ${pnl(m.change_percent ?? 0)}`}>
                    {formatPercent(m.change_percent ?? 0)}
                  </Text>
                </Pressable>
              ))}
            </Card>

            <Card className="mb-4">
              <View className="mb-2 flex-row items-center justify-between">
                <Text className="text-sm font-medium text-slate-400">Recent alerts</Text>
                <Pressable onPress={() => navigation.navigate('Alerts')}>
                  <Text className="text-sm font-medium text-emerald-400">Manage</Text>
                </Pressable>
              </View>
              {(data?.alerts ?? []).length > 0 ? (
                data!.alerts.slice(0, 3).map((a) => (
                  <Text key={a.id} className="py-0.5 text-sm text-slate-300">
                    • {a.rule_name}
                  </Text>
                ))
              ) : (
                <Text className="text-slate-500">No alerts triggered yet.</Text>
              )}
            </Card>

            <Card className="mb-6">
              <Text className="mb-2 text-sm font-medium text-slate-400">Market news</Text>
              {(data?.top_news ?? []).map((n) => (
                <View key={n.id} className="py-1">
                  <Text className="text-sm text-slate-200" numberOfLines={2}>
                    {n.is_breaking ? '🔴 ' : ''}
                    {n.title}
                  </Text>
                  <Text className="text-xs text-slate-500">
                    {n.source}
                    {n.sentiment ? ` · ${n.sentiment}` : ''}
                  </Text>
                </View>
              ))}
            </Card>

            <Pressable
              accessibilityRole="button"
              onPress={onLogout}
              className="items-center rounded-xl border border-slate-700 py-3 active:bg-slate-800"
            >
              <Text className="text-base font-semibold text-slate-300">
                {loggingOut ? 'Logging out…' : 'Log out'}
              </Text>
            </Pressable>
          </>
        )}
      </ScrollView>
      <InstrumentPicker
        visible={searchOpen}
        onClose={() => setSearchOpen(false)}
        onSelect={(inst) => navigation.navigate('InstrumentDetail', { symbol: inst.symbol })}
      />
      <BottomNav active="home" />
    </Screen>
  );
}
