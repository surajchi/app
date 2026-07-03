import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { useEffect } from 'react';
import { ActivityIndicator, View } from 'react-native';

import { AlertsScreen } from '@/screens/AlertsScreen';
import { HomeScreen } from '@/screens/HomeScreen';
import { InstrumentDetailScreen } from '@/screens/InstrumentDetailScreen';
import { LoginScreen } from '@/screens/LoginScreen';
import { MarketsScreen } from '@/screens/MarketsScreen';
import { NewsScreen } from '@/screens/NewsScreen';
import { PortfolioScreen } from '@/screens/PortfolioScreen';
import { ProfileScreen } from '@/screens/ProfileScreen';
import { RegisterScreen } from '@/screens/RegisterScreen';
import { WatchlistScreen } from '@/screens/WatchlistScreen';
import { useAuthStore } from '@/store/authStore';
import type { RootStackParamList } from './types';

const Stack = createNativeStackNavigator<RootStackParamList>();

export function RootNavigator() {
  const user = useAuthStore((s) => s.user);
  const hydrated = useAuthStore((s) => s.hydrated);
  const hydrate = useAuthStore((s) => s.hydrate);

  useEffect(() => {
    void hydrate();
  }, [hydrate]);

  if (!hydrated) {
    return (
      <View className="flex-1 items-center justify-center bg-white">
        <ActivityIndicator color="#4f46e5" />
      </View>
    );
  }

  return (
    <NavigationContainer>
      <Stack.Navigator screenOptions={{ headerShown: false }}>
        {user ? (
          <>
            <Stack.Screen name="Home" component={HomeScreen} />
            <Stack.Screen name="Watchlist" component={WatchlistScreen} />
            <Stack.Screen name="Portfolio" component={PortfolioScreen} />
            <Stack.Screen name="Alerts" component={AlertsScreen} />
            <Stack.Screen name="Markets" component={MarketsScreen} />
            <Stack.Screen name="News" component={NewsScreen} />
            <Stack.Screen name="InstrumentDetail" component={InstrumentDetailScreen} />
            <Stack.Screen
              name="Profile"
              component={ProfileScreen}
              options={{ headerShown: true, title: 'Profile' }}
            />
          </>
        ) : (
          <>
            <Stack.Screen name="Login" component={LoginScreen} />
            <Stack.Screen name="Register" component={RegisterScreen} />
          </>
        )}
      </Stack.Navigator>
    </NavigationContainer>
  );
}
