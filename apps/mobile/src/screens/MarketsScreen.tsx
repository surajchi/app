import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import { ActivityIndicator, FlatList, Pressable, Text, TextInput, View } from 'react-native';

import { Badge } from '@/components/ui';
import { Card } from '@/components/ui/Card';
import { Screen } from '@/components/ui/Screen';
import { SegmentedControl } from '@/components/ui/SegmentedControl';
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

export function MarketsScreen({ navigation }: RootScreenProps<'Markets'>) {
  const [assetClass, setAssetClass] = useState('all');
  const [search, setSearch] = useState('');

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
      </View>

      {isLoading ? (
        <ActivityIndicator className="mt-10" color="#34d399" />
      ) : (
        <FlatList
          data={data ?? []}
          keyExtractor={(i) => i.id}
          contentContainerStyle={{ padding: 16, paddingTop: 8 }}
          ListEmptyComponent={
            <Text className="mt-10 text-center text-slate-500">No instruments found.</Text>
          }
          renderItem={({ item }) => (
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
              <View className="flex-row items-center">
                <Badge label={item.asset_class} variant="secondary" />
                <Text className="ml-2 text-slate-600">›</Text>
              </View>
            </Card>
          )}
        />
      )}
    </Screen>
  );
}
