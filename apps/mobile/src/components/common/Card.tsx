import type { PropsWithChildren } from 'react';
import { Pressable, View } from 'react-native';

interface CardProps {
  className?: string;
  onPress?: () => void;
}

export function Card({ children, className = '', onPress }: PropsWithChildren<CardProps>) {
  const classes = `rounded-2xl border border-slate-200 bg-white p-4 ${className}`;
  if (onPress) {
    return (
      <Pressable onPress={onPress} className={`${classes} active:bg-slate-50`}>
        {children}
      </Pressable>
    );
  }
  return <View className={classes}>{children}</View>;
}
