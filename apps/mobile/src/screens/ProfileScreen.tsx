import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useEffect, useState } from 'react';
import { ActivityIndicator, ScrollView, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Button } from '@/components/common/Button';
import { TextField } from '@/components/common/TextField';
import { profileApi } from '@/services/api/profile';
import { usersApi } from '@/services/api/users';
import { extractErrorMessage } from '@/services/api/errors';

export function ProfileScreen() {
  const queryClient = useQueryClient();

  const meQuery = useQuery({ queryKey: ['me'], queryFn: usersApi.me });
  const profileQuery = useQuery({ queryKey: ['profile'], queryFn: profileApi.get });

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
      <View className="flex-1 items-center justify-center bg-white">
        <ActivityIndicator color="#4f46e5" />
      </View>
    );
  }

  const me = meQuery.data;

  return (
    <SafeAreaView className="flex-1 bg-white" edges={['bottom']}>
      <ScrollView contentContainerStyle={{ padding: 24 }}>
        <Text className="mb-1 text-sm uppercase tracking-wide text-slate-400">Account</Text>
        <Text className="mb-4 text-2xl font-bold text-slate-900">{me?.email}</Text>

        <View className="mb-6 flex-row flex-wrap gap-2">
          {(me?.roles ?? []).map((role) => (
            <View key={role} className="rounded-full bg-indigo-100 px-3 py-1">
              <Text className="text-xs font-semibold text-brand-600">{role}</Text>
            </View>
          ))}
        </View>

        <TextField label="Full name" value={fullName} onChangeText={setFullName} />
        <TextField
          label="Base currency"
          autoCapitalize="characters"
          maxLength={3}
          value={baseCurrency}
          onChangeText={setBaseCurrency}
        />

        {message ? <Text className="mb-3 text-sm text-green-600">{message}</Text> : null}
        {error ? <Text className="mb-3 text-sm text-red-500">{error}</Text> : null}

        <Button title="Save changes" loading={save.isPending} onPress={() => save.mutate()} />

        <View className="mt-8 rounded-2xl border border-slate-200 p-4">
          <Text className="mb-1 text-xs uppercase text-slate-400">Preferences</Text>
          <Text className="text-slate-600">
            Language: {profileQuery.data?.language} · Risk: {profileQuery.data?.risk_appetite} ·
            Experience: {profileQuery.data?.experience_level}
          </Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}
