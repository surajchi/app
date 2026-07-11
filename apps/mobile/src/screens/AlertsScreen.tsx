import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import {
  ActivityIndicator,
  Alert as RNAlert,
  Modal,
  Pressable,
  ScrollView,
  Switch,
  Text,
  TextInput,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import type { AlertTriggerType, Instrument, NewAlertRule } from '@finpulse/types';

import { InstrumentPicker } from '@/components/InstrumentPicker';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Screen } from '@/components/ui/Screen';
import { alertsApi } from '@/services/api/alerts';
import type { RootScreenProps } from '@/navigation/types';

const PRICE_TRIGGERS: { key: AlertTriggerType; label: string }[] = [
  { key: 'price_above', label: 'Price above' },
  { key: 'price_below', label: 'Price below' },
  { key: 'pct_change', label: '% change' },
];

interface CreateModalProps {
  visible: boolean;
  submitting: boolean;
  onClose: () => void;
  onSubmit: (rule: NewAlertRule) => void;
}

function CreateAlertModal({ visible, submitting, onClose, onSubmit }: CreateModalProps) {
  const [instrument, setInstrument] = useState<Instrument | null>(null);
  const [trigger, setTrigger] = useState<AlertTriggerType>('price_above');
  const [value, setValue] = useState('');
  const [pickerOpen, setPickerOpen] = useState(false);

  const canSubmit = instrument && Number(value) > 0;

  return (
    <Modal visible={visible} animationType="slide" onRequestClose={onClose}>
      <SafeAreaView className="flex-1 bg-slate-950">
        <View className="flex-row items-center justify-between border-b border-slate-800 px-4 py-3">
          <Text className="text-lg font-semibold text-slate-50">New price alert</Text>
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

          <Text className="mb-1 text-sm font-medium text-slate-400">Condition</Text>
          <View className="mb-4 flex-row">
            {PRICE_TRIGGERS.map((t) => (
              <Pressable
                key={t.key}
                onPress={() => setTrigger(t.key)}
                className={`mr-2 flex-1 items-center rounded-xl border py-3 ${
                  trigger === t.key ? 'border-emerald-500 bg-emerald-500' : 'border-slate-800'
                }`}
              >
                <Text
                  className={`text-xs ${trigger === t.key ? 'font-semibold text-slate-950' : 'text-slate-300'}`}
                >
                  {t.label}
                </Text>
              </Pressable>
            ))}
          </View>

          <Text className="mb-1 text-sm font-medium text-slate-400">
            {trigger === 'pct_change' ? 'Percent (%)' : 'Threshold price'}
          </Text>
          <TextInput
            value={value}
            onChangeText={setValue}
            keyboardType="decimal-pad"
            placeholder="0"
            placeholderTextColor="#64748b"
            className="mb-6 rounded-xl border border-slate-800 bg-slate-900 px-4 py-3 text-base text-slate-100"
          />

          <Button
            title="Create alert"
            loading={submitting}
            disabled={!canSubmit}
            onPress={() => {
              if (!instrument) return;
              onSubmit({
                name: `${instrument.symbol} ${trigger.replace('_', ' ')} ${value}`,
                instrument: instrument.id,
                trigger_type: trigger,
                condition: { value: Number(value) },
              });
              setInstrument(null);
              setValue('');
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

export function AlertsScreen({ navigation }: RootScreenProps<'Alerts'>) {
  const qc = useQueryClient();
  const [createOpen, setCreateOpen] = useState(false);

  const rulesQuery = useQuery({ queryKey: ['alert-rules'], queryFn: alertsApi.listRules });
  const historyQuery = useQuery({ queryKey: ['alert-history'], queryFn: alertsApi.history });

  const invalidateRules = () => qc.invalidateQueries({ queryKey: ['alert-rules'] });

  const createRule = useMutation({
    mutationFn: (rule: NewAlertRule) => alertsApi.createRule(rule),
    onSuccess: () => {
      void invalidateRules();
      setCreateOpen(false);
    },
    onError: () => RNAlert.alert('Could not create alert', 'Please check the values and try again.'),
  });

  const toggleRule = useMutation({
    mutationFn: ({ id, isActive }: { id: string; isActive: boolean }) =>
      alertsApi.updateRule(id, { is_active: isActive }),
    onSuccess: invalidateRules,
  });

  const deleteRule = useMutation({
    mutationFn: (id: string) => alertsApi.deleteRule(id),
    onSuccess: invalidateRules,
  });

  return (
    <Screen>
      <View className="flex-row items-center justify-between px-4 py-3">
        <Pressable onPress={() => navigation.goBack()} accessibilityRole="button">
          <Text className="text-base text-slate-300">‹ Back</Text>
        </Pressable>
        <Text className="text-lg font-semibold text-slate-50">Alerts</Text>
        <Pressable onPress={() => setCreateOpen(true)} accessibilityRole="button">
          <Text className="text-base text-emerald-400">+ New</Text>
        </Pressable>
      </View>

      <ScrollView contentContainerStyle={{ padding: 16 }}>
        <Text className="mb-2 text-sm font-semibold uppercase tracking-wide text-slate-500">
          Rules
        </Text>
        {rulesQuery.isLoading ? (
          <ActivityIndicator color="#34d399" />
        ) : (rulesQuery.data ?? []).length === 0 ? (
          <Text className="mb-4 text-slate-500">No alert rules yet. Tap “+ New”.</Text>
        ) : (
          rulesQuery.data!.map((rule) => (
            <Card key={rule.id} className="mb-2">
              <View className="flex-row items-center justify-between">
                <View className="flex-1 pr-3">
                  <Text className="text-base font-semibold text-slate-50">{rule.name}</Text>
                  <Text className="text-xs text-slate-500">
                    {rule.trigger_type} · {rule.frequency}
                    {rule.last_triggered_at ? ' · fired' : ''}
                  </Text>
                </View>
                <Switch
                  value={rule.is_active}
                  onValueChange={(v) => toggleRule.mutate({ id: rule.id, isActive: v })}
                />
                <Pressable
                  accessibilityRole="button"
                  onPress={() =>
                    RNAlert.alert('Delete alert', `Remove “${rule.name}”?`, [
                      { text: 'Cancel', style: 'cancel' },
                      {
                        text: 'Delete',
                        style: 'destructive',
                        onPress: () => deleteRule.mutate(rule.id),
                      },
                    ])
                  }
                  className="ml-3 h-8 w-8 items-center justify-center rounded-full bg-slate-800 active:bg-slate-700"
                >
                  <Text className="text-slate-400">✕</Text>
                </Pressable>
              </View>
            </Card>
          ))
        )}

        <Text className="mb-2 mt-6 text-sm font-semibold uppercase tracking-wide text-slate-500">
          History
        </Text>
        {(historyQuery.data ?? []).length === 0 ? (
          <Text className="text-slate-500">Nothing triggered yet.</Text>
        ) : (
          historyQuery.data!.map((fired) => (
            <View key={fired.id} className="mb-2 rounded-xl border border-slate-800 bg-slate-900 p-3">
              <Text className="text-sm font-medium text-slate-100">{fired.rule_name}</Text>
              <Text className="text-xs text-slate-500">
                {fired.trigger_type} · {new Date(fired.triggered_at).toLocaleString()}
              </Text>
            </View>
          ))
        )}
      </ScrollView>

      <CreateAlertModal
        visible={createOpen}
        submitting={createRule.isPending}
        onClose={() => setCreateOpen(false)}
        onSubmit={(rule) => createRule.mutate(rule)}
      />
    </Screen>
  );
}
