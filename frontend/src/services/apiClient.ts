export type ApiResponse<T> = {
  success: boolean;
  message: string;
  data: T;
  meta: Record<string, unknown>;
};

const API_BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';
const ACCESS_TOKEN_KEY = 'crm_bds_access_token';

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

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  });

  const payload = (await response.json().catch(() => ({ detail: 'Unexpected API response' }))) as
    | ApiResponse<T>
    | { detail?: string };

  if (response.status === 401) {
    clearAccessToken();
    localStorage.removeItem('crm_bds_refresh_token');
    localStorage.removeItem('crm_bds_current_user');
    if (window.location.pathname !== '/login') {
      window.location.assign('/login');
    }
  }

  if (!response.ok) {
    const message = 'detail' in payload ? payload.detail : 'Request failed';
    throw new Error(message ?? 'Request failed');
  }

  return payload as ApiResponse<T>;
}
