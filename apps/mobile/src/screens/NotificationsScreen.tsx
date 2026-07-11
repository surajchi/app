import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { ActivityIndicator, FlatList, Pressable, RefreshControl, Text, View } from 'react-native';
import type { BadgeVariant } from '@/components/ui';
import type { Notification } from '@finpulse/types';

import { Badge } from '@/components/ui/Badge';
import { Screen } from '@/components/ui/Screen';
import { notificationsApi } from '@/services/api/notifications';
import type { RootScreenProps } from '@/navigation/types';

function priorityVariant(priority: string): BadgeVariant {
  if (priority === 'critical') return 'danger';
  if (priority === 'high') return 'warning';
  return 'secondary';
}

function timeAgo(iso: string): string {
  const mins = Math.floor((Date.now() - new Date(iso).getTime()) / 60000);
  if (mins < 60) return `${Math.max(mins, 0)}m ago`;
  const hrs = Math.floor(mins / 60);
  return hrs < 24 ? `${hrs}h ago` : `${Math.floor(hrs / 24)}d ago`;
}

export function NotificationsScreen({ navigation }: RootScreenProps<'Notifications'>) {
  const qc = useQueryClient();
  const { data, isLoading, refetch, isRefetching } = useQuery({
    queryKey: ['notifications'],
    queryFn: () => notificationsApi.list(),
  });

  const invalidate = () => qc.invalidateQueries({ queryKey: ['notifications'] });

  const markRead = useMutation({
    mutationFn: (ids: string[]) => notificationsApi.markRead(ids),
    onSuccess: invalidate,
  });
  const markAll = useMutation({ mutationFn: () => notificationsApi.markAll(), onSuccess: invalidate });

  const unread = (data ?? []).filter((n) => !n.read_at).length;

  return (
    <Screen>
      <View className="flex-row items-center justify-between px-4 py-3">
        <Pressable onPress={() => navigation.goBack()} accessibilityRole="button">
          <Text className="text-base text-slate-300">‹ Back</Text>
        </Pressable>
        <Text className="text-lg font-semibold text-slate-50">
          Notifications{unread > 0 ? ` (${unread})` : ''}
        </Text>
        <Pressable
          onPress={() => unread > 0 && markAll.mutate()}
          disabled={unread === 0}
          accessibilityRole="button"
        >
          <Text className={`text-sm ${unread > 0 ? 'text-emerald-400' : 'text-slate-600'}`}>
            Read all
          </Text>
        </Pressable>
      </View>

      {isLoading ? (
        <ActivityIndicator className="mt-10" color="#34d399" />
      ) : (
        <FlatList
          data={data ?? []}
          keyExtractor={(n) => n.id}
          contentContainerStyle={{ padding: 16, paddingTop: 8 }}
          refreshControl={
            <RefreshControl tintColor="#34d399" refreshing={isRefetching} onRefresh={() => void refetch()} />
          }
          ListEmptyComponent={
            <Text className="mt-10 text-center text-slate-500">No notifications yet.</Text>
          }
          renderItem={({ item }: { item: Notification }) => {
            const isUnread = !item.read_at;
            return (
              <Pressable
                onPress={() => isUnread && markRead.mutate([item.id])}
                className={`mb-2 rounded-2xl border p-4 ${
                  isUnread ? 'border-emerald-500/30 bg-slate-900' : 'border-slate-800 bg-slate-950'
                }`}
              >
                <View className="mb-1 flex-row items-center justify-between">
                  <View className="flex-row items-center">
                    {isUnread ? <View className="mr-2 h-2 w-2 rounded-full bg-emerald-400" /> : null}
                    <Badge label={item.type} variant={priorityVariant(item.priority)} />
                  </View>
                  <Text className="text-xs text-slate-500">{timeAgo(item.created_at)}</Text>
                </View>
                <Text className="text-sm font-semibold text-slate-100">{item.title}</Text>
                {item.body ? (
                  <Text className="mt-0.5 text-sm text-slate-400" numberOfLines={3}>
                    {item.body}
                  </Text>
                ) : null}
              </Pressable>
            );
          }}
        />
      )}
    </Screen>
  );
}
