import { forwardRef } from 'react';
import { Text, TextInput, type TextInputProps, View } from 'react-native';

interface TextFieldProps extends TextInputProps {
  label?: string;
  error?: string;
}

export const TextField = forwardRef<TextInput, TextFieldProps>(function TextField(
  { label, error, ...props },
  ref
) {
  return (
    <View className="mb-4">
      {label ? (
        <Text className="mb-1 text-sm font-medium text-slate-700">{label}</Text>
      ) : null}
      <TextInput
        ref={ref}
        placeholderTextColor="#94a3b8"
        className={`rounded-xl border px-4 py-3 text-base text-slate-900 ${
          error ? 'border-red-500' : 'border-slate-300'
        }`}
        {...props}
      />
      {error ? <Text className="mt-1 text-xs text-red-500">{error}</Text> : null}
    </View>
  );
});
