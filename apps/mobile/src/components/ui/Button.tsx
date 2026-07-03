import { ActivityIndicator, Pressable, Text } from 'react-native';

type Variant = 'primary' | 'secondary' | 'ghost';

const CONTAINER: Record<Variant, string> = {
  primary: 'bg-emerald-500 active:bg-emerald-600',
  secondary: 'bg-slate-800 active:bg-slate-700 border border-slate-700',
  ghost: 'bg-transparent active:bg-slate-800/60',
};
const LABEL: Record<Variant, string> = {
  primary: 'text-slate-950',
  secondary: 'text-slate-100',
  ghost: 'text-slate-300',
};

export function Button({
  title,
  onPress,
  loading = false,
  disabled = false,
  variant = 'primary',
  className = '',
}: {
  title: string;
  onPress?: () => void;
  loading?: boolean;
  disabled?: boolean;
  variant?: Variant;
  className?: string;
}) {
  const isDisabled = disabled || loading;
  return (
    <Pressable
      accessibilityRole="button"
      disabled={isDisabled}
      onPress={onPress}
      className={`items-center rounded-xl py-3 ${CONTAINER[variant]} ${isDisabled ? 'opacity-50' : ''} ${className}`}
    >
      {loading ? (
        <ActivityIndicator color={variant === 'primary' ? '#020617' : '#e2e8f0'} />
      ) : (
        <Text className={`text-base font-semibold ${LABEL[variant]}`}>{title}</Text>
      )}
    </Pressable>
  );
}
