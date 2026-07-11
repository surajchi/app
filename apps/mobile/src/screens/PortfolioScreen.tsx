import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  FlatList,
  Modal,
  Pressable,
  RefreshControl,
  Text,
  TextInput,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import type { AxiosError } from 'axios';
import type { Instrument, NewTransaction, Transaction, TransactionType } from '@finpulse/types';

import { AllocationDonut } from '@/components/AllocationDonut';
import { BottomNav } from '@/components/BottomNav';
import { InstrumentPicker } from '@/components/InstrumentPicker';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Screen } from '@/components/ui/Screen';
import { SegmentedControl } from '@/components/ui/SegmentedControl';
import { formatCurrency, formatNumber, formatPercent } from '@/lib/format';
import { portfoliosApi } from '@/services/api/portfolios';
import type { RootScreenProps } from '@/navigation/types';

function pnl(value: number): string {
  return value >= 0 ? 'text-emerald-400' : 'text-rose-400';
}

interface TradeModalProps {
  visible: boolean;
  currency: string;
  submitting: boolean;
  onClose: () => void;
  onSubmit: (txn: NewTransaction) => void;
}

function TradeModal({ visible, currency, submitting, onClose, onSubmit }: TradeModalProps) {
  const [instrument, setInstrument] = useState<Instrument | null>(null);
  const [type, setType] = useState<TransactionType>('buy');
  const [quantity, setQuantity] = useState('');
  const [price, setPrice] = useState('');
  const [pickerOpen, setPickerOpen] = useState(false);

  const reset = () => {
    setInstrument(null);
    setType('buy');
    setQuantity('');
    setPrice('');
  };

  const canSubmit = instrument && Number(quantity) > 0 && Number(price) >= 0;

  return (
    <Modal visible={visible} animationType="slide" onRequestClose={onClose}>
      <SafeAreaView className="flex-1 bg-slate-950">
        <View className="flex-row items-center justify-between border-b border-slate-800 px-4 py-3">
          <Text className="text-lg font-semibold text-slate-50">Record trade</Text>
          <Pressable onPress={onClose} accessibilityRole="button">
            <Text className="text-base font-medium text-emerald-400">Close</Text>
          </Pressable>
        </View>

        <View className="px-4 py-4">
          <Text className="mb-1 text-sm font-medium text-slate-400">Instrument</Text>
          <Pressable
            onPress={() => setPickerOpen(true)}
            className="mb-4 rounded-xl border border-slate-800 bg-slate-900 px-4 py-3 active:bg-slate-800"
          >
            <Text className={instrument ? 'text-slate-100' : 'text-slate-500'}>
              {instrument ? `${instrument.symbol} — ${instrument.name}` : 'Select instrument…'}
            </Text>
          </Pressable>

          <View className="mb-4 flex-row">
            {(['buy', 'sell'] as TransactionType[]).map((t) => (
              <Pressable
                key={t}
                onPress={() => setType(t)}
                className={`mr-2 flex-1 items-center rounded-xl border py-3 ${
                  type === t ? 'border-emerald-500 bg-emerald-500' : 'border-slate-800'
                }`}
              >
                <Text className={type === t ? 'font-semibold text-slate-950' : 'text-slate-300'}>
                  {t.toUpperCase()}
                </Text>
              </Pressable>
            ))}
          </View>

          <Text className="mb-1 text-sm font-medium text-slate-400">Quantity</Text>
          <TextInput
            value={quantity}
            onChangeText={setQuantity}
            keyboardType="decimal-pad"
            placeholder="0"
            placeholderTextColor="#64748b"
            className="mb-4 rounded-xl border border-slate-800 bg-slate-900 px-4 py-3 text-base text-slate-100"
          />

          <Text className="mb-1 text-sm font-medium text-slate-400">Price ({currency})</Text>
          <TextInput
            value={price}
            onChangeText={setPrice}
            keyboardType="decimal-pad"
            placeholder="0.00"
            placeholderTextColor="#64748b"
            className="mb-6 rounded-xl border border-slate-800 bg-slate-900 px-4 py-3 text-base text-slate-100"
          />

          <Button
            title="Save trade"
            loading={submitting}
            disabled={!canSubmit}
            onPress={() => {
              if (!instrument) return;
              onSubmit({ instrument_id: instrument.id, type, quantity, price: price || '0' });
              reset();
            }}
          />
        </View>

        <InstrumentPicker
          visible={pickerOpen}
          onClose={() => setPickerOpen(false)}
          onSelect={setInstrument}
        />
      </SafeAreaView>
    </Modal>
  );
}

