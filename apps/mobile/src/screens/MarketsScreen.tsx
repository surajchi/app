import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import { ActivityIndicator, FlatList, Pressable, Text, TextInput, View } from 'react-native';

import { BottomNav } from '@/components/BottomNav';
import { Badge } from '@/components/ui';
import { Card } from '@/components/ui/Card';
import { Screen } from '@/components/ui/Screen';
import { SegmentedControl } from '@/components/ui/SegmentedControl';
import { formatCurrency, formatPercent } from '@/lib/format';
import { marketsApi } from '@/services/api/markets';
import type { RootScreenProps } from '@/navigation/types';

const ASSETS = [
  { label: 'All', value: 'all' },
  { label: 'Forex', value: 'forex' },
  { label: 'Stocks', value: 'stock' },
  { label: 'Commodities', value: 'commodity' },
  { label: 'Indices', value: 'index' },
  { label: 'ETFs', value: 'etf' },
  { label: 'Crypto', value: 'crypto' },
];

const VIEWS = [
  { label: 'List', value: 'list' },
  { label: 'Heatmap', value: 'heatmap' },
];

function heatColor(changePercent: number | null | undefined): string {
  if (changePercent == null) return 'bg-slate-900 border-slate-800';
  if (changePercent >= 2) return 'bg-emerald-700 border-emerald-500/40';
  if (changePercent > 0) return 'bg-emerald-900 border-emerald-600/40';
  if (changePercent <= -2) return 'bg-rose-700 border-rose-500/40';
  if (changePercent < 0) return 'bg-rose-950 border-rose-700/40';
  return 'bg-slate-900 border-slate-800';
}

export function MarketsScreen({ navigation }: RootScreenProps<'Markets'>) {
  const [assetClass, setAssetClass] = useState('all');
  const [search, setSearch] = useState('');
  const [viewMode, setViewMode] = useState('list');

  const { data, isLoading } = useQuery({
    queryKey: ['instruments-list', assetClass, search],
    queryFn: () => marketsApi.listInstruments({ search, assetClass }),
  });

  return (
    <Screen>
      <View className="flex-row items-center justify-between px-4 py-3">
        <Pressable onPress={() => navigation.goBack()} accessibilityRole="button">
          <Text className="text-base text-slate-300">‹ Back</Text>
        </Pressable>
        <Text className="text-lg font-semibold text-slate-50">Markets</Text>
        <View className="w-10" />
      </View>

      <View className="px-4 pb-2">
        <TextInput
          value={search}
          onChangeText={setSearch}
          placeholder="Search symbol or name…"
          placeholderTextColor="#64748b"
          autoCapitalize="characters"
          autoCorrect={false}
          className="mb-3 rounded-xl border border-slate-800 bg-slate-900 px-4 py-3 text-base text-slate-100"
        />
        <SegmentedControl options={ASSETS} value={assetClass} onChange={setAssetClass} scroll />
        <View className="mt-3">
          <SegmentedControl options={VIEWS} value={viewMode} onChange={setViewMode} />
        </View>
      </View>

      {isLoading ? (
        <ActivityIndicator className="mt-10" color="#34d399" />
      ) : (
        <FlatList
          key={viewMode}
          data={data ?? []}
          numColumns={viewMode === 'heatmap' ? 2 : 1}
          keyExtractor={(i) => i.id}
          contentContainerStyle={{ padding: 16, paddingTop: 8 }}
          columnWrapperStyle={viewMode === 'heatmap' ? { gap: 8 } : undefined}
          ListEmptyComponent={
            <Text className="mt-10 text-center text-slate-500">No instruments found.</Text>
          }
          renderItem={({ item }) => (
            viewMode === 'heatmap' ? (
              <Pressable
                onPress={() => navigation.navigate('InstrumentDetail', { symbol: item.symbol })}
                className={`mb-2 flex-1 rounded-lg border p-3 active:opacity-80 ${heatColor(
                  item.quote?.change_percent
                )}`}
                style={{ minHeight: 112 }}
              >
                <View className="mb-2 flex-row items-start justify-between">
                  <View className="flex-1 pr-2">
                    <Text className="text-lg font-bold text-slate-50">{item.symbol}</Text>
                    <Text className="text-xs text-slate-300" numberOfLines={1}>
                      {item.name}
                    </Text>
                  </View>
                  <Text className="text-xs font-semibold uppercase text-slate-300">
                    {item.asset_class}
                  </Text>
                </View>
                <Text className="text-base font-semibold text-slate-50">
                  {item.quote ? formatCurrency(item.quote.price, item.currency) : 'No quote'}
                </Text>
                <Text className="mt-1 text-sm font-bold text-slate-100">
                  {item.quote ? formatPercent(item.quote.change_percent) : '—'}
                </Text>
              </Pressable>
            ) : (
              <Card
                className="mb-2 flex-row items-center justify-between"
                onPress={() => navigation.navigate('InstrumentDetail', { symbol: item.symbol })}
              >
                <View className="flex-1 pr-3">
                  <Text className="text-base font-semibold text-slate-50">{item.symbol}</Text>
                  <Text className="text-sm text-slate-400" numberOfLines={1}>
                    {item.name}
                    {item.exchange ? ` · ${item.exchange}` : ''}
                  </Text>
                </View>
                <View className="items-end">
                  {item.quote ? (
                    <>
                      <Text className="text-sm font-semibold text-slate-100">
                        {formatCurrency(item.quote.price, item.currency)}
                      </Text>
                      <Text
                        className={`text-xs font-semibold ${
                          item.quote.change_percent >= 0 ? 'text-emerald-400' : 'text-rose-400'
                        }`}
                      >
                        {formatPercent(item.quote.change_percent)}
                      </Text>
                    </>
                  ) : (
                    <Badge label={item.asset_class} variant="secondary" />
                  )}
                </View>
              </Card>
            )
          )}
        />
      )}
      <BottomNav active="markets" />
    </Screen>
  );
}
