/** Standard API envelope returned by the backend (see core/renderers.py). */

export interface ApiMeta {
  page?: number;
  page_size?: number;
  count?: number;
  next?: string | null;
  previous?: string | null;
}

export interface ApiSuccess<T> {
  success: true;
  data: T;
  meta?: ApiMeta;
}

export interface ApiErrorBody {
  code: string;
  message: string;
  details?: Record<string, unknown> | null;
}

export interface ApiError {
  success: false;
  error: ApiErrorBody;
}

export type ApiResponse<T> = ApiSuccess<T> | ApiError;
