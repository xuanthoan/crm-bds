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
const listeners = new Set<() => void>();

function readState(): AuthState {
  const rawValue = window.localStorage.getItem(STORAGE_KEY);
  if (!rawValue) {
    return { accessToken: null, refreshToken: null, user: null };
  }

  try {
    return JSON.parse(rawValue) as AuthState;
  } catch {
    window.localStorage.removeItem(STORAGE_KEY);
    return { accessToken: null, refreshToken: null, user: null };
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
    state = { accessToken: null, refreshToken: null, user: null };
    window.localStorage.removeItem(STORAGE_KEY);
    emit();
  },
};

export function can(permissionCode: string): boolean {
  const user = authStore.getState().user;
  return Boolean(user?.is_superuser || user?.permissions.includes(permissionCode));
}
