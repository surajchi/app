import type { PropsWithChildren } from 'react';
import { SafeAreaView } from 'react-native-safe-area-context';

/** Dark app-shell background (shadcn-style neutral surface). */
export function Screen({ children, className = '' }: PropsWithChildren<{ className?: string }>) {
  return <SafeAreaView className={`flex-1 bg-slate-950 ${className}`}>{children}</SafeAreaView>;
}