export function PortfolioScreen({ navigation }: RootScreenProps<'Portfolio'>) {
  const qc = useQueryClient();
  const [tradeOpen, setTradeOpen] = useState(false);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const listQuery = useQuery({ queryKey: ['portfolios'], queryFn: portfoliosApi.list });
  const portfolios = listQuery.data ?? [];
  const selected =
    portfolios.find((p) => p.id === selectedId) ??
    portfolios.find((p) => p.is_default) ??
    portfolios[0];

  const summaryQuery = useQuery({
    queryKey: ['portfolio-summary', selected?.id],
    queryFn: () => portfoliosApi.summary(selected!.id),
    enabled: Boolean(selected),
  });

  const txnQuery = useQuery({
    queryKey: ['portfolio-txns', selected?.id],
    queryFn: () => portfoliosApi.transactions(selected!.id),
    enabled: Boolean(selected),
  });

  const invalidate = () => {
    void qc.invalidateQueries({ queryKey: ['portfolio-summary', selected?.id] });
    void qc.invalidateQueries({ queryKey: ['portfolio-txns', selected?.id] });
    void qc.invalidateQueries({ queryKey: ['dashboard'] });
  };

  const createPortfolio = useMutation({
    mutationFn: () =>
      portfoliosApi.create(
        portfolios.length === 0 ? 'Main' : `Portfolio ${portfolios.length + 1}`,
        'USD',
        portfolios.length === 0
      ),
    onSuccess: (created) => {
      setSelectedId(created.id);
      void qc.invalidateQueries({ queryKey: ['portfolios'] });
    },
  });

  const addTxn = useMutation({
    mutationFn: (txn: NewTransaction) => portfoliosApi.addTransaction(selected!.id, txn),
    onSuccess: () => {
      invalidate();
      setTradeOpen(false);
    },
    onError: (err: AxiosError<{ error?: { message?: string } }>) => {
      Alert.alert('Trade rejected', err.response?.data?.error?.message ?? 'Please try again.');
    },
  });

  if (listQuery.isLoading) {
    return (
      <Screen className="items-center justify-center">
        <ActivityIndicator color="#34d399" />
      </Screen>
    );
  }

  const currency = selected?.base_currency ?? 'USD';
  const totals = summaryQuery.data?.totals;
  const positions = summaryQuery.data?.positions ?? [];

  return (
    <Screen>
      <View className="flex-row items-center justify-between px-4 py-3">
        <Pressable onPress={() => navigation.goBack()} accessibilityRole="button">
          <Text className="text-base text-slate-300">‹ Back</Text>
        </Pressable>
        <Text className="text-lg font-semibold text-slate-50">{selected?.name ?? 'Portfolio'}</Text>
        <Pressable
          onPress={() => selected && setTradeOpen(true)}
          disabled={!selected}
          accessibilityRole="button"
        >
          <Text className={`text-base ${selected ? 'text-emerald-400' : 'text-slate-600'}`}>
            + Trade
          </Text>
        </Pressable>
      </View>

      {portfolios.length > 0 ? (
        <View className="flex-row items-center px-4 pb-2">
          <View className="flex-1">
            <SegmentedControl
              options={portfolios.map((p) => ({ label: p.name, value: p.id }))}
              value={selected?.id ?? ''}
              onChange={setSelectedId}
              scroll
            />
          </View>
          <Pressable
            onPress={() => createPortfolio.mutate()}
            className="ml-2"
            accessibilityRole="button"
          >
            <Text className="text-sm text-emerald-400">＋ New</Text>
          </Pressable>
        </View>
      ) : null}

      {!selected ? (
        <View className="flex-1 items-center justify-center px-8">
          <Text className="mb-4 text-center text-slate-400">No portfolio yet.</Text>
          <Button
            title="Create portfolio"
            loading={createPortfolio.isPending}
            onPress={() => createPortfolio.mutate()}
          />
        </View>
      ) : (
        <FlatList
          data={positions}
          keyExtractor={(p) => p.instrument_id}
          contentContainerStyle={{ paddingHorizontal: 16, paddingBottom: 24 }}
          refreshControl={
            <RefreshControl
              tintColor="#34d399"
              refreshing={summaryQuery.isRefetching}
              onRefresh={() => void summaryQuery.refetch()}
            />
          }
          ListHeaderComponent={
            <>
              <Card className="mb-4">
                <Text className="text-sm font-medium text-slate-400">Total value</Text>
                <Text className="text-3xl font-bold text-slate-50">
                  {formatCurrency(totals?.market_value ?? 0, currency)}
                </Text>
                {totals ? (
                  <Text className={`mt-1 text-base font-semibold ${pnl(totals.unrealized_pnl)}`}>
                    {formatCurrency(totals.unrealized_pnl, currency)} ({formatPercent(totals.unrealized_pct)})
                  </Text>
                ) : null}
                {totals && totals.realized_pnl !== 0 ? (
                  <Text className="mt-1 text-xs text-slate-500">
                    Realized: {formatCurrency(totals.realized_pnl, currency)}
                  </Text>
                ) : null}
              </Card>

              {positions.length > 0 ? (
                <Card className="mb-4">
                  <Text className="mb-3 text-sm font-medium text-slate-400">Allocation</Text>
                  <AllocationDonut positions={positions} />
                </Card>
              ) : null}
            </>
          }
          ListFooterComponent={
            (txnQuery.data ?? []).length > 0 ? (
              <View className="mt-4">
                <Text className="mb-2 text-sm font-medium text-slate-400">Recent trades</Text>
                {(txnQuery.data ?? []).slice(0, 10).map((t: Transaction) => (
                  <View
                    key={t.id}
                    className="mb-1 flex-row items-center justify-between rounded-xl border border-slate-800 bg-slate-900 px-3 py-2.5"
                  >
                    <View className="flex-row items-center">
                      <Text
                        className={`mr-2 text-xs font-bold uppercase ${
                          t.type === 'buy' ? 'text-emerald-400' : 'text-rose-400'
                        }`}
                      >
                        {t.type}
                      </Text>
                      <Text className="text-sm text-slate-100">{t.instrument.symbol}</Text>
                    </View>
                    <Text className="text-sm text-slate-300">
                      {formatNumber(Number(t.quantity))} @ {formatCurrency(Number(t.price), currency)}
                    </Text>
                  </View>
                ))}
              </View>
            ) : null
          }
          ListEmptyComponent={
            <Text className="mt-10 text-center text-slate-500">
              No holdings. Tap “+ Trade” to record a buy.
            </Text>
          }
          renderItem={({ item }) => (
            <View className="mb-2 rounded-2xl border border-slate-800 bg-slate-900 p-4">
              <View className="flex-row items-center justify-between">
                <Text className="text-base font-semibold text-slate-50">{item.symbol}</Text>
                <Text className="text-base text-slate-100">
                  {formatCurrency(item.market_value, currency)}
                </Text>
              </View>
              <View className="mt-1 flex-row items-center justify-between">
                <Text className="text-sm text-slate-400">
                  {formatNumber(item.quantity)} @ {formatCurrency(item.avg_cost, currency)}
                </Text>
                <Text className={`text-sm ${pnl(item.unrealized_pnl)}`}>
                  {formatCurrency(item.unrealized_pnl, currency)} ({formatPercent(item.unrealized_pct)})
                </Text>
              </View>
              <Text className="mt-1 text-xs text-slate-500">
                {formatPercent(item.allocation_pct)} of portfolio
                {item.priced ? '' : ' · price stale'}
              </Text>
            </View>
          )}
        />
      )}

      <TradeModal
        visible={tradeOpen}
        currency={currency}
        submitting={addTxn.isPending}
        onClose={() => setTradeOpen(false)}
        onSubmit={(txn) => addTxn.mutate(txn)}
      />
      <BottomNav active="portfolio" />
    </Screen>
  );
}
