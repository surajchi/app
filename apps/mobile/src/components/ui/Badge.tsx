import { Text, View } from 'react-native';

export type BadgeVariant = 'default' | 'success' | 'danger' | 'warning' | 'secondary';

const VARIANTS: Record<BadgeVariant, { box: string; text: string }> = {
  default: { box: 'bg-slate-700/40', text: 'text-slate-200' },
  success: { box: 'bg-emerald-500/15', text: 'text-emerald-400' },
  danger: { box: 'bg-rose-500/15', text: 'text-rose-400' },
  warning: { box: 'bg-amber-500/15', text: 'text-amber-400' },
  secondary: { box: 'bg-slate-800', text: 'text-slate-300' },
};

export function Badge({
  label,
  variant = 'default',
  className = '',
}: {
  label: string;
  variant?: BadgeVariant;
  className?: string;
}) {
  const v = VARIANTS[variant];
  return (
    <View className={`self-start rounded-full px-2.5 py-0.5 ${v.box} ${className}`}>
      <Text className={`text-xs font-semibold ${v.text}`}>{label}</Text>
    </View>
  );
}
