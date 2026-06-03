import { useSyncExternalStore } from 'react';

export type CurrentUser = {
  id: string;
  email: string;
  full_name: string;
  status: string;
  roles: string[];
  permissions: string[];
  is_superuser: boolean;
};

type AuthState = {
  accessToken: string | null;
  refreshToken: string | null;
  user: CurrentUser | null;
};

const STORAGE_KEY = 'crm_bds_auth';
const emptyState: AuthState = { accessToken: null, refreshToken: null, user: null };
const listeners = new Set<() => void>();

function readState(): AuthState {
  const rawValue = window.localStorage.getItem(STORAGE_KEY);
  if (!rawValue) {
    return emptyState;
  }

  try {
    return JSON.parse(rawValue) as AuthState;
  } catch {
    window.localStorage.removeItem(STORAGE_KEY);
    return emptyState;
  }
}

let state: AuthState = readState();

function emit() {
  listeners.forEach((listener) => listener());
}

export const authStore = {
  getState: () => state,
  subscribe: (listener: () => void) => {
    listeners.add(listener);
    return () => listeners.delete(listener);
  },
  setAuth: (nextState: AuthState) => {
    state = nextState;
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    emit();
  },
  clear: () => {
    state = emptyState;
    window.localStorage.removeItem(STORAGE_KEY);
    emit();
  },
};

export function useAuth(): AuthState {
  return useSyncExternalStore(authStore.subscribe, authStore.getState, authStore.getState);
}

export function can(permissionCode: string, user: CurrentUser | null = authStore.getState().user): boolean {
  return Boolean(user?.is_superuser || user?.permissions.includes(permissionCode));
}
