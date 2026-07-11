import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import { ActivityIndicator, Alert, FlatList, Pressable, RefreshControl, Text, View } from 'react-native';
import type { AxiosError } from 'axios';
import type { Instrument } from '@finpulse/types';

import { InstrumentPicker } from '@/components/InstrumentPicker';
import { Button } from '@/components/ui/Button';
import { Screen } from '@/components/ui/Screen';
import { SegmentedControl } from '@/components/ui/SegmentedControl';
import { formatCurrency, formatPercent } from '@/lib/format';
import { watchlistsApi } from '@/services/api/watchlists';
import type { RootScreenProps } from '@/navigation/types';

function pnl(value: number): string {
  return value >= 0 ? 'text-emerald-400' : 'text-rose-400';
}

export function WatchlistScreen({ navigation }: RootScreenProps<'Watchlist'>) {
  const qc = useQueryClient();
  const [pickerOpen, setPickerOpen] = useState(false);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const listsQuery = useQuery({ queryKey: ['watchlists'], queryFn: watchlistsApi.list });
  const lists = listsQuery.data ?? [];
  const selected =
    lists.find((w) => w.id === selectedId) ?? lists.find((w) => w.is_default) ?? lists[0];

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
    mutationFn: () =>
      watchlistsApi.create(lists.length === 0 ? 'My Watchlist' : `Watchlist ${lists.length + 1}`, lists.length === 0),
    onSuccess: (created) => {
      setSelectedId(created.id);
      invalidate();
    },
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
      <Screen className="items-center justify-center">
        <ActivityIndicator color="#34d399" />
      </Screen>
    );
  }

  return (
    <Screen>
      <View className="flex-row items-center justify-between px-4 py-3">
        <Pressable onPress={() => navigation.goBack()} accessibilityRole="button">
          <Text className="text-base text-slate-300">‹ Back</Text>
        </Pressable>
        <Text className="text-lg font-semibold text-slate-50">{selected?.name ?? 'Watchlist'}</Text>
        <Pressable
          onPress={() => selected && setPickerOpen(true)}
          disabled={!selected}
          accessibilityRole="button"
        >
          <Text className={`text-base ${selected ? 'text-emerald-400' : 'text-slate-600'}`}>+ Add</Text>
        </Pressable>
      </View>

      {lists.length > 0 ? (
        <View className="flex-row items-center px-4 pb-2">
          <View className="flex-1">
            <SegmentedControl
              options={lists.map((l) => ({ label: l.name, value: l.id }))}
              value={selected?.id ?? ''}
              onChange={setSelectedId}
              scroll
            />
          </View>
          <Pressable onPress={() => createList.mutate()} className="ml-2" accessibilityRole="button">
            <Text className="text-sm text-emerald-400">＋ New</Text>
          </Pressable>
        </View>
      ) : null}

      {!selected ? (
        <View className="flex-1 items-center justify-center px-8">
          <Text className="mb-4 text-center text-slate-400">You don&apos;t have a watchlist yet.</Text>
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
              tintColor="#34d399"
              refreshing={detailQuery.isRefetching}
              onRefresh={() => void detailQuery.refetch()}
            />
          }
          ListEmptyComponent={
            <Text className="mt-10 text-center text-slate-500">No instruments yet. Tap “+ Add”.</Text>
          }
          renderItem={({ item }) => (
            <View className="mb-2 flex-row items-center justify-between rounded-2xl border border-slate-800 bg-slate-900 p-4">
              <Pressable
                accessibilityRole="button"
                onPress={() =>
                  navigation.navigate('InstrumentDetail', { symbol: item.instrument.symbol })
                }
                className="flex-1 flex-row items-center justify-between active:opacity-70"
              >
                <View className="flex-1">
                  <Text className="text-base font-semibold text-slate-50">
                    {item.instrument.symbol}
                  </Text>
                  <Text className="text-sm text-slate-400" numberOfLines={1}>
                    {item.instrument.name}
                  </Text>
                </View>
                <View className="items-end">
                  <Text className="text-base text-slate-100">
                    {item.quote ? formatCurrency(item.quote.price, item.instrument.currency) : '—'}
                  </Text>
                  {item.quote ? (
                    <Text className={`text-sm ${pnl(item.quote.change_percent)}`}>
                      {formatPercent(item.quote.change_percent)}
                    </Text>
                  ) : null}
                </View>
              </Pressable>
              <Pressable
                accessibilityRole="button"
                onPress={() => removeItem.mutate(item.id)}
                className="ml-4 h-8 w-8 items-center justify-center rounded-full bg-slate-800 active:bg-slate-700"
              >
                <Text className="text-slate-400">✕</Text>
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
    </Screen>
  );
}
