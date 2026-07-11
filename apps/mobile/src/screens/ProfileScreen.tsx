import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useEffect, useState } from 'react';
import { ActivityIndicator, ScrollView, Text, View } from 'react-native';

import { BottomNav } from '@/components/BottomNav';
import { TextField } from '@/components/common/TextField';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Screen } from '@/components/ui/Screen';
import { billingApi } from '@/services/api/billing';
import { extractErrorMessage } from '@/services/api/errors';
import { profileApi } from '@/services/api/profile';
import { usersApi } from '@/services/api/users';
import type { RootScreenProps } from '@/navigation/types';

export function ProfileScreen({ navigation }: RootScreenProps<'Profile'>) {
  const queryClient = useQueryClient();

  const meQuery = useQuery({ queryKey: ['me'], queryFn: usersApi.me });
  const profileQuery = useQuery({ queryKey: ['profile'], queryFn: profileApi.get });
  const subQuery = useQuery({ queryKey: ['subscription'], queryFn: billingApi.subscription });

  const [fullName, setFullName] = useState('');
  const [baseCurrency, setBaseCurrency] = useState('');
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (meQuery.data) setFullName(meQuery.data.full_name);
  }, [meQuery.data]);
  useEffect(() => {
    if (profileQuery.data) setBaseCurrency(profileQuery.data.base_currency);
  }, [profileQuery.data]);

  const save = useMutation({
    mutationFn: async () => {
      await usersApi.updateMe({ full_name: fullName });
      await profileApi.update({ base_currency: baseCurrency });
    },
    onSuccess: async () => {
      setError(null);
      setMessage('Saved.');
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['me'] }),
        queryClient.invalidateQueries({ queryKey: ['profile'] }),
      ]);
    },
    onError: (e) => {
      setMessage(null);
      setError(extractErrorMessage(e));
    },
  });

  if (meQuery.isLoading || profileQuery.isLoading) {
    return (
      <Screen className="items-center justify-center">
        <ActivityIndicator color="#34d399" />
      </Screen>
    );
  }

  const me = meQuery.data;
  const plan = subQuery.data?.entitlements.plan ?? 'free';

  return (
    <Screen>
      <ScrollView contentContainerStyle={{ padding: 24 }}>
        <Text className="mb-1 text-sm uppercase tracking-wide text-slate-500">Account</Text>
        <Text className="mb-4 text-2xl font-bold text-slate-50">{me?.email}</Text>

        <View className="mb-6 flex-row flex-wrap gap-2">
          {(me?.roles ?? []).map((role) => (
            <View key={role} className="rounded-full bg-emerald-500/15 px-3 py-1">
              <Text className="text-xs font-semibold text-emerald-400">{role}</Text>
            </View>
          ))}
        </View>

        <Card className="mb-6" onPress={() => navigation.navigate('Subscription')}>
          <View className="flex-row items-center justify-between">
            <View>
              <Text className="text-xs uppercase text-slate-500">Plan</Text>
              <Text className="text-lg font-bold uppercase text-slate-50">{plan}</Text>
            </View>
            <Text className="text-sm text-emerald-400">Manage ›</Text>
          </View>
        </Card>

        <TextField label="Full name" value={fullName} onChangeText={setFullName} />
        <TextField
          label="Base currency"
          autoCapitalize="characters"
          maxLength={3}
          value={baseCurrency}
          onChangeText={setBaseCurrency}
        />

        {message ? <Text className="mb-3 text-sm text-emerald-400">{message}</Text> : null}
        {error ? <Text className="mb-3 text-sm text-rose-400">{error}</Text> : null}

        <Button title="Save changes" loading={save.isPending} onPress={() => save.mutate()} />

        <View className="mt-8 rounded-2xl border border-slate-800 bg-slate-900 p-4">
          <Text className="mb-1 text-xs uppercase text-slate-500">Preferences</Text>
          <Text className="text-slate-300">
            Language: {profileQuery.data?.language} · Risk: {profileQuery.data?.risk_appetite} ·
            Experience: {profileQuery.data?.experience_level}
          </Text>
        </View>
      </ScrollView>
      <BottomNav active="profile" />
    </Screen>
  );
}
