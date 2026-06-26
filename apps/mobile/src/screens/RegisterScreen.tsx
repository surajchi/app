import { zodResolver } from '@hookform/resolvers/zod';
import { useMutation } from '@tanstack/react-query';
import { useState } from 'react';
import { Controller, useForm } from 'react-hook-form';
import { Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { z } from 'zod';

import { Button } from '@/components/common/Button';
import { TextField } from '@/components/common/TextField';
import { authApi } from '@/services/api/auth';
import { extractErrorMessage } from '@/services/api/errors';
import { useAuthStore } from '@/store/authStore';
import type { RootScreenProps } from '@/navigation/types';

const schema = z.object({
  full_name: z.string().min(2, 'Enter your name'),
  email: z.string().email('Enter a valid email'),
  password: z.string().min(8, 'At least 8 characters'),
});

type RegisterForm = z.infer<typeof schema>;

export function RegisterScreen({ navigation }: RootScreenProps<'Register'>) {
  const setSession = useAuthStore((s) => s.setSession);
  const [serverError, setServerError] = useState<string | null>(null);

  const {
    control,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterForm>({
    resolver: zodResolver(schema),
    defaultValues: { full_name: '', email: '', password: '' },
  });

  const mutation = useMutation({
    mutationFn: (values: RegisterForm) => authApi.register(values),
    onSuccess: async (result) => {
      await setSession(result);
    },
    onError: (error) => setServerError(extractErrorMessage(error)),
  });

  const onSubmit = (values: RegisterForm) => {
    setServerError(null);
    mutation.mutate(values);
  };

  return (
    <SafeAreaView className="flex-1 bg-white">
      <View className="flex-1 justify-center px-6">
        <Text className="mb-1 text-3xl font-bold text-slate-900">Create account</Text>
        <Text className="mb-8 text-base text-slate-500">Start tracking the markets</Text>

        <Controller
          control={control}
          name="full_name"
          render={({ field: { value, onChange, onBlur } }) => (
            <TextField
              label="Full name"
              placeholder="Jane Doe"
              value={value}
              onChangeText={onChange}
              onBlur={onBlur}
              error={errors.full_name?.message}
            />
          )}
        />

        <Controller
          control={control}
          name="email"
          render={({ field: { value, onChange, onBlur } }) => (
            <TextField
              label="Email"
              autoCapitalize="none"
              autoComplete="email"
              keyboardType="email-address"
              placeholder="you@example.com"
              value={value}
              onChangeText={onChange}
              onBlur={onBlur}
              error={errors.email?.message}
            />
          )}
        />

        <Controller
          control={control}
          name="password"
          render={({ field: { value, onChange, onBlur } }) => (
            <TextField
              label="Password"
              secureTextEntry
              placeholder="••••••••"
              value={value}
              onChangeText={onChange}
              onBlur={onBlur}
              error={errors.password?.message}
            />
          )}
        />

        {serverError ? (
          <Text className="mb-3 text-sm text-red-500">{serverError}</Text>
        ) : null}

        <Button
          title="Create account"
          loading={mutation.isPending}
          onPress={handleSubmit(onSubmit)}
        />

        <View className="mt-4 flex-row justify-center">
          <Text className="text-slate-500">Already have an account? </Text>
          <Text
            className="font-semibold text-brand-600"
            onPress={() => navigation.navigate('Login')}
          >
            Log in
          </Text>
        </View>
      </View>
    </SafeAreaView>
  );
}
