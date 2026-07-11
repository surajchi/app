import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import { ActivityIndicator, Pressable, Text, TextInput, View } from 'react-native';

import { BottomNav } from '@/components/BottomNav';
import { Card } from '@/components/ui/Card';
import { Screen } from '@/components/ui/Screen';
import { SegmentedControl } from '@/components/ui/SegmentedControl';
import { marketsApi } from '@/services/api/markets';
import type { RootScreenProps } from '@/navigation/types';

const CCYS = [
  { label: 'USD', value: 'USD' },
  { label: 'EUR', value: 'EUR' },
  { label: 'INR', value: 'INR' },
];

export function ConverterScreen({ navigation }: RootScreenProps<'Converter'>) {
  const [amount, setAmount] = useState('100');
  const [from, setFrom] = useState('USD');
  const [to, setTo] = useState('EUR');

  const { data, isLoading } = useQuery({
    queryKey: ['fx'],
    queryFn: () => marketsApi.listInstruments({ assetClass: 'forex' }),
  });

  const price = (sym: string) => data?.find((i) => i.symbol === sym)?.quote?.price;
  const eurusd = price('EURUSD');
  const usdinr = price('USDINR');

  // USD per 1 unit of currency.
  const usdPer: Record<string, number | undefined> = {
    USD: 1,
    EUR: eurusd,
    INR: usdinr ? 1 / usdinr : undefined,
  };

  const fromRate = usdPer[from];
  const toRate = usdPer[to];
  const n = Number(amount);
  const result =
    Number.isFinite(n) && fromRate && toRate ? (n * fromRate) / toRate : null;

  const swap = () => {
    setFrom(to);
    setTo(from);
  };

  return (
    <Screen>
      <View className="flex-row items-center justify-between px-4 py-3">
        <Pressable onPress={() => navigation.goBack()} accessibilityRole="button">
          <Text className="text-base text-slate-300">‹ Back</Text>
        </Pressable>
        <Text className="text-lg font-semibold text-slate-50">Currency converter</Text>
        <View className="w-10" />
      </View>

      {isLoading ? (
        <ActivityIndicator className="mt-10" color="#34d399" />
      ) : (
        <View className="px-4">
          <Card className="mb-4">
            <Text className="mb-1 text-sm font-medium text-slate-400">Amount</Text>
            <TextInput
              value={amount}
              onChangeText={setAmount}
              keyboardType="decimal-pad"
              placeholder="0"
              placeholderTextColor="#64748b"
              className="mb-4 rounded-xl border border-slate-800 bg-slate-950 px-4 py-3 text-lg text-slate-50"
            />

            <Text className="mb-1 text-xs font-medium text-slate-500">From</Text>
            <SegmentedControl options={CCYS} value={from} onChange={setFrom} />

            <Pressable onPress={swap} className="my-2 items-center py-1">
              <Text className="text-lg text-emerald-400">⇅</Text>
            </Pressable>

            <Text className="mb-1 text-xs font-medium text-slate-500">To</Text>
            <SegmentedControl options={CCYS} value={to} onChange={setTo} />
          </Card>

          <Card>
            <Text className="text-sm font-medium text-slate-400">Result</Text>
            <Text className="mt-1 text-3xl font-bold text-slate-50">
              {result !== null
                ? `${result.toLocaleString(undefined, { maximumFractionDigits: 2 })} ${to}`
                : '—'}
            </Text>
            {fromRate && toRate ? (
              <Text className="mt-1 text-xs text-slate-500">
                1 {from} = {(fromRate / toRate).toFixed(4)} {to} · live rate
              </Text>
            ) : (
              <Text className="mt-1 text-xs text-amber-400">Rate unavailable.</Text>
            )}
          </Card>
        </View>
      )}
      <BottomNav active="" />
    </Screen>
  );
}
