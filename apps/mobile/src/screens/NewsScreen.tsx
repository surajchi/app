import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import {
  ActivityIndicator,
  FlatList,
  Linking,
  Pressable,
  ScrollView,
  Text,
  View,
} from 'react-native';
import type { BadgeVariant } from '@/components/ui';
import type { EconomicEvent, SentimentLabel } from '@finpulse/types';

import { Badge } from '@/components/ui/Badge';
import { Card } from '@/components/ui/Card';
import { Screen } from '@/components/ui/Screen';
import { SegmentedControl } from '@/components/ui/SegmentedControl';
import { calendarApi } from '@/services/api/calendar';
import { newsApi } from '@/services/api/news';
import type { RootScreenProps } from '@/navigation/types';

const TABS = [
  { label: 'News', value: 'news' },
  { label: 'This week', value: 'calendar' },
];

function impactDot(score: number): string {
  if (score >= 70) return 'bg-rose-500';
  if (score >= 40) return 'bg-amber-500';
  return 'bg-yellow-400';
}

function importanceDot(importance: string): string {
  if (importance === 'high') return 'bg-rose-500';
  if (importance === 'medium') return 'bg-amber-500';
  return 'bg-slate-500';
}

function sentimentVariant(label: SentimentLabel | undefined): BadgeVariant {
  if (label === 'positive') return 'success';
  if (label === 'negative') return 'danger';
  return 'secondary';
}

function timeAgo(iso: string): string {
  const mins = Math.floor((Date.now() - new Date(iso).getTime()) / 60000);
  if (mins < 60) return `${Math.max(mins, 0)}m ago`;
  const hrs = Math.floor(mins / 60);
  return hrs < 24 ? `${hrs}h ago` : `${Math.floor(hrs / 24)}d ago`;
}

function clock(iso: string): string {
  return new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function NewsTab() {
  const [category, setCategory] = useState('');
  const categoriesQuery = useQuery({ queryKey: ['news-categories'], queryFn: newsApi.categories });
  const feedQuery = useQuery({
    queryKey: ['news-feed', category],
    queryFn: () => newsApi.feed(category ? { category } : {}),
  });

  const options = [
    { label: 'All', value: '' },
    ...(categoriesQuery.data ?? []).map((c) => ({ label: c.name, value: c.slug })),
  ];

  return (
    <>
      <View className="px-4 pb-2">
        <SegmentedControl options={options} value={category} onChange={setCategory} scroll />
      </View>
      {feedQuery.isLoading ? (
        <ActivityIndicator className="mt-10" color="#34d399" />
      ) : (
        <FlatList
          data={feedQuery.data ?? []}
          keyExtractor={(a) => a.id}
          contentContainerStyle={{ padding: 16, paddingTop: 8 }}
          ListEmptyComponent={
            <Text className="mt-10 text-center text-slate-500">No news yet.</Text>
          }
          renderItem={({ item }) => (
            <Card
              className="mb-2"
              onPress={() => item.source_url && Linking.openURL(item.source_url)}
            >
              <View className="flex-row items-start">
                <View className={`mt-1.5 mr-3 h-2.5 w-2.5 rounded-full ${impactDot(item.impact_score)}`} />
                <View className="flex-1">
                  <Text className="text-sm font-medium text-slate-100" numberOfLines={3}>
                    {item.is_breaking ? '🔴 ' : ''}
                    {item.title}
                  </Text>
                  <View className="mt-1.5 flex-row items-center">
                    <Text className="text-xs text-slate-500">
                      {item.source} · {timeAgo(item.published_at)}
                    </Text>
                    {item.sentiment ? (
                      <Badge
                        className="ml-2"
                        label={item.sentiment.label}
                        variant={sentimentVariant(item.sentiment.label)}
                      />
                    ) : null}
                  </View>
                </View>
              </View>
            </Card>
          )}
        />
      )}
    </>
  );
}

function CalendarTab() {
  const { data, isLoading } = useQuery({ queryKey: ['calendar-week'], queryFn: () => calendarApi.week() });

  if (isLoading) {
    return <ActivityIndicator className="mt-10" color="#34d399" />;
  }

  const events = data?.events ?? [];
  const byDay = new Map<string, EconomicEvent[]>();
  for (const e of events) {
    const key = new Date(e.event_time).toDateString();
    const list = byDay.get(key) ?? [];
    list.push(e);
    byDay.set(key, list);
  }
  const days = [...byDay.entries()];

  return (
    <ScrollView contentContainerStyle={{ padding: 16, paddingTop: 8 }}>
      {days.length === 0 ? (
        <Text className="mt-10 text-center text-slate-500">No events scheduled this week.</Text>
      ) : (
        days.map(([day, list]) => (
          <View key={day} className="mb-4">
            <Text className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
              {day}
            </Text>
            {list.map((e) => (
              <View
                key={e.id}
                className="mb-1 flex-row items-center rounded-xl border border-slate-800 bg-slate-900 px-3 py-2.5"
              >
                <Text className="w-14 text-xs text-slate-400">{clock(e.event_time)}</Text>
                <View className={`mx-2 h-2 w-2 rounded-full ${importanceDot(e.importance)}`} />
                <Badge label={e.currency} variant="secondary" />
                <View className="ml-2 flex-1">
                  <Text className="text-sm text-slate-100" numberOfLines={1}>
                    {e.title}
                  </Text>
                  <Text className="text-xs text-slate-500">
                    A: {e.actual || '—'} · F: {e.forecast || '—'} · P: {e.previous || '—'}
                  </Text>
                </View>
              </View>
            ))}
          </View>
        ))
      )}
    </ScrollView>
  );
}

export function NewsScreen({ navigation }: RootScreenProps<'News'>) {
  const [tab, setTab] = useState('news');
  return (
    <Screen>
      <View className="flex-row items-center justify-between px-4 py-3">
        <Pressable onPress={() => navigation.goBack()} accessibilityRole="button">
          <Text className="text-base text-slate-300">‹ Back</Text>
        </Pressable>
        <Text className="text-lg font-semibold text-slate-50">Markets News</Text>
        <View className="w-10" />
      </View>
      <View className="px-4 pb-2">
        <SegmentedControl options={TABS} value={tab} onChange={setTab} />
      </View>
      {tab === 'news' ? <NewsTab /> : <CalendarTab />}
    </Screen>
  );
}
