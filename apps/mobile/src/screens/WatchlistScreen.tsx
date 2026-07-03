import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  FlatList,
  Pressable,
  RefreshControl,
  Text,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import type { AxiosError } from 'axios';
import type { Instrument } from '@finpulse/types';

import { Button } from '@/components/common/Button';
import { InstrumentPicker } from '@/components/InstrumentPicker';
import { formatCurrency, formatPercent, pnlColor } from '@/lib/format';
import { watchlistsApi } from '@/services/api/watchlists';
import type { RootScreenProps } from '@/navigation/types';

export function WatchlistScreen({ navigation }: RootScreenProps<'Watchlist'>) {
  const qc = useQueryClient();
  const [pickerOpen, setPickerOpen] = useState(false);

  const listsQuery = useQuery({ queryKey: ['watchlists'], queryFn: watchlistsApi.list });
  const selected = listsQuery.data?.find((w) => w.is_default) ?? listsQuery.data?.[0];

  const detailQuery = useQuery({
    queryKey: ['watchlist', selected?.id],
    queryFn: () => watchlistsApi.get(selected!.id),
    enabled: Boolean(selected),
  });

  const invalidate = () => {
    void qc.invalidateQueries({ queryKey: ['watchlist', selected?.id] });
    void qc.invalidateQueries({ queryKey: ['watchlists'] });
    void qc.invalidateQueries({ queryKey: ['dashboard'] });
  };

  const createList = useMutation({
    mutationFn: () => watchlistsApi.create('My Watchlist', true),
    onSuccess: invalidate,
  });

  const addItem = useMutation({
    mutationFn: (instrument: Instrument) =>
      watchlistsApi.addItem(selected!.id, { instrument_id: instrument.id }),
    onSuccess: invalidate,
    onError: (err: AxiosError) => {
      Alert.alert(
        err.response?.status === 409 ? 'Already added' : 'Could not add',
        err.response?.status === 409
          ? 'That instrument is already in this watchlist.'
          : 'Please try again.'
      );
    },
  });

  const removeItem = useMutation({
    mutationFn: (itemId: string) => watchlistsApi.removeItem(selected!.id, itemId),
    onSuccess: invalidate,
  });

  if (listsQuery.isLoading) {
    return (
      <SafeAreaView className="flex-1 items-center justify-center bg-slate-50">
        <ActivityIndicator color="#4f46e5" />
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView className="flex-1 bg-slate-50">
      <View className="flex-row items-center justify-between px-4 py-3">
        <Pressable onPress={() => navigation.goBack()} accessibilityRole="button">
          <Text className="text-base text-brand-600">‹ Back</Text>
        </Pressable>
        <Text className="text-lg font-semibold text-slate-900">
          {selected?.name ?? 'Watchlist'}
        </Text>
        <Pressable
          onPress={() => selected && setPickerOpen(true)}
          disabled={!selected}
          accessibilityRole="button"
        >
          <Text className={`text-base ${selected ? 'text-brand-600' : 'text-slate-300'}`}>+ Add</Text>
        </Pressable>
      </View>

      {!selected ? (
        <View className="flex-1 items-center justify-center px-8">
          <Text className="mb-4 text-center text-slate-500">
            You don't have a watchlist yet.
          </Text>
          <Button
            title="Create watchlist"
            loading={createList.isPending}
            onPress={() => createList.mutate()}
          />
        </View>
      ) : (
        <FlatList
          data={detailQuery.data?.items ?? []}
          keyExtractor={(item) => item.id}
          contentContainerStyle={{ paddingHorizontal: 16, paddingBottom: 24 }}
          refreshControl={
            <RefreshControl
              refreshing={detailQuery.isRefetching}
              onRefresh={() => void detailQuery.refetch()}
            />
          }
          ListEmptyComponent={
            <Text className="mt-10 text-center text-slate-400">
              No instruments yet. Tap “+ Add”.
            </Text>
          }
          renderItem={({ item }) => (
            <View className="mb-2 flex-row items-center justify-between rounded-2xl border border-slate-200 bg-white p-4">
              <Pressable
                accessibilityRole="button"
                onPress={() =>
                  navigation.navigate('InstrumentDetail', { symbol: item.instrument.symbol })
                }
                className="flex-1 flex-row items-center justify-between active:opacity-70"
              >
                <View className="flex-1">
                  <Text className="text-base font-semibold text-slate-900">
                    {item.instrument.symbol}
                  </Text>
                  <Text className="text-sm text-slate-500" numberOfLines={1}>
                    {item.instrument.name}
                  </Text>
                </View>
                <View className="items-end">
                  <Text className="text-base text-slate-900">
                    {item.quote
                      ? formatCurrency(item.quote.price, item.instrument.currency)
                      : '—'}
                  </Text>
                  {item.quote ? (
                    <Text className={`text-sm ${pnlColor(item.quote.change_percent)}`}>
                      {formatPercent(item.quote.change_percent)}
                    </Text>
                  ) : null}
                </View>
              </Pressable>
              <Pressable
                accessibilityRole="button"
                onPress={() => removeItem.mutate(item.id)}
                className="ml-4 h-8 w-8 items-center justify-center rounded-full bg-slate-100 active:bg-slate-200"
              >
                <Text className="text-slate-500">✕</Text>
              </Pressable>
            </View>
          )}
        />
      )}

      <InstrumentPicker
        visible={pickerOpen}
        onClose={() => setPickerOpen(false)}
        onSelect={(instrument) => addItem.mutate(instrument)}
      />
    </SafeAreaView>
  );
}
