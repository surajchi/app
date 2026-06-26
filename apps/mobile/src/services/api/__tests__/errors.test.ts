import { AxiosError } from 'axios';

import { extractErrorMessage } from '../errors';

describe('extractErrorMessage', () => {
  it('pulls the message from our API error envelope', () => {
    const error = new AxiosError('Request failed');
    // @ts-expect-error partial response shape for the test
    error.response = {
      data: { success: false, error: { code: 'AUTH', message: 'Invalid credentials.' } },
    };
    expect(extractErrorMessage(error)).toBe('Invalid credentials.');
  });

  it('falls back to the axios message when no envelope is present', () => {
    const error = new AxiosError('Network Error');
    expect(extractErrorMessage(error)).toBe('Network Error');
  });

  it('returns a generic message for unknown errors', () => {
    expect(extractErrorMessage({})).toBe('Something went wrong. Please try again.');
  });
});
