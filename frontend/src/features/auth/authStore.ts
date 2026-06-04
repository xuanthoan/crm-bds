import { clearAccessToken, setAccessToken } from '../../services/apiClient';
import type { AuthUser } from './api';

const REFRESH_TOKEN_KEY = 'crm_bds_refresh_token';
const USER_KEY = 'crm_bds_current_user';

type Listener = () => void;
const listeners = new Set<Listener>();

function notify(): void {
  listeners.forEach((listener) => listener());
}

export function subscribeAuth(listener: Listener): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

export function getRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

export function getCurrentUser(): AuthUser | null {
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as AuthUser;
  } catch {
    return null;
  }
}

export function setSession(accessToken: string, refreshToken: string, user: AuthUser): void {
  setAccessToken(accessToken);
  localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
  notify();
}

export function clearSession(): void {
  clearAccessToken();
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
  notify();
}

export function isAuthenticated(): boolean {
  return Boolean(getCurrentUser());
}

export function can(permissionCode: string): boolean {
  const user = getCurrentUser();
  if (!user) return false;
  return user.is_superuser || user.permissions.includes(permissionCode);
}
