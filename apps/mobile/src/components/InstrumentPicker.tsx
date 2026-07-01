import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import {
  ActivityIndicator,
  FlatList,
  Modal,
  Pressable,
  Text,
  TextInput,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import type { Instrument } from '@finpulse/types';

import { marketsApi } from '@/services/api/markets';

interface InstrumentPickerProps {
  visible: boolean;
  onClose: () => void;
  onSelect: (instrument: Instrument) => void;
}

export function InstrumentPicker({ visible, onClose, onSelect }: InstrumentPickerProps) {
  const [query, setQuery] = useState('');

  const { data, isLoading } = useQuery({
    queryKey: ['instruments', query],
    queryFn: () => marketsApi.searchInstruments(query),
    enabled: visible,
  });

  return (
    <Modal visible={visible} animationType="slide" onRequestClose={onClose}>
      <SafeAreaView className="flex-1 bg-white">
        <View className="flex-row items-center justify-between border-b border-slate-100 px-4 py-3">
          <Text className="text-lg font-semibold text-slate-900">Select instrument</Text>
          <Pressable onPress={onClose} accessibilityRole="button">
            <Text className="text-base font-medium text-brand-600">Close</Text>
          </Pressable>
        </View>

        <View className="px-4 py-3">
          <TextInput
            value={query}
            onChangeText={setQuery}
            placeholder="Search symbol or name…"
            autoCapitalize="characters"
            autoCorrect={false}
            className="rounded-xl border border-slate-200 px-4 py-3 text-base text-slate-900"
          />
        </View>

        {isLoading ? (
          <ActivityIndicator className="mt-6" color="#4f46e5" />
        ) : (
          <FlatList
            data={data ?? []}
            keyExtractor={(item) => item.id}
            contentContainerStyle={{ paddingHorizontal: 16 }}
            ListEmptyComponent={
              <Text className="mt-6 text-center text-slate-400">No instruments found.</Text>
            }
            renderItem={({ item }) => (
              <Pressable
                accessibilityRole="button"
                onPress={() => {
                  onSelect(item);
                  onClose();
                }}
                className="border-b border-slate-100 py-3 active:bg-slate-50"
              >
                <Text className="text-base font-semibold text-slate-900">{item.symbol}</Text>
                <Text className="text-sm text-slate-500">
                  {item.name} · {item.asset_class}
                </Text>
              </Pressable>
            )}
          />
        )}
      </SafeAreaView>
    </Modal>
  );
}
