import type { PropsWithChildren } from 'react';
import { Pressable, View } from 'react-native';

interface CardProps {
  className?: string;
  onPress?: () => void;
}

export function Card({ children, className = '', onPress }: PropsWithChildren<CardProps>) {
  const base = `rounded-2xl border border-slate-800 bg-slate-900 p-4 ${className}`;
  if (onPress) {
    return (
      <Pressable onPress={onPress} className={`${base} active:bg-slate-800/60`}>
        {children}
      </Pressable>
    );
  }
  return <View className={base}>{children}</View>;
}
