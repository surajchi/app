import { useNavigation } from '@react-navigation/native';
import type { NavigationProp } from '@react-navigation/native';
import { Pressable, Text, View } from 'react-native';

import type { RootStackParamList } from '@/navigation/types';

type Tab = { key: string; label: string; icon: string; route: keyof RootStackParamList };

const TABS: Tab[] = [
  { key: 'home', label: 'Home', icon: '🏠', route: 'Home' },
  { key: 'markets', label: 'Markets', icon: '📈', route: 'Markets' },
  { key: 'news', label: 'News', icon: '📰', route: 'News' },
  { key: 'portfolio', label: 'Portfolio', icon: '💼', route: 'Portfolio' },
  { key: 'profile', label: 'Profile', icon: '👤', route: 'Profile' },
];

/** App-style bottom tab bar. Pass the active tab key. */
export function BottomNav({ active }: { active: string }) {
  const navigation = useNavigation<NavigationProp<RootStackParamList>>();

  return (
    <View className="flex-row border-t border-slate-800 bg-slate-950 pb-1 pt-1.5">
      {TABS.map((tab) => {
        const isActive = tab.key === active;
        return (
          <Pressable
            key={tab.key}
            accessibilityRole="button"
            onPress={() => {
              if (!isActive) navigation.navigate(tab.route as never);
            }}
            className="flex-1 items-center py-1 active:opacity-70"
          >
            <Text className="text-lg">{tab.icon}</Text>
            <Text
              className={`mt-0.5 text-[11px] ${
                isActive ? 'font-semibold text-emerald-400' : 'text-slate-500'
              }`}
            >
              {tab.label}
            </Text>
          </Pressable>
        );
      })}
    </View>
  );
}
