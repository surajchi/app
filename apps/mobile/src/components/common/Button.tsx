import { ActivityIndicator, Pressable, Text } from 'react-native';

interface ButtonProps {
  title: string;
  onPress?: () => void;
  loading?: boolean;
  disabled?: boolean;
  variant?: 'primary' | 'ghost';
}

export function Button({
  title,
  onPress,
  loading = false,
  disabled = false,
  variant = 'primary',
}: ButtonProps) {
  const isDisabled = disabled || loading;
  const container =
    variant === 'primary'
      ? 'bg-brand-600 active:bg-brand-700'
      : 'bg-transparent active:bg-slate-100';
  const label = variant === 'primary' ? 'text-white' : 'text-brand-600';

  return (
    <Pressable
      accessibilityRole="button"
      disabled={isDisabled}
      onPress={onPress}
      className={`items-center rounded-xl py-3 ${container} ${isDisabled ? 'opacity-60' : ''}`}
    >
      {loading ? (
        <ActivityIndicator color={variant === 'primary' ? '#ffffff' : '#4f46e5'} />
      ) : (
        <Text className={`text-base font-semibold ${label}`}>{title}</Text>
      )}
    </Pressable>
  );
}
