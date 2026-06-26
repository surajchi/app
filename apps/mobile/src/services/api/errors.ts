import { AxiosError } from 'axios';
import type { ApiError } from '@finpulse/types';

/** Extract a human-readable message from an Axios error carrying our envelope. */
export function extractErrorMessage(error: unknown): string {
  const axiosError = error as AxiosError<ApiError>;
  const body = axiosError?.response?.data;
  if (body && body.success === false && body.error?.message) {
    return body.error.message;
  }
  if (axiosError?.message) {
    return axiosError.message;
  }
  return 'Something went wrong. Please try again.';
}
