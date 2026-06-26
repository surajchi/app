import { useState } from 'react';
import { Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Button } from '@/components/common/Button';
import { authApi } from '@/services/api/auth';
import { useAuthStore } from '@/store/authStore';
import type { RootScreenProps } from '@/navigation/types';

export function HomeScreen({ navigation }: RootScreenProps<'Home'>) {
  const user = useAuthStore((s) => s.user);
  const refreshToken = useAuthStore((s) => s.refreshToken);
  const logout = useAuthStore((s) => s.logout);
  const [loading, setLoading] = useState(false);

  const onLogout = async () => {
    setLoading(true);
    try {
      if (refreshToken) {
        // Best-effort server-side blacklist; local logout happens regardless.
        await authApi.logout(refreshToken).catch(() => undefined);
      }
    } finally {
      await logout();
      setLoading(false);
    }
  };

  return (
    <SafeAreaView className="flex-1 bg-white">
      <View className="flex-1 justify-center px-6">
        <Text className="text-sm uppercase tracking-wide text-slate-400">Welcome back</Text>
        <Text className="mb-2 text-3xl font-bold text-slate-900">
          {user?.full_name ?? 'Trader'}
        </Text>
        <Text className="mb-8 text-base text-slate-500">{user?.email}</Text>

        <View className="mb-8 rounded-2xl border border-slate-200 p-4">
          <Text className="text-slate-600">
            🎉 You're signed in. Markets, watchlists, news, and AI insights land in the
            upcoming phases.
          </Text>
        </View>

        <Button title="View profile" onPress={() => navigation.navigate('Profile')} />
        <View className="h-3" />
        <Button title="Log out" variant="ghost" loading={loading} onPress={onLogout} />
      </View>
    </SafeAreaView>
  );
}
