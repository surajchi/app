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
import type { Instrument, NewTransaction, TransactionType } from '@finpulse/types';

import { Button } from '@/components/common/Button';
import { Card } from '@/components/common/Card';
import { InstrumentPicker } from '@/components/InstrumentPicker';
import { formatCurrency, formatNumber, formatPercent, pnlColor } from '@/lib/format';
import { portfoliosApi } from '@/services/api/portfolios';
import type { RootScreenProps } from '@/navigation/types';

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
      <SafeAreaView className="flex-1 bg-white">
        <View className="flex-row items-center justify-between border-b border-slate-100 px-4 py-3">
          <Text className="text-lg font-semibold text-slate-900">Record trade</Text>
          <Pressable onPress={onClose} accessibilityRole="button">
            <Text className="text-base font-medium text-brand-600">Close</Text>
          </Pressable>
        </View>

        <View className="px-4 py-4">
          <Text className="mb-1 text-sm font-medium text-slate-500">Instrument</Text>
          <Pressable
            onPress={() => setPickerOpen(true)}
            className="mb-4 rounded-xl border border-slate-200 px-4 py-3 active:bg-slate-50"
          >
            <Text className={instrument ? 'text-slate-900' : 'text-slate-400'}>
              {instrument ? `${instrument.symbol} — ${instrument.name}` : 'Select instrument…'}
            </Text>
          </Pressable>

          <View className="mb-4 flex-row">
            {(['buy', 'sell'] as TransactionType[]).map((t) => (
              <Pressable
                key={t}
                onPress={() => setType(t)}
                className={`mr-2 flex-1 items-center rounded-xl border py-3 ${
                  type === t ? 'border-brand-600 bg-brand-600' : 'border-slate-200'
                }`}
              >
                <Text className={type === t ? 'font-semibold text-white' : 'text-slate-600'}>
                  {t.toUpperCase()}
                </Text>
              </Pressable>
            ))}
          </View>

          <Text className="mb-1 text-sm font-medium text-slate-500">Quantity</Text>
          <TextInput
            value={quantity}
            onChangeText={setQuantity}
            keyboardType="decimal-pad"
            placeholder="0"
            className="mb-4 rounded-xl border border-slate-200 px-4 py-3 text-base text-slate-900"
          />

          <Text className="mb-1 text-sm font-medium text-slate-500">Price ({currency})</Text>
          <TextInput
            value={price}
            onChangeText={setPrice}
            keyboardType="decimal-pad"
            placeholder="0.00"
            className="mb-6 rounded-xl border border-slate-200 px-4 py-3 text-base text-slate-900"
          />

          <Button
            title="Save trade"
            loading={submitting}
            disabled={!canSubmit}
            onPress={() => {
              if (!instrument) return;
              onSubmit({
                instrument_id: instrument.id,
                type,
                quantity,
                price: price || '0',
              });
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

  const listQuery = useQuery({ queryKey: ['portfolios'], queryFn: portfoliosApi.list });
  const selected = listQuery.data?.find((p) => p.is_default) ?? listQuery.data?.[0];

  const summaryQuery = useQuery({
    queryKey: ['portfolio-summary', selected?.id],
    queryFn: () => portfoliosApi.summary(selected!.id),
    enabled: Boolean(selected),
  });

  const invalidate = () => {
    void qc.invalidateQueries({ queryKey: ['portfolio-summary', selected?.id] });
    void qc.invalidateQueries({ queryKey: ['dashboard'] });
  };

  const createPortfolio = useMutation({
    mutationFn: () => portfoliosApi.create('Main', 'USD', true),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['portfolios'] }),
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
      <SafeAreaView className="flex-1 items-center justify-center bg-slate-50">
        <ActivityIndicator color="#4f46e5" />
      </SafeAreaView>
    );
  }

  const currency = selected?.base_currency ?? 'USD';
  const totals = summaryQuery.data?.totals;

  return (
    <SafeAreaView className="flex-1 bg-slate-50">
      <View className="flex-row items-center justify-between px-4 py-3">
        <Pressable onPress={() => navigation.goBack()} accessibilityRole="button">
          <Text className="text-base text-brand-600">‹ Back</Text>
        </Pressable>
        <Text className="text-lg font-semibold text-slate-900">{selected?.name ?? 'Portfolio'}</Text>
        <Pressable
          onPress={() => selected && setTradeOpen(true)}
          disabled={!selected}
          accessibilityRole="button"
        >
          <Text className={`text-base ${selected ? 'text-brand-600' : 'text-slate-300'}`}>
            + Trade
          </Text>
        </Pressable>
      </View>

      {!selected ? (
        <View className="flex-1 items-center justify-center px-8">
          <Text className="mb-4 text-center text-slate-500">No portfolio yet.</Text>
          <Button
            title="Create portfolio"
            loading={createPortfolio.isPending}
            onPress={() => createPortfolio.mutate()}
          />
        </View>
      ) : (
        <FlatList
          data={summaryQuery.data?.positions ?? []}
          keyExtractor={(p) => p.instrument_id}
          contentContainerStyle={{ paddingHorizontal: 16, paddingBottom: 24 }}
          refreshControl={
            <RefreshControl
              refreshing={summaryQuery.isRefetching}
              onRefresh={() => void summaryQuery.refetch()}
            />
          }
          ListHeaderComponent={
            <Card className="mb-4">
              <Text className="text-sm font-medium text-slate-500">Total value</Text>
              <Text className="text-3xl font-bold text-slate-900">
                {formatCurrency(totals?.market_value ?? 0, currency)}
              </Text>
              {totals ? (
                <Text className={`mt-1 text-base font-semibold ${pnlColor(totals.unrealized_pnl)}`}>
                  {formatCurrency(totals.unrealized_pnl, currency)} ({formatPercent(totals.unrealized_pct)})
                </Text>
              ) : null}
              {totals && totals.realized_pnl !== 0 ? (
                <Text className="mt-1 text-xs text-slate-400">
                  Realized: {formatCurrency(totals.realized_pnl, currency)}
                </Text>
              ) : null}
            </Card>
          }
          ListEmptyComponent={
            <Text className="mt-10 text-center text-slate-400">
              No holdings. Tap “+ Trade” to record a buy.
            </Text>
          }
          renderItem={({ item }) => (
            <View className="mb-2 rounded-2xl border border-slate-200 bg-white p-4">
              <View className="flex-row items-center justify-between">
                <Text className="text-base font-semibold text-slate-900">{item.symbol}</Text>
                <Text className="text-base text-slate-900">
                  {formatCurrency(item.market_value, currency)}
                </Text>
              </View>
              <View className="mt-1 flex-row items-center justify-between">
                <Text className="text-sm text-slate-500">
                  {formatNumber(item.quantity)} @ {formatCurrency(item.avg_cost, currency)}
                </Text>
                <Text className={`text-sm ${pnlColor(item.unrealized_pnl)}`}>
                  {formatCurrency(item.unrealized_pnl, currency)} ({formatPercent(item.unrealized_pct)})
                </Text>
              </View>
              <Text className="mt-1 text-xs text-slate-400">
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
    </SafeAreaView>
  );
}
