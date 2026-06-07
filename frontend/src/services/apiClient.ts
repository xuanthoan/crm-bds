export type ApiResponse<T> = {
  success: boolean;
  message: string;
  data: T;
  meta: Record<string, unknown>;
};

type FastApiValidationError = {
  loc?: Array<string | number>;
  msg?: string;
  type?: string;
};

type ErrorPayload = {
  detail?: unknown;
  message?: unknown;
};

export class ApiRequestError extends Error {
  status: number;
  payload: unknown;

  constructor(status: number, payload: unknown) {
    const messages = formatApiErrorPayload(payload);
    super(messages.join('\n'));
    this.name = 'ApiRequestError';
    this.status = status;
    this.payload = payload;
  }
}

const API_BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';
const ACCESS_TOKEN_KEY = 'crm_bds_access_token';
const RAW_OBJECT_ERROR_MESSAGE = String({});

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null;
}

function normalizeValidationMessage(message: string): string {
  const withoutPrefix = message
    .replace(/^value error,\s*/i, '')
    .replace(/^assertion failed,\s*/i, '')
    .trim();

  if (/^input should be/i.test(withoutPrefix)) {
    return 'Dữ liệu không hợp lệ';
  }

  return withoutPrefix;
}

function translateMessage(message: string, validationError?: FastApiValidationError): string {
  const cleanedMessage = normalizeValidationMessage(message);
  const field = validationError?.loc?.map(String).join('.').toLowerCase() ?? '';
  const normalized = cleanedMessage.toLowerCase();

  if (cleanedMessage === 'Email already exists') {
    return 'Email đã tồn tại';
  }

  if (field.includes('password') && (normalized.includes('at least 8') || normalized.includes('min_length'))) {
    return 'Mật khẩu phải có ít nhất 8 ký tự';
  }

  if (normalized.includes('value is not a valid email') || normalized.includes('valid email')) {
    return 'Email không hợp lệ';
  }

  if (normalized.includes('field required') || normalized.includes('missing')) {
    const lastField = validationError?.loc?.[validationError.loc.length - 1];
    return lastField ? `${String(lastField)} là bắt buộc` : 'Thiếu thông tin bắt buộc';
  }

  return cleanedMessage;
}

function formatApiErrorPayload(payload: unknown): string[] {
  if (!isRecord(payload)) {
    return typeof payload === 'string' ? [payload] : [];
  }

  const detail = (payload as ErrorPayload).detail;
  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) => {
        if (!isRecord(item)) return null;
        const validationError = item as FastApiValidationError;
        return validationError.msg ? translateMessage(validationError.msg, validationError) : null;
      })
      .filter((message): message is string => Boolean(message));
    return messages.length ? messages : ['Dữ liệu không hợp lệ'];
  }

  if (typeof detail === 'string') {
    return [translateMessage(detail)];
  }

  const message = (payload as ErrorPayload).message;
  if (typeof message === 'string') {
    return [translateMessage(message)];
  }

  return [];
}

export function formatApiError(error: unknown, fallback = 'Đã có lỗi xảy ra.'): string[] {
  if (error instanceof ApiRequestError) {
    const messages = formatApiErrorPayload(error.payload);
    return messages.length ? messages : [fallback];
  }

  if (isRecord(error)) {
    const messages = formatApiErrorPayload(error);
    if (messages.length) return messages;
  }

  if (error instanceof Error) {
    return error.message && error.message !== RAW_OBJECT_ERROR_MESSAGE ? [translateMessage(error.message)] : [fallback];
  }

  if (typeof error === 'string') {
    return [translateMessage(error)];
  }

  return [fallback];
}

export function getAccessToken(): string | null {
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function setAccessToken(token: string): void {
  localStorage.setItem(ACCESS_TOKEN_KEY, token);
}

export function clearAccessToken(): void {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
}

export async function apiRequest<T>(path: string, options: RequestInit = {}): Promise<ApiResponse<T>> {
  const headers = new Headers(options.headers);
  headers.set('Content-Type', 'application/json');

  const token = getAccessToken();
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      headers,
    });
  } catch (error) {
    throw new ApiRequestError(0, { detail: error instanceof Error ? error.message : 'Không thể kết nối máy chủ' });
  }

  const payload = (await response.json().catch(() => ({ detail: 'Unexpected API response' }))) as ApiResponse<T> | ErrorPayload;

  if (response.status === 401) {
    clearAccessToken();
    localStorage.removeItem('crm_bds_refresh_token');
    localStorage.removeItem('crm_bds_current_user');
    if (window.location.pathname !== '/login') {
      window.location.assign('/login');
    }
  }

  if (!response.ok) {
    throw new ApiRequestError(response.status, payload);
  }

  return payload as ApiResponse<T>;
}
