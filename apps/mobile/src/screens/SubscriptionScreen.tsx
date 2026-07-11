import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { ActivityIndicator, Alert, Pressable, ScrollView, Text, View } from 'react-native';
import type { AxiosError } from 'axios';
import type { Plan } from '@finpulse/types';

import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Screen } from '@/components/ui/Screen';
import { billingApi } from '@/services/api/billing';
import type { RootScreenProps } from '@/navigation/types';

const FEATURE_LABELS: { key: string; label: string }[] = [
  { key: 'max_watchlists', label: 'Watchlists' },
  { key: 'max_watchlist_items', label: 'Watchlist items' },
  { key: 'max_alerts', label: 'Alerts' },
  { key: 'ai_requests_per_day', label: 'AI requests/day' },
];

export function SubscriptionScreen({ navigation }: RootScreenProps<'Subscription'>) {
  const qc = useQueryClient();
  const plansQuery = useQuery({ queryKey: ['plans'], queryFn: billingApi.plans });
  const subQuery = useQuery({ queryKey: ['subscription'], queryFn: billingApi.subscription });

  const invalidate = () => {
    void qc.invalidateQueries({ queryKey: ['subscription'] });
    void qc.invalidateQueries({ queryKey: ['dashboard'] });
  };

  const subscribe = useMutation({
    mutationFn: (code: string) => billingApi.subscribe(code),
    onSuccess: invalidate,
    onError: (err: AxiosError<{ error?: { message?: string } }>) =>
      Alert.alert('Could not subscribe', err.response?.data?.error?.message ?? 'Try again.'),
  });

  const cancel = useMutation({
    mutationFn: () => billingApi.cancel(true),
    onSuccess: invalidate,
  });

  const currentPlan = subQuery.data?.entitlements.plan ?? 'free';
  const status = subQuery.data?.entitlements.status ?? 'none';
  const cancelAtEnd = subQuery.data?.entitlements.cancel_at_period_end;

  return (
    <Screen>
      <View className="flex-row items-center justify-between px-4 py-3">
        <Pressable onPress={() => navigation.goBack()} accessibilityRole="button">
          <Text className="text-base text-slate-300">‹ Back</Text>
        </Pressable>
        <Text className="text-lg font-semibold text-slate-50">Subscription</Text>
        <View className="w-10" />
      </View>

      {plansQuery.isLoading ? (
        <ActivityIndicator className="mt-10" color="#34d399" />
      ) : (
        <ScrollView contentContainerStyle={{ padding: 16, paddingTop: 8 }}>
          <Card className="mb-4">
            <Text className="text-sm font-medium text-slate-400">Current plan</Text>
            <View className="mt-1 flex-row items-center">
              <Text className="text-2xl font-bold uppercase text-slate-50">{currentPlan}</Text>
              <Badge
                className="ml-2"
                label={status}
                variant={status === 'active' || status === 'trialing' ? 'success' : 'secondary'}
              />
            </View>
            {cancelAtEnd ? (
              <Text className="mt-1 text-xs text-amber-400">Cancels at period end.</Text>
            ) : null}
            {currentPlan !== 'free' && status !== 'none' ? (
              <Pressable className="mt-3" onPress={() => cancel.mutate()}>
                <Text className="text-sm text-rose-400">
                  {cancel.isPending ? 'Cancelling…' : 'Cancel subscription'}
                </Text>
              </Pressable>
            ) : null}
          </Card>

          {(plansQuery.data ?? []).map((plan: Plan) => {
            const isCurrent = plan.code === currentPlan;
            return (
              <Card key={plan.id} className="mb-3">
                <View className="flex-row items-center justify-between">
                  <View>
                    <Text className="text-lg font-bold text-slate-50">{plan.name}</Text>
                    <Text className="text-sm text-slate-400">{plan.description}</Text>
                  </View>
                  <View className="items-end">
                    <Text className="text-xl font-bold text-slate-50">
                      {plan.price_cents === 0 ? 'Free' : `$${plan.price}`}
                    </Text>
                    {plan.price_cents > 0 ? (
                      <Text className="text-xs text-slate-500">/{plan.interval}</Text>
                    ) : null}
                  </View>
                </View>

                <View className="mt-3">
                  {FEATURE_LABELS.map((f) => (
                    <View key={f.key} className="flex-row justify-between py-0.5">
                      <Text className="text-xs text-slate-400">{f.label}</Text>
                      <Text className="text-xs font-medium text-slate-200">
                        {String(plan.features[f.key] ?? '—')}
                      </Text>
                    </View>
                  ))}
                  <View className="flex-row justify-between py-0.5">
                    <Text className="text-xs text-slate-400">Realtime</Text>
                    <Text className="text-xs font-medium text-slate-200">
                      {plan.features.realtime ? 'Yes' : 'No'}
                    </Text>
                  </View>
                </View>

                <View className="mt-3">
                  {isCurrent ? (
                    <Badge label="Current plan" variant="success" />
                  ) : (
                    <Button
                      title={plan.price_cents === 0 ? 'Switch to Free' : `Subscribe · $${plan.price}`}
                      loading={subscribe.isPending && subscribe.variables === plan.code}
                      onPress={() => subscribe.mutate(plan.code)}
                    />
                  )}
                </View>
              </Card>
            );
          })}

          <Text className="mt-2 text-center text-xs text-slate-600">
            Mock payments — no real charge.
          </Text>
        </ScrollView>
      )}
    </Screen>
  );
}
