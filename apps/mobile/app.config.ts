import type { ExpoConfig } from 'expo/config';

const config: ExpoConfig = {
  name: 'FinPulse',
  slug: 'finpulse',
  scheme: 'finpulse',
  version: '0.1.0',
  orientation: 'portrait',
  userInterfaceStyle: 'automatic',
  newArchEnabled: true,
  assetBundlePatterns: ['**/*'],
  ios: {
    supportsTablet: true,
    bundleIdentifier: 'app.finpulse.mobile',
  },
  android: {
    package: 'app.finpulse.mobile',
  },
  web: {
    bundler: 'metro',
    output: 'single',
  },
  plugins: ['expo-secure-store'],
  experiments: {
    tsconfigPaths: true,
  },
};

export default config;
